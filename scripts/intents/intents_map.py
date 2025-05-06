# intents/intents_map.py
# Mapeamento de intents para palavras-chave/gatilhos.
# Usado pelo NLUClassifier baseado em keywords.
# Considere usar um formato mais estruturado (ex: YAML) se ficar muito grande.

INTENTS = {
    # 🚀 INÍCIO DO FUNIL
    "boas_vindas": [
        "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "e aí", "fala comigo", "tudo bem", "como vai"
    ],

    # 👤 QUERO AGENDAR / HORÁRIOS
    "quero_agendar": [
        "quero agendar", "como agendo", "quero atendimento", "quero uma consulta", "como marcar",
        "tem como agendar", "preciso de um médico", "consulta urgente", "quero ajuda médica",
        "agendar", "marcar consulta", "atendimento médico", "agendar consulta"
    ],
    "ver_horario": [
        "tem horário", "que horas tem", "tem agenda", "qual o próximo horário", "quero saber os horários",
        "horários disponíveis", "agenda livre", "consultar horário", "ver agenda"
    ],

    # 💰 VALORES E PAGAMENTO
    "duvida_valores": [
        "quanto custa", "qual o valor", "preço", "tem plano", "é caro", "valores da consulta", "paga quanto", "é gratuito?",
        "aceita convênio", "plano de saúde", "parcelar", "tem desconto", "formas de pagamento", "pagamento", "custo"
    ],

    # ❓ DÚVIDAS GERAIS / CONFIANÇA
    "duvida_geral": [
        "como funciona", "me explica", "o que vocês fazem", "isso é pra quê", "como ajudam", "qual o tratamento",
        "o que é isso", "para que serve", "me fale mais", "detalhes"
    ],
    "desconfianca": [
        "isso é real?", "posso confiar?", "é golpe?", "tem CNPJ?", "quem são vocês?", "é confiável?", "funciona mesmo?",
        "é seguro?", "garantia", "é empresa?"
    ],

    # 📚 SOBRE DEPENDÊNCIA / VÍCIO
    "duvida_dependencia": [
        "o que é dependência química", "quais os sintomas", "isso tem cura", "como saber se sou dependente",
        "vício em drogas", "meu caso tem jeito", "isso é doença?", "uso mas não sou viciado", "tem tratamento",
        "dependência", "vício", "drogas", "alcoolismo", "sintomas de vício"
    ],
    "sou_dependente": [
        "sou viciado", "tenho vício", "sou dependente químico", "tenho problema com droga", "uso todo dia",
        "não consigo parar", "preciso parar de usar", "sou alcoólatra", "viciado"
    ],
    "recaida": [
        "tive recaída", "usei de novo", "não consegui parar", "recomecei", "caí de novo",
        "recaí", "voltei a usar", "escorreguei", "tive um deslize"
    ],
    "abstinencia": [
        "tô tremendo", "tô suando", "não tô bem", "tô em abstinência", "tô agoniado", "tô passando mal sem usar",
        "sintomas de abstinência", "fissura", "crise de abstinência"
    ],

    # 🧠 SINTOMAS GRAVES / CRISE / URGÊNCIA
    "sintomas_graves": [
        "tá surtando", "alucinação", "tá agressivo", "não dorme há dias", "visões", "delírio", "tá em crise",
        "descontrolado", "sem noção do que faz", "paranoia", "confusão mental", "surto psicótico"
    ],
    "ameaça_vida": [ # Risco de suicídio/auto-mutilação
        "quero morrer", "vou me matar", "não quero viver", "quero sumir", "vou acabar com tudo", "vida não faz sentido",
        "me cortar", "me machucar", "despedida", "adeus"
    ],
     "urgencia_medica": [ # Emergência médica clara
        "overdose", "passando muito mal", "não consigo respirar", "dor no peito forte",
        "desmaiado", "convulsão", "sangrando muito", "veneno", "infarto", "avc", "emergência"
    ],


    # 👨‍👩‍👦 FAMILIAR EM BUSCA DE AJUDA
    "sou_familiar": [
        "sou mãe", "sou pai", "sou esposa", "sou marido", "sou irmão", "sou irmã", "sou filho", "sou filha",
        "estou procurando ajuda pra ele", "meu filho usa droga", "minha filha usa droga",
        "quero ajudar meu marido", "quero ajudar minha esposa", "meu parente", "familiar"
    ],
    "familia_pedindo_ajuda": [
        "meu filho tá viciado", "minha filha tá usando", "meu marido não aceita ajuda", "ele não quer se tratar",
        "não sei mais o que fazer com ele", "ajuda para familiar", "parente com problema", "como ajudar"
    ],
    "familiar_em_crise": [
        "ele surtou agora", "ela tá gritando", "quebrou tudo", "ele fugiu", "ela fugiu", "tá se machucando", "tá em crise agora",
        "parente em crise", "familiar agressivo", "preciso de ajuda urgente para ele"
    ],
     "resistencia_paciente": [ # Familiar relata que o paciente resiste
        "ele não quer ajuda", "ela não aceita", "não quer tratamento", "não admite que tem problema",
        "não quer ser internado", "não aceita médico", "resiste ao tratamento"
    ],

    # 🏥 INTERNAÇÃO
    "duvida_internacao": [
        "como funciona a internação", "quanto tempo dura", "volta pra casa depois?", "como é o lugar",
        "tem visita?", "fica trancado?", "internação involuntária", "é forçado?", "tem psiquiatra?",
        "internação", "clínica de recuperação", "tratamento internado"
    ],
    "quero_internar": [
        "quero internar meu filho", "como faço pra internar", "internar contra a vontade", "internar urgente",
        "preciso internar", "internação compulsória", "internação involuntária"
    ],
    "nao_quero_internar": [ # Paciente ou familiar expressa não querer internação
        "não quero internar", "sem internação", "tratamento sem internar", "não precisa de clínica",
        "alternativa à internação", "tratamento ambulatorial"
    ],

    # ⚖️ QUESTÕES LEGAIS / JURÍDICAS
    "internacao_judicial": [
        "posso pedir pra justiça?", "como internar judicialmente", "internar por ordem judicial", "meu advogado falou",
        "internação compulsória", "justiça", "ordem do juiz"
    ],
    "menor_de_idade": [
        "meu filho é menor", "ela tem 15 anos", "posso internar menor?", "menor pode ser internado?",
        "tratamento para adolescente", "menor de idade", "criança"
    ],
    "direitos_paciente": [
        "ele pode sair?", "ele é obrigado?", "isso é legal?", "tem que assinar algo?", "respeita os direitos?",
        "direitos humanos", "advogado", "lei"
    ],

    # 💬 OUTRAS SITUAÇÕES / RELATOS
     "meu_parente_usa_droga": [ # Relato mais geral sobre uso de drogas por parente
        "meu parente usa droga", "descobri que meu filho fuma", "meu marido bebe demais",
        "preocupado com familiar que usa drogas"
    ],
     "relato_dependencia": [ # Usuário falando sobre seu próprio uso/dificuldades
        "uso crack faz tempo", "bebo todo dia", "gasto tudo com droga", "minha vida tá destruída",
        "preciso de ajuda com meu vício"
    ],
     "resistencia_familiar": [ # Paciente relata que a família não apoia/atrapalha
        "minha família não me apoia", "minha esposa não entende", "meus pais não aceitam",
        "família contra o tratamento", "não tenho apoio"
    ],
     "nao_sou_usuario": [ # Deixa claro que não é o paciente
        "não sou eu que uso", "é para um amigo", "só estou pesquisando", "quero informação para outra pessoa",
        "não sou usuário"
    ],

    # ℹ️ BUSCA DE INFORMAÇÕES ADICIONAIS
     "quero_entender": [ # Pedido explícito para entender o serviço/processo
        "quero entender melhor", "me explica o processo", "como funciona o atendimento",
        "quais as etapas", "o que acontece depois"
    ],
     "curioso": [ # Demonstração de curiosidade ou teste
        "só testando", "kkk", "haha", "curioso", "testando sistema", "só vendo como funciona",
        "teste", "simulação"
    ],
    "pergunta_medico": [ # Dúvida específica sobre o profissional médico
        "quem é o médico?", "qual a especialidade?", "é psiquiatra?", "posso escolher o médico?",
        "falar com o médico"
    ],
     "duvida_medicacao": [ # Dúvida sobre remédios
        "vai precisar de remédio?", "usam medicação?", "quais remédios?", "tratamento com remédio",
        "medicação psiquiátrica"
    ],
     "duvida_psicologo": [ # Dúvida sobre psicólogo/terapia
        "tem psicólogo?", "faz terapia?", "atendimento psicológico", "terapia de grupo",
        "psicoterapia"
    ],
    "duvida_local": [ # Dúvida sobre local físico/online
        "onde fica?", "tem na minha cidade?", "qual o endereço?", "atende onde?", "é presencial ou online?",
        "atendimento online", "unidade física", "endereço da clínica"
    ],
     "duvida_profissionais": [ # Dúvida geral sobre a equipe
        "quem são os profissionais?", "tem terapeuta?", "quem atende?", "é só médico?",
        "equipe multidisciplinar"
    ],
    "duvida_sigilo": [ # Dúvida sobre confidencialidade
        "isso é sigiloso?", "meus dados estão protegidos?", "alguém vai saber?", "é confidencial?",
        "privacidade", "segredo médico"
    ],


    # ❤️ INTENTS EMOCIONAIS / REDE DE APOIO
     "desistiu_antes": [ # Já tentou tratamento antes e parou
        "já tentei parar antes", "desisti do tratamento", "não funcionou da outra vez",
        "já fiz tratamento e não adiantou", "recomeçar tratamento"
    ],
    "vergonha_de_falar": [
        "tenho vergonha", "me sinto mal de contar", "nunca falei isso pra ninguém", "é difícil falar sobre isso",
        "medo de julgamento", "constrangido"
    ],
    "culpa_familiar": [ # Familiar expressando culpa
        "acho que é culpa minha", "fui negligente", "acho que errei como pai", "deixei isso acontecer",
        "me sinto culpado", "onde eu errei"
    ],
    "busca_ajuda_emocional": [ # Pedido de ajuda mais amplo, focado no emocional
        "preciso de ajuda emocional", "tô mal", "tô triste", "ansiedade", "crise de pânico", "sou depressivo", "tô vazio",
        "angustiado", "preciso conversar", "apoio emocional"
    ],
    "ajuda_espiritual": [ # Questões sobre religião/espiritualidade
        "é contra religião?", "tem algo espiritual?", "sou evangélico", "sou católico", "tem apoio religioso?",
        "minha fé", "igreja"
    ],

    # 🛑 CONTROLE DE FLUXO / META
    "cancelar": [ # Cancelar ação atual (agendamento, etc.)
        "quero cancelar", "mudei de ideia", "não quero mais", "cancela tudo", "desisti",
        "cancelar agendamento", "não posso ir"
    ],
    "confirmacao_positiva": [ # Confirmação genérica (sim, ok, pode ser)
        "sim", "claro", "com certeza", "pode ser", "ok", "tá", "tá bom", "isso", "por favor", "quero sim", "pode"
    ],
    "confirmacao_negativa": [ # Negação genérica (não, agora não)
        "não", "nao", "talvez depois", "não agora", "deixa pra depois", "agora não", "não quero", "não obrigado"
    ],
    "elogio": [
        "ótimo atendimento", "gostei muito", "vocês são bons", "obrigado", "atendimento top", "amei",
        "parabéns", "muito bom", "excelente"
    ],
    "erro": [ # Usuário reporta um erro técnico
        "link não abre", "deu erro", "não consegui pagar", "o site caiu", "não carrega",
        "problema técnico", "não funciona", "bug"
    ],
    "sem_compreensao": [ # Bot não entendeu ou mensagem ininteligível
        "asdfgh", "oiaueia", "????", "não entendi", "fala direito", "msg estranha", "...", "??",
        "o que?", "não faz sentido"
    ],

    # Adicione intents mais específicas conforme necessário
    # Ex: "duvida_tipo_droga_especifica", "duvida_comorbidades", etc.
}