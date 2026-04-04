#!/usr/bin/env python3
"""
获取微信公众号文章数据（阅读量、分享量等）

使用方法:
    python get_article_stats.py
"""

import os
import json
import re
import urllib.request
from pathlib import Path


def read_config():
    """从项目 .env 文件读取 API 配置"""
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
            return {
                "appid": config["WECHAT_APPID"],
                "secret": config["WECHAT_SECRET"]
            }
    
    print("❌ 错误: 配置文件不存在")
    sys.exit(1)


def get_access_token(appid: str, secret: str) -> str:
    """获取微信 Access Token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())
    
    if "access_token" not in data:
        print(f"❌ 无法获取 Access Token: {data}")
        sys.exit(1)
    
    return data["access_token"]


def get_article_list(access_token: str, offset: int = 0, count: int = 20):
    """获取已发布的文章列表（永久素材）"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={access_token}"
    
    payload = {
        "type": "news",
        "offset": offset,
        "count": count
    }
    
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
    
    if "errcode" in result and result["errcode"] != 0:
        print(f"❌ 获取文章列表失败: {result}")
        return None
    
    return result


def get_article_stats(access_token: str, begin_date: str, end_date: str):
    """获取文章统计数据（阅读量、分享量等）
    
    需要用户已开通"数据统计"权限
    https://developers.weixin.qq.com/doc/offiaccount/Data_Service/get_article_summary.html
    """
    url = f"https://api.weixin.qq.com/datacube/getarticlesummary?access_token={access_token}"
    
    payload = {
        "begin_date": begin_date,
        "end_date": end_date
    }
    
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
    
    if "errcode" in result and result["errcode"] != 0:
        if result["errcode"] == 61501:
            print(f"⚠️  API 权限不足，需要先开通数据统计权限")
        else:
            print(f"❌ 获取统计数据失败: {result}")
        return None
    
    return result


def main():
    # 读取配置
    print("⚙️  读取配置...")
    config = read_config()
    
    # 获取 Access Token
    print("🔑 获取 Access Token...")
    access_token = get_access_token(config["appid"], config["secret"])
    print(f"   ✅ Token: {access_token[:20]}...")
    
    # 方法1: 获取已发布的文章列表（永久素材）
    print("\n📋 获取已发布文章列表...")
    article_list = get_article_list(access_token, offset=0, count=20)
    
    if article_list:
        print(f"\n找到 {article_list.get('total_count', 0)} 篇文章\n")
        for i, item in enumerate(article_list.get("item", []), 1):
            content = item.get("content", {})
            news_items = content.get("news_item", [])
            for news in news_items:
                title = news.get("title", "")
                url = news.get("url", "")
                digest = news.get("digest", "")
                print(f"  {i}. {title}")
                print(f"     {url}")
                print(f"     {digest[:50] if digest else ''}")
                print()
    
    # 方法2: 获取文章统计数据（最近7天）
    from datetime import datetime, timedelta
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    begin_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"\n📊 获取文章统计数据（{begin_date} 到 {end_date}）...")
    stats = get_article_stats(access_token, begin_date, end_date)
    
    if stats:
        articles = stats.get("list", [])
        if articles:
            print(f"\n找到 {len(articles)} 条统计数据\n")
            for article in sorted(articles, key=lambda x: x.get("int_page_read_count", 0), reverse=True):
                title = article.get("title", "")
                read_count = article.get("int_page_read_count", 0)
                share_count = article.get("share_count", 0)
                fav_count = article.get("add_to_fav_count", 0)
                date = article.get("ref_date", "")
                print(f"  📅 {date}")
                print(f"  📝 {title}")
                print(f"  👁 阅读: {read_count}  分享: {share_count}  收藏: {fav_count}")
                print()
        else:
            print("  没有找到统计数据（可能需要更长时间范围，或该日期范围内无文章发布）")


if __name__ == "__main__":
    main()
