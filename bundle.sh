#!/bin/bash

# bundle_project.sh
# Combina la estructura y contenido de un proyecto en un único archivo de texto

# === Configuración por defecto ===
MAX_LINES=100
EXTENSIONS="py|md|json|yml|env|toml|txt|html|js|ts|css|sh"
EXCLUDE_DIRS=".git|node_modules|venv|__pycache__"

# === Uso ===
if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <salida.txt> [directorio_a_excluir...]"
  exit 1
fi

OUTPUT_FILE="$1"
shift

# Agregar exclusiones adicionales desde argumentos
for dir in "$@"; do
  EXCLUDE_DIRS+="|$dir"
done

# === Paso 1: Estructura del proyecto ===
echo "📁 ESTRUCTURA DEL PROYECTO" > "$OUTPUT_FILE"
tree -I "$EXCLUDE_DIRS" >> "$OUTPUT_FILE"

echo -e "\n\n🧠 CONTENIDO RELEVANTE\n" >> "$OUTPUT_FILE"

# === Paso 2: Recorrer archivos y agregar su contenido ===
find . -type f | grep -Ev "$EXCLUDE_DIRS" | while read file; do
  # Extraer extensión del archivo
  ext="${file##*.}"

  # Verificar si la extensión está permitida
  if [[ "$file" =~ \.($EXTENSIONS)$ ]]; then
    echo "### $file ###" >> "$OUTPUT_FILE"
    head -n $MAX_LINES "$file" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"
  elif [[ "$(basename "$file")" == "requirements.txt" ]]; then
    echo "### $file ###" >> "$OUTPUT_FILE"
    echo "(Contenido omitido: dependencias externas)" >> "$OUTPUT_FILE"
    head -n 5 "$file" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"
  fi
done

echo "✅ Bundle generado exitosamente en $OUTPUT_FILE"

