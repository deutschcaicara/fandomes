#!/bin/bash

echo "🧪 Testando FAMDOMES via FastAPI (sem n8n)..."

BASE="https://api.famdomes.com.br"
NUM="553799999999"
NOME="Diego Teste"

echo -e "\n📩 Teste WhatsApp > FastAPI > IA"
curl -s -X POST "$BASE/chat/webhook/whatsapp/" \
-H "Content-Type: application/json" \
-d @scripts_final_mvp/payload_whatsapp.json

echo -e "\n\n💳 Criar Sessão Stripe"
curl -s -X POST "$BASE/pagamento/criar_sessao" \
-H "Content-Type: application/json" \
-H "X-API-Key: famdomes_master_key" \
-d @scripts_final_mvp/payload_criar_sessao.json

echo -e "\n\n📦 Simular Webhook Stripe"
curl -s -X POST "$BASE/pagamento/webhook" \
-H "Content-Type: application/json" \
-H "stripe-signature: whsec_Lj0mUYVFOtrat0wzwmrsgwRmj0fbzyOX" \
-d @scripts_final_mvp/payload_stripe_webhook.json

echo -e "\n✅ Fim dos testes."
