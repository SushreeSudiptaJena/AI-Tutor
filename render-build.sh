#!/usr/bin/env bash
# Render build. One service serves both halves of the app, so this builds both.
#
# Render's Python runtime ships node/npm in the same image, which is why the
# frontend can be built here instead of in a second service.
#
# Anything written during BUILD survives a free-tier spin-down; anything
# written at RUNTIME does not. That is the whole reason the embedding model is
# fetched down here rather than left to download itself on the first question.

set -o errexit -o pipefail -o nounset

echo "==> Python dependencies"
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "==> Frontend build"
# --include=dev because the build needs tsc, vite and tailwind, and Render may
# set NODE_ENV=production, which would otherwise skip devDependencies.
npm --prefix frontend ci --include=dev --no-fund --no-audit
npm --prefix frontend run build

echo "==> Pre-fetching the embedding model"
# ~130MB from HuggingFace. Left to itself fastembed downloads this lazily, on
# the first embed call -- which on the free tier means the first student to ask
# a question after every wake-up waits for it. FASTEMBED_CACHE_PATH (set in
# render.yaml, so it applies at build AND at runtime) puts it in the project
# directory instead of /tmp, so it is baked into the deploy.
python - <<'PY'
import os
from fastembed import TextEmbedding

name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
TextEmbedding(name)
print(f"    cached {name} -> {os.getenv('FASTEMBED_CACHE_PATH', '(default tmp dir)')}")
PY

echo "==> Build complete"
