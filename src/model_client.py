"""
模型客户端 - 封装与 Ollama 的通信
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

# 加载 .env 配置
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:7b")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))


class ModelClient:
    """与 Ollama 模型通信的客户端"""

    def __init__(self, base_url=None, model=None):
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or MODEL_NAME
        self.total_tokens = 0
        self.total_cost = 0.0  # 本地模型免费，保留用于统计

    def generate(self, prompt, max_tokens=None, temperature=None):
        """
        调用模型生成回复
        
        Args:
            prompt: 输入提示词
            max_tokens: 最大输出词元数
            temperature: 温度参数
            
        Returns:
            dict: {"content": 回复内容, "tokens": 使用词元数, "time": 耗时秒数}
        """
        max_tokens = max_tokens or MAX_TOKENS
        temperature = temperature or TEMPERATURE

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }

        start_time = time.time()

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            elapsed = time.time() - start_time
            content = data.get("response", "")
            tokens = data.get("eval_count", 0)

            # 统计词元使用
            self.total_tokens += tokens

            return {
                "content": content,
                "tokens": tokens,
                "time": round(elapsed, 2),
                "success": True
            }

        except requests.exceptions.Timeout:
            return {
                "content": "",
                "tokens": 0,
                "time": 60.0,
                "success": False,
                "error": "请求超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "content": "",
                "tokens": 0,
                "time": 0,
                "success": False,
                "error": "无法连接到 Ollama，请确保 Ollama 正在运行 (ollama serve)"
            }
        except Exception as e:
            return {
                "content": "",
                "tokens": 0,
                "time": 0,
                "success": False,
                "error": str(e)
            }

    def check_connectivity(self):
        """检查模型连通性"""
        return self.generate("请回复：连接成功", max_tokens=20)


# 单例客户端
_client = None


def get_client():
    global _client
    if _client is None:
        _client = ModelClient()
    return _client


def check_model():
    """命令行连通性测试函数"""
    print(f"模型: {MODEL_NAME}")
    print(f"服务地址: {OLLAMA_BASE_URL}")
    print("正在测试连通性...")

    client = get_client()
    result = client.generate("你好，请用一句话确认你已连接", max_tokens=50)

    if result["success"]:
        print(f"✅ 连接成功")
        print(f"回复: {result['content']}")
        print(f"耗时: {result['time']} 秒")
        print(f"词元数: {result['tokens']}")
        print(f"累计词元: {client.total_tokens}")
    else:
        print(f"❌ 连接失败")
        print(f"错误: {result.get('error', '未知错误')}")

    return result["success"]


if __name__ == "__main__":
    # 直接运行此文件可测试连通性
    check_model()