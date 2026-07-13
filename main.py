"""
项目入口文件 - 直接运行
"""

import sys
import os

# 把 src 目录加入模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("📁 本地文件管家智能体")
print("=" * 50)
print()
print("请选择运行方式：")
print("  1. 启动 Web 界面 (浏览器访问)")
print("  2. 命令行测试 (扫描当前目录)")
print()

choice = input("请输入数字 (1 或 2): ").strip()

if choice == "1":
    print("\n🚀 正在启动 Web 界面...")
    print("请访问: http://127.0.0.1:7860")
    print("按 Ctrl+C 停止服务")
    print()
    # 启动 Web 界面
    from src.app import create_ui
    demo = create_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)

elif choice == "2":
    print("\n🚀 正在扫描当前目录...")
    print()
    from src.workflow import main as workflow_main
    workflow_main()

else:
    print("❌ 无效选择，请输入 1 或 2")
