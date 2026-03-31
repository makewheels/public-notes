#!/usr/bin/env python3
"""
微信公众号草稿上传脚本

使用方法:
    python upload_draft.py <文章目录> <标题> [摘要]

示例:
    python upload_draft.py ~/Documents/public-notes/公众号/2026-04-02-ai-impact-gap \
        "程序员慌了，CAD工程师为什么不慌？" \
        "为什么同样是数字化工作者..."

依赖:
    pip install markdown
    brew install librsvg  # macOS，用于 SVG 转 PNG
"""

import os
import re
import sys
import json
import subprocess
import urllib.request
from pathlib import Path

import markdown


def read_config():
    """从项目 .env 文件读取 API 配置"""
    # 优先从项目目录读取
    script_dir = Path(__file__).parent.parent  # 脚本在 scripts/，项目根目录是上一级
    env_path = script_dir / ".env"
    
    if env_path.exists():
        # 解析 .env 文件
        env_content = env_path.read_text()
        config = {}
        for line in env_content.strip().split("\n"):
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
        
        if "WECHAT_APPID" in config and "WECHAT_SECRET" in config:
            return {
                "appid": config["WECHAT_APPID"],
                "secret": config["WECHAT_SECRET"]
            }
    
    # 兼容旧配置位置
    config_path = Path.home() / ".openclaw" / "workspace" / "WECHAT_CONFIG.md"
    if config_path.exists():
        content = config_path.read_text()
        appid_match = re.search(r"AppID:\s*(\S+)", content)
        secret_match = re.search(r"AppSecret:\s*(\S+)", content)
        if appid_match and secret_match:
            return {
                "appid": appid_match.group(1),
                "secret": secret_match.group(1)
            }
    
    print("❌ 错误: 配置文件不存在")
    print(f"   请在项目目录创建 .env 文件")
    sys.exit(1)


def get_access_token(appid: str, secret: str) -> str:
    """获取微信 Access Token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())
    
    if "access_token" not in data:
        print("❌ 错误: 无法获取 Access Token")
        print(f"   响应: {data}")
        sys.exit(1)
    
    return data["access_token"]


def svg_to_png(svg_path: Path, png_path: Path):
    """SVG 转 PNG（调用 rsvg-convert）"""
    try:
        subprocess.run(
            ["rsvg-convert", "-o", str(png_path), str(svg_path)],
            check=True,
            capture_output=True
        )
    except FileNotFoundError:
        print("❌ 错误: rsvg-convert 未安装")
        print("   安装: brew install librsvg")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("❌ SVG 转换失败")
        print(f"   错误: {e.stderr.decode()}")
        sys.exit(1)


def upload_image(access_token: str, image_path: Path) -> str:
    """上传图片到永久素材，返回 media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = image_path.name
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"media\"; filename=\"{filename}\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    
    if "media_id" not in data:
        print("❌ 封面上传失败")
        print(f"   响应: {data}")
        sys.exit(1)
    
    return data["media_id"]


def markdown_to_html(md_path: Path) -> str:
    """Markdown 转 HTML（使用 markdown 库）"""
    content = md_path.read_text()
    
    # 使用 markdown 库转换
    html_content = markdown.markdown(
        content,
        extensions=["tables", "fenced_code"]
    )
    
    # 公众号样式映射
    style_map = {
        "<h1>": "<h1 style=\"font-size: 22px; font-weight: bold; margin: 25px 0 15px 0;\">",
        "</h1>": "</h1>",
        "<h2>": "<h2 style=\"font-size: 18px; font-weight: bold; margin: 20px 0 12px 0;\">",
        "</h2>": "</h2>",
        "<h3>": "<h3 style=\"font-size: 16px; font-weight: bold; margin: 15px 0 10px 0;\">",
        "</h3>": "</h3>",
        "<p>": "<p style=\"margin-bottom: 1.5em; line-height: 1.8;\">",
        "</p>": "</p>",
        "<hr>": "<hr style=\"margin: 20px 0; border: none; border-top: 1px solid #eee;\">",
        "<hr/>": "<hr style=\"margin: 20px 0; border: none; border-top: 1px solid #eee;\">",
        "<table>": "<table style=\"width: 100%; margin-bottom: 1em; border-collapse: collapse;\">",
        "<th>": "<th style=\"padding: 8px; border: 1px solid #ddd; background: #f5f5f5;\">",
        "<td>": "<td style=\"padding: 8px; border: 1px solid #ddd;\">",
    }
    
    for old, new in style_map.items():
        html_content = html_content.replace(old, new)
    
    # 处理列表：把 <ul><li> 转成 <p>• xxx</p>，避免公众号双重圆点
    html_content = html_content.replace("<ul>", "")
    html_content = html_content.replace("</ul>", "")
    html_content = html_content.replace("<li>", "<p style=\"margin-bottom: 0.5em; line-height: 1.8;\">• ")
    html_content = html_content.replace("</li>", "</p>")
    
    return html_content


