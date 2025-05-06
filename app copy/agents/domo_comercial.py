from __future__ import annotations
from app.agents.agente_base import AgenteBase
from app.core.scoring import score_lead
from app.utils.contexto import salvar_contexto, obter_contexto
from app.core.ia_direct import gerar_resposta_ia

PERGUNTAS = [
    "1/3 – Você procura ajuda para si ou para um familiar?",
    "2/3 – Prefere atendimento online ou presencial?",
    "3/3 – Consegue investir num cuidado profissional mensal?",
]

class DomoComercial(AgenteBase):
    async def _gerar_resposta(self, telefone: str, msg: str) -> str | None:
        ctx = obter_contexto(telefone)
        estado = ctx.get("estado", "INICIAL")
        meta = ctx.get("meta_conversa", {})
        etapa = meta.get("etapa_quali", 0)
        score = meta.get("score_lead", 0)

        # ---------------- Fluxo ----------------
        if estado == "INICIAL":
            salvar_contexto(telefone, novo_estado="MICRO", meta_conversa={"etapa_quali": 0})
            resposta = "Posso fazer 3 perguntas rápidas pra personalizar sua ajuda? 🙂"

        elif estado == "MICRO":
            if etapa < 3:
                prox = etapa + 1
                salvar_contexto(telefone, meta_conversa={"etapa_quali": prox})
                resposta = PERGUNTAS[etapa]
            else:
                score = score_lead(msg)
                salvar_contexto(
                    telefone, novo_estado="PITCH",
                    meta_conversa={"score_lead": score}
                )
                resposta = (
                    "Excelente! Recomendo o Plano Premium (R$ 199/mês). Topa conhecer?"
                    if score >= 4 else
                    "Perfeito! Temos Plano Essencial por R$ 79/mês. Quer saber mais?"
                )

        elif estado == "PITCH":
            salvar_contexto(telefone, novo_estado="CTA")
            resposta = "Segue o link de pagamento Pix instantâneo: https://pay.famdomes.com/px"

        elif estado == "CTA":
            if "sim" in msg.lower():
                salvar_contexto(telefone, novo_estado="AGUARDANDO_PAGTO")
                resposta = "Ótimo! Assim que o pagamento confirmar, começamos a triagem. 💚"
            else:
                salvar_contexto(telefone, novo_estado="RECUSA")
                resposta = "Sem problemas. Posso enviar conteúdo gratuito sobre primeiros passos?"

        else:
            resposta = None  # queda para generativo

        # ---------- Antiloop ----------
        if resposta:
            ultimo = ctx.get("ultimo_texto_bot", "")
            if resposta.strip().lower() == ultimo.strip().lower():
                resposta = await gerar_resposta_ia({"tel": telefone, "msg": msg})

        return resposta
