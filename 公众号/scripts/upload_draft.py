#!/usr/bin/env python3
"""
微信公众号草稿上传脚本

用法: python upload_draft.py <文章目录> <标题> [摘要]

去重策略：先拉所有草稿列表，把同标题的旧草稿全部删除，再建新草稿。
"""

import json
import sys
import subprocess
import urllib.request
from pathlib import Path

import markdown


def read_config():
    script_dir = Path(__file__).parent.parent
    env_path = script_dir / ".env"
    if env_path.exists():
        env_content = env_path.read_text()
        config = {}
        for line in env_content.strip().split("\n"):
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
        if "WECHAT_APPID" in config and "WECHAT_SECRET" in config:
            return config["WECHAT_APPID"], config["WECHAT_SECRET"]
    print("❌ 错误: 配置文件不存在")
    sys.exit(1)


def get_access_token(appid, secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())
    if "access_token" not in data:
        print(f"❌ 无法获取 Access Token: {data}")
        sys.exit(1)
    return data["access_token"]


def list_drafts(access_token):
    """获取所有草稿列表"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
    body = json.dumps({"offset": 0, "count": 50, "no_content": 1}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def delete_draft(access_token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/delete?access_token={access_token}"
    body = json.dumps({"media_id": media_id}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def svg_to_png(svg_path, png_path):
    try:
        subprocess.run(["rsvg-convert", "-o", str(png_path), str(svg_path)], check=True, capture_output=True)
    except FileNotFoundError:
        print("❌ rsvg-convert 未安装: brew install librsvg")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ SVG 转换失败: {e.stderr.decode()}")
        sys.exit(1)


def upload_image(access_token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(image_path, "rb") as f:
        image_data = f.read()
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"media\"; filename=\"{image_path.name}\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    if "media_id" not in data:
        print(f"❌ 封面上传失败: {data}")
        sys.exit(1)
    return data["media_id"]


def upload_illustrations(access_token, md_path, article_dir):
    """找到 markdown 中的本地 SVG 引用，转 PNG → 上传 → 返回替换映射"""
    import re
    content = md_path.read_text()
    url_map = {}
    temp_pngs = []
    for match in re.finditer(r'!\[.*?\]\((\.\./.+?\.svg)\)', content):
        svg_rel = match.group(1)
        svg_path = (md_path.parent / svg_rel).resolve()
        if not svg_path.exists():
            print(f"   ⚠️  SVG 不存在，跳过: {svg_path}")
            continue
        png_path = svg_path.with_suffix('.png')
        print(f"   🖼️  {svg_path.name} → PNG → 上传...")
        svg_to_png(svg_path, png_path)
        temp_pngs.append(png_path)
        result = upload_image_file(access_token, png_path)
        url_map[svg_rel] = result
    # 清理临时 PNG
    for p in temp_pngs:
        p.unlink(missing_ok=True)
    return url_map


def upload_image_file(access_token, image_path):
    """上传图片并返回 URL"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(image_path, "rb") as f:
        image_data = f.read()
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"media\"; filename=\"{image_path.name}\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    if "url" not in data:
        print(f"   ❌ 插图上传失败: {data}")
        return None
    return data["url"]


