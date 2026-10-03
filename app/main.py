"""FastAPI application entrypoint: app instance, static files, and router registration."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, pages

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(health.router)
app.include_router(pages.router)
