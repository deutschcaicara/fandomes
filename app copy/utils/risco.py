# ===========================================================
# Arquivo: utils/risco.py
# ===========================================================
import logging

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Listas de Palavras-Chave para Detecção de Risco ---

# Lista de palavras/frases críticas indicando risco de vida (suicídio, automutilação)
# ATENÇÃO: Esta lista é um ponto de partida e deve ser refinada com cuidado.
PALAVRAS_CRITICAS_VIDA = [
    "suicídio", "me matar", "quero morrer", "não aguento mais", "acabar com tudo",
    "sumir", "desaparecer", "sem esperança", "adeus mundo", "não quero viver",
    "me cortar", "me machucar", "automutilação", "tirar minha vida", "fim da linha",
    "não vejo saída", "desistir de tudo"
]

# Lista de palavras/frases que indicam URGÊNCIA MÉDICA (Overdose, sintomas graves)
PALAVRAS_URGENCIA_MEDICA = [
    "overdose", "passando muito mal", "não consigo respirar", "dor no peito forte",
    "desmaiado", "convulsão", "sangrando muito", "veneno", "infarto", "avc",
    "muita dor", "sem ar", "falta de ar", "alucinação grave", "delírio intenso",
    "tomou muito remédio", "ingeriu substância"
]

# --- Função de Análise de Risco ---

def analisar_risco(texto: str) -> dict:
    """
    Analisa o texto em busca de indicadores de risco (risco de vida, urgência médica).
    Retorna um dicionário com booleanos para 'risco_vida' e 'urgencia_medica'.

    Args:
        texto (str): O texto da mensagem do usuário a ser analisada.

    Returns:
        dict: Dicionário contendo:
            - 'risco_vida' (bool): True se detectar palavras críticas de risco de vida.
            - 'urgencia_medica' (bool): True se detectar palavras de urgência médica.
    """
    # Retorna False para ambos se o texto for vazio ou nulo
    if not texto:
        return {"risco_vida": False, "urgencia_medica": False}

    # Converte o texto para minúsculas para comparação case-insensitive
    texto_lower = texto.lower()

    # Verifica se alguma palavra/frase da lista de risco de vida está presente no texto
    # Usar busca de substring para pegar variações (ex: "quero me matar agora")
    risco_vida_detectado = any(palavra in texto_lower for palavra in PALAVRAS_CRITICAS_VIDA)

    # Verifica se alguma palavra/frase da lista de urgência médica está presente no texto
    urgencia_medica_detectada = any(palavra in texto_lower for palavra in PALAVRAS_URGENCIA_MEDICA)

    # Loga um aviso se algum risco for detectado (o log principal será feito em nlp.py)
    # if risco_vida_detectado:
    #     logging.debug(f"RISCO: Risco de vida potencialmente detectado em '{texto[:50]}...'")
    # if urgencia_medica_detectada:
    #     logging.debug(f"RISCO: Urgência médica potencialmente detectada em '{texto[:50]}...'")

    # Retorna o dicionário com os resultados da análise
    return {
        "risco_vida": risco_vida_detectado,
        "urgencia_medica": urgencia_medica_detectada
    }
