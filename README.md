📁 本地文件管家智能体
基于 AI 智能体的本地文件整理工具，自动扫描目录、分类文件、生成整理建议。

🚀 快速开始
1. 安装 Ollama 并下载模型
bash
# 下载安装 Ollama
# https://ollama.com/download

# 拉取模型
ollama pull qwen2.5:7b
2. 创建 conda 环境
bash
conda create -n file-butler python=3.11 -y
conda activate file-butler
pip install -r requirements.txt
3. 配置环境变量
复制 .env.example 为 .env：

bash
cp .env.example .env
4. 启动 Web 界面
bash
conda activate file-butler
python -m src.app
浏览器访问：http://127.0.0.1:7860

5. 命令行测试（无需浏览器）
bash
python -m src.workflow .
6. 运行自动化测试
bash
pytest tests/test_tools.py -v
功能特性
🔍 智能扫描：自动扫描指定目录下的所有文件

📊 自动分类：按文件类型（图片、文档、视频等）自动分类

🤖 AI 建议：调用大模型生成智能整理建议

🔒 安全只读：仅生成建议，不会实际移动或修改任何文件

🌐 Web 界面：基于 Gradio 的友好交互界面

技术栈
Python 3.11

Ollama + Qwen2.5:7b（本地大模型）

Gradio（Web 界面）

pytest（自动化测试）

项目结构
text
file_butler/
├── src/
│   ├── app.py              # Web 界面入口
│   ├── workflow.py         # 智能体工作流
│   ├── tools.py            # 工具函数（含 MCP 契约）
│   ├── guardrails.py       # 安全护栏
│   └── model_client.py     # 模型客户端
├── tests/
│   └── test_tools.py       # 自动化测试
├── docs/
│   └── tool_contracts.md   # MCP 风格工具契约
├── .env.example            # 环境变量模板
├── requirements.txt
└── README.md
安全说明
仅允许访问用户目录下的路径

禁止访问系统敏感目录（如 C:\Windows）

只读模式，不会修改任何文件

日志自动脱敏，不记录敏感信息

已知限制
不支持子目录递归扫描

最大文件数限制为 500 个

需要 Ollama 服务在后台运行
