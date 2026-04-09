#!/usr/bin/env python3
"""
公众号草稿管理 - 每天检查并自动补稿

如果草稿少于3篇，自动从AI热点生成新文章并发布到草稿箱
"""

import sys
import os
from pathlib import Path
import subprocess

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from check_draft_count import count_drafts

def main():
    print("=== 公众号草稿管理 ===\n")
    
    # 1. 检查草稿数量
    print("📊 检查草稿数量...")
    count = count_drafts()
    if count < 0:
        print("❌ 无法获取草稿数量")
        sys.exit(1)
    
    print(f"   当前草稿: {count} 篇\n")
    
    # 2. 如果少于3篇，自动补稿
    if count < 3:
        need = 3 - count
        print(f"⚠️  草稿不足，需要补 {need} 篇\n")
        
        for i in range(need):
            print(f"--- 补稿 {i+1}/{need} ---")
            result = subprocess.run(
                ["python3", str(script_dir / "auto_fill_drafts.py")],
                capture_output=False
            )
            if result.returncode != 0:
                print(f"❌ 补稿 {i+1} 失败")
            else:
                print(f"✅ 补稿 {i+1} 完成\n")
    else:
        print("✅ 草稿充足，无需补稿")

if __name__ == "__main__":
    main()
