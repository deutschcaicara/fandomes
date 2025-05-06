# ===========================================================
# Arquivo: config.py
# (Baseado no arquivo original fornecido)
# ===========================================================
import os
from dotenv import load_dotenv
import logging # Adicionado para logar carregamento

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações do Banco de Dados ---
MONGO_URI = os.getenv("MONGO_URI") # String de conexão do MongoDB

# --- Configurações de Pagamento (Stripe) ---
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY") # Chave secreta do Stripe
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET") # Chave secreta do webhook do Stripe

# --- Configurações da IA (Ollama) ---
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434") # URL base da API do Ollama (com default)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3") # Modelo padrão do Ollama a ser usado

# --- Configurações da API Interna ---
API_KEY = os.getenv("API_KEY") # Chave para proteger endpoints internos da API (se houver)

# --- Configurações do WhatsApp Cloud API ---
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL") # URL da API do WhatsApp (ex: https://graph.facebook.com/v19.0/MEU_PHONE_ID/messages)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN") # Token de acesso permanente ou temporário da API
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN") # Token de verificação do webhook do WhatsApp
WHATSAPP_FAMILIAR = os.getenv("WHATSAPP_FAMILIAR") # Número de telefone para receber alertas de risco (formato internacional)

# --- Configurações do RocketChat (Opcional, se usado para escalação) ---
ROCKETCHAT_URL = os.getenv("ROCKETCHAT_URL") # URL da instância do RocketChat
ROCKETCHAT_TOKEN = os.getenv("ROCKETCHAT_TOKEN") # Token de API do RocketChat
ROCKETCHAT_USER_ID = os.getenv("ROCKETCHAT_USER_ID") # ID do usuário bot no RocketChat

# --- Configurações do Google (Opcional, se usado para OAuth ou outras APIs) ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# --- Diretório Base da Aplicação ---
# Obtém o diretório onde este arquivo config.py está localizado
# Útil para construir caminhos para outros arquivos (ex: prompts)
# Ajuste o __file__ se a estrutura for diferente (ex: app/config.py)
try:
    # Assume que este arquivo está em app/config.py
    # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Diretório pai (app)
    # Ou se estiver na raiz do projeto:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback se __file__ não estiver definido (ex: execução interativa)
    BASE_DIR = os.getcwd()


# --- Validações e Logging ---
# Configuração básica de logging (pode ser movida para main.py)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("Carregando configurações...") # Usar logging.info seria melhor
logging.info("Carregando configurações...")

# Validações essenciais
essential_vars = {
    "MONGO_URI": MONGO_URI,
    "OLLAMA_API_URL": OLLAMA_API_URL,
    "WHATSAPP_API_URL": WHATSAPP_API_URL,
    "WHATSAPP_TOKEN": WHATSAPP_TOKEN,
    "WHATSAPP_VERIFY_TOKEN": WHATSAPP_VERIFY_TOKEN,
    "STRIPE_SECRET_KEY": STRIPE_SECRET_KEY,
    "STRIPE_WEBHOOK_SECRET": STRIPE_WEBHOOK_SECRET,
}

missing_vars = [name for name, value in essential_vars.items() if not value]
if missing_vars:
    logging.error(f"❌ ERRO FATAL: Variáveis de ambiente essenciais não definidas: {', '.join(missing_vars)}")
    # Considerar levantar uma exceção para impedir a inicialização da aplicação
    # raise ValueError(f"Variáveis de ambiente essenciais não definidas: {', '.join(missing_vars)}")
else:
    logging.info("✅ Variáveis de ambiente essenciais carregadas.")

# Log informativo das configurações (sem expor segredos completos)
logging.info(f" - MONGO_URI: {'Definido' if MONGO_URI else 'Não definido'}")
logging.info(f" - OLLAMA_API_URL: {OLLAMA_API_URL}")
logging.info(f" - OLLAMA_MODEL: {OLLAMA_MODEL}")
logging.info(f" - WHATSAPP_API_URL: {'Definido' if WHATSAPP_API_URL else 'Não definido'}")
logging.info(f" - WHATSAPP_TOKEN: {'Definido' if WHATSAPP_TOKEN else 'Não definido'}")
logging.info(f" - WHATSAPP_VERIFY_TOKEN: {'Definido' if WHATSAPP_VERIFY_TOKEN else 'Não definido'}")
logging.info(f" - WHATSAPP_FAMILIAR: {WHATSAPP_FAMILIAR if WHATSAPP_FAMILIAR else 'Não definido'}")
logging.info(f" - STRIPE_SECRET_KEY: {'Definido' if STRIPE_SECRET_KEY else 'Não definido'}")
logging.info(f" - STRIPE_WEBHOOK_SECRET: {'Definido' if STRIPE_WEBHOOK_SECRET else 'Não definido'}")
logging.info(f" - BASE_DIR: {BASE_DIR}")

