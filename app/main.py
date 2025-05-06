# ===========================================================
# Arquivo: main.py  –  Versão consolidada para MCP Server
# - Inclui o novo roteador do Dashboard.
# - Mantém roteadores existentes.
# ===========================================================
import logging
import time
import sys # Para adicionar caminhos
from pathlib import Path # Para construir caminhos

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import dashboard_analytics
from app.routes.kanban import router as kanban_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.kanban import router as kanban_router
from app.routes.sugestao import router as sugestao_router

# Adiciona o diretório raiz do projeto ao sys.path
# Isso ajuda a resolver imports como 'from app.core...'
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR.parent)) # Adiciona famdomes_backend/ ao path

# Imports da aplicação (agora devem funcionar)
try:
    from app.core.scheduler import iniciar as iniciar_scheduler, parar as parar_scheduler
    from app.config import settings # Usar settings centralizadas
    from app.utils.contexto import conectar_db # Para conectar ao iniciar
    # Roteadores existentes
    from app.routes import whatsapp, ia, stripe, agendamento # Adicione outros se tiver
    # Roteador MCP (se separado)
    # from app.routes.entrada import router as entrada_router
    # Roteador Admin (se separado)
    # from app.routes.admin import router as admin_router
    # NOVO Roteador do Dashboard
    from app.routes.dashboard import router as dashboard_router
except ImportError as e:
    logging.basicConfig(level="INFO") # Configuração mínima para logar o erro
    logger = logging.getLogger("famdomes.main_import_error")
    logger.critical(f"Erro de importação ao iniciar a aplicação: {e}")
    logger.critical("Verifique se a estrutura de pastas está correta e se o PYTHONPATH está configurado ou se está executando a partir do diretório raiz.")
    sys.exit(1) # Aborta a execução se imports essenciais falharem


# ---------- Logging ----------
# Configura o logging usando o nível definido em settings
logging.basicConfig(
level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("famdomes.main")

# ---------- FastAPI App ----------
app = FastAPI(
title="FAMDOMES API + Dashboard Backend",
description="Servidor MCP do FAMDOMES com API para o Domo Hub.",
version="1.2.0", # Incrementa versão
on_startup=[conectar_db, iniciar_scheduler], # Conecta DB e inicia scheduler no startup
on_shutdown=[parar_scheduler] # Para o scheduler no shutdown
)

# ---------- CORS Middleware ----------
# Ajuste as origens permitidas conforme necessário para seu ambiente de desenvolvimento e produção
origins = [
"http://localhost", # Comum para desenvolvimento local
"http://localhost:3000",# Porta comum para React dev server (Create React App)
"http://localhost:5173",# Porta comum para React dev server (Vite)
"https://app.famdomes.com.br", # Exemplo de URL de produção do dashboard
# Adicione a URL onde seu frontend React estará hospedado em produção
]
# Se settings tiver uma variável para origens CORS, use-a
# origins = getattr(settings, "CORS_ORIGINS", origins)

app.add_middleware(
    CORSMiddleware,
    
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"], # Permite todos os métodos (GET, POST, PUT, etc.)
    allow_headers=["*"], # Permite todos os cabeçalhos
)
app.include_router(kanban_router)
app.include_router(sugestao_router)
# ---------- Middleware de Logging de Requisições ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    # Loga o início do processamento
    logger.info(f"Req Início : {request.method} {request.url.path} from {request.client.host}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        # Loga o fim do processamento com status code e tempo
        logger.info(f"Req Fim: {request.method} {request.url.path} - Status {response.status_code} ({process_time:.4f}s)")
    except Exception as e:
        process_time = time.time() - start_time
        logger.exception(f"Req Erro   : {request.method} {request.url.path} - Erro após {process_time:.4f}s: {e}")
        # Re-levanta a exceção para que o handler de erros do FastAPI a capture
        raise e
    return response

# ---------- Roteadores da Aplicação ----------
# Inclui os roteadores existentes
app.include_router(whatsapp.router)
app.include_router(ia.router)
app.include_router(stripe.router)
app.include_router(agendamento.router)
app.include_router(dashboard_analytics.router)
app.include_router(kanban_router)
# Adicione outros roteadores existentes aqui (entrada, admin, etc.)
# Exemplo:
# app.include_router(entrada_router, prefix="/v1")
# app.include_router(admin_router)

# Inclui o NOVO roteador do Dashboard
app.include_router(dashboard_router) # O prefixo "/dashboard" já está definido no roteador

# ---------- Rota Raiz / Health Check ----------
@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz para verificar se a API está online."""
    return {"status": "ok", "message": "FAMDOMES API com Domo Hub ativa!"}


# ---------- Execução (se rodar diretamente com uvicorn main:app) ----------
# if __name__ == "__main__":
#     import uvicorn
#     port = getattr(settings, "API_PORT", 8000)
#     logger.info(f"Iniciando Uvicorn diretamente em http://0.0.0.0:{port}")
#     uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) # Use reload=True apenas em dev
