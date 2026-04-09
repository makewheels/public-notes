#!/usr/bin/env python3
"""
自动补稿脚本 - 当草稿少于3篇时，自动生成并发布一篇AI热点文章

流程：
1. 从 Anthropic/OpenAI Engineering 抓最新文章
2. 调用 AI 写一篇公众号风格的文章
3. 生成封面
4. 上传到草稿箱
"""

import json
import sys
import os
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.upload_draft import get_access_token, read_config, create_draft, upload_image


def fetch_anthropic_latest():
    """获取 Anthropic Engineering 最新文章"""
    url = "https://www.anthropic.com/engineering"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8')
        
        import re
        hrefs = re.findall(r'href="(/engineering/[^"]+)"', html)
        articles = []
        seen = set()
        for href in hrefs[:5]:  # 只取前5篇
            full_url = 'https://www.anthropic.com' + href
            if full_url not in seen:
                seen.add(full_url)
                slug = href.replace('/engineering/', '').replace('-', ' ').title()
                articles.append({"title": slug, "url": full_url})
        return articles
    except Exception as e:
        print(f"获取 Anthropic 文章失败: {e}")
        return []


def fetch_openai_latest():
    """获取 OpenAI 最新发布"""
    url = "https://openai.com/index/"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8')
        
        import re
        hrefs = re.findall(r'href="(/index/[^"]+)"', html)
        articles = []
        seen = set()
        for href in hrefs[:5]:
            full_url = 'https://openai.com' + href
            if full_url not in seen:
                seen.add(full_url)
                slug = href.replace('/index/', '').replace('-', ' ').title()
                articles.append({"title": slug, "url": full_url})
        return articles
    except Exception as e:
        print(f"获取 OpenAI 文章失败: {e}")
        return []


def generate_article(topic_title, topic_url):
    """调用 AI 生成公众号文章"""
    prompt = f"""写一篇公众号文章，主题是关于这个AI领域的最新动态：{topic_title}
原文链接：{topic_url}

要求：
1. 文章开头加引用块，包含原文链接
2. 用通俗易懂的语言解释技术内容
3. 加入自己的深度思考和观点
4. 文章长度 1500-2500 字
5. 风格理性、有洞察力，类似刘润的写作风格
6. 不要写标题（公众号后台已有标题字段）
7. 段落清晰，适当使用小标题

直接输出文章内容，不要有任何 Markdown 代码块标记。"""

    # 使用 OpenClaw 的 AI 能力生成文章
    # 这里简化处理，实际应该调用 sessions_spawn 或类似机制
    print(f"正在生成文章...")
    print(f"主题: {topic_title}")
    
    # 临时方案：返回一个占位文章
    article_content = f"""> 引用：[{topic_title}]({topic_url})

## 引言

{topic_title} 是近期 AI 领域的一个重要动态。让我们一起来深入探讨这个话题。

## 背景

（这里需要 AI 生成具体内容...）

## 深度分析

（这里需要 AI 生成深度分析...）

## 我的观点

（这里需要 AI 生成个人观点...）

## 结语

这个变化对行业意味着什么？值得我们持续关注。
"""
    return article_content


def create_article_dir(title):
    """创建文章目录结构"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    # 简化标题作为目录名
    safe_title = title.replace(" ", "-").replace("/", "-")[:50]
    dir_name = f"{date_str}-{safe_title}"
    
    base_dir = Path(__file__).parent.parent / "articles" / dir_name
    draft_dir = base_dir / "draft"
    draft_dir.mkdir(parents=True, exist_ok=True)
    
    return base_dir, draft_dir


def main():
    print("=== 自动补稿脚本 ===\n")
    
    # 1. 获取热点话题
    print("🔍 获取 AI 热点...")
    anthropic = fetch_anthropic_latest()
    openai = fetch_openai_latest()
    
    all_topics = anthropic + openai
    if not all_topics:
        print("❌ 无法获取热点话题")
        sys.exit(1)
    
    # 取第一个话题
    topic = all_topics[0]
    print(f"   选中话题: {topic['title']}")
    
    # 2. 生成文章
    print("\n✍️  生成文章...")
    content = generate_article(topic['title'], topic['url'])
    
    # 3. 创建目录结构
    base_dir, draft_dir = create_article_dir(topic['title'])
    article_path = draft_dir / "article.md"
    article_path.write_text(content, encoding='utf-8')
    print(f"   文章已保存: {article_path}")
    
    # 4. 生成简单封面（用纯色背景+文字）
    cover_path = base_dir / "cover.png"
    print(f"   生成封面...")
    # 这里简化：用一个占位封面，实际应该用 AI 生成
    # 创建一个 900x383 的纯色 PNG
    subprocess.run([
        "convert", "-size", "900x383", "xc:#1a1a2e",
        "-fill", "white", "-pointsize", "48",
        "-gravity", "center",
        topic['title'][:30],
        str(cover_path)
    ], capture_output=True)
    
    if not cover_path.exists():
        print("   ⚠️ ImageMagick 不可用，使用默认封面")
        # 复制一个默认封面
        default_cover = Path(__file__).parent.parent / "assets" / "default_cover.png"
        if default_cover.exists():
            import shutil
            shutil.copy(default_cover, cover_path)
    
    # 5. 上传草稿
    print("\n📤 上传草稿...")
    appid, secret = read_config()
    access_token = get_access_token(appid, secret)
    if not access_token:
        sys.exit(1)
    
    # 调用现有的 upload_draft 逻辑
    title = f"AI动态：{topic['title'][:40]}"
    digest = "点击查看最新文章分析..."
    
    # 读取文章 HTML
    import markdown
    html_content = markdown.markdown(content, extensions=["tables", "fenced_code"])
    
    # 上传封面
    thumb_media_id = upload_image(access_token, cover_path)
    
    # 创建草稿
    draft_media_id = create_draft(access_token, title, digest, html_content, thumb_media_id)
    
    print(f"\n✅ 补稿完成！")
    print(f"   标题: {title}")
    print(f"   Draft ID: {draft_media_id[:20]}...")
    print(f"   目录: {base_dir}")


if __name__ == "__main__":
    main()
