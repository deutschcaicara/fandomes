# ===========================================================
# Arquivo: utils/questionario_pos_pagamento.py
# Define as perguntas e a introdução para o questionário pós-pagamento.
# ===========================================================
import asyncio
import logging
# Ajuste o import se mensageria.py estiver em um diretório diferente
# from .mensageria import enviar_mensagem # A função de envio agora é feita pelo Agente DomoTriagem

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Textos do Questionário ---

INTRODUCAO_QUESTIONARIO = "Ótimo! Pagamento confirmado e consulta agendada. ✅\n\nPara que o profissional possa aproveitar ao máximo o tempo da consulta e já ter um bom entendimento do caso, preciso fazer algumas perguntas rápidas agora. Leva só alguns minutos."

# Perguntas Fatuais (Originais ou Adaptadas)
PERGUNTAS_FACTUAIS = [
    "Vamos começar com algumas perguntas rápidas para ajudar nosso profissional a entender melhor. Qual o nome completo da pessoa que será avaliada?",
    "Qual a idade aproximada dela?",
    "Qual o seu grau de parentesco com essa pessoa (você é filho(a), esposa(o), irmão(ã), amigo(a), ou a própria pessoa)?",
    "Quais são as principais substâncias que ela está usando atualmente (por exemplo: álcool, cocaína, crack, maconha, medicamentos controlados sem prescrição)?",
    "Há quanto tempo, aproximadamente, esse uso se tornou um problema ou se intensificou?",
    "A pessoa já passou por algum tipo de tratamento para dependência química antes? Se sim, qual(is) e quando?",
    "Além da dependência, existe alguma outra condição de saúde importante, física ou mental (como diabetes, pressão alta, depressão, ansiedade, esquizofrenia), que devemos saber?",
    "Em qual cidade e estado a pessoa se encontra neste momento?"
]

# Perguntas Emocionais (Adicionadas para a Trilha Emocional)
PERGUNTAS_EMOCIONAIS = [
    "Pensando na situação atual, quais são as maiores preocupações ou medos que você (ou a pessoa a ser avaliada, se não for você) tem enfrentado recentemente?",
    "Olhando para frente, o que você (ou a pessoa) mais deseja ou espera alcançar ao buscar ajuda ou iniciar um tratamento?",
    "Em relação aos sentimentos, existe algum que tem sido muito presente ultimamente por causa dessa situação (por exemplo: culpa, vergonha, raiva, medo, frustração, tristeza, mas também esperança ou alívio)?",
    "De que forma você percebe que essa situação tem impactado o dia a dia, o trabalho/estudos e os relacionamentos familiares?"
]

# Combina as perguntas na ordem desejada para o questionário completo
# Pode ajustar a ordem se preferir intercalar fatuais e emocionais
# Exemplo: Intercalando
QUESTIONARIO_COMPLETO_POS_PAGAMENTO = []
len_fat = len(PERGUNTAS_FACTUAIS)
len_emo = len(PERGUNTAS_EMOCIONAIS)
max_len = max(len_fat, len_emo)

for i in range(max_len):
    if i < len_fat:
        QUESTIONARIO_COMPLETO_POS_PAGAMENTO.append(PERGUNTAS_FACTUAIS[i])
    if i < len_emo:
        QUESTIONARIO_COMPLETO_POS_PAGAMENTO.append(PERGUNTAS_EMOCIONAIS[i])

# --- Função para Iniciar o Questionário (NÃO MAIS NECESSÁRIA DIRETAMENTE) ---
# A lógica de iniciar e conduzir o questionário agora reside no Agente DomoTriagem.
# Esta função pode ser removida ou mantida apenas para referência.

# async def iniciar_questionario_pos_pagamento(telefone: str):
#     """
#     [DEPRECATED] A lógica agora está no Agente DomoTriagem.
#     Esta função enviava a primeira pergunta do questionário.
#     """
#     total_perguntas = len(QUESTIONARIO_COMPLETO_POS_PAGAMENTO)
#     logging.info(f"[DEPRECATED] QUESTIONARIO: Preparando para iniciar ({total_perguntas} perguntas) para {telefone}")
#
#     if QUESTIONARIO_COMPLETO_POS_PAGAMENTO:
#         primeira_pergunta = QUESTIONARIO_COMPLETO_POS_PAGAMENTO[0]
#         mensagem_inicial = f"{INTRODUCAO_QUESTIONARIO}\n\n{primeira_pergunta}"
#         try:
#             # O envio agora é feito pelo Agente DomoTriagem
#             # await enviar_mensagem(telefone, mensagem_inicial)
#             logging.info(f"[DEPRECATED] QUESTIONARIO: Primeira pergunta seria enviada para {telefone}.")
#             # O estado seria atualizado para algo como "COLETANDO_RESPOSTA_QUESTIONARIO"
#         except Exception as e:
#             logging.error(f"[DEPRECATED] QUESTIONARIO: Erro ao tentar enviar primeira pergunta para {telefone}: {e}")
#     else:
#         logging.warning(f"[DEPRECATED] QUESTIONARIO: Nenhuma pergunta definida. Questionário não iniciado para {telefone}.")

