"""Production launcher for the read-only Infinite Trading Intelligence API."""
from src.python.api.mvp import app

__all__ = ["app"]

if __name__ == "__main__":
    import os
    import uvicorn

    host = os.getenv("ITP_HOST", "127.0.0.1")
    port = int(os.getenv("ITP_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
