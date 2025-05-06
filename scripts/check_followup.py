from utils.followup import checar_followup
from app.utils.mensageria import enviar_mensagem

mensagens = checar_followup()

for texto in mensagens:
    print(f"[ENVIAR] {texto}")
    # Aqui você pode acionar o canal real de mensageria se desejar:
    # telefone = extrair_telefone(texto)  # ou adaptar o followup para retornar tel
    # enviar_mensagem(telefone, texto)
