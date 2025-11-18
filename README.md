# AI对话系统 - 基于LM Studio的智能对话平台

## 🚀 项目概述

一个基于FastAPI和LM Studio构建的AI对话系统，提供完整的Web界面和API接口。使用JSON文件存储数据，无需数据库，适合轻量级部署。
部分代码由AI完成

## ✨ 核心特性

- **智能对话** 🤖 - 与LM Studio无缝集成，实现流畅的AI对话体验
- **预设管理** 🎨 - 创建和管理多个AI角色预设，定制不同对话风格
- **历史记录** 📝 - 自动保存对话历史，支持搜索和导出
- **自动清理** 🧹 - 定期清理早期对话记录，防止存储溢出
- **多接口支持** 🌐 - 提供RESTful API和WebSocket接口
- **响应式设计** 📱 - 现代化Web界面，适配各种设备

## 🛠️ 技术栈

- **后端**: FastAPI, Uvicorn
- **前端**: Jinja2模板, Tailwind CSS
- **存储**: JSON文件存储
- **AI集成**: LM Studio本地API

## 📦 安装指南

### 前置要求

- Python 3.8+
- LM Studio (本地运行，端口1234)

### 快速开始

```bash
# 克隆项目
git clone https://github.com/your-repo/DaYiJieNanAi.git
cd DaYiJieNanAi

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 根据需要编辑.env文件

# 启动应用
python start.py
```

访问 [http://localhost:8100](http://localhost:8100) 开始使用

## 🏗️ 项目结构

```
DaYiJieNanAi/
├── app/                      # 应用核心代码
│   ├── api/                  # API路由
│   ├── services/             # 业务逻辑
│   ├── storage/              # 数据存储
│   ├── websocket/            # WebSocket处理
│   ├── routes.py             # 页面路由
│   └── main.py               # 应用入口
├── templates/                # HTML模板
├── static/                   # 静态资源
├── data/                     # JSON数据存储
├── requirements.txt          # 依赖列表
├── start.py                  # 启动脚本
└── README.md                # 项目文档
```

## 🔍 详细文档

### 数据存储

系统使用JSON文件存储数据，位于`data/`目录：

- `conversations.json` - 对话元数据
- `messages.json` - 对话消息内容
- `presets.json` - AI预设配置

### API文档

启动应用后访问：
- 交互式API文档: [http://localhost:8000/docs](http://localhost:8000/docs)
- API文档页面: [http://localhost:8000/api-docs](http://localhost:8000/api-docs)

主要API端点包括：
- 对话管理 (`/api/conversations`)
- 消息交互 (`/api/chat`)
- 预设管理 (`/api/presets`)
- WebSocket实时通信 (`/api/ws`)

## ⚙️ 配置选项

编辑`.env`文件配置应用：

```ini
# LM Studio配置
LM_STUDIO_BASE_URL=http://localhost:1234

# 数据保留策略
MAX_CONVERSATION_AGE_DAYS=30

# 开发模式
DEBUG=true
```

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## ⚠️ 注意事项

1. 确保LM Studio在本地运行并开放API端口
2. 定期备份`data/`目录
3. 大量数据建议使用数据库替代JSON存储

## 许可证

本项目仅供学习和研究使用。
