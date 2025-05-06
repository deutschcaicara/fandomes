#!/bin/bash

echo "🌐 Healthcheck externo via domínio público"
echo "=========================================="

BASE_URL="https://api.famdomes.com.br"
API_KEY="SUA_CHAVE_REAL_AQUI"

# Teste do WhatsApp webhook externo (mock)
echo -e "\n📲 Webhook WhatsApp público:"
curl -s -X POST "$BASE_URL/chat/webhook/whatsapp" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"messages": [{"from": "55999999999", "text": {"body": "oi"}}]}' | jq .

# Teste comando IA externo
echo -e "\n🤖 Comando IA externo:"
curl -s -X POST "$BASE_URL/ia-comando" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"comando": "quero agendar", "telefone": "55999999999", "nome": "Diego"}' | jq .

# Teste agendamento público
echo -e "\n📅 Agendamento próximo (público):"
curl -s -X GET "$BASE_URL/agendamento/proximo" -H "x-api-key: $API_KEY" | jq .

echo -e "\n✅ Tudo respondendo externamente? Se sim, webhook do Facebook vai funcionar perfeito!"
