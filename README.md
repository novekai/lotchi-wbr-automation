# lotchi-wbr-automation

Dépôt support de la routine Claude « WBR hebdo — toutes villes (wbr-generation) ».

Chaque lundi à 8h30, une routine Claude (cloud) clone ce dépôt et utilise le skill
`wbr-generation` pour générer le WBR de chaque ville active (liste tirée du datalake :
`SELECT city FROM mart_wbr.cities`), puis archive les fichiers dans la table Airtable
`WBR Générés`. Un workflow n8n prend le relais à 9h30 pour l'envoi par mail.

## Pipeline du skill wbr-generation

Contrairement à l'ancien skill (`wbr-airtable-design-white`, données Airtable, build
local du deck), `wbr-generation` s'appuie sur le datalake et un service distant :

1. `wbr_metrics.py` lit le schéma `mart_wbr` (Postgres, rôle `analyst_wbr` lecture
   seule) et calcule les progressions W-2 → W-1 (`metrics.json`).
2. Le deck `WBR_<Ville>_W<sem>.pptx` (graphiques, vignettes) est téléchargé depuis
   l'endpoint distant (`WBR_ENDPOINT_URL` + Bearer `WBR_ENDPOINT_TOKEN`).
3. Claude rédige Key Metrics, Action Plans, To do et commentaires de campagne
   (`PROMPT-key-metrics-action-plan.md`) → `textes.json`.
4. `wbr_write_text.py` injecte les textes, supprime les slides fantômes et vérifie
   l'intégrité du PPTX.

## Structure

```
lotchi-wbr-automation/
├── README.md
├── ROUTINE.md          # Instructions à coller dans le champ prompt de la routine
├── setup.sh            # Setup de l'environnement cloud (deps + .env.wbr.local)
├── .gitignore          # Exclut les secrets et artefacts de run
└── .claude/
    └── skills/
        └── wbr-generation/
            ├── SKILL.md
            ├── PROMPT-key-metrics-action-plan.md
            ├── requirements.txt
            ├── .env.wbr.local.example   # Gabarit — le vrai .env n'est jamais committé
            └── scripts/ (wbr_metrics.py, wbr_write_text.py)
```

## Sécurité — secrets

Le fichier `.env.wbr.local` du skill n'est **pas** committé (voir `.gitignore`).
Les secrets sont fournis via les variables d'environnement de l'environnement cloud
de la routine ; `setup.sh` les recopie dans `.env.wbr.local` au démarrage de chaque run :

- `WBR_DATABASE_URL` — URL Postgres du datalake (rôle `analyst_wbr`, lecture seule).
- `WBR_ENDPOINT_URL` — endpoint du service de génération (terminé par `/wbr`).
- `WBR_ENDPOINT_TOKEN` — token Bearer de cet endpoint.
- `AIRTABLE_API_KEY` — PAT Airtable, utilisé uniquement pour l'upload des pièces
  jointes (endpoint `uploadAttachment`). Scopes requis : `data.records:read`,
  `data.records:write`, `schema.bases:write` sur la base `appfKTIV0MZCvLfbb`.

Les lectures/écritures d'enregistrements Airtable passent, elles, par le connecteur
Hub (mcp1 / airtable novek) activé sur la routine.

## Mise en service de la routine

1. Créer une routine (Remote) : trigger Schedule, lundi 08:30 (fuseau Africa/Porto-Novo).
2. Attacher ce dépôt GitHub à la routine (dépôt privé supporté via le compte GitHub
   connecté — Claude GitHub App ou `/web-setup`).
3. Dans l'environnement cloud : ajouter les 4 variables ci-dessus et déclarer
   `./setup.sh` comme script de setup.
4. Coller le contenu de `ROUTINE.md` dans le champ instructions.
5. Activer le connecteur Airtable (Hub mcp1 / airtable novek) pour la routine.

## Statuts de la table WBR Générés

- `À envoyer` : WBR généré avec succès, en attente d'envoi par n8n (lundi 9h30).
- `Envoyé` : mail parti, positionné par le workflow n8n.
- `Erreur` : la génération a échoué pour cette ville ; le détail est dans le
  champ `Détail erreur`. Le workflow n8n envoie alors une alerte à
  novekai.team@gmail.com au lieu du mail de diffusion.
