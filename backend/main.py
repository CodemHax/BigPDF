import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers import merge, split, compress, convert, watermark, rotate, security, page_numbers, filter, flatten
from services.file_service import ensure_dirs, periodic_cleanup

# Configure max upload size (100MB)
# Set this environment variable if you need to adjust at runtime
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 100 * 1024 * 1024))

EXPOSED_HEADERS = ["X-Original-Size", "X-Compressed-Size", "X-Reduction-Percent"]


def _parse_allowed_origins() -> list[str]:
    raw_origins = os.getenv("BIGPDF_ALLOWED_ORIGINS", "")
    return [origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip()]


def _request_origin(request: Request) -> str:
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip()
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    return f"{scheme}://{host}".rstrip("/")


def _source_origin(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _allowed_origins_for_request(request: Request) -> set[str]:
    return {_request_origin(request), *_parse_allowed_origins()}


def _is_allowed_api_source(request: Request) -> bool:
    allowed_origins = _allowed_origins_for_request(request)
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    if origin:
        return origin.rstrip("/") in allowed_origins
    if referer:
        return _source_origin(referer) in allowed_origins

    if request.headers.get("sec-fetch-site") == "same-origin":
        return True

    return os.getenv("BIGPDF_ALLOW_DIRECT_API", "").lower() in {"1", "true", "yes"}


app = FastAPI(
    title="BigPDF API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Add middleware to handle large uploads by setting max_receive_size
from starlette.datastructures import Headers

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=EXPOSED_HEADERS,
)


@app.middleware("http")
async def restrict_api_to_frontend(request: Request, call_next):
    if request.url.path.startswith("/api") and request.method != "OPTIONS":
        if not _is_allowed_api_source(request):
            return JSONResponse(
                status_code=403,
                content={"detail": "API access is allowed only from the BigPDF frontend."},
            )
    return await call_next(request)

app.include_router(merge.router)
app.include_router(split.router)
app.include_router(compress.router)
app.include_router(convert.router)
app.include_router(watermark.router)
app.include_router(rotate.router)
app.include_router(security.router)
app.include_router(page_numbers.router)
app.include_router(filter.router)
app.include_router(flatten.router)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.on_event("startup")
async def startup_event():
    ensure_dirs()
    asyncio.create_task(periodic_cleanup())


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "BigPDF"}


@app.get("/docs", include_in_schema=False)
@app.get("/redoc", include_in_schema=False)
@app.get("/openapi.json", include_in_schema=False)
async def disabled_api_docs():
    return JSONResponse(status_code=404, content={"detail": "API documentation is disabled."})


if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Frontend not found"}


@app.get("/")
async def root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Frontend not found"}
