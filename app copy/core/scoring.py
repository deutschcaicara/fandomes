"""
Score simples de lead (0‑6) para escolher pitch.
"""
import re

PAT_URGENCIA = re.compile(r"\b(crise|desesperad[oa]|suic[ií]dio)\b", re.I)
PAT_PAGANTE  = re.compile(r"\b(cart[aã]o|pix|particular)\b", re.I)
PAT_NEG_PRECO = re.compile(r"\b(caro|muito caro|sem dinheiro|nao posso)\b", re.I)

def score_lead(texto: str) -> int:
    s = 0
    if PAT_URGENCIA.search(texto):
        s += 3
    if PAT_PAGANTE.search(texto):
        s += 2
    if PAT_NEG_PRECO.search(texto):
        s -= 2
    return max(0, min(6, s))
