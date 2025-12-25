# app/utils/baidu_ocr.py
from aip import AipOcr
from app.config import settings
import requests  # <--- [新增 1] 引入 requests 库用于下载图片


class BaiduOCR:
    def __init__(self):
        self.client = AipOcr(
            settings.BAIDU_APP_ID,
            settings.BAIDU_API_KEY,
            settings.BAIDU_SECRET_KEY
        )

    def idcard_front(self, image_url: str):
        """
        识别身份证正面
        """
        options = {"detect_direction": "true"}

        # === [核心修复] 开始 ===
        # 1. 先下载图片获取二进制数据 (bytes)
        try:
            print(f"正在下载图片: {image_url}")
            resp = requests.get(image_url, timeout=10)
            if resp.status_code != 200:
                print(f"图片下载失败，状态码: {resp.status_code}")
                return None
            image_bytes = resp.content  # 拿到二进制数据
        except Exception as e:
            print(f"下载图片异常: {e}")
            return None

        # 2. 将二进制数据传给 SDK
        # SDK 会自动对其进行 Base64 编码，这样就不会报错了
        result = self.client.idcard(image_bytes, "front", options)
        # === [核心修复] 结束 ===

        print(f"[BaiduOCR] 识别结果: {result}")

        if "words_result" in result:
            return {
                "name": result["words_result"]["姓名"]["words"],
                "id_num": result["words_result"]["公民身份号码"]["words"],
                "address": result["words_result"]["住址"]["words"]
            }

        return None

    def idcard_back(self, image_url: str):
        """识别身份证反面 (可选，主要用于校验是否是身份证)"""
        result = self.client.idcard(image_url, "back")
        return "words_result" in result