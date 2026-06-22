"""
智能体工作流 - 目标 → 计划 → 工具调用 → 结果
"""

import json
import time
from datetime import datetime
from src.model_client import get_client
from src.tools import scan_directory, generate_plan
from src.guardrails import validate_directory_input, safe_log_message


class AgentWorkflow:
    """智能体工作流引擎"""

    def __init__(self):
        self.client = get_client()
        self.logs = []
        self.total_tokens = 0
        self.start_time = None
        self.end_time = None

    def log(self, step, message, data=None):
        """记录执行日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "message": safe_log_message(message, max_length=300),
            "data": data
        }
        self.logs.append(entry)
        print(f"[{step}] {message}")
        return entry

    def run(self, user_goal):
        """执行智能体工作流"""
        self.start_time = time.time()
        self.logs = []
        self.total_tokens = 0

        self.log("START", f"收到用户目标: {user_goal}")

        # 步骤 1: 安全护栏
        self.log("STEP1", "安全护栏检查 - 校验输入路径")
        valid, error_msg = validate_directory_input(user_goal)
        if not valid:
            self.log("FAIL", f"安全护栏拒绝: {error_msg}")
            return self._finalize(False, f"❌ 安全拒绝: {error_msg}")

        self.log("STEP1_OK", f"路径校验通过: {user_goal}")

        # 步骤 2: 扫描目录
        self.log("STEP2", "调用工具 scan_directory 扫描目录")
        scan_result = scan_directory(user_goal, max_files=50)

        if not scan_result["success"]:
            error = scan_result.get("error", "未知错误")
            self.log("FAIL", f"扫描失败: {error}")
            return self._finalize(False, f"❌ 扫描目录失败: {error}")

        files = scan_result["files"]
        file_count = scan_result["total"]
        self.log("STEP2_OK", f"扫描完成，找到 {file_count} 个文件")

        if file_count == 0:
            self.log("WARN", "目录为空，无需整理")
            return self._finalize(True, "📂 目录为空，没有文件需要整理")

        # 步骤 3: 生成整理计划
        self.log("STEP3", "调用工具 generate_plan 生成整理建议")
        plan_result = generate_plan(files)

        if not plan_result["success"]:
            error = plan_result.get("error", "未知错误")
            self.log("FAIL", f"生成计划失败: {error}")
            return self._finalize(False, f"❌ 生成整理计划失败: {error}")

        plan = plan_result["plan"]
        summary = plan_result["summary"]
        self.log("STEP3_OK", f"生成 {len(plan)} 条整理建议")

        # 步骤 4: 调用大模型
        self.log("STEP4", "调用大模型生成智能整理建议")

        categories = summary.get("categories", {})
        prompt = f"""
你是一个文件整理助手。用户目录中有 {len(plan)} 个文件。

文件分类统计:
{json.dumps(categories, ensure_ascii=False, indent=2)}

前5个文件建议:
{json.dumps(plan[:5], ensure_ascii=False, indent=2)}

请用一段自然语言（50-80字）给出整理建议：
- 指出最多文件类型
- 建议创建哪些文件夹
- 给出具体操作步骤
"""

        model_result = self.client.generate(prompt, max_tokens=300)

        if model_result["success"]:
            ai_suggestion = model_result["content"]
            self.total_tokens += model_result["tokens"]
            self.log("STEP4_OK", f"模型生成建议成功，词元数: {model_result['tokens']}")
        else:
            error = model_result.get("error", "未知错误")
            self.log("WARN", f"模型调用失败: {error}，使用默认建议")
            ai_suggestion = self._generate_fallback_suggestion(summary)

        # 步骤 5: 汇总结果
        self.log("STEP5", "汇总结果")

        result = {
            "dir_path": user_goal,
            "file_count": file_count,
            "categories": categories,
            "plan": plan,
            "ai_suggestion": ai_suggestion,
            "total_size_mb": summary.get("total_size_mb", 0),
            "plan_preview": plan[:20],
            "plan_total": len(plan)
        }

        self.log("SUCCESS", f"✅ 整理完成！共 {file_count} 个文件，{len(categories)} 个分类")
        return self._finalize(True, result)

    def _generate_fallback_suggestion(self, summary):
        """备用建议"""
        categories = summary.get("categories", {})
        if not categories:
            return "未检测到文件，无需整理。"
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        top = sorted_cats[0]
        return f"共 {summary['total']} 个文件。最多的是「{top[0]}」类（{top[1]}个）。建议创建对应文件夹进行分类存放。"

    def _finalize(self, success, result):
        """结束工作流"""
        self.end_time = time.time()
        total_time = round(self.end_time - self.start_time, 2)

        return {
            "success": success,
            "result": result,
            "logs": self.logs,
            "tokens": self.total_tokens,
            "time": total_time
        }

    def print_summary(self, output):
        """打印结果摘要"""
        print("\n" + "=" * 60)
        print("📋 智能体执行摘要")
        print("=" * 60)

        if not output["success"]:
            print(f"❌ 执行失败: {output['result']}")
            return

        result = output["result"]
        print(f"📂 目录: {result['dir_path']}")
        print(f"📄 文件数: {result['file_count']}")
        print(f"📊 分类数: {len(result['categories'])}")
        print(f"💾 总大小: {result['total_size_mb']:.2f} MB")
        print(f"⏱️  耗时: {output['time']} 秒")
        print(f"🔢 词元数: {output['tokens']}")

        print("\n📁 分类统计:")
        for cat, count in sorted(result['categories'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {cat}: {count} 个")

        print("\n🤖 AI 整理建议:")
        print(f"   {result['ai_suggestion']}")

        print("\n📝 整理计划（前5条）:")
        for p in result['plan_preview'][:5]:
            print(f"   📄 {p['file']} → {p['target_dir']}/")

        if result.get('plan_total', 0) > 5:
            print(f"   ... 共 {result['plan_total']} 条建议")

        print("\n" + "=" * 60)


def main():
    import sys
    test_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"🚀 智能体工作流测试")
    print(f"📂 目标目录: {test_dir}")
    print("-" * 60)
    workflow = AgentWorkflow()
    result = workflow.run(test_dir)
    workflow.print_summary(result)


if __name__ == "__main__":
    main()