from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.session import init_engine
from app.routers import auth, tenants, users, products

static_dir = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="srKasse API",
        description="Sunrise Supermarket – multi-tenant API",
        version="0.1.0",
    )

    init_engine()

    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(auth.router, prefix="/api")
    app.include_router(tenants.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(products.router, prefix="/api")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "app": "srKasse",
            "brand": "Sunrise Supermarket",
            "docs": "/docs",
            "logo": "/static/logo.png",
        }

    return app


app = create_app()
