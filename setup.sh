#!/usr/bin/env bash
# Setup de l'environnement pour la routine WBR Lotchi (skill wbr-generation).
# Pré-requis : les variables d'environnement WBR_DATABASE_URL, WBR_ENDPOINT_URL
# et WBR_ENDPOINT_TOKEN doivent être définies dans l'environnement cloud de la
# routine (Settings > Environment variables). AIRTABLE_API_KEY reste nécessaire
# pour l'upload des pièces jointes (endpoint uploadAttachment).
set -e

SKILL_DIR="$(dirname "$0")/.claude/skills/wbr-generation"
ENV_FILE="$SKILL_DIR/.env.wbr.local"

echo "[setup] Installation des dépendances Python..."
pip install --quiet -r "$SKILL_DIR/requirements.txt"

if [ -n "$WBR_DATABASE_URL" ] && [ -n "$WBR_ENDPOINT_URL" ] && [ -n "$WBR_ENDPOINT_TOKEN" ]; then
  {
    echo "WBR_DATABASE_URL=$WBR_DATABASE_URL"
    echo "WBR_ENDPOINT_URL=$WBR_ENDPOINT_URL"
    echo "WBR_ENDPOINT_TOKEN=$WBR_ENDPOINT_TOKEN"
  } > "$ENV_FILE"
  echo "[setup] .env.wbr.local écrit dans le skill à partir des variables d'environnement."
else
  echo "[setup] ATTENTION : au moins une variable WBR_* est absente de l'environnement." >&2
  echo "[setup] Ajoutez WBR_DATABASE_URL, WBR_ENDPOINT_URL et WBR_ENDPOINT_TOKEN dans l'environnement cloud de la routine." >&2
fi

echo "[setup] Préflight d'intégrité des scripts (py_compile)..."
python3 -m py_compile "$SKILL_DIR"/scripts/*.py

echo "[setup] Terminé."
