from fastapi import APIRouter, Request
from app.models.pagamentos import PagamentoRequest
import stripe
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from app.utils.agenda import agendar_consulta
from app.utils.mensageria import enviar_mensagem

stripe.api_key = STRIPE_SECRET_KEY
router = APIRouter()

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return {"erro": str(e)}

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        telefone = session["metadata"].get("telefone")
        nome = session["metadata"].get("nome", "Paciente")
        email = session["metadata"].get("email")

        horario = agendar_consulta(telefone, nome, email)

        msg_paciente = (
            f"✅ Olá {nome}, seu agendamento está confirmado!\n"
            f"🕒 Horário: {horario.strftime('%d/%m %H:%M')}\n"
            "Você será chamado pelo profissional nesse horário. Até lá!"
        )
        enviar_mensagem(telefone, msg_paciente)

        msg_medico = f"👨‍⚕️ Novo agendamento: {nome} ({telefone}) às {horario.strftime('%d/%m %H:%M')}."
        enviar_mensagem("MEDICO", msg_medico)

        return {"status": "confirmado"}

    return {"status": "ignorado"}
