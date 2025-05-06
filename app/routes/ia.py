# ===========================================================
# Arquivo: routes/ia.py
# (Contém a lógica para processar comandos específicos como agendar)
# ===========================================================
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import stripe # Importa a biblioteca do Stripe
from datetime import datetime, timedelta # Para expiração da sessão

# Ajuste os imports das funções utilitárias conforme a estrutura do seu projeto
# Assume que estão em app/utils/
from app.utils.agenda import (
    agendar_consulta,
    cancelar_consulta,
    consultar_proximo_horario_disponivel,
    formatar_horario_local
)
from app.utils.mensageria import enviar_mensagem
# Assume que followup.py existe e tem iniciar_sessao (se usado)
# from app.utils.followup import iniciar_sessao
# Assume que config.py existe e tem a chave do Stripe
from app.config import STRIPE_SECRET_KEY

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cria um roteador FastAPI para este módulo
router = APIRouter()

# Define a chave secreta do Stripe (carregada da configuração)
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    logging.info("IA Route: Chave secreta do Stripe configurada.")
else:
    logging.warning("IA Route: ⚠️ Chave secreta do Stripe (STRIPE_SECRET_KEY) não configurada.")
    # Considerar levantar um erro ou desabilitar funcionalidade de pagamento

# Modelo Pydantic para validar a entrada da API /ia-comando (se usada)
class ComandoIAInput(BaseModel):
    telefone: str
    nome: str
    comando: str # Ex: "quero agendar", "ver horário", "cancelar"

# --- Endpoint da API (Opcional) ---
@router.post("/ia-comando", summary="Processa comandos específicos da IA", tags=["IA"])
async def processar_comando_post(dados: ComandoIAInput):
    """
    Recebe um comando específico (agendar, cancelar, ver horário)
    e executa a ação correspondente. (Endpoint HTTP opcional)
    """
    # Verifica se a API do Stripe está configurada antes de prosseguir com agendamento
    if "agendar" in dados.comando.lower() and not STRIPE_SECRET_KEY:
         logging.error("IA Route: ❌ Tentativa de agendamento via API sem STRIPE_SECRET_KEY.")
         raise HTTPException(status_code=503, detail="Funcionalidade de pagamento indisponível.")

    # Chama a função principal que processa o comando
    resultado = await processar_comando(dados.dict())
    # Retorna o resultado da função
    return resultado

# --- Função Principal de Processamento de Comandos ---
# Esta função é chamada pelo endpoint acima e também diretamente por nlp.py

async def processar_comando(dados: dict) -> dict:
    """
    Processa comandos específicos vindos da interação do usuário ou da IA.

    Args:
        dados (dict): Dicionário contendo 'telefone', 'nome' e 'comando'.

    Returns:
        dict: Dicionário com o status da operação e mensagens relevantes.
    """
    telefone = dados.get("telefone")
    nome = dados.get("nome", "Cliente") # Usa 'Cliente' como nome padrão
    comando = dados.get("comando", "").lower() # Pega o comando e converte para minúsculas

    # Validação básica de entrada
    if not telefone or not comando:
        logging.warning("IA Route: Comando recebido sem telefone ou comando.")
        # Retorna um erro ou uma resposta padrão indicando falha
        # Não levanta HTTPException aqui pois pode ser chamado internamente por nlp.py
        return {"status": "erro_input", "mensagem": "Dados insuficientes para processar comando."}

    logging.info(f"IA Route: Processando comando '{comando}' para {telefone} ({nome})...")

    # --- Lógica para Comando "agendar" ---
    if "agendar" in comando:
        # Verifica novamente se Stripe está configurado
        if not STRIPE_SECRET_KEY:
            logging.error("IA Route: ❌ Tentativa de agendamento sem STRIPE_SECRET_KEY configurada.")
            msg_erro = "Desculpe, a opção de agendamento online não está disponível no momento."
            # Não envia mensagem aqui, pois nlp.py tratará a resposta
            # await enviar_mensagem(telefone, msg_erro)
            return {"status": "erro_config_stripe", "mensagem": msg_erro}

        # TODO: Descomentar se a função iniciar_sessao for usada para tracking
        # Inicia a sessão de pagamento/follow-up (se aplicável)
        # iniciar_sessao(telefone, nome) # Registra a tentativa no DB de follow-up

        try:
            # Cria uma sessão de checkout no Stripe
            logging.info(f"IA Route: Criando sessão Stripe Checkout para {telefone}...")
            # Define o URL base (pode vir do .env)
            base_url = os.getenv("APP_BASE_URL", "[https://famdomes.com.br](https://famdomes.com.br)") # Exemplo
            success_url = f"{base_url}/sucesso?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{base_url}/cancelado"

            session = stripe.checkout.Session.create(
                payment_method_types=["card", "boleto"], # Aceita cartão e boleto
                line_items=[{
                    "price_data": {
                        "currency": "brl", # Moeda brasileira
                        "product_data": {"name": "Consulta Inicial FAMDOMES"}, # Nome do produto
                        "unit_amount": 10000, # Preço em centavos (R$ 100,00)
                    },
                    "quantity": 1, # Quantidade
                }],
                mode="payment", # Modo de pagamento único
                # URLs para redirecionamento após sucesso ou cancelamento
                success_url=success_url,
                cancel_url=cancel_url,
                # Metadados para identificar o cliente no webhook
                metadata={
                    "telefone": telefone,
                    "nome": nome
                },
                # Configuração para Boleto (opcional, mas recomendada)
                payment_intent_data={
                     # 'setup_future_usage': 'off_session' # Pode não ser necessário para pagamentos únicos
                },
                # Expiração da sessão de checkout (ex: 2 horas)
                expires_at=int((datetime.now() + timedelta(hours=2)).timestamp())
            )
            logging.info(f"IA Route: Sessão Stripe criada com ID: {session.id} para {telefone}")

            # Monta a mensagem com o link de pagamento para o usuário
            msg_link = f"✅ Ótimo! Para agendar sua consulta inicial (valor R$100,00), por favor, realize o pagamento seguro através deste link:\n{session.url}\n\nO link expira em breve."
            # A mensagem será enviada por nlp.py, aqui apenas retornamos os dados
            # await enviar_mensagem(telefone, msg_link)
            # Retorna o status e a URL de checkout
            return {"status": "link_gerado", "checkout_url": session.url, "mensagem": msg_link}

        except stripe.error.StripeError as e:
             # Erro específico do Stripe
             logging.error(f"IA Route: ❌ Erro Stripe ao criar checkout para {telefone}: {e}")
             msg_erro = "❌ Desculpe, ocorreu um erro ao tentar gerar o link de pagamento com nosso parceiro. Por favor, tente novamente mais tarde ou entre em contato conosco."
             # await enviar_mensagem(telefone, msg_erro)
             return {"status": "erro_stripe", "mensagem": msg_erro}
        except Exception as e:
             # Outro erro inesperado
             logging.exception(f"IA Route: ❌ Erro inesperado ao criar checkout para {telefone}:")
             msg_erro = "❌ Desculpe, ocorreu um erro inesperado ao gerar seu link de pagamento. Tente novamente mais tarde."
             # await enviar_mensagem(telefone, msg_erro)
             return {"status": "erro_desconhecido", "mensagem": msg_erro}

    # --- Lógica para Comando "cancelar" ---
    elif "cancelar" in comando:
        logging.info(f"IA Route: Processando cancelamento de consulta para {telefone}...")
        # Chama a função para cancelar consultas futuras
        # TODO: Implementar a função cancelar_consulta em utils/agenda.py
        consultas_canceladas = cancelar_consulta(telefone) # Assume que retorna int
        if consultas_canceladas > 0:
            msg = f"✅ Sua(s) {consultas_canceladas} consulta(s) futura(s) foi(ram) cancelada(s) com sucesso."
            # await enviar_mensagem(telefone, msg)
            return {"status": "consulta_cancelada", "quantidade": consultas_canceladas, "mensagem": msg}
        else:
            msg = "Não encontrei nenhuma consulta futura agendada para cancelar em seu nome."
            # await enviar_mensagem(telefone, msg)
            return {"status": "nenhuma_consulta_encontrada", "mensagem": msg}

    # --- Lógica para Comando "horário" ou "disponível" ---
    elif "horário" in comando or "disponível" in comando or "disponivel" in comando:
        logging.info(f"IA Route: Consultando próximo horário disponível para {telefone}...")
        # Chama a função para consultar o próximo horário livre
        # TODO: Implementar consultar_proximo_horario_disponivel e formatar_horario_local em utils/agenda.py
        proximo_horario_utc = consultar_proximo_horario_disponivel() # Assume que retorna datetime UTC ou None
        if proximo_horario_utc:
            # Formata o horário para o fuso local antes de enviar
            horario_formatado = formatar_horario_local(proximo_horario_utc, 'America/Sao_Paulo') # Exemplo de fuso
            msg = f"📅 O próximo horário disponível para agendamento é: {horario_formatado} (Horário de Brasília)."
            # await enviar_mensagem(telefone, msg)
            return {"status": "horario_enviado", "horario_utc": proximo_horario_utc.isoformat(), "horario_formatado": horario_formatado, "mensagem": msg}
        else:
            msg = "📅 Desculpe, não consegui encontrar um horário disponível no momento. Por favor, tente novamente mais tarde."
            # await enviar_mensagem(telefone, msg)
            return {"status": "horario_indisponivel", "mensagem": msg}

    # --- Comando Desconhecido ---
    else:
        logging.warning(f"IA Route: Comando IA desconhecido recebido de {telefone}: '{comando}'")
        # Mensagem padrão para comandos não reconhecidos
        msg = "🤖 Desculpe, não entendi o que você deseja fazer. Você pode me pedir para 'agendar consulta', 'cancelar consulta' ou 'ver próximo horário disponível'."
        # await enviar_mensagem(telefone, msg)
        return {"status": "comando_desconhecido", "mensagem": msg}

# Adicionar import timedelta se não estiver presente
from datetime import timedelta

