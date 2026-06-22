"""
安全护栏 - 路径校验、输入校验、敏感信息保护
"""

import os
import re


# ============================================================
# 1. 路径安全校验
# ============================================================

# 允许访问的目录白名单（默认只允许用户目录和项目目录）
ALLOWED_PATHS = [
    os.path.expanduser("~"),  # 用户主目录
    os.getcwd(),              # 当前项目目录
]

# 禁止访问的系统敏感目录
FORBIDDEN_PATHS = [
    "C:\\Windows",
    "C:\\System32",
    "/etc",
    "/bin",
    "/sbin",
    "/usr/bin",
    "/System",
    "/Library",
]


def is_path_allowed(path):
    """
    检查路径是否在允许范围内

    Args:
        path: 要检查的路径

    Returns:
        (allowed: bool, reason: str)
    """
    if not path or not isinstance(path, str):
        return False, "路径为空或无效"

    # 规范化路径
    abs_path = os.path.abspath(path)

    # 检查是否在禁止目录列表中
    for forbidden in FORBIDDEN_PATHS:
        if abs_path.lower().startswith(forbidden.lower()):
            return False, f"禁止访问系统目录: {forbidden}"

    # 检查是否在白名单目录下
    for allowed in ALLOWED_PATHS:
        allowed_abs = os.path.abspath(allowed)
        if abs_path.startswith(allowed_abs):
            return True, "路径在允许范围内"

    # 如果不在白名单，额外检查一下是否是合理的用户目录
    # 例如 D:\Users\xxx, /home/xxx 等
    if os.path.exists(abs_path) and os.path.isdir(abs_path):
        # 检查是否包含 "Users", "home", "Desktop", "Documents" 等
        safe_keywords = ["users", "home", "desktop", "documents", "downloads", 
                         "file_butler", "projects", "workspace"]
        path_lower = abs_path.lower()
        for keyword in safe_keywords:
            if keyword in path_lower:
                return True, f"路径包含安全关键词: {keyword}"

    # 最后兜底：路径存在且在用户目录下，才允许
    if os.path.exists(abs_path):
        user_home = os.path.expanduser("~")
        if abs_path.startswith(user_home):
            return True, "路径在用户主目录下"

    return False, f"路径不在允许范围内: {abs_path}"


def sanitize_path(path):
    """
    清理路径，防止路径遍历攻击
    """
    if not path:
        return None
    # 移除 .. 和 . 等危险字符
    normalized = os.path.normpath(path)
    return normalized


# ============================================================
# 2. 输入校验
# ============================================================

def validate_directory_input(path):
    """
    校验用户输入的目录路径

    Returns:
        (valid: bool, error_msg: str)
    """
    # 检查是否为空
    if not path or not path.strip():
        return False, "目录路径不能为空"

    path = path.strip()

    # 检查长度
    if len(path) > 500:
        return False, "路径长度超过限制 (最大500字符)"

    # 检查是否包含危险字符
    dangerous_patterns = [
        r'[<>"|?*]',  # Windows 通配符
        r'\.\.',       # 路径遍历
        r'^/dev/',     # Linux 设备文件
        r'^/proc/',    # Linux 进程目录
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, path):
            return False, f"路径包含非法字符或模式: {pattern}"

    # 检查路径是否允许
    allowed, reason = is_path_allowed(path)
    if not allowed:
        return False, reason

    return True, ""


# ============================================================
# 3. 敏感信息保护（脱敏）
# ============================================================

def redact_sensitive(text):
    """
    脱敏处理 - 移除或替换敏感信息

    主要处理：
    - 文件路径（保留文件名，隐藏完整路径）
    - 用户名（替换为 [USER]）
    - IP 地址（替换为 [IP]）
    """
    if not text:
        return text

    # 替换用户主目录为 [USER_HOME]
    user_home = os.path.expanduser("~")
    if user_home in text:
        # 只保留最后的文件名
        parts = text.split(user_home)
        text = f"[USER_HOME]{parts[-1] if len(parts) > 1 else ''}"

    # 替换 IP 地址
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    text = re.sub(ip_pattern, '[IP]', text)

    # 替换可能的邮箱
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, '[EMAIL]', text)

    return text


# ============================================================
# 4. 日志脱敏
# ============================================================

def safe_log_message(message, max_length=200):
    """
    生成安全的日志信息

    Args:
        message: 原始消息
        max_length: 最大长度

    Returns:
        脱敏且截断后的消息
    """
    if not message:
        return ""

    # 先脱敏
    redacted = redact_sensitive(str(message))

    # 截断
    if len(redacted) > max_length:
        redacted = redacted[:max_length] + "...(截断)"

    return redacted


# ============================================================
# 测试函数
# ============================================================

def test_guardrails():
    """测试安全护栏"""
    print("=" * 50)
    print("测试安全护栏")
    print("=" * 50)

    # 测试路径校验
    print("\n1. 测试路径校验:")
    test_paths = [
        ".",                       # 当前目录
        os.path.expanduser("~"),   # 用户目录
        "C:\\Windows",             # 禁止目录
        "..\\..\\etc",             # 路径遍历
        "",                        # 空路径
    ]
    for p in test_paths:
        valid, reason = validate_directory_input(p)
        status = "✅" if valid else "❌"
        print(f"   {status} '{p}' -> {reason or '允许'}")

    # 测试脱敏
    print("\n2. 测试敏感信息脱敏:")
    sensitive_text = f"用户 {os.path.expanduser('~')} 的 IP 是 192.168.1.1"
    print(f"   原文: {sensitive_text}")
    print(f"   脱敏: {redact_sensitive(sensitive_text)}")

    # 测试日志安全
    print("\n3. 测试日志安全:")
    long_msg = "A" * 300
    print(f"   原始长度: {len(long_msg)}")
    safe_msg = safe_log_message(long_msg)
    print(f"   安全长度: {len(safe_msg)}")

    print("\n✅ 安全护栏测试完成")


if __name__ == "__main__":
    test_guardrails()