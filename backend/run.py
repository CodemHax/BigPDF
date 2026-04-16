import uvicorn
import os

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8006)),
        timeout_keep_alive=5,
        lifespan="on",
    )
