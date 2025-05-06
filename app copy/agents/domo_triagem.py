"""
Aplica as 12 perguntas de triagem, persistindo cursor por telefone.
"""
from pathlib import Path
import json
from app.agents.agente_base import AgenteBase
from app.utils.contexto import obter_contexto, salvar_contexto

TRILHA_ID = "POS_TRIAGEM"
TRILHA_PATH = Path(__file__).resolve().parent.parent / "trilhas" / "trilha_pos_triagem.json"
TRILHA = json.loads(TRILHA_PATH.read_text(encoding="utf-8"))["etapas"]
TOTAL = len(TRILHA)

class DomoTriagem(AgenteBase):
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        ctx = obter_contexto(telefone)
        cursor = ctx.get("trilha_cursor", {"id": TRILHA_ID, "etapa": 0})
        if cursor["id"] != TRILHA_ID:
            cursor = {"id": TRILHA_ID, "etapa": 0}

        prox = cursor["etapa"] + 1
        if prox > TOTAL:
            # trilha concluída, muda estado
            salvar_contexto(telefone, novo_estado="TRIAGEM_CONCLUIDA", trilha_cursor=None)
            return "Obrigado! Triagem concluída. Em breve um profissional analisará suas respostas. 🙏"

        pergunta = TRILHA[str(prox)]["pergunta"]
        salvar_contexto(telefone, trilha_cursor={"id": TRILHA_ID, "etapa": prox})
        return pergunta
