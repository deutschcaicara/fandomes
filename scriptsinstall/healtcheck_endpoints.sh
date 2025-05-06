#!/bin/bash

echo "🔍 Healthcheck do Backend FastAPI FAMDOMES"
echo "========================================="

BASE_URL="http://localhost:8000"

# Lista de endpoints principais
declare -A endpoints=(
  ["/ia-in"]="POST"
  ["/ia-comando"]="POST"
  ["/agendamento/proximo"]="GET"
  ["/pagamento/webhook"]="POST"
  ["/chat/webhook/whatsapp"]="POST"
)

# Teste IA-IN
echo -e "\n🤖 /ia-in (teste IA)"
curl -s -X POST "$BASE_URL/ia-in" \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "Qual seu nome?", "telefone": "55999999999"}' | jq .

# Teste IA-COMANDO
echo -e "\n⚙️ /ia-comando (teste agendar)"
curl -s -X POST "$BASE_URL/ia-comando" \
  -H "Content-Type: application/json" \
  -d '{"comando": "quero agendar", "telefone": "55999999999", "nome": "Teste"}' | jq .

# Teste AGENDAMENTO
echo -e "\n📅 /agendamento/proximo"
curl -s "$BASE_URL/agendamento/proximo" | jq .

# Teste WEBHOOK Stripe
echo -e "\n💳 /pagamento/webhook (sem assinatura - deve falhar)"
curl -s -X POST "$BASE_URL/pagamento/webhook" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

# Teste WEBHOOK WhatsApp
echo -e "\n📲 /chat/webhook/whatsapp (mock)"
curl -s -X POST "$BASE_URL/chat/webhook/whatsapp" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"from": "55999999999", "text": {"body": "oi"}}]}' | jq .

echo -e "\n✅ Healthcheck finalizado."
