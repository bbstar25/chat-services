import os
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:8000")
CHAT_SERVICE_URL = os.environ.get("CHAT_SERVICE_URL", "http://chat-service:8000")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="API Gateway")
Instrumentator().instrument(app).expose(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

client = httpx.AsyncClient()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "gateway"}


@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("20/minute")
async def proxy_auth(request: Request, path: str):
    return await proxy_request(request, AUTH_SERVICE_URL, path)


@app.api_route("/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("60/minute")
async def proxy_chat(request: Request, path: str):
    return await proxy_request(request, CHAT_SERVICE_URL, path)


async def proxy_request(request: Request, base_url: str, path: str):
    url = f"{base_url}/{path}"
    body = await request.body()

    response = await client.request(
        method=request.method,
        url=url,
        headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
        content=body,
        params=request.query_params,
    )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
