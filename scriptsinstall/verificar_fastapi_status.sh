#!/bin/bash

echo "🔍 Verificando status do serviço FastAPI..."

# Exibe status resumido do systemd
echo -e "\n🟦 STATUS DO SERVIÇO:"
systemctl status fastapi.service --no-pager -n 10

# Exibe logs recentes do journal
echo -e "\n📜 ÚLTIMOS LOGS (últimos 20 eventos):"
journalctl -u fastapi.service -n 20 --no-pager --output=short

# Pergunta se deseja seguir acompanhando o log ao vivo
echo -e "\n👁️ Deseja seguir monitorando em tempo real? (CTRL+C para sair)"
read -p "Pressione ENTER para continuar..."

# Log ao vivo com filtro
journalctl -u fastapi.service -f --output=short
