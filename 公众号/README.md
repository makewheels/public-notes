# 微信公众号文章管理

## 项目结构

```
公众号/
├── .env                    # API 密钥
├── scripts/                # 脚本
│   └── upload_draft.py    # 上传草稿
├── docs/                   # 文档
│   ├── 写作指南.md
│   ├── 发布工作流.md
│   └── 封面生成指南.md
└── articles/               # 文章
    └── YYYY-MM-DD-标题/
        ├── draft/         # 草稿
        │   └── article.md
        ├── published/     # 发布后
        └── cover.svg      # 封面
```

## 快速开始

### 1. 配置密钥

创建 `.env` 文件：
```
WECHAT_APPID=你的AppID
WECHAT_SECRET=你的AppSecret
```

### 2. 安装依赖

```bash
python3 -m venv .venv
.venv/bin/pip install markdown
brew install librsvg  # macOS，用于 SVG 转 PNG
```

### 3. 上传草稿

```bash
.venv/bin/python scripts/upload_draft.py articles/YYYY-MM-DD-标题 <标题> <摘要>
```

## 文档

- [写作指南](docs/写作指南.md)
- [发布工作流](docs/发布工作流.md)
- [封面生成指南](docs/封面生成指南.md)