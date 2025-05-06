#!/bin/bash

# Cabeçalho da árvore
tree_header="."
tree_header_line="--"
for i in $(seq 1 78); do
  tree_header_line="${tree_header_line}-"
done

echo "$tree_header" > todos_arquivos_python.txt
echo "$tree_header_line" >> todos_arquivos_python.txt

find . -name "*.py" -print0 | while IFS= read -r -d $'\0' file; do
  echo "Arquivo: $file" >> todos_arquivos_python.txt
  echo "-------------------------------------------------------------------------------" >> todos_arquivos_python.txt
  cat "$file" >> todos_arquivos_python.txt
  echo "" >> todos_arquivos_python.txt
done

echo "Todos os arquivos Python foram salvos em todos_arquivos_python.txt com o cabeçalho da árvore."