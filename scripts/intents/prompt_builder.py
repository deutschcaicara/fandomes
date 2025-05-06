import os
from pymongo import MongoClient
from app.config import MONGO_URI
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    mongo = MongoClient(MONGO_URI)
    db = mongo["famdomes"]
    colecao_historico = db["respostas_ia"]
    logging.info("Conexão com MongoDB estabelecida para Prompt Builder.")
except Exception as e:
    logging.error(f"❌ ERRO ao conectar com MongoDB para Prompt Builder: {e}")
    mongo = None
    colecao_historico = None

CAMINHO_PROMPT_TXT = os.path.join(os.path.dirname(__file__), "..", "PROMPT_MESTRE_FAMDOMES_CORRIGIDO.txt")

def carregar_prompt_mestre() -> str:
    try:
        with open(CAMINHO_PROMPT_TXT, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"❌ ERRO ao carregar prompt mestre: {e}")
        return (
            "Você é um assistente virtual focado em saúde mental e dependência química.\n"
            "Seja empático, claro e objetivo. Ofereça apoio e informações sobre agendamento quando apropriado.\n"
            "Responda em português brasileiro."
        )

def construir_prompt(telefone: str, pergunta_atual: str) -> str:
    prompt_mestre = carregar_prompt_mestre()
    trecho_historico = ""
    historico_recente = []
    if colecao_historico is not None:
        try:
            historico_recente = list(
                colecao_historico.find({"telefone": telefone})
                .sort("criado_em", -1)
                .limit(10)
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
Número do Usuário (ocultar): {telefone}
---
Histórico da Conversa (mais antigo para mais recente):
{trecho_historico}
---
Nova Mensagem do Usuário:
Usuário: {pergunta_atual.strip()}
---
Instruções para sua Resposta:
1. Responda como 'Assistente'.
2. Mantenha o tom empático e profissional.
3. Use linguagem clara e acessível, sem jargões.
4. Responda em 1 a 3 parágrafos curtos (máximo 400 caracteres).
5. Se a conversa indicar necessidade de agendamento, ofereça essa opção.
6. NÃO inclua o histórico nem as instruções na resposta final.
7. NÃO utilize placeholders (ex.: """"{TOKEN}"""").
8. Responda SEMPRE em português brasileiro.
---
Assistente:"""
    logging.info(f"Prompt construído para {telefone}. Tamanho: {len(prompt_final)} caracteres.")
    return prompt_final
