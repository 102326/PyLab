#  AI-FullStack-Engine (PyLab)

> **基于微服务思维构建的高性能 AI 全栈应用底座。** 集成异步 Web 框架、向量数据库、分布式缓存及大模型观测台，旨在为 AI Agent 或复杂业务系统提供稳健的工程化实践。

## 📖 项目简介

本项目不仅仅是一个 Web 应用，更是一套完整的 **本地化开发基础设施方案**。它通过 Docker 容器化编排，统一了多种数据库环境，并结合了最新的 LangChain 观测技术，支持从本地模型调试（Ollama）到生产级数据同步（BinLog to ES）的全流程能力。

### 核心功能

- **🤖 AI 智能引擎**: 基于 LangChain 封装，支持多模型切换（WSL 部署的 Ollama），集成 Langfuse 全链路追踪。
- **⚡ 高性能后端**: 采用 FastAPI 异步架构，支持 PostgreSQL (pgvector) 向量存储。
- **🎨 现代响应式前端**: Vue 3 + Element Plus，并引入 Tailwind CSS 进行极致的 UI 样式控制。
- **🛠️ 基础设施容器化**: 包含 MySQL (BinLog 开启)、Redis、MongoDB、Elasticsearch 等全套中间件，一键启停。
- **📂 对象存储与异步任务**: 集成 MinIO 处理文件资产，RabbitMQ 处理高并发异步任务。

## 目录结构 (Mono-repo)

Plaintext

```
.
├── backend/            # FastAPI 异步后端服务
├── frontend/           # Vue 3 + Tailwind 现代前端
├── infra.yml           # 基础数据库组 (MySQL, PG, Mongo, Redis)
├── ai_monitor.yml      # AI 观测组 (Langfuse, ClickHouse)
├── async_storage.yml   # 存储组 (MinIO, RabbitMQ)
├── search.yml          # 搜索组 (Elasticsearch, Kibana)
├── conf/               # 数据库及服务自定义配置文件
└── volumes/            # 持久化数据挂载点 (Git 已忽略)
```

## 🛠️ 技术栈

| **领域**       | **技术选型**                                        |
| -------------- | --------------------------------------------------- |
| **前端**       | Vue 3, Element Plus, Tailwind CSS, Vite             |
| **后端**       | Python 3.14+, FastAPI, SQLAlchemy (Async), Motor    |
| **AI 框架**    | LangChain, Ollama (Local LLM), Langfuse (Tracing)   |
| **数据库**     | MySQL 8.0, PostgreSQL 16 (pgvector), MongoDB, Redis |
| **搜索与消息** | Elasticsearch 9.2, RabbitMQ                         |
| **存储与部署** | MinIO, Docker Compose                               |

## 🚦 快速开始

### 1. 环境准备

- 安装 [Docker Desktop](https://www.docker.com/)
- 安装 [uv](https://github.com/astral-sh/uv) (推荐) 或 Conda
- (可选) 在 WSL 中安装 [Ollama](https://ollama.com/) 并确保其在 `11434` 端口运行。

### 2. 启动基础设施

在项目根目录下，按需启动组件：

Bash

```
# 1. 启动核心数据库
docker-compose -f infra.yml up -d

# 2. 启动 AI 观测与存储
docker-compose -f ai_monitor.yml -f async_storage.yml up -d
```

### 3. 后端开发

Bash

```
cd backend
uv pip install -r requirements.txt
python main.py
```

### 4. 前端开发

Bash

```
cd frontend
npm install
npm run dev
```

------

## 🛡️ 许可证

根据 [MIT License](https://www.google.com/search?q=LICENSE) 许可。

------

## ✉️ 联系与支持

- **作者**: YourName
- **个人主页**: [Your GitHub Profile](https://github.com/YourUsername)
- **项目初衷**: 探索 AI 技术在复杂业务系统中的工程化落地边界。