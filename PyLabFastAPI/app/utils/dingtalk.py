# app/utils/dingtalk.py
import httpx
from app.config import settings


class DingTalkHelper:
    @staticmethod
    async def get_user_info_by_code(auth_code: str):
        """文档: https://open.dingtalk.com/document/orgapp/tutorial-obtaining-user-personal-information"""
        async with httpx.AsyncClient() as client:
            #1.获取access_token
            token_url = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"
            payload = {
                "clientId": settings.DINGTALK_APPID,
                "clientSecret": settings.DINGTALK_APPSECRET,
                "code": auth_code,
                "grantType": "authorization_code"
            }
            try:
                token_resp = await client.post(token_url, json=payload)
                token_data = token_resp.json()
            except Exception as e:
                return None, f"网络请求失败: {str(e)}"
            if "accessToken" not in token_data:
                return None, f"获取Token失败: {token_data.get('message', '未知错误')}"
            #2.获取用户信息
            info_url = "https://api.dingtalk.com/v1.0/contact/users/me"
            headers = {
                "x-acs-dingtalk-access-token": token_data["accessToken"]
            }
            try:
                info_resp = await client.get(info_url, headers=headers)
                info_data = info_resp.json()
                print("用户信息:",info_data)
            except Exception as e:
                return None, f"获取用户信息失败: {str(e)}"
            if "openId" not in info_data:
                return None, f"用户信息无效: {info_data.get('message', '未知错误')}"
            return {
                "unionid": info_data.get("unionId"),  # 钉钉全局唯一ID
                "openid": info_data.get("openId"),  # 应用内唯一ID
                "nick": info_data.get("nick"),
                "avatar": info_data.get("avatarUrl", ""),
                "phone":info_data.get("mobile"), #获取手机号
            }, None