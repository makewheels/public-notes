#!/usr/bin/env python3
"""上传单张图片到公众号素材库"""
import os
import sys
import json
import urllib.request
from pathlib import Path
import re

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
            return {"appid": config["WECHAT_APPID"], "secret": config["WECHAT_SECRET"]}
    sys.exit(1)

def get_access_token(appid, secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())["access_token"]

def upload_image(access_token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = image_path.name
    with open(image_path, "rb") as f:
        image_data = f.read()
    body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"{filename}\"\r\nContent-Type: image/png\r\n\r\n".encode() + image_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python upload_image.py <图片路径>")
        sys.exit(1)
    image_path = Path(sys.argv[1]).expanduser()
    config = read_config()
    token = get_access_token(config["appid"], config["secret"])
    result = upload_image(token, image_path)
    print(json.dumps(result, ensure_ascii=False))
