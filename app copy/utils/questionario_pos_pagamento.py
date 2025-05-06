# ===========================================================
# Arquivo: utils/questionario_pos_pagamento.py
# ===========================================================
import asyncio
# Ajuste o import se mensageria.py estiver em um diretório diferente
from .mensageria import enviar_mensagem
import logging

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Definição das Perguntas ---

# Perguntas Fatuais (Originais ou Adaptadas)
PERGUNTAS_FACTUAIS = [
    "Vamos começar com algumas perguntas rápidas para ajudar nosso médico a entender melhor. Qual o nome completo da pessoa que será avaliada?",
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
QUESTIONARIO_COMPLETO_POS_PAGAMENTO = PERGUNTAS_FACTUAIS + PERGUNTAS_EMOCIONAIS

# --- Função para Iniciar o Questionário ---

async def iniciar_questionario_pos_pagamento(telefone: str):
    """
    Envia a primeira pergunta do questionário pós-pagamento.
    A lógica de salvar o questionário no contexto e enviar as perguntas
    subsequentes é gerenciada por nlp.py.
    """
    total_perguntas = len(QUESTIONARIO_COMPLETO_POS_PAGAMENTO)
    logging.info(f"QUESTIONARIO: 📋 Preparando para iniciar ({total_perguntas} perguntas) para {telefone}")

    # Verifica se a lista de perguntas não está vazia
    if QUESTIONARIO_COMPLETO_POS_PAGAMENTO:
        # Pega a primeira pergunta da lista combinada
        primeira_pergunta = QUESTIONARIO_COMPLETO_POS_PAGAMENTO[0]
        try:
            # Envia a primeira pergunta para o usuário
            await enviar_mensagem(telefone, primeira_pergunta)
            logging.info(f"QUESTIONARIO: Enviada primeira pergunta para {telefone}.")
            # A continuação do fluxo (salvar contexto, enviar próximas perguntas)
            # será tratada em nlp.py quando a resposta do usuário chegar.
        except Exception as e:
            logging.error(f"QUESTIONARIO: ❌ Erro ao enviar a primeira pergunta para {telefone}: {e}")
            # Considerar o que fazer neste caso: tentar novamente? Notificar? Mudar estado?
    else:
        # Loga um aviso se a lista de perguntas estiver vazia
        logging.warning(f"QUESTIONARIO: ⚠️ Nenhuma pergunta definida. Questionário não iniciado para {telefone}.")

