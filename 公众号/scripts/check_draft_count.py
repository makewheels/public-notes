#!/usr/bin/env python3
"""
检查公众号草稿数量，如果少于3篇则自动补稿
"""

import json
import sys
import os
import urllib.request
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        return None
    return data["access_token"]

def list_drafts(access_token):
    """获取所有草稿列表"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
    body = json.dumps({"offset": 0, "count": 50, "no_content": 1}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"❌ 获取草稿列表失败: {e}")
        return None

def count_drafts():
    """统计草稿数量"""
    appid, secret = read_config()
    access_token = get_access_token(appid, secret)
    if not access_token:
        return -1
    
    drafts = list_drafts(access_token)
    if not drafts:
        return -1
    
    count = len(drafts.get("item", []))
    return count

def main():
    count = count_drafts()
    if count < 0:
        print("❌ 无法获取草稿数量")
        sys.exit(1)
    
    print(f"当前草稿数量: {count}")
    
    if count < 3:
        print(f"⚠️  草稿少于3篇，需要补 {3 - count} 篇")
        # 返回需要补稿的数量，供调用者使用
        print(f"NEED_AUTO_POST: {3 - count}")
    else:
        print("✅ 草稿充足，无需补稿")

if __name__ == "__main__":
    main()
