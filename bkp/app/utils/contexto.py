# ===========================================================
# Arquivo: utils/contexto.py
# (v5 - Adicionado estado AGUARDANDO_RESPOSTA_QUALIFICACAO)
# ===========================================================
from pymongo import MongoClient
# Ajuste o import se config.py estiver em um diretório diferente
from app.config import MONGO_URI
from datetime import datetime
import logging

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Estados Possíveis da Conversa (Baseado no Mapeamento) ---
ESTADOS_CONVERSA = [
    "INICIAL",
    "IDENTIFICANDO_NECESSIDADE", # Recebe a 1a resposta do usuário
    "AGUARDANDO_RESPOSTA_QUALIFICACAO", # Estado após enviar a pergunta combinada (emocional + para quem)
    "EXPLICANDO_CONSULTA",
    "CONFIRMANDO_INTERESSE_AGENDAMENTO",
    "GERANDO_LINK_PAGAMENTO",
    "AGUARDANDO_PAGAMENTO",
    "PAGAMENTO_CONFIRMADO",
    "CONFIRMANDO_AGENDAMENTO",
    "INICIANDO_QUESTIONARIO",
    "COLETANDO_RESPOSTA_QUESTIONARIO",
    "FINALIZANDO_ONBOARDING",
    "SUPORTE_FAQ",
    "RESPONDENDO_COM_IA",
    "VERIFICANDO_SATISFACAO_RESPOSTA",
    "RISCO_DETECTADO",
    "PEDIDO_ATENDENTE_HUMANO",
    "NOTIFICANDO_EQUIPE", # Estado transitório antes de AGUARDANDO_ATENDENTE
    "AGUARDANDO_ATENDENTE"
]
# -------------------------------------------------------------

# Variáveis globais para conexão com DB (inicializadas no bloco try)
mongo = None
db = None
contextos_db = None
respostas_ia_db = None

try:
    # Estabelece conexão com MongoDB
    if MONGO_URI:
        mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # Timeout de conexão
        # Força a conexão para verificar se está funcionando
        mongo.server_info()
        db = mongo["famdomes"] # Nome do banco de dados
        contextos_db = db["contexto_conversa"] # Coleção para contextos
        respostas_ia_db = db["respostas_ia"] # Coleção para histórico de interações
        # Cria índices se não existirem (melhora performance de busca)
        contextos_db.create_index("telefone", unique=True)
        respostas_ia_db.create_index("telefone")
        respostas_ia_db.create_index("criado_em")
        logging.info("Conexão com MongoDB estabelecida e índices verificados/criados.")
    else:
        logging.error("❌ MONGO_URI não definido. Não foi possível conectar ao MongoDB.")
except Exception as e:
    # Loga erro se a conexão falhar
    logging.error(f"❌ ERRO ao conectar com MongoDB ou criar índices: {e}")
    mongo = None
    db = None
    contextos_db = None
    respostas_ia_db = None

def salvar_contexto(telefone: str, dados_atualizacao: dict):
    """
    Salva ou atualiza o contexto da conversa para um telefone.
    Inclui o estado atual da conversa e metadados.
    """
    # Validação inicial
    if contextos_db is None or not telefone or not isinstance(dados_atualizacao, dict):
        logging.error(f"❌ Falha ao salvar contexto para {telefone}: DB indisponível ou dados inválidos.")
        return False
    try:
        # Garante que o estado seja válido, se fornecido
        if "estado" in dados_atualizacao and dados_atualizacao["estado"] not in ESTADOS_CONVERSA:
            logging.warning(f"⚠️ Tentativa de salvar estado inválido '{dados_atualizacao['estado']}' para {telefone}. Usando estado anterior ou INICIAL.")
            contexto_atual = obter_contexto(telefone) # Busca contexto atual para pegar estado válido
            dados_atualizacao["estado"] = contexto_atual.get("estado", "INICIAL") # Mantém o atual ou vai para INICIAL

        # Recupera o contexto anterior para mesclar metadados
        contexto_anterior = contextos_db.find_one({"telefone": telefone}) or {}

        # 🔁 Fundir metadados (meta_conversa) de forma inteligente
        meta_conversa_atualizada = contexto_anterior.get("meta_conversa", {})
        if "meta_conversa" in dados_atualizacao:
            meta_nova = dados_atualizacao["meta_conversa"]
            meta_conversa_atualizada = atualizar_meta_conversa(meta_conversa_atualizada, meta_nova)
        # Garante que a meta_conversa final esteja nos dados a serem salvos
        dados_atualizacao["meta_conversa"] = meta_conversa_atualizada


        # Prepara o $set, garantindo que não sobrescreva campos imutáveis como telefone ou _id
        update_set = {k: v for k, v in dados_atualizacao.items() if k not in ['telefone', '_id', 'criado_em']}

        # Operação de update/insert (upsert) no MongoDB
        result = contextos_db.update_one(
            {"telefone": telefone}, # Filtro para encontrar o documento
            {
                "$set": update_set, # Campos a serem atualizados ou adicionados
                "$currentDate": {"ultima_atualizacao": True}, # Atualiza timestamp da última modificação
                # Define campos apenas na inserção (se o documento não existir)
                "$setOnInsert": {
                    "telefone": telefone,
                    "criado_em": datetime.utcnow(), # Timestamp de criação
                    "estado": dados_atualizacao.get("estado", "INICIAL") # Garante estado inicial no upsert
                 }
            },
            upsert=True # Cria o documento se não existir
        )
        # Log de sucesso
        if result.upserted_id:
            logging.info(f"📌 Novo contexto criado para {telefone}. Estado inicial: {dados_atualizacao.get('estado', 'INICIAL')}")
        elif result.modified_count > 0:
            logging.info(f"📌 Contexto atualizado para {telefone}. Novo estado: {dados_atualizacao.get('estado', 'N/A')}")
        else:
            # Se não modificou, pode ser que os dados sejam os mesmos
            logging.info(f"📌 Contexto para {telefone} não modificado (dados iguais?). Estado: {dados_atualizacao.get('estado', 'N/A')}")

        return True
    except Exception as e:
        # Log de erro crítico com traceback
        logging.exception(f"❌ ERRO CRÍTICO ao salvar contexto para {telefone}:")
        return False

def atualizar_meta_conversa(meta_antiga: dict, meta_nova: dict) -> dict:
    """
    Mescla campos do novo JSON (meta_nova) com os anteriores (meta_antiga).
    Prioriza dados novos, mas não sobrescreve dados antigos com valores vazios ou nulos.
    Listas são concatenadas e duplicatas removidas (se possível).
    """
    # Garante que ambos sejam dicionários
    if not isinstance(meta_antiga, dict): meta_antiga = {}
    if not isinstance(meta_nova, dict): meta_nova = {}

    resultado = meta_antiga.copy() # Começa com os dados antigos

    for chave, valor_novo in meta_nova.items():
        # Ignora chaves com valores nulos ou vazios no novo dict,
        # a menos que a chave não exista no antigo (para permitir adicionar chaves vazias)
        if valor_novo is None or valor_novo == "" or (isinstance(valor_novo, list) and not valor_novo):
             if chave not in resultado: # Se a chave é nova, adiciona mesmo se vazia/nula
                 resultado[chave] = valor_novo
             continue # Caso contrário (chave já existe), ignora para não sobrescrever dado existente com vazio

        valor_antigo = resultado.get(chave)

        # Se for uma lista, combina e remove duplicatas (se os itens forem hashable)
        if isinstance(valor_novo, list):
            lista_antiga = valor_antigo if isinstance(valor_antigo, list) else []
            try:
                # Tenta converter para set para remover duplicatas (pode falhar se lista contiver dicts)
                resultado[chave] = list(set(lista_antiga + valor_novo))
            except TypeError:
                # Se não puder usar set (ex: lista de dicts), apenas concatena itens únicos
                resultado[chave] = lista_antiga + [item for item in valor_novo if item not in lista_antiga] # Evita duplicatas simples
        # Se o valor antigo não existe, ou é considerado "vazio", atualiza com o novo
        elif valor_antigo is None or valor_antigo == "" or valor_antigo == "desconhecido":
             resultado[chave] = valor_novo
        # Se ambos existem e não são listas, o novo valor geralmente prevalece
        # Exceção: não sobrescrever um valor específico com 'desconhecido'
        elif valor_novo != "desconhecido":
             resultado[chave] = valor_novo
        # Se valor_novo é 'desconhecido' e já existe um valor antigo, mantém o antigo

    return resultado


def obter_contexto(telefone: str) -> dict:
    """Obtém o contexto completo da conversa para um telefone."""
    # Validação inicial
    if contextos_db is None or not telefone:
        logging.warning(f"Tentativa de obter contexto sem DB ou telefone para {telefone}.")
        return {"estado": "INICIAL", "meta_conversa": {}} # Retorna um contexto padrão mínimo
    try:
        # Busca o contexto no MongoDB
        contexto = contextos_db.find_one({"telefone": telefone})
        if contexto:
            # Garante que sempre tenha 'estado' e 'meta_conversa' para evitar erros posteriores
            if "estado" not in contexto or not contexto["estado"]:
                contexto["estado"] = "INICIAL"
            if "meta_conversa" not in contexto or not isinstance(contexto["meta_conversa"], dict):
                contexto["meta_conversa"] = {}
            # Remove o _id do MongoDB para evitar problemas de serialização se necessário
            contexto.pop('_id', None)
            return contexto
        else:
            # Se não encontrou, retorna um contexto inicial padrão
            logging.info(f"Nenhum contexto encontrado para {telefone}, retornando padrão INICIAL.")
            return {"estado": "INICIAL", "meta_conversa": {}, "telefone": telefone}
    except Exception as e:
        # Log de erro e retorna padrão seguro
        logging.error(f"❌ ERRO ao obter contexto para {telefone}: {e}")
        return {"estado": "INICIAL", "meta_conversa": {}, "erro": "Falha ao buscar contexto"}

def limpar_contexto(telefone: str) -> bool:
    """Remove o contexto de conversa e histórico de IA para um telefone."""
    deleted_context = False
    deleted_history = False

    # Limpa contexto da conversa
    if contextos_db is not None and telefone:
        try:
            result_context = contextos_db.delete_one({"telefone": telefone})
            deleted_context = result_context.deleted_count > 0
            if deleted_context:
                 logging.info(f"🗑️ Contexto da conversa limpo para {telefone}.")
            else:
                 logging.info(f"Nenhum contexto de conversa encontrado para limpar para {telefone}.")
        except Exception as e:
            logging.error(f"❌ ERRO ao limpar contexto da conversa para {telefone}: {e}")

    # Limpa histórico de IA associado
    if respostas_ia_db is not None and telefone:
        try:
            result_history = respostas_ia_db.delete_many({"telefone": telefone})
            deleted_history = result_history.deleted_count > 0
            if deleted_history:
                 logging.info(f"🗑️ Histórico de IA ({result_history.deleted_count} registros) limpo para {telefone}.")
        except Exception as e:
            logging.error(f"❌ ERRO ao limpar histórico de IA para {telefone}: {e}")

    # Retorna True se pelo menos um dos dois foi limpo com sucesso
    return deleted_context or deleted_history


def salvar_resposta_ia(telefone: str, canal: str, mensagem_usuario: str, resposta_gerada: str, intent: str, entidades: dict, risco: bool, sentimento: str | None = None):
    """Salva a interação (mensagem do usuário e resposta da IA) no histórico."""
    # Validação inicial
    if respostas_ia_db is None:
        logging.error("❌ Falha ao salvar resposta IA: DB indisponível.")
        return
    try:
        # Garante que entidades seja um dicionário, mesmo que vazio
        entidades_validas = entidades if isinstance(entidades, dict) else {}

        # Cria o documento para inserir no histórico
        doc = {
            "telefone": telefone,
            "canal": canal,
            "mensagem_usuario": mensagem_usuario,
            "resposta_gerada": resposta_gerada,
            "intent": intent,
            "entidades": entidades_validas, # Dados extraídos pela IA (ex: nome, substância)
            "risco": risco, # Resultado da análise de risco
            "sentimento_detectado": sentimento, # [Trilha Emocional] Sentimento da mensagem do usuário
            "criado_em": datetime.utcnow() # Timestamp da interação
        }
        # Insere o documento na coleção de histórico
        respostas_ia_db.insert_one(doc)
        logging.info(f"💾 Interação salva no histórico de IA para {telefone}.")
    except Exception as e:
        # Log de erro
        logging.error(f"❌ ERRO ao salvar resposta IA no histórico: {e}")

