# lotchi-wbr-automation

Dépôt support de la routine Claude « WBR hebdo — toutes villes (wbr-generation) ».

Chaque lundi à 8h30, une routine Claude (cloud) clone ce dépôt et utilise le skill
`wbr-generation` pour générer le WBR de chaque ville active (liste fournie par le
service WBR : `GET /cities`), puis dépose les fichiers dans Google Drive : un
sous-dossier nommé `AAAA-Wnn` (semaine de présentation, ex. `2026-W30`) dans le
dossier parent `1THMDoOXXRHTAczButWxxYymGMXJrRnP9`. Un workflow n8n prend le
relais pour l'envoi par mail à partir du dossier de la semaine.

## Pipeline du skill wbr-generation

Contrairement à l'ancien skill (`wbr-airtable-design-white`, données Airtable, build
local du deck), `wbr-generation` s'appuie sur le datalake et un service distant :

1. Les métriques W-2 → W-1 (`metrics.json`) sont fournies par le service distant
   (`GET /metrics?city=<ville>`), qui exécute côté serveur la même logique que
   `wbr_metrics.py`. La liste des villes actives vient de `GET /cities`.
   (En session locale, `wbr_metrics.py` peut aussi interroger Postgres en direct ;
   en routine cloud c'est impossible : seul le HTTPS sort de l'environnement.)
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

- `WBR_ENDPOINT_URL` — endpoint du service de génération (terminé par `/wbr` ;
  la base de cette URL expose aussi `/cities` et `/metrics`).
- `WBR_ENDPOINT_TOKEN` — token Bearer de ce service.
- `WBR_DATABASE_URL` — optionnelle en routine (aucun accès Postgres possible
  depuis le cloud) ; utile seulement pour exécuter `wbr_metrics.py` en local.
- `WBR_UPLOAD_URL` — webhook n8n d'upload vers Drive (`.../webhook/wbr-upload`).
- `WBR_UPLOAD_SECRET` — secret du header `x-wbr-secret` de ce webhook.

Le dépôt des fichiers dans Google Drive passe par le workflow n8n
« WBR - Réception upload Drive » (webhook + credential Google Drive côté n8n) :
les outils Drive directement connectés à la routine n'acceptent pas des fichiers
de la taille des decks (6-8 Mo), et l'environnement cloud ne sort qu'en HTTPS.
Le workflow trouve/crée le dossier `AAAA-Wnn`, remplace les fichiers du même nom
(pas de doublon en re-run) et gère `action=delete` pour retirer un `ERREURS.md`
obsolète.

## Mise en service de la routine

1. Créer une routine (Remote) : trigger Schedule, lundi 08:30 (fuseau Africa/Porto-Novo).
2. Attacher ce dépôt GitHub à la routine (dépôt privé supporté via le compte GitHub
   connecté — Claude GitHub App ou `/web-setup`).
3. Dans l'environnement cloud : ajouter les variables ci-dessus et mettre dans le
   champ « setup script » le bloc qui localise le dépôt puis lance `bash setup.sh`
   (le script de settings est exécuté hors du dépôt).
4. Coller le contenu de `ROUTINE.md` dans le champ instructions.
5. Network access : autoriser les domaines du service WBR et du n8n (mode Full,
   ou Custom avec ces domaines). Aucun connecteur n'est requis sur la routine.

## Contrat avec le workflow n8n

La routine écrit dans le dossier Drive de la semaine (`AAAA-Wnn`) ; le workflow n8n
lit ce dossier pour l'envoi des mails. Le contrat :

- **PPTX présents** : WBR générés avec succès, à envoyer.
- **`ERREURS.md` présent** : au moins une ville a échoué — envoyer son contenu en
  alerte au lieu du mail de diffusion pour les villes concernées. Ce fichier
  reflète toujours l'état du dernier run (un re-run réussi le supprime).
- **Dossier de la semaine absent** à l'heure du workflow : panne complète de la
  routine (rien n'a pu être écrit) — à traiter comme une alerte également.
