#!/usr/bin/env bash
# Setup de l'environnement pour la routine WBR Lotchi (skill wbr-generation).
# Pré-requis : les variables d'environnement WBR_DATABASE_URL, WBR_ENDPOINT_URL
# et WBR_ENDPOINT_TOKEN doivent être définies dans l'environnement cloud de la
# routine (Settings > Environment variables). AIRTABLE_API_KEY reste nécessaire
# pour l'upload des pièces jointes (endpoint uploadAttachment).
#
# NB : l'environnement cloud copie ce script hors du dépôt avant de l'exécuter
# ($0 pointe alors vers /tmp) — on localise donc le dépôt sans se fier à $0.
set -e

REL_SKILL=".claude/skills/wbr-generation"
REPO_DIR=""
for cand in "$(cd "$(dirname "$0")" 2>/dev/null && pwd)" "$PWD" "$(git rev-parse --show-toplevel 2>/dev/null)"; do
  if [ -n "$cand" ] && [ -d "$cand/$REL_SKILL" ]; then
    REPO_DIR="$cand"
    break
  fi
done
if [ -z "$REPO_DIR" ]; then
  REPO_DIR="$(dirname "$(find "$HOME" /workspace /repo . -maxdepth 6 -type d -path "*/$REL_SKILL" 2>/dev/null | head -1)")"
  REPO_DIR="${REPO_DIR%/.claude/skills}"
fi
if [ -z "$REPO_DIR" ] || [ ! -d "$REPO_DIR/$REL_SKILL" ]; then
  echo "[setup] ERREUR : impossible de localiser le dépôt cloné (dossier $REL_SKILL introuvable)." >&2
  exit 1
fi

SKILL_DIR="$REPO_DIR/$REL_SKILL"
ENV_FILE="$SKILL_DIR/.env.wbr.local"
echo "[setup] Dépôt localisé : $REPO_DIR"

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
