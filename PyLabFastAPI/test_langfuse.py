import os
import time
from dotenv import load_dotenv
# 👇 [修正点 1] 根据你的源码，直接从 langfuse 导入 observe
from langfuse import Langfuse, observe

# 1. 强制加载环境变量
load_dotenv(override=True)

# 2. 强制修正 Host (避开 localhost 解析坑)
original_host = os.getenv("LANGFUSE_HOST", "")
if "localhost" in original_host:
    print(f"⚠️ 检测到 Host 为 localhost，正在修正为 127.0.0.1...")
    os.environ["LANGFUSE_HOST"] = original_host.replace("localhost", "127.0.0.1")

# 重新获取配置用于打印
pk = os.getenv("LANGFUSE_PUBLIC_KEY")
sk = os.getenv("LANGFUSE_SECRET_KEY")
host = os.getenv("LANGFUSE_HOST")

print(f"--- Langfuse 连通性测试 ---")
print(f"Public Key: {pk[:5]}******" if pk else "❌ Public Key 为空!")
print(f"Secret Key: {sk[:5]}******" if sk else "❌ Secret Key 为空!")
print(f"Host:       {host}")
print(f"---------------------------")

try:
    # 3. 初始化客户端
    langfuse = Langfuse()

    # 4. 网络连通性检查
    print("📡 正在尝试连接 Langfuse 服务器...")
    if langfuse.auth_check():
        print("✅ 网络连接成功！API Key 验证通过！")
    else:
        print("❌ 连接失败：Key 无效 或 服务器不可达。")
        print("   -> 请检查 http://127.0.0.1:3000 是否能访问")
        exit(1)

    # 5. 发送测试数据 (使用装饰器)
    print("🚀 正在发送测试 Trace (observe模式)...")


    @observe(name="heartbeat-v3-final")
    def test_function():
        time.sleep(0.1)
        return "Heartbeat Success"


    test_function()

    # 6. 强制刷新
    print("⏳ 正在强制上报数据 (Flush)...")
    langfuse.flush()
    print("✅ Flush 完成! 请去 Langfuse 后台 -> Traces 页面查看 'heartbeat-v3-final'")

except Exception as e:
    print(f"❌ 发生程序错误: {e}")