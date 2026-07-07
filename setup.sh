#!/usr/bin/env bash
# Setup de l'environnement pour la routine WBR Lotchi.
# Pré-requis : la variable d'environnement AIRTABLE_API_KEY doit être définie
# dans l'environnement cloud de la routine (Settings > Environment variables).
set -e

echo "[setup] Installation des dépendances Python..."
pip install --quiet python-pptx matplotlib requests pillow python-dateutil

SKILL_DIR="$(dirname "$0")/.claude/skills/wbr-airtable-design-white"

if [ -n "$AIRTABLE_API_KEY" ]; then
  echo "AIRTABLE_API_KEY=$AIRTABLE_API_KEY" > "$SKILL_DIR/.env"
  echo "[setup] .env écrit dans le skill à partir de la variable d'environnement."
else
  echo "[setup] ATTENTION : AIRTABLE_API_KEY absente de l'environnement." >&2
  echo "[setup] Ajoutez-la dans l'environnement cloud de la routine." >&2
fi

echo "[setup] Terminé."
