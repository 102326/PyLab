# app/utils/baidu_ocr.py
from aip import AipOcr
from app.config import settings


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
        :param image_url: 图片的公网 URL (七牛云链接)
        """
        options = {"detect_direction": "true"}
        # 百度支持直接传 URL
        result = self.client.idcard(image_url, "front", options)

        # 检查是否识别成功
        if "words_result" in result:
            return {
                "name": result["words_result"]["姓名"]["words"],
                "id_num": result["words_result"]["公民身份号码"]["words"],
                "address": result["words_result"]["住址"]["words"]
            }

        # 如果出错，打印日志方便调试
        print(f"OCR识别失败: {result}")
        return None

    def idcard_back(self, image_url: str):
        """识别身份证反面 (可选，主要用于校验是否是身份证)"""
        result = self.client.idcard(image_url, "back")
        return "words_result" in result