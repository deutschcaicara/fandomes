# ===========================================================
# carrega e pesquisa intents de TODOS os arquivos .json
# ===========================================================
from __future__ import annotations
from pathlib import Path
import json, re, difflib
from functools import lru_cache
from typing import Dict, Any, Tuple

PASTA = Path(__file__).resolve().parents[1] / "intents"
RGX_CLEAN = re.compile(r"[^a-z0-9 ]")

def _normalizar(txt: str) -> str:
    return RGX_CLEAN.sub("", txt.casefold())

@lru_cache
def _carga() -> Dict[str, Dict[str, Any]]:
    dados: Dict[str, Dict[str, Any]] = {}
    for arq in PASTA.glob("*.json"):
        with arq.open(encoding="utf-8") as f:
            dados.update(json.load(f))
    # index de triggers normalizados
    for k, v in dados.items():
        v["triggers_norm"] = [_normalizar(t) for t in v.get("triggers", [])]
    return dados

# ---------- API pública ----------
def obter_intent(id_intent: str) -> Dict[str, Any] | None:
    return _carga().get(id_intent)

def buscar_por_trigger(texto: str, limiar: float = 0.75) -> Tuple[str | None, float]:
    txt_norm = _normalizar(texto)
    melhor, score = None, 0.0
    for intent_id, info in _carga().items():
        for trg in info["triggers_norm"]:
            if not trg:
                continue
            s = difflib.SequenceMatcher(None, txt_norm, trg).ratio()
            if s > score:
                melhor, score = intent_id, s
    return (melhor, score) if score >= limiar else (None, score)
