import uvicorn
import os

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        limit_max_connections=1000,
        limit_concurrency=None,
        timeout_keep_alive=5,
        lifespan="on",
        # Add environment variable for request body limit
        # Note: This is handled by the middleware in main.py
    )