def create_draft(access_token: str, title: str, digest: str, content: str, thumb_media_id: str) -> str:
    """创建草稿，返回 draft media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    
    payload = {
        "articles": [{
            "title": title,
            "author": "",
            "digest": digest,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }]
    }
    
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
    
    if "media_id" not in result:
        print("❌ 草稿创建失败")
        print(f"   响应: {result}")
        sys.exit(1)
    
    return result["media_id"]


def delete_duplicate_drafts(access_token: str, title: str):
    """删除同标题的旧草稿（去重）"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
    data = json.dumps({"offset": 0, "count": 20, "no_content": 1}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
    
    # 找到同标题的旧草稿
    for item in result.get("item", []):
        for news in item.get("content", {}).get("news_item", []):
            if news.get("title") == title:
                media_id = item.get("media_id")
                # 删除旧草稿
                del_url = f"https://api.weixin.qq.com/cgi-bin/draft/delete?access_token={access_token}"
                del_data = json.dumps({"media_id": media_id}).encode()
                del_req = urllib.request.Request(del_url, data=del_data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(del_req) as del_resp:
                    print(f"   🗑️  已删除旧草稿")
                return


def main():
    if len(sys.argv) < 3:
        print("用法: python upload_draft.py <文章目录> <标题> [摘要]")
        print("")
        print("示例:")
        print("  python upload_draft.py articles/2026-04-02-ai-impact-gap \\")
        print("    '程序员慌了，CAD工程师为什么不慌？' \\")
        print("    '为什么同样是数字化工作者...'")
        sys.exit(1)
    
    article_dir = Path(sys.argv[1]).expanduser()
    title = sys.argv[2]
    digest = sys.argv[3] if len(sys.argv) > 3 else "点击查看全文..."
    
    # 检查目录
    if not article_dir.exists():
        print(f"❌ 错误: 目录不存在 {article_dir}")
        sys.exit(1)
    
    article_path = article_dir / "draft" / "article.md"
    if not article_path.exists():
        print(f"❌ 错误: 文章不存在 {article_path}")
        sys.exit(1)
    
    # 读取配置
    print("⚙️  读取 API 配置...")
    config = read_config()
    
    # 获取 Access Token
    print("🔑 获取 Access Token...")
    access_token = get_access_token(config["appid"], config["secret"])
    print(f"   ✅ Token: {access_token[:20]}...")
    
    # 检查并删除同标题的旧草稿（去重）
    print("🔍 检查重复草稿...")
    delete_duplicate_drafts(access_token, title)
    
    # 检查/生成封面
    png_path = article_dir / "cover.png"
    svg_path = article_dir / "cover.svg"
    
    if not png_path.exists():
        if svg_path.exists():
            print("🖼️  SVG 转 PNG...")
            svg_to_png(svg_path, png_path)
        else:
            print(f"❌ 错误: 找不到封面文件")
            sys.exit(1)
    
    # 上传封面
    print("📤 上传封面...")
    thumb_media_id = upload_image(access_token, png_path)
    print(f"   ✅ Media ID: {thumb_media_id[:20]}...")
    
    # Markdown 转 HTML（用 markdown 库）
    print("📝 转换文章内容...")
    content = markdown_to_html(article_path)
    
    # 创建草稿
    print("📤 创建草稿...")
    draft_media_id = create_draft(access_token, title, digest, content, thumb_media_id)
    print(f"   ✅ Draft ID: {draft_media_id[:20]}...")
    
    # 清理 PNG
    if png_path.exists():
        png_path.unlink()
        print("🧹 已删除临时 PNG")
    
    print("")
    print("✅ 草稿创建成功！请前往公众号后台查看并定时发布")


if __name__ == "__main__":
    main()