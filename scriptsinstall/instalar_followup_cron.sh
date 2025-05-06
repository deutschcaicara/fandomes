#!/bin/bash

echo "🔧 Criando pasta de logs..."
mkdir -p /home/ubuntu/famdomes_backend/logs

echo "📄 Criando script check_followup.py..."
cat << 'EOF' > /home/ubuntu/famdomes_backend/scripts/check_followup.py
from utils.followup import checar_followup
from app.utils.mensageria import enviar_mensagem

mensagens = checar_followup()

for texto in mensagens:
    print(f"[ENVIAR] {texto}")
    # Aqui você pode acionar o canal real de mensageria se desejar:
    # telefone = extrair_telefone(texto)  # ou adaptar o followup para retornar tel
    # enviar_mensagem(telefone, texto)
EOF

echo "🛠️ Adicionando cron job para rodar a cada 5 minutos..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/famdomes_backend/venv/bin/python /home/ubuntu/famdomes_backend/scripts/check_followup.py >> /home/ubuntu/famdomes_backend/logs/followup.log 2>&1") | crontab -

echo "✅ Cronjob de follow-up criado com sucesso."
