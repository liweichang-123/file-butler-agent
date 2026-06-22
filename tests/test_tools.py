"""
自动化测试 - 工具函数测试
"""

import os
import pytest
import tempfile
from src.tools import scan_directory, generate_plan
from src.guardrails import validate_directory_input, is_path_allowed


class TestScanDirectory:
    """测试 scan_directory 工具"""

    def test_scan_valid_directory(self):
        """测试 1: 扫描有效目录"""
        result = scan_directory(".")
        assert result["success"] is True
        assert "files" in result
        assert "total" in result
        assert result["total"] >= 0

    def test_scan_nonexistent_directory(self):
        """测试 2: 扫描不存在的目录"""
        result = scan_directory("/nonexistent_path_12345")
        assert result["success"] is False
        assert result["error"] == "directory_not_found"

    def test_scan_invalid_max_files(self):
        """测试 3: 无效的 max_files 参数"""
        result = scan_directory(".", max_files=1000)
        assert result["success"] is False
        assert result["error"] == "invalid_max_files"

    def test_scan_empty_path(self):
        """测试 4: 空路径"""
        result = scan_directory("")
        assert result["success"] is False
        assert result["error"] == "validation_error"

    def test_scan_with_temp_dir(self):
        """测试 5: 临时目录扫描"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建几个测试文件
            for i in range(3):
                f = open(os.path.join(tmpdir, f"test_{i}.txt"), "w")
                f.write("test")
                f.close()

            result = scan_directory(tmpdir)
            assert result["success"] is True
            assert result["total"] == 3


class TestGeneratePlan:
    """测试 generate_plan 工具"""

    def test_generate_plan_valid(self):
        """测试 6: 有效文件列表生成计划"""
        files = [
            {"name": "a.jpg", "ext": ".jpg", "size": 1000},
            {"name": "b.pdf", "ext": ".pdf", "size": 2000},
            {"name": "c.txt", "ext": ".txt", "size": 500},
        ]
        result = generate_plan(files)
        assert result["success"] is True
        assert result["summary"]["total"] == 3
        assert "图片" in result["summary"]["categories"]
        assert "PDF" in result["summary"]["categories"]

    def test_generate_plan_empty(self):
        """测试 7: 空文件列表"""
        result = generate_plan([])
        assert result["success"] is True
        assert result["summary"]["total"] == 0

    def test_generate_plan_invalid_input(self):
        """测试 8: 无效输入"""
        result = generate_plan("not a list")
        assert result["success"] is False


class TestGuardrails:
    """测试安全护栏"""

    def test_path_allowed_current_dir(self):
        """测试 9: 当前目录允许"""
        allowed, _ = is_path_allowed(".")
        assert allowed is True

    def test_path_rejected_system(self):
        """测试 10: 系统目录拒绝"""
        allowed, _ = is_path_allowed("C:\\Windows")
        assert allowed is False

    def test_validate_valid_path(self):
        """测试 11: 有效路径校验"""
        valid, msg = validate_directory_input(".")
        assert valid is True

    def test_validate_empty_path(self):
        """测试 12: 空路径校验"""
        valid, msg = validate_directory_input("")
        assert valid is False
        assert "不能为空" in msg

    def test_validate_path_traversal(self):
        """测试 13: 路径遍历攻击检测"""
        valid, msg = validate_directory_input("..\\..\\etc")
        assert valid is False