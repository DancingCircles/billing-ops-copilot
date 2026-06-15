import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()],
)


class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    temperature: float = float(os.getenv("TEMPERATURE", "0"))
    api_port: int = int(os.getenv("API_PORT", "8000"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5173")
    recent_message_limit: int = int(os.getenv("RECENT_MESSAGE_LIMIT", "12"))
    app_title: str = "Subscription Billing Support Assistant"
    app_description: str = (
        "内部订阅账单支持助手，可查询客户订阅、发票、支付、退款和工单证据。"
        "查询账户相关数据前，请先提供 Customer ID、邮箱或手机号。"
    )


settings = Settings()
