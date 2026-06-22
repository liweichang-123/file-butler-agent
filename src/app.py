"""
Gradio Web 界面 - 本地文件管家智能体
"""

import gradio as gr
from src.workflow import AgentWorkflow
from src.model_client import check_model


def process_directory(dir_path):
    """
    处理用户输入的目录路径，调用智能体工作流
    """
    if not dir_path or not dir_path.strip():
        return "❌ 请输入目录路径", "", ""

    dir_path = dir_path.strip()

    # 调用智能体
    workflow = AgentWorkflow()
    result = workflow.run(dir_path)

    if not result["success"]:
        return f"❌ {result['result']}", "", ""

    data = result["result"]

    # 生成 Markdown 格式的结果展示
    markdown_output = f"""
## 📂 目录整理报告

**目录**: `{data['dir_path']}`
**文件总数**: {data['file_count']}
**分类数**: {len(data['categories'])}
**总大小**: {data['total_size_mb']:.2f} MB
**耗时**: {result['time']} 秒
**词元消耗**: {result['tokens']}

---

### 📊 分类统计
"""

    for cat, count in sorted(data['categories'].items(), key=lambda x: x[1], reverse=True):
        markdown_output += f"\n- **{cat}**: {count} 个文件"

    markdown_output += f"""

---

### 🤖 AI 智能整理建议

{data['ai_suggestion']}

---

### 📝 整理计划（共 {data['plan_total']} 条建议）

| 文件名 | 建议操作 |
|--------|----------|
"""

    for p in data['plan_preview'][:15]:
        markdown_output += f"| `{p['file']}` | 移动到 **{p['target_dir']}/** |\n"

    if data['plan_total'] > 15:
        markdown_output += f"\n... 还有 {data['plan_total'] - 15} 条建议未显示"

    # 生成日志文本
    log_text = ""
    for log in result["logs"]:
        log_text += f"[{log['timestamp'][11:19]}] [{log['step']}] {log['message']}\n"

    return markdown_output, log_text, f"✅ 处理完成！共 {data['file_count']} 个文件，{len(data['categories'])} 个分类"


def check_model_status():
    """检查模型连通性"""
    success = check_model()
    if success:
        return "✅ 模型连接正常"
    else:
        return "❌ 模型连接失败，请确保 Ollama 正在运行"


# ============================================================
# 创建 Gradio 界面
# ============================================================

def create_ui():
    with gr.Blocks(title="📁 本地文件管家", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 📁 本地文件管家智能体

        输入一个目录路径，智能体会自动扫描文件、分类并生成整理建议。

        > ⚠️ **安全模式**：本工具为只读模式，**不会实际移动或修改任何文件**，仅生成建议。
        """)

        with gr.Row():
            with gr.Column(scale=4):
                dir_input = gr.Textbox(
                    label="📂 目录路径",
                    placeholder="例如: C:\\Users\\Administrator\\Downloads",
                    value=".",
                    lines=1
                )
            with gr.Column(scale=1):
                run_btn = gr.Button("🚀 开始整理", variant="primary", size="lg")

        with gr.Row():
            with gr.Column(scale=1):
                status_btn = gr.Button("🔌 检查模型状态", size="sm")

        with gr.Row():
            status_output = gr.Textbox(
                label="📡 模型状态",
                value="点击「检查模型状态」查看",
                lines=1
            )

        with gr.Row():
            result_output = gr.Markdown(
                label="📊 整理结果",
                value="输入目录路径后点击「开始整理」"
            )

        with gr.Row():
            log_output = gr.Textbox(
                label="📋 执行日志",
                lines=10,
                max_lines=15
            )

        # 绑定事件
        run_btn.click(
            fn=process_directory,
            inputs=dir_input,
            outputs=[result_output, log_output, status_output]
        )

        status_btn.click(
            fn=check_model_status,
            inputs=[],
            outputs=status_output
        )

        # 按回车键触发
        dir_input.submit(
            fn=process_directory,
            inputs=dir_input,
            outputs=[result_output, log_output, status_output]
        )

        gr.Markdown("""
        ---
        ### 📖 使用说明

        1. 输入要整理的目录路径（支持绝对路径或相对路径）
        2. 点击「开始整理」或按回车键
        3. 智能体会扫描文件、分类并生成整理建议
        4. **所有操作均为只读，不会修改任何文件**

        ### 🔒 安全边界
        - 只允许访问用户目录下的路径
        - 禁止访问系统目录（如 `C:\\Windows`）
        - 不会执行任何文件写入或删除操作
        """)

    return demo


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)