# app/utils/baidu_ocr.py
from aip import AipOcr
from app.config import settings
import requests


class BaiduOCR:
    def __init__(self):
        self.client = AipOcr(
            settings.BAIDU_APP_ID,
            settings.BAIDU_API_KEY,
            settings.BAIDU_SECRET_KEY
        )

    def _get_image_content(self, image_url: str) -> bytes:
        """
        [内部通用方法] 下载图片并返回二进制数据
        """
        try:
            print(f"⬇️ [IO] 正在下载图片: {image_url}")
            resp = requests.get(image_url, timeout=10)
            if resp.status_code != 200:
                print(f"❌ 下载失败，状态码: {resp.status_code}")
                return None
            return resp.content
        except Exception as e:
            print(f"❌ 下载异常: {e}")
            return None

    def idcard_front(self, image_url: str):
        """
        识别身份证正面 (纯Python版)
        """
        options = {"detect_direction": "true"}

        # 1. 下载图片 (不经过 Rust 处理)
        image_bytes = self._get_image_content(image_url)
        if not image_bytes:
            return None

        # 2. 传给百度 API
        result = self.client.idcard(image_bytes, "front", options)
        print(f"[BaiduOCR] 正面识别结果: {result}")

        if "words_result" in result:
            return {
                "name": result["words_result"]["姓名"]["words"],
                "id_num": result["words_result"]["公民身份号码"]["words"],
                "address": result["words_result"]["住址"]["words"]
            }
        return None

    def idcard_back(self, image_url: str):
        """
        识别身份证反面 (纯Python版)
        """
        image_bytes = self._get_image_content(image_url)
        if not image_bytes:
            return False

        result = self.client.idcard(image_bytes, "back")
        print(f"[BaiduOCR] 反面识别结果: {result}")

        return "words_result" in result