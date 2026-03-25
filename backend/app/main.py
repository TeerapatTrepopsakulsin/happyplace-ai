from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.dashboard import router as dashboard_router
from app.api.guidelines import router as guidelines_router
from app.api.invitations import router as invitations_router

app = FastAPI()

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chat_router, tags=["chat"])
app.include_router(dashboard_router, prefix="/api/v1", tags=["dashboard"])
app.include_router(guidelines_router, prefix="/api/v1", tags=["guidelines"])
app.include_router(invitations_router, prefix="/api/v1", tags=["invitations"])


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
