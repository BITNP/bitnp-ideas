from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bitnp_ideas.api.router import api_router
from bitnp_ideas.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        openapi_url=settings.app.openapi_url,
        docs_url=settings.app.docs_url,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origin_strings,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"service": settings.app.name, "docs": settings.app.docs_url}

    return app


app = create_app()
