"""
Scheduler assíncrono (apscheduler) para tarefas recorrentes.
"""
import asyncio, logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.utils.contexto import obter_contexto
from app.agents.domo_followup import DomoFollowUp

logger = logging.getLogger("famdomes.scheduler")
sched = AsyncIOScheduler()

async def _job_followup():
    limite = datetime.now(timezone.utc) - timedelta(hours=24)
    from pymongo import MongoClient
    from app.config import MONGO_URI
    mongo = MongoClient(MONGO_URI)
    col = mongo["famdomes"]["contextos"]

    # contexto em PITCH ou CTA sem pagamento há >24 h
    filtro = {
        "estado": {"$in": ["PITCH", "CTA"]},
        "ts": {"$lt": limite}
    }
    for ctx in col.find(filtro):
        tel = ctx["tel"]
        logger.info("Follow‑up 24 h → %s", tel)
        await DomoFollowUp(intent="FOLLOW_UP_24H").executar(telefone=tel, mensagem_original="")

def iniciar():
    sched.add_job(_job_followup, "interval", hours=1, id="followup24h")
    sched.start()
