from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router

app = FastAPI()

# Include auth router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
