# ===========================================================
# Arquivo: utils/agenda.py
# (Implementação das funções de agendamento com DB)
# ===========================================================
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import ConnectionFailure, DuplicateKeyError
# Ajuste o import se config.py estiver em um diretório diferente
from app.config import MONGO_URI
import logging
import pytz # Para lidar com fusos horários corretamente

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes de Configuração da Agenda ---
DURACAO_CONSULTA_MINUTOS = 20 # Duração de cada bloco de consulta
MAX_TENTATIVAS_AGENDAMENTO = 500 # Limite de blocos a procurar (~6 dias úteis)
HORARIO_OPERACAO_INICIO = 9 # Horário de início das consultas (9:00)
HORARIO_OPERACAO_FIM = 18  # Horário de fim (não agenda às 18:00, último bloco começa antes)
DIAS_UTEIS = [0, 1, 2, 3, 4] # 0=Segunda, 1=Terça, ..., 4=Sexta
FUSO_HORARIO_LOCAL = 'America/Sao_Paulo' # Fuso horário de operação

# --- Conexão com MongoDB ---
mongo_agenda = None
db_agenda = None
consultas_db = None

try:
    # Estabelece conexão com MongoDB
    if MONGO_URI:
        mongo_agenda = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_agenda.server_info() # Testa a conexão
        db_agenda = mongo_agenda["famdomes"] # Nome do banco de dados
        consultas_db = db_agenda["consultas_agendadas"] # Coleção para agendamentos
        # Cria índice único para garantir que não haja duas consultas no mesmo horário (UTC)
        consultas_db.create_index("horario_utc", unique=True)
        consultas_db.create_index("telefone") # Índice para busca por telefone
        consultas_db.create_index([("status", 1), ("horario_utc", 1)]) # Índice composto
        logging.info("AGENDA: Conexão com MongoDB estabelecida e índices verificados/criados.")
    else:
        logging.error("AGENDA: ❌ MONGO_URI não definido. Não foi possível conectar ao MongoDB.")
except ConnectionFailure as e:
     logging.error(f"AGENDA: ❌ Falha na conexão com MongoDB: {e}")
except Exception as e:
    logging.error(f"AGENDA: ❌ ERRO ao conectar com MongoDB ou criar índices: {e}")
    mongo_agenda = None
    db_agenda = None
    consultas_db = None

# --- Funções Auxiliares ---

def _proximo_horario_util(inicio_base_utc: datetime) -> datetime:
    """
    Avança o horário UTC para o próximo bloco de X minutos disponível
    dentro do horário de operação e dias úteis definidos.
    """
    horario_utc = inicio_base_utc.replace(tzinfo=timezone.utc) # Garante que está ciente do fuso UTC
    tz_local = pytz.timezone(FUSO_HORARIO_LOCAL)

    while True:
        # Arredonda para o início do próximo bloco de N minutos (para cima)
        minutos_atuais = horario_utc.minute
        minutos_para_proximo_bloco = (DURACAO_CONSULTA_MINUTOS - (minutos_atuais % DURACAO_CONSULTA_MINUTOS)) % DURACAO_CONSULTA_MINUTOS
        if minutos_para_proximo_bloco == 0 and (horario_utc.second > 0 or horario_utc.microsecond > 0):
            # Se já está no início do bloco mas tem segundos, avança um bloco inteiro
             horario_utc += timedelta(minutes=DURACAO_CONSULTA_MINUTOS)
        elif minutos_para_proximo_bloco > 0 :
            # Avança para o início do próximo bloco
            horario_utc += timedelta(minutes=minutos_para_proximo_bloco)

        # Zera segundos e microssegundos
        horario_utc = horario_utc.replace(second=0, microsecond=0)

        # Converte para o fuso local para verificar horário de operação e dia da semana
        horario_local = horario_utc.astimezone(tz_local)

        # Verifica se está dentro do horário de operação
        if horario_local.hour < HORARIO_OPERACAO_INICIO:
            # Se for antes do início, ajusta para o início do dia no fuso local e converte de volta para UTC
            horario_local = horario_local.replace(hour=HORARIO_OPERACAO_INICIO, minute=0)
            horario_utc = horario_local.astimezone(timezone.utc)
            continue # Reavalia o novo horário

        if horario_local.hour >= HORARIO_OPERACAO_FIM:
            # Se for depois do fim, avança para o dia seguinte e ajusta para o início
            horario_local += timedelta(days=1)
            horario_local = horario_local.replace(hour=HORARIO_OPERACAO_INICIO, minute=0)
            horario_utc = horario_local.astimezone(timezone.utc)
            continue # Reavalia o novo horário

        # Verifica se é dia útil (no fuso local)
        if horario_local.weekday() not in DIAS_UTEIS:
            # Se não for dia útil, avança para o próximo dia e ajusta para o início
            # Loop para garantir que caia em um dia útil
            while horario_local.weekday() not in DIAS_UTEIS:
                 horario_local += timedelta(days=1)
            horario_local = horario_local.replace(hour=HORARIO_OPERACAO_INICIO, minute=0)
            horario_utc = horario_local.astimezone(timezone.utc)
            continue # Reavalia o novo horário

        # Se passou por todas as verificações, o horário é válido
        return horario_utc

def formatar_horario_local(horario_utc: datetime | None, fuso_destino: str = FUSO_HORARIO_LOCAL) -> str:
    """Formata um horário UTC para uma string legível no fuso horário local."""
    if not horario_utc or not isinstance(horario_utc, datetime):
        return "Indisponível"
    try:
        # Garante que o datetime de entrada está ciente do fuso (UTC)
        if horario_utc.tzinfo is None:
            horario_utc = pytz.utc.localize(horario_utc)

        tz_destino = pytz.timezone(fuso_destino)
        horario_local = horario_utc.astimezone(tz_destino)
        # Formato: DD/MM/AAAA HH:MM (ex: 05/08/2025 14:30)
        return horario_local.strftime("%d/%m/%Y %H:%M")
    except ImportError:
        logging.warning("AGENDA: Biblioteca pytz não instalada. Usando formatação UTC.")
        return horario_utc.strftime("%d/%m/%Y %H:%M (UTC)") # Fallback para UTC
    except Exception as e:
        logging.error(f"AGENDA: Erro ao formatar horário {horario_utc} para fuso {fuso_destino}: {e}")
        return "Erro na formatação"

# --- Funções Principais da Agenda ---

def agendar_consulta(telefone: str, nome: str, email: str | None = None) -> datetime | None:
    """
    Encontra o próximo horário livre e tenta agendar a consulta.
    Retorna o datetime UTC do horário agendado ou None se não conseguir.
    """
    if consultas_db is None:
        logging.error("AGENDA: ❌ Não é possível agendar: Sem conexão com DB.")
        return None

    # Usar UTC para armazenamento e lógica interna
    agora_utc = datetime.now(timezone.utc)
    # Começa a procurar X minutos à frente para dar tempo de processamento/pagamento
    inicio_procura_utc = agora_utc + timedelta(minutes=DURACAO_CONSULTA_MINUTOS)

    for i in range(MAX_TENTATIVAS_AGENDAMENTO):
        # Encontra o próximo bloco de horário válido (dia útil, horário de operação)
        horario_tentativa_utc = _proximo_horario_util(inicio_procura_utc)

        # Tenta inserir o agendamento no horário encontrado
        consulta_doc = {
            "telefone": telefone,
            "nome": nome,
            "email": email,
            "horario_utc": horario_tentativa_utc, # Armazena em UTC
            "status": "agendado", # Status inicial
            "criado_em": agora_utc
        }
        try:
            # Tenta inserir o documento. Se o horário já estiver ocupado,
            # o índice único ("horario_utc") causará um DuplicateKeyError.
            result = consultas_db.insert_one(consulta_doc)
            if result.inserted_id:
                horario_formatado = formatar_horario_local(horario_tentativa_utc)
                logging.info(f"AGENDA: ✅ Consulta marcada para {nome} ({telefone}) em {horario_formatado} ({horario_tentativa_utc.isoformat()} UTC)")
                return horario_tentativa_utc # Retorna o horário em UTC
            else:
                # Caso improvável de falha na inserção sem exceção
                logging.error(f"AGENDA: ❌ Falha desconhecida ao inserir agendamento para {horario_tentativa_utc}.")
                return None

        except DuplicateKeyError:
            # Horário ocupado, avança a procura para depois deste bloco
            logging.debug(f"AGENDA: Horário {horario_tentativa_utc.isoformat()} UTC ocupado. Tentando próximo.")
            inicio_procura_utc = horario_tentativa_utc + timedelta(minutes=1) # Avança 1 min para recalcular próximo bloco
            continue # Tenta o próximo horário

        except Exception as e:
            # Outro erro durante a inserção
            logging.error(f"AGENDA: ❌ ERRO ao tentar inserir agendamento para {horario_tentativa_utc}: {e}")
            return None # Falha no agendamento

    # Se o loop terminar sem encontrar horário
    logging.warning(f"AGENDA: ⚠️ Não foram encontrados horários disponíveis para {telefone} ({nome}) após {MAX_TENTATIVAS_AGENDAMENTO} tentativas.")
    return None

