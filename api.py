"""FastAPI entry point for the React billing ops interface."""

import uvicorn

from src.api.app import create_api_app
from src.config import settings

app = create_api_app()


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=settings.api_port,
        reload=False,
    )
