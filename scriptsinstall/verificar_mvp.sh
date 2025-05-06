#!/bin/bash

echo "🔍 Verificando variáveis de ambiente essenciais..."

vars=(
  "MONGO_URI"
  "STRIPE_SECRET_KEY"
  "STRIPE_WEBHOOK_SECRET"
  "OLLAMA_API_URL"
  "OLLAMA_MODEL"
  "WHATSAPP_API_URL"
  "WHATSAPP_TOKEN"
  "WHATSAPP_VERIFY_TOKEN"
  "WHATSAPP_FAMILIAR"
  "WHATSAPP_MEDICO"
  "API_KEY"
)

for var in "${vars[@]}"; do
  if [[ -z "${!var}" ]]; then
    echo "❌ Variável $var está vazia ou não definida"
  else
    echo "✅ $var encontrada"
  fi
done

echo "🔎 Verificando rotas da API em produção..."

curl -s https://api.famdomes.com.br/openapi.json | jq '.paths' > /dev/null && echo "✅ FastAPI ativo em produção" || echo "❌ Erro ao acessar API FastAPI"

echo "🔄 Teste de comando IA (modo produção):"
curl -s -X POST https://api.famdomes.com.br/ia-comando \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"telefone": "559999999999", "nome": "Teste", "comando": "quero agendar"}' | jq

echo "📦 Verificação completa."
echo "🔍 Verificando variáveis de ambiente essenciais...
"