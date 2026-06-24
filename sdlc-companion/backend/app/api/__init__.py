"""API package (P07). register_routers wires feature routers into the app."""
from __future__ import annotations

from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    from app.api import artifacts, chat, gates, impact, projects

    app.include_router(projects.router)
    app.include_router(artifacts.router)
    app.include_router(gates.router)
    app.include_router(impact.router)
    app.include_router(chat.router)
