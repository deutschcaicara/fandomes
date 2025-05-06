import os
from datetime import datetime
import logging
from pymongo import MongoClient
from app.config import MONGO_URI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

mongo = MongoClient(MONGO_URI)
db = mongo["famdomes"]
colecao_historico = db["respostas_ia"]

# Ajuste o caminho conforme sua estrutura – certifique-se de que o arquivo existe ou use o fallback
CAMINHO_PROMPT_TXT = os.path.join(os.path.dirname(__file__), "..", "PROMPT_MESTRE_FAMDOMES_CORRIGIDO.txt")

def carregar_prompt_mestre() -> str:
    try:
        with open(CAMINHO_PROMPT_TXT, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"❌ ERRO ao carregar prompt mestre: {e}")
        return (
            "Você é um assistente virtual especializado em saúde mental e dependência química. "
            "Responda com empatia, clareza e objetividade, seguindo as diretrizes de atendimento."
        )

def construir_prompt(telefone: str, pergunta_atual: str) -> str:
    prompt_mestre = carregar_prompt_mestre()
    trecho_historico = ""
    historico_recente = []
    if colecao_historico is not None:
        try:
            historico_recente = list(
                colecao_historico.find({"telefone": telefone}).sort("criado_em", -1).limit(10)
            )
            historico_recente.reverse()
            pares_formatados = []
            mensagem_usuario_pendente = None
            for item in historico_recente:
                if 'mensagem' in item:
                    mensagem_usuario_pendente = item['mensagem']
                elif 'resposta' in item and mensagem_usuario_pendente:
                    pares_formatados.append(f"Usuário: {mensagem_usuario_pendente}\nAssistente: {item['resposta']}")
                    mensagem_usuario_pendente = None
            trecho_historico = "\n".join(pares_formatados)
            if not trecho_historico:
                trecho_historico = "Nenhuma conversa anterior registrada."
        except Exception as e:
            logging.error(f"❌ ERRO ao buscar histórico para {telefone}: {e}")
            trecho_historico = "Erro ao carregar histórico."
    else:
        trecho_historico = "Histórico indisponível (sem conexão DB)."
    
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt_final = f"""{prompt_mestre}

---
Contexto Atual:
Data/Hora: {agora}
Telefone: {telefone}
---
Histórico da Conversa:
{trecho_historico}
---
Nova Mensagem do Usuário:
{pergunta_atual.strip()}
---
Instruções para sua Resposta:
1. Responda com empatia, clareza e objetividade.
2. Se apropriado, sugira o agendamento.
3. Use no máximo 400 caracteres.
---
Assistente:"""
    logging.info(f"Prompt construído para {telefone}. Tamanho: {len(prompt_final)} caracteres.")
    return prompt_final
