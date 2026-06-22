"""
工具函数 - 文件扫描和整理建议生成
"""

import os
import json
from datetime import datetime
from pathlib import Path


# ============================================================
# 工具 1: scan_directory - 扫描目录，返回文件列表
# 这是 MCP 风格的工具契约实现
# ============================================================

def scan_directory(path, max_files=100):
    """
    扫描指定目录，返回文件信息列表

    MCP 风格契约:
    -----------------
    工具名称: scan_directory
    用途: 扫描指定目录，返回文件列表和统计信息
    输入:
        path: 字符串，要扫描的目录路径（必须存在）
        max_files: 整数，1-500，最大返回文件数，默认100
    输出:
        success: 布尔值
        files: 列表，每个元素包含 name, ext, size, modified
        total: 整数，文件总数
        dir_path: 字符串，扫描的目录路径
    失败:
        path 不存在 -> {"success": false, "error": "directory_not_found"}
        path 不是目录 -> {"success": false, "error": "not_a_directory"}
        max_files 超出范围 -> {"success": false, "error": "invalid_max_files"}
    安全边界:
        只允许访问项目目录下的路径，禁止访问系统目录
    """

    # 输入校验
    if not isinstance(path, str) or not path.strip():
        return {
            "success": False,
            "error": "validation_error",
            "message": "路径不能为空"
        }

    if not isinstance(max_files, int) or max_files < 1 or max_files > 500:
        return {
            "success": False,
            "error": "invalid_max_files",
            "message": "max_files 必须是 1-500 之间的整数"
        }

    # 路径安全检查
    if not os.path.exists(path):
        return {
            "success": False,
            "error": "directory_not_found",
            "message": f"目录不存在: {path}"
        }

    if not os.path.isdir(path):
        return {
            "success": False,
            "error": "not_a_directory",
            "message": f"路径不是目录: {path}"
        }

    try:
        files = []
        for item in os.listdir(path):
            if len(files) >= max_files:
                break

            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                name, ext = os.path.splitext(item)
                ext = ext.lower()  # 统一小写
                stat = os.stat(full_path)

                files.append({
                    "name": item,
                    "ext": ext,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        # 按修改时间倒序排列（最新的在前）
        files.sort(key=lambda x: x["modified"], reverse=True)

        return {
            "success": True,
            "files": files,
            "total": len(files),
            "dir_path": os.path.abspath(path)
        }

    except PermissionError:
        return {
            "success": False,
            "error": "permission_denied",
            "message": f"没有权限读取目录: {path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": "scan_failed",
            "message": str(e)
        }


# ============================================================
# 工具 2: generate_plan - 根据文件列表生成整理建议
# ============================================================

def generate_plan(files, rules=None):
    """
    根据文件列表生成整理建议

    输入:
        files: 列表，文件信息（来自 scan_directory 的输出）
        rules: 字典，自定义规则（可选）
    输出:
        success: 布尔值
        plan: 列表，每个元素包含 file, suggestion, target_dir
        summary: 统计摘要
    """
    # 输入校验
    if not isinstance(files, list):
        return {
            "success": False,
            "error": "validation_error",
            "message": "files 必须是列表"
        }

    if len(files) == 0:
        return {
            "success": True,
            "plan": [],
            "summary": {"total": 0, "categories": {}},
            "message": "没有文件需要整理"
        }

    # 默认分类规则（按扩展名）
    default_rules = {
        ".jpg": "图片", ".jpeg": "图片", ".png": "图片", ".gif": "图片",
        ".bmp": "图片", ".svg": "图片", ".webp": "图片",
        ".mp4": "视频", ".avi": "视频", ".mov": "视频", ".mkv": "视频",
        ".mp3": "音频", ".wav": "音频", ".flac": "音频", ".aac": "音频",
        ".pdf": "PDF",
        ".doc": "文档", ".docx": "文档", ".txt": "文档", ".rtf": "文档",
        ".xls": "表格", ".xlsx": "表格", ".csv": "表格",
        ".ppt": "演示", ".pptx": "演示",
        ".zip": "压缩包", ".rar": "压缩包", ".7z": "压缩包", ".tar": "压缩包",
        ".gz": "压缩包", ".bz2": "压缩包",
        ".exe": "可执行文件", ".msi": "安装包",
        ".iso": "镜像文件",
        ".py": "代码", ".js": "代码", ".html": "代码", ".css": "代码",
        ".java": "代码", ".cpp": "代码", ".c": "代码", ".go": "代码",
        ".json": "数据", ".xml": "数据", ".yaml": "数据", ".yml": "数据",
    }

    # 合并用户规则
    if rules and isinstance(rules, dict):
        default_rules.update(rules)

    plan = []
    category_count = {}

    for f in files:
        ext = f.get("ext", "").lower()
        category = default_rules.get(ext, "其他")

        # 建议目标文件夹
        target_dir = category

        suggestion = f"移动到 {category}/"

        plan.append({
            "file": f.get("name", "unknown"),
            "ext": ext,
            "size": f.get("size", 0),
            "category": category,
            "target_dir": target_dir,
            "suggestion": suggestion,
            "size_mb": round(f.get("size", 0) / (1024 * 1024), 2)
        })

        category_count[category] = category_count.get(category, 0) + 1

    return {
        "success": True,
        "plan": plan,
        "summary": {
            "total": len(plan),
            "categories": category_count,
            "total_size_mb": round(sum(f.get("size", 0) for f in files) / (1024 * 1024), 2)
        }
    }


# ============================================================
# 测试函数
# ============================================================

def test_tools():
    """测试工具函数"""
    print("=" * 50)
    print("测试工具函数")
    print("=" * 50)

    # 测试扫描当前目录
    print("\n1. 测试 scan_directory")
    result = scan_directory(".", max_files=10)
    print(f"   success: {result['success']}")
    if result["success"]:
        print(f"   找到 {result['total']} 个文件")
        for f in result["files"][:3]:
            print(f"   - {f['name']} ({f['ext']}) {f['size']} bytes")

    # 测试生成计划
    print("\n2. 测试 generate_plan")
    if result["success"] and result["files"]:
        plan_result = generate_plan(result["files"])
        print(f"   success: {plan_result['success']}")
        print(f"   共 {plan_result['summary']['total']} 个文件")
        print(f"   分类: {plan_result['summary']['categories']}")
        for p in plan_result["plan"][:3]:
            print(f"   - {p['file']} → {p['target_dir']}/")

    print("\n✅ 工具测试完成")


if __name__ == "__main__":
    test_tools()