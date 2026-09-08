from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.games import agent_turn_service
from app.api.games import router as games_router
from app.mcp_server import build_mcp_server

app = FastAPI(title="Tic-Tac-Toe API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(games_router)
mcp_server = build_mcp_server(app)
mcp_app = mcp_server.http_app(path="/", transport="http")
app.state.mcp_server = mcp_server
app.state.mcp_app = mcp_app


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with mcp_app.lifespan(application):
        try:
            yield
        finally:
            await agent_turn_service.close()


app.router.lifespan_context = lifespan
app.mount("/mcp", mcp_app)
