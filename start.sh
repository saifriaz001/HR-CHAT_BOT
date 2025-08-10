#!/usr/bin/env bash
set -euo pipefail

# Render checks your repo out here
APP_ROOT="${RENDER_ROOT:-/opt/render/project/src}"

# Read envs with sane defaults
VECTOR_DIR="${VECTORSTORE_DIR:-vectorstore}"
EMP_JSON="${EMP_JSON_PATH:-data/employees.json}"

# Anchor relative paths into APP_ROOT
[[ "$VECTOR_DIR" = /* ]] || VECTOR_DIR="$APP_ROOT/$VECTOR_DIR"
[[ "$EMP_JSON" = /* ]]   || EMP_JSON="$APP_ROOT/$EMP_JSON"

mkdir -p "$VECTOR_DIR"
echo "🔹 APP_ROOT=$APP_ROOT"
echo "🔹 VECTOR_DIR=$VECTOR_DIR"
echo "🔹 EMP_JSON=$EMP_JSON"
echo "🔹 PWD=$(pwd)"
echo "🔹 Tree:"; ls -la "$APP_ROOT" || true

# Decide if we need to rebuild
NEED_REBUILD=0
[[ ! -f "$VECTOR_DIR/faiss_ip.index" ]] && NEED_REBUILD=1
[[ ! -f "$VECTOR_DIR/id_mapping.json" ]] && NEED_REBUILD=1

EMP_HASH_FILE="$VECTOR_DIR/.employees.sha256"
CURR_HASH=""
if [[ -f "$EMP_JSON" ]]; then
  CURR_HASH=$(sha256sum "$EMP_JSON" | awk '{print $1}')
  if [[ -f "$EMP_HASH_FILE" ]]; then
    OLD_HASH=$(cat "$EMP_HASH_FILE" || true)
    [[ "$CURR_HASH" != "$OLD_HASH" ]] && NEED_REBUILD=1
  else
    NEED_REBUILD=1
  fi
else
  echo "ℹ️  $EMP_JSON not found. If vectors already exist, we'll skip rebuild."
fi

# Rebuild only when needed and data exists
if [[ "$NEED_REBUILD" -eq 1 ]]; then
  if [[ -f "$EMP_JSON" ]]; then
    echo "⚙️  (Re)building embeddings..."
    # Ensure the Python script sees the same resolved paths
    VECTORSTORE_DIR="$VECTOR_DIR" EMP_JSON_PATH="$EMP_JSON" \
      python rag_engine/embedding_generator.py
    [[ -n "$CURR_HASH" ]] && echo "$CURR_HASH" > "$EMP_HASH_FILE" || true
  else
    echo "⚠️  No embeddings found AND $EMP_JSON missing — cannot rebuild. Starting API anyway."
  fi
else
  echo "✅ Embeddings up to date."
fi

echo "🚀 Starting API..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
