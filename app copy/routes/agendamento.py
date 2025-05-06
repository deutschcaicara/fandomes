# ===========================================================
# Arquivo: routes/agendamento.py
# (Corrigido para importar a função correta de agenda.py)
# ===========================================================
from fastapi import APIRouter, HTTPException
import logging

# Ajuste o import conforme a estrutura do seu projeto
# Importa a função correta para consultar o próximo horário
from app.utils.agenda import consultar_proximo_horario_disponivel, formatar_horario_local

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cria um roteador FastAPI para este módulo
router = APIRouter(prefix="/agenda", tags=["Agendamento"]) # Adiciona prefixo e tag

@router.get("/proximo", summary="Consulta o próximo horário de agendamento disponível")
async def proximo_agendamento_disponivel():
    """
    Endpoint para verificar o próximo horário livre na agenda.
    Retorna o horário formatado ou uma mensagem indicando indisponibilidade.
    """
    logging.info("AGENDAMENTO Route: Consultando próximo horário disponível...")
    try:
        # Chama a função correta para obter o próximo horário UTC
        horario_utc = consultar_proximo_horario_disponivel()

        if horario_utc:
            # Formata o horário para o fuso local
            horario_formatado = formatar_horario_local(horario_utc)
            logging.info(f"AGENDAMENTO Route: Próximo horário encontrado: {horario_formatado}")
            return {"proximo_horario_disponivel": horario_formatado, "horario_utc": horario_utc.isoformat()}
        else:
            # Se a função retornar None (sem horário ou erro no DB)
            logging.info("AGENDAMENTO Route: Nenhum horário disponível encontrado.")
            return {"proximo_horario_disponivel": None, "mensagem": "Nenhum horário disponível encontrado no momento."}
    except Exception as e:
        # Captura qualquer erro inesperado durante a consulta
        logging.exception("AGENDAMENTO Route: ❌ Erro inesperado ao consultar próximo horário:")
        raise HTTPException(status_code=500, detail="Erro interno ao consultar a agenda.")

