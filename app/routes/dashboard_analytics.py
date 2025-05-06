from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from app.core.metrics import atualizar, LEADS, QUALIFICADOS, PAGOS, TEMPO_PG_SECS


router = APIRouter(prefix="/dashboard/analytics", tags=["Dashboard"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="dashboard/token")  # reaproveita auth existente

def _collect() -> dict:
    atualizar()  # atualiza gauges
    return {
        "leads": LEADS._value.get(),
        "qualificados": QUALIFICADOS._value.get(),
        "pagos": PAGOS._value.get(),
        "tempo_pg_segundos": TEMPO_PG_SECS._value.get(),
    }

@router.get("", summary="KPIs para o dashboard")
async def get_analytics(_: str = Depends(oauth2_scheme)):
    return _collect()
