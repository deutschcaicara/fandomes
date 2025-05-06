# ===========================================================
# Arquivo: main.py  –  Versão consolidada para MCP Server
# ===========================================================
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging, time
from app.core.scheduler import iniciar as iniciar_scheduler
# Configurações centralizadas
from app.config import settings

# Roteadores herdados
from app.routes import whatsapp, ia, stripe, agendamento
# Novo roteador de entrada (MCP)
from app.routes.entrada import router as entrada_router
from app.routes.admin import router as admin_router

# ---------- Logging ----------
logging.basicConfig(level=settings.LOG_LEVEL,
                    format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("famdomes.main")

# ---------- FastAPI ----------
app = FastAPI(
    title="FAMDOMES API",
    description="Servidor MCP do FAMDOMES – cuidado emocional e dependência química",
    version="1.1.0",
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost", "http://localhost:3000", "https://famdomes.com.br"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Middleware de logging ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    ini = time.time()
    resp = await call_next(request)
    logger.info("%s %s → %s • %.3fs",
                request.method, request.url.path, resp.status_code, time.time()-ini)
    return resp

# ---------- Roteadores ----------
app.include_router(whatsapp.router)
app.include_router(ia.router)
app.include_router(stripe.router)
app.include_router(agendamento.router)
app.include_router(entrada_router, prefix="/v1")   # <‑‑ NOVO
app.include_router(admin_router)
# ---------- Health / root ----------
@app.get("/", tags=["Root"])
async def root(): return {"status": "ok", "mcp": True}

# ---------- Eventos ----------
@app.on_event("startup")
async def _startup():  logger.info("▶️ API iniciada na porta %s", settings.API_PORT)
iniciar_scheduler()
@app.on_event("shutdown")
async def _shutdown(): logger.info("⏹️ API finalizada")