def cancelar_consulta(telefone: str) -> int:
    """
    Cancela todas as consultas futuras com status 'agendado' para um telefone.
    Retorna o número de consultas canceladas.
    """
    if consultas_db is None:
        logging.error("AGENDA: ❌ Não é possível cancelar: Sem conexão com DB.")
        return 0

    agora_utc = datetime.now(timezone.utc)
    try:
        # Filtro para encontrar consultas futuras e agendadas do telefone
        filtro = {
            "telefone": telefone,
            "horario_utc": {"$gt": agora_utc}, # Apenas horários futuros
            "status": "agendado" # Apenas consultas que ainda estão agendadas
        }
        # Atualiza o status para 'cancelado_usuario' em vez de deletar (mantém histórico)
        resultado = consultas_db.update_many(
            filtro,
            {"$set": {"status": "cancelado_usuario", "cancelado_em": agora_utc}}
        )

        canceladas = resultado.modified_count
        if canceladas > 0:
            logging.info(f"AGENDA: 🗑️ Cancelada(s) {canceladas} consulta(s) futura(s) de {telefone}")
        else:
            logging.info(f"AGENDA: Nenhuma consulta futura encontrada para cancelar para {telefone}")
        return canceladas
    except Exception as e:
        logging.error(f"AGENDA: ❌ ERRO ao cancelar consulta(s) para {telefone}: {e}")
        return 0

def consultar_proximo_horario_disponivel() -> datetime | None:
    """
    Consulta o próximo horário disponível sem agendar.
    Retorna o datetime UTC do horário ou None se não encontrar/erro.
    """
    if consultas_db is None:
        logging.error("AGENDA: ❌ Não é possível consultar horário: Sem conexão com DB.")
        return None

    agora_utc = datetime.now(timezone.utc)
    # Começa a procurar um pouco à frente
    inicio_procura_utc = agora_utc + timedelta(minutes=5) # Pequena margem

    for i in range(MAX_TENTATIVAS_AGENDAMENTO):
        horario_tentativa_utc = _proximo_horario_util(inicio_procura_utc)
        try:
            # Verifica se existe alguma consulta agendada ou confirmada para este horário
            filtro_conflito = {
                "horario_utc": horario_tentativa_utc,
                "status": {"$in": ["agendado", "confirmado"]} # Considera ambos como ocupados
            }
            conflito = consultas_db.find_one(filtro_conflito)
            if not conflito:
                # Encontrou horário livre
                logging.info(f"AGENDA: Próximo horário disponível encontrado: {formatar_horario_local(horario_tentativa_utc)} ({horario_tentativa_utc.isoformat()} UTC)")
                return horario_tentativa_utc # Retorna horário em UTC
            else:
                # Horário ocupado, avança para o próximo bloco
                logging.debug(f"AGENDA: Horário {horario_tentativa_utc.isoformat()} UTC ocupado (Status: {conflito.get('status')}). Tentando próximo.")
                inicio_procura_utc = horario_tentativa_utc + timedelta(minutes=1) # Avança 1 min
                continue
        except Exception as e:
            logging.error(f"AGENDA: ❌ ERRO ao consultar próximo horário ({horario_tentativa_utc}): {e}")
            return None # Retorna None em caso de erro na consulta

    # Se o loop terminar
    logging.warning(f"AGENDA: ⚠️ Nenhum horário disponível encontrado na consulta após {MAX_TENTATIVAS_AGENDAMENTO} tentativas.")
    return None