def markdown_to_html(md_path, illustration_urls=None):
    content = md_path.read_text()
    # 替换本地 SVG 引用为微信图片 URL
    if illustration_urls:
        import re
        for svg_rel, wx_url in illustration_urls.items():
            if wx_url:
                content = content.replace(
                    f"![](../{svg_rel.lstrip('../')})",
                    f"![]({wx_url})"
                ).replace(
                    f"![]({svg_rel})",
                    f"![]({wx_url})"
                )
    html_content = markdown.markdown(content, extensions=["tables", "fenced_code"])
    style_map = {
        "<h1>": '<h1 style="font-size: 22px; font-weight: bold; margin: 25px 0 15px 0;">',
        "<h2>": '<h2 style="font-size: 18px; font-weight: bold; margin: 20px 0 12px 0;">',
        "<h3>": '<h3 style="font-size: 16px; font-weight: bold; margin: 15px 0 10px 0;">',
        "<p>": '<p style="margin-bottom: 1.5em; line-height: 1.8;">',
        "<hr>": '<hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">',
        "<hr/>": '<hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">',
        "<table>": '<table style="width: 100%; margin-bottom: 1em; border-collapse: collapse;">',
        "<th>": '<th style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;">',
        "<td>": '<td style="padding: 8px; border: 1px solid #ddd;">',
    }
    for old, new in style_map.items():
        html_content = html_content.replace(old, new)
    html_content = html_content.replace("<ul>", "").replace("</ul>", "")
    html_content = html_content.replace("<li>", '<p style="margin-bottom: 0.5em; line-height: 1.8;">• ')
    html_content = html_content.replace("</li>", "</p>")
    return html_content


def create_draft(access_token, title, digest, content, thumb_media_id):
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
    body = json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
    if "media_id" not in result:
        print(f"❌ 草稿创建失败: {result}")
        sys.exit(1)
    return result["media_id"]


def main():
    if len(sys.argv) < 3:
        print("用法: python upload_draft.py <文章目录> <标题> [摘要]")
        sys.exit(1)

    article_dir = Path(sys.argv[1]).expanduser()
    title = sys.argv[2]
    digest = sys.argv[3] if len(sys.argv) > 3 else "点击查看全文..."

    if not article_dir.exists():
        print(f"❌ 目录不存在: {article_dir}")
        sys.exit(1)

    article_path = article_dir / "draft" / "article.md"
    if not article_path.exists():
        print(f"❌ 文章不存在: {article_path}")
        sys.exit(1)

    # 获取 token
    print("⚙️  读取配置...")
    appid, secret = read_config()
    print("🔑 获取 Access Token...")
    access_token = get_access_token(appid, secret)
    print(f"   ✅ Token: {access_token[:20]}...")

    # 拉所有草稿，按标题精准删除旧的
    print("🔍 检查同标题旧草稿...")
    drafts = list_drafts(access_token)
    deleted = 0
    for item in drafts.get("item", []):
        news_items = item.get("content", {}).get("news_item", [])
        for news in news_items:
            if news.get("title") == title:
                mid = item.get("media_id")
                print(f"   🗑️  删除: {title}")
                delete_draft(access_token, mid)
                deleted += 1
    if deleted == 0:
        print("   ✅ 无旧草稿")
    else:
        print(f"   ✅ 已删除 {deleted} 篇旧草稿")

    # 封面
    png_path = article_dir / "cover.png"
    svg_path = article_dir / "cover.svg"
    if not png_path.exists():
        if svg_path.exists():
            print("🖼️  SVG 转 PNG...")
            svg_to_png(svg_path, png_path)
        else:
            print(f"❌ 找不到封面文件")
            sys.exit(1)

    print("📤 上传封面...")
    thumb_media_id = upload_image(access_token, png_path)

    print("📝 转换文章内容...")
    # 上传插图并获取 URL 映射
    print("🖼️  处理插图...")
    illustration_urls = upload_illustrations(access_token, article_path, article_dir)
    if illustration_urls:
        print(f"   ✅ 已上传 {len(illustration_urls)} 张插图")
    else:
        print("   ℹ️  无本地插图引用")
    content = markdown_to_html(article_path, illustration_urls)

    print("📤 建草稿...")
    draft_media_id = create_draft(access_token, title, digest, content, thumb_media_id)
    print(f"   ✅ Draft ID: {draft_media_id[:20]}...")

    # 保存 media_id（供下次直接使用，但主要去重靠标题匹配）
    draft_id_file = article_dir / ".draft_id"
    draft_id_file.write_text(draft_media_id)

    if png_path.exists():
        png_path.unlink(missing_ok=True)

    print("")
    print("✅ 草稿创建成功！")


if __name__ == "__main__":
    main()
