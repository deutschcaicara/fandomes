"""
Coleta KPIs e expõe para Prometheus + JSON.
"""
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

from app.config import MONGO_URI

# ---------- Gauges ----------
LEADS         = Gauge("domo_leads_total", "Leads captados nas últimas 24h")
QUALIFICADOS  = Gauge("domo_qualificados_total", "Leads com score >=2 últimas 24h")
PAGOS         = Gauge("domo_pagamentos_total", "Pagamentos confirmados últimas 24h")
TEMPO_PG_SECS = Gauge("domo_tempo_medio_pg_segundos", "Tempo médio lead→pagamento (s)")

# ---------- Coleta ----------
def atualizar():
    mongo = MongoClient(MONGO_URI)
    ctx   = mongo["famdomes"]["contextos"]

    ini = datetime.now(timezone.utc) - timedelta(days=1)

    # Leads = primeira interação nas 24h
    leads = ctx.count_documents({"ts": {"$gt": ini}, "interacoes": 1})
    LEADS.set(leads)

    # Qualificados = score_lead >=2
    qual = ctx.count_documents({"ts": {"$gt": ini}, "meta_conversa.score_lead": {"$gte": 2}})
    QUALIFICADOS.set(qual)

    # Pagos
    pagos = ctx.count_documents({"ts": {"$gt": ini}, "estado": "PAGAMENTO_OK"})
    PAGOS.set(pagos)

    # Tempo médio até pagamento
    pipeline = [
        {"$match": {"estado": "PAGAMENTO_OK", "ts": {"$gt": ini}}},
        {"$project": {"delta": {"$subtract": ["$ts", "$criado_em"]}}},
        {"$group": {"_id": None, "avg": {"$avg": "$delta"}}},
    ]
    res = list(ctx.aggregate(pipeline))
    TEMPO_PG_SECS.set(res[0]["avg"] / 1000 if res else 0)  # ms→s

def prometheus_response():
    atualizar()
    return generate_latest(), CONTENT_TYPE_LATEST

def json_response():
    atualizar()
    return {
        "leads": LEADS.collect()[0].samples[0].value,
        "qualificados": QUALIFICADOS.collect()[0].samples[0].value,
        "pagamentos": PAGOS.collect()[0].samples[0].value,
        "tempo_medio_pg_s": TEMPO_PG_SECS.collect()[0].samples[0].value,
    }
