[README_CN.md](https://github.com/user-attachments/files/26432125/README_CN.md)
# 🚀 TripPlanner 旅行规划系统

> 一个基于多智能体（Multi-Agent）和大语言模型（LLM）的智能旅行规划系统，可根据用户需求自动生成个性化行程。

---

## 📌 项目简介

TripPlanner 是一个智能旅行规划系统，结合**多智能体架构**与**大模型能力**，能够自动为用户生成个性化旅行方案。

系统可以帮助用户：
- 🧭 发现目的地
- 📅 生成每日行程安排
- 🏨 推荐酒店、景点与活动
- 💡 根据用户偏好优化路线

---

## ✨ 核心功能

- 🤖 **多智能体系统**
  - 目的地分析 Agent
  - 行程规划 Agent
  - 推荐 Agent
  - 预算/约束 Agent

- 🧠 **AI 驱动规划**
  - 支持自然语言输入
  - 自动生成个性化行程

- 📊 **个性化配置**
  - 预算控制
  - 旅行天数
  - 兴趣偏好（美食、文化、自然等）

- 🌐 **可扩展架构**
  - 支持接入地图、天气、预订等 API

---

## 🏗️ 项目结构

```
TripPlanner/
│── agents/                # 多智能体模块
│── tools/                 # 外部工具与API
│── utils/                 # 工具函数
│── configs/               # 配置文件
│── main.py                # 程序入口
│── requirements.txt       # 依赖列表
└── README.md
```

---

## ⚙️ 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/zhengye123188/TripPlanner.git
cd TripPlanner
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

---

## 🔑 配置说明

运行前请配置 API Key：

```
OPENAI_API_KEY=你的API_KEY
SERPAPI_API_KEY=你的API_KEY
```

可以通过以下方式配置：
- `.env` 文件  
或  
- 系统环境变量

---

## ▶️ 使用方法

运行主程序：

```bash
python main.py
```

示例输入：

```
帮我规划一个去东京的5天旅行，预算中等，偏好美食和文化。
```

输出内容包括：
- 每日行程安排
- 景点推荐
- 酒店建议
- 出行提示

---

## 🧠 工作流程

1. 用户输入解析
2. 任务拆解
3. 多智能体协同
4. 调用工具/API
5. 生成最终行程

---

## 🔧 技术栈

- Python
- 大语言模型（OpenAI 等）
- LangChain / LangGraph（如使用）
- 各类第三方 API（地图、天气、旅行数据）

