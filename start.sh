#!/usr/bin/env bash
set -e

VECTOR_DIR="${VECTORSTORE_DIR:-vectorstore}"
EMP_JSON="${EMP_JSON_PATH:-data/employees.json}"

mkdir -p "$VECTOR_DIR"

echo "🔹 Checking embeddings in $VECTOR_DIR ..."
NEED_REBUILD=0
[ ! -f "$VECTOR_DIR/faiss_ip.index" ] && NEED_REBUILD=1
[ ! -f "$VECTOR_DIR/id_mapping.json" ] && NEED_REBUILD=1

EMP_HASH_FILE="$VECTOR_DIR/.employees.sha256"
CURR_HASH=$(sha256sum "$EMP_JSON" | awk '{print $1}')
if [ -f "$EMP_HASH_FILE" ]; then
  OLD_HASH=$(cat "$EMP_HASH_FILE")
  [ "$CURR_HASH" != "$OLD_HASH" ] && NEED_REBUILD=1
else
  NEED_REBUILD=1
fi

if [ "$NEED_REBUILD" -eq 1 ]; then
  echo "⚙️  (Re)building embeddings..."
  python rag_engine/embedding_generator.py
  echo "$CURR_HASH" > "$EMP_HASH_FILE"
else
  echo "✅ Embeddings up to date."
fi

echo "🚀 Starting API..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
