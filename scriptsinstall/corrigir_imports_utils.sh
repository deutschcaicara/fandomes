#!/bin/bash

echo "🔧 Corrigindo imports quebrados de 'utils' para 'app.utils'..."

# Caminho base do seu backend
BASE_DIR="/home/ubuntu/famdomes_backend/app"

# Lista de arquivos com imports quebrados
ARQUIVOS=(
    "$BASE_DIR/routes/agendamento.py"
    "$BASE_DIR/routes/ia_comandos.py"
    "$BASE_DIR/routes/pagamentos.py"
    "$BASE_DIR/routes/stripe.py"
    "$BASE_DIR/routes/ia.py"
    "$BASE_DIR/utils/followup.py"
)

# Loop para substituir os imports em cada arquivo
for arquivo in "${ARQUIVOS[@]}"; do
    if [[ -f "$arquivo" ]]; then
        sed -i 's/from utils\./from app.utils./g' "$arquivo"
        echo "✅ Corrigido: $arquivo"
    else
        echo "⚠️ Arquivo não encontrado: $arquivo"
    fi
done

echo "✅ Todos os imports corrigidos com sucesso!"
#!/bin/bash

echo "🔧 Corrigindo imports quebrados de 'utils' para 'app.utils'..."

# Caminho base do seu backend
BASE_DIR="/home/ubuntu/famdomes_backend/app"

# Lista de arquivos com imports quebrados
ARQUIVOS=(
    "$BASE_DIR/routes/agendamento.py"
    "$BASE_DIR/routes/ia_comandos.py"
    "$BASE_DIR/routes/pagamentos.py"
    "$BASE_DIR/routes/stripe.py"
    "$BASE_DIR/routes/ia.py"
    "$BASE_DIR/utils/followup.py"
)

# Loop para substituir os imports em cada arquivo
for arquivo in "${ARQUIVOS[@]}"; do
    if [[ -f "$arquivo" ]]; then
        sed -i 's/from utils\./from app.utils./g' "$arquivo"
        echo "✅ Corrigido: $arquivo"
    else
        echo "⚠️ Arquivo não encontrado: $arquivo"
    fi
done

echo "✅ Todos os imports corrigidos com sucesso!"
