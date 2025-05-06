from datetime import datetime
from pymongo import MongoClient
from app.config import MONGO_URI
from app.utils.risco import analisar_risco
from app.utils.agenda import consultar_proximo_horario_disponivel as consultar_horario
from app.utils.followup import iniciar_sessao
from app.utils.mensageria import enviar_mensagem
from app.utils.ia_fallback import chamar_ollama
from app.utils.contexto import salvar_contexto, obter_contexto, limpar_contexto
from app.intents.intents_map import INTENTS
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

mongo = MongoClient(MONGO_URI)
db = mongo["famdomes"]
historico = db["respostas_ia"]

# Listas padronizadas para confirmação e negação
RESPOSTAS_CONFIRMATIVAS = [
    "sim", "claro", "com certeza", "prossiga", "quero", "vim pra isso",
    "pode sim", "segue", "vai", "tô aqui pra isso", "pode falar", "é isso",
    "ok", "tá", "tá bom", "isso", "por favor", "sim quero"
]
RESPOSTAS_NEGATIVAS = [
    "não", "nao", "talvez depois", "não agora", "deixa pra depois",
    "tô só olhando", "só pesquisando", "agora não"
]

class IntentExecutor:
    def __init__(self, telefone: str, mensagem: str, nome: str = "Paciente"):
        self.telefone = telefone
        self.mensagem = mensagem.strip()
        self.nome = nome
        self.mensagem_normalizada = self.mensagem.lower().strip()
        self.contexto = obter_contexto(self.telefone)
        self.intent_confianca = 1.0

    def detectar_intent(self):
        if self.mensagem_normalizada == "melancia vermelha":
            return "reset_manual"
        if self.contexto.get("aguardando_confirmacao"):
            if any(resp in self.mensagem_normalizada.split() for resp in RESPOSTAS_CONFIRMATIVAS):
                return self.contexto.get("intent_esperada", "confirmacao_positiva")
            elif any(resp in self.mensagem_normalizada.split() for resp in RESPOSTAS_NEGATIVAS):
                return "cancelar"
        for intent, gatilhos in INTENTS.items():
            for g in gatilhos:
                if g.lower() in self.mensagem_normalizada:
                    return intent
        self.intent_confianca = 0.5
        return "desconhecida"

    async def _processar_intents_e_responder(self):
        intent = self.detectar_intent()
        risco = analisar_risco(self.mensagem)
        if intent == "reset_manual":
            limpar_contexto(self.telefone)
            self.intent_confianca = 1.0
            resposta = "🔄 Histórico de testes apagado. Inicie uma nova simulação."
        else:
            resposta = self.responder_por_intent(intent)
        salvar_contexto(self.telefone, {"ultima_intent": intent, "aguardando_confirmacao": False})
        historico.insert_one({
            "telefone": self.telefone,
            "mensagem": self.mensagem,
            "resposta": resposta,
            "intent": intent,
            "confianca_intent": self.intent_confianca,
            "risco": risco,
            "nome": self.nome,
            "criado_em": datetime.utcnow()
        })
        return {"intent": intent, "resposta": resposta, "risco": risco}


    def limpar_resposta(self, texto: str) -> str:
        return re.sub(r"\(.*?\)", "", texto).strip()

    def responder_por_intent(self, intent):
        respostas = {
            "boas_vindas": "🧡 Você deu um passo importante ao chegar aqui. Sabemos que não é fácil buscar ajuda. Quer saber como podemos ajudar?",
            "quero_agendar": f"📅 Ótimo! Posso te ajudar a agendar com nosso especialista. Deseja que eu envie o link, {self.nome}?",
            "cancelar": "✅ Consulta cancelada. Se desejar retomar, estou à disposição.",
             "quero_agendar": f"📅 Ótimo! Posso te ajudar a agendar com nosso médico especialista. Quer que eu envie o link agora, {self.nome}?",
        "ver_horario": f"📆 O próximo horário disponível é: {consultar_horario()}. Posso reservar pra você?",

        # VALORES
        "duvida_valores": "💰 Temos valores acessíveis, com parcelamento. Posso te mostrar os detalhes e como agendar.",

        # GERAL / CONFIANÇA
        "duvida_geral": "📋 Nosso sistema conecta você com médicos especialistas de verdade. Quer saber como funciona na prática?",
        "desconfianca": "🔍 Entendo. Somos um sistema oficial, com CRM e CNPJ. Posso te mostrar o atendimento real, se quiser.",

        # DEPENDÊNCIA / RECAÍDA / SINTOMAS
        "duvida_dependencia": "🧠 A dependência química é tratável. Nosso médico pode avaliar sintomas físicos e emocionais. Quer agendar?",
        "sou_dependente": "💬 Reconhecer isso é um passo gigante. Posso agendar uma escuta com um especialista agora mesmo, se quiser.",
        "recaida": "🔁 Recaídas fazem parte do processo. Quer que eu agende um atendimento pra te ajudar a retomar o cuidado?",
        "abstinencia": "😓 Os sintomas de abstinência são desafiadores. Podemos te orientar com segurança. Posso marcar agora?",

        # CRISE / URGÊNCIA
        "sintomas_graves": "⚠️ Sinais de crise detectados. Posso encaminhar você para um atendimento urgente. Deseja ajuda agora?",
        "ameaça_vida": "🚨 Sua vida importa. Posso ativar nosso acolhimento de urgência. Quer que eu inicie agora?",

        # FAMILIAR
        "sou_familiar": "👪 Você quer ajudar alguém importante. Posso te explicar como funciona e agendar uma escuta para você ou para ele(a).",
        "familia_pedindo_ajuda": "🧭 Você está no caminho certo. Posso te mostrar como nossa equipe pode avaliar e orientar esse caso.",
        "familiar_em_crise": "🚨 Situação familiar crítica. Posso acionar nosso time de apoio agora mesmo. Posso seguir com isso?",
        "familia_nao_aceita": "😔 É difícil quando a família não apoia. Mas há caminhos. Posso te explicar como funciona, mesmo sem o consentimento total.",
        "familia_quebrada": "💔 Muitas famílias passam por isso. Podemos ajudar na reconstrução. Quer agendar uma orientação especializada?",
        "familiar_violento": "⚠️ Em casos de violência, segurança vem primeiro. Posso te mostrar como agir com respaldo médico e legal.",

        # INTERNAÇÃO
        "duvida_internacao": "🏥 A internação pode ser voluntária ou involuntária, sempre com avaliação médica. Quer saber como isso funciona?",
        "quero_internar": "✅ Posso te mostrar o processo completo, legal e clínico. Posso agendar agora com nosso médico?",

        # FUNIL / OBJECÕES / CIRCUNSTÂNCIAS
        "nao_quero_internar": "Tudo bem. Internação não é a única saída. Posso te explicar outras opções com orientação médica.",
        "meu_parente_usa_droga": "💬 Entendo. Posso agendar com o especialista pra avaliar a situação de forma profissional.",
        "crise_agora": "⚠️ Se a crise for agora, posso acionar ajuda imediatamente. Deseja isso?",
        "relato_dependencia": "💡 Obrigado por compartilhar. Posso te ajudar com os próximos passos. Deseja conversar com o especialista?",
        "resistencia_paciente": "😔 A resistência é comum. Mesmo assim, a família pode iniciar a ação. Quer que eu te oriente sobre isso?",
        "resistencia_familiar": "👥 Se a família não colabora, podemos trabalhar com quem estiver disponível. Posso mostrar como agir mesmo assim?",
        "nao_sou_usuario": "👍 Tranquilo. Se quiser ajudar alguém ou tirar dúvidas, posso te explicar tudo com calma.",

        # INFORMAÇÕES COMPLEMENTARES
        "quero_entender": "📘 Posso te explicar tudo sobre o atendimento, desde a escuta até o tratamento. Quer começar agora?",
        "curioso": "😄 Sem problema. Posso te mostrar como o sistema funciona de verdade. Quer experimentar uma simulação real?",
        "pergunta_medico": "👨‍⚕️ O médico é especialista em dependência química e avaliação clínica. Quer agendar a escuta?",
        "duvida_medicacao": "💊 Medicamentos só são indicados após avaliação. Posso agendar com o profissional, se quiser.",
        "duvida_psicologo": "🧠 Temos psicólogos na equipe. A avaliação inicial é médica. Quer seguir por esse caminho?",

        # INTENTS EMOCIONAIS / REDE DE APOIO
        "desistiu_antes": "🔁 Recomeçar é possível. Estamos aqui pra isso. Quer conversar com o médico novamente?",
        "vergonha_de_falar": "🧡 Tudo bem. Não precisa se explicar agora. Posso só ouvir, se quiser.",
        "culpa_familiar": "🤝 A culpa não ajuda, mas o cuidado sim. Posso te mostrar como começar com leveza.",
        "busca_ajuda_emocional": "💬 Também acolhemos sofrimento emocional. Quer conversar com um profissional agora?",
        "ajuda_espiritual": "🛐 Respeitamos todas as crenças. O acolhimento é humano, com base ética. Posso te explicar melhor?",

        # LEGAIS / CIDADANIA
        "internacao_judicial": "⚖️ A internação judicial é possível. Posso te explicar o processo legal e como iniciar.",
        "menor_de_idade": "👶 Tratamos casos de menores com responsabilidade. Posso te mostrar os critérios e caminhos.",
        "direitos_paciente": "📜 Tudo é feito conforme a ética médica e a lei. Posso esclarecer o que for preciso.",

        # INSTITUCIONAIS
        "duvida_local": "📍 Temos atendimento online e unidades físicas. Quer saber se tem perto de você?",
        "duvida_profissionais": "👩‍⚕️ Temos médicos, terapeutas e psicólogos. Posso te mostrar como funciona cada etapa.",
        "duvida_sigilo": "🔒 Todo atendimento é sigiloso. Nada é compartilhado sem sua autorização. Pode confiar.",

        # CONTROLE DE FLUXO
        "cancelar":"✅ Consulta cancelada. Se quiser retomar, é só me avisar.",
        "teste": "🧪 Está testando? Posso te mostrar o fluxo real se quiser experimentar de verdade.",
        "elogio": "❤️ Obrigado! Se quiser seguir com o cuidado, posso te mostrar como funciona na prática.",
        "erro": "🔁 Algo deu errado? Posso reenviar ou corrigir rapidinho.",
        "sem_compreensao": "🤔 Não entendi muito bem. Pode tentar explicar de outra forma?",
        "confirmacao_positiva": "👍 Perfeito. Vou seguir com o que propus antes.",
        "confirmacao_negativa": "Tudo bem. Estou aqui se quiser retomar depois.",
    }
        # Adicione sugestões de próximos passos para manter o fluxo
        proximos_passos = {
            "quero_agendar": "\nPosso te enviar o link de agendamento ou você gostaria de saber mais sobre o processo?",
            "duvida_valores": "\nPosso te mostrar as formas de pagamento ou você tem alguma outra dúvida?",
            "duvida_geral": "\nPosso te explicar em mais detalhes ou você gostaria de agendar uma consulta?",
            "sou_dependente": "\nVocê gostaria de agendar uma consulta ou precisa de mais informações?",
            "sintomas_graves": "\nPosso te conectar com um profissional de imediato. Deseja prosseguir?",
            "sou_familiar": "\nVocê gostaria de agendar uma consulta para você ou para o seu familiar?",
            "duvida_internacao": "\nPosso te explicar o processo de internação ou você gostaria de saber as opções de tratamento?",
            "desconhecida": "\nPosso tentar entender melhor se você reformular a pergunta ou gostaria de ver as opções de ajuda disponíveis?",
            "default": "\nPosso te ajudar com mais alguma coisa?"  # Um caso padrão
        }
        
        proximos_passos = {
            "quero_agendar": "\nPosso te enviar o link ou explicar o processo, se preferir.",
            "default": "\nPosso ajudar com mais alguma coisa."
        }
        resposta = respostas.get(intent, "Tô por aqui, pode me contar mais?")
        resposta += proximos_passos.get(intent, proximos_passos["default"])
        return resposta

    async def executar(self):
        return await self._processar_intents_e_responder()

    