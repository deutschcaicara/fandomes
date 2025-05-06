"""
Gera intents/intents.json a partir de 'MAPEAMENTO DE INTENÇÕES – DOMO (FAM.txt)'.

Uso:
    python utils/gerar_intents.py > intents/intents.json
"""
import re, json, pathlib, sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
MAPA = RAIZ / "FAM.txt"

BASE = {
    "ACOLHIMENTO": {
        "triggers": ["", ""],
        "resposta": "Olá! Eu sou o DOMO. Estou aqui para te acompanhar. Como posso ajudar?",
        "escala_humano": False,
    },
    "PRESENCA_VIVA": {
        "triggers": [],
        "resposta": "Só passando para lembrar que estou aqui com você. Qualquer coisa, é só chamar. 🤗",
        "escala_humano": False,
    },
}

def parse():
    txt = MAPA.read_text(encoding="utf-8")
    blocos = re.split(r"\n────────────────────────────\n", txt)
    for bloco in blocos:
        m_id = re.search(r"INTENT\s+(\d+):\s+(.+)", bloco)
        if not m_id:
            continue
        intent_id = f"INTENT_{m_id.group(1).zfill(3)}"
        triggers = re.findall(r"TRIGGERS:\s+(.+)", bloco)
        resposta = re.findall(r"RESPOSTA:\s+(.+)", bloco)
        escala = "✅" in bloco or "⚠️" in bloco or "✅✅" in bloco
        yield intent_id, {
            "triggers": [t.strip("“”\" ") for t in (triggers[0].split("”,") if triggers else [])],
            "resposta": resposta[0] if resposta else "",
            "escala_humano": escala,
        }

def main():
    data = {**BASE, **{k: v for k, v in parse()}}
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
