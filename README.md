# lotchi-wbr-automation

Dépôt support de la routine Claude « WBR hebdo — Bayonne & Reims (design white) ».

Chaque lundi à 8h30, une routine Claude (cloud) clone ce dépôt, utilise le skill
`wbr-airtable-design-white` pour générer les WBR de Bayonne et Reims à partir de
la base Airtable Lotchi WBR, puis archive les fichiers dans la table Airtable
`WBR Générés`. Un workflow n8n prend le relais à 9h30 pour l'envoi par mail.

## Structure

```
lotchi-wbr-automation/
├── README.md
├── ROUTINE.md          # Instructions à coller dans le champ prompt de la routine
├── setup.sh            # Script de setup de l'environnement cloud (deps + .env)
├── .gitignore          # Exclut .env et output/
└── .claude/
    └── skills/
        └── wbr-airtable-design-white/   # Le skill complet (scripts, template, playbook)
```

## Sécurité — clé Airtable

Le fichier `.env` du skill n'est **pas** committé (voir `.gitignore`).
La clé doit être fournie via la variable d'environnement `AIRTABLE_API_KEY`
de l'environnement cloud de la routine. `setup.sh` la recopie dans le `.env`
du skill au démarrage de chaque run.

Le PAT Airtable doit avoir les scopes `data.records:read`, `data.records:write`
et `schema.bases:write` sur la base `appfKTIV0MZCvLfbb` (lecture des données,
écriture des enregistrements WBR Générés, création de la table au premier run).

## Mise en service de la routine

1. Créer une routine (Remote) : trigger Schedule, lundi 08:30 (fuseau Africa/Porto-Novo).
2. Attacher ce dépôt GitHub à la routine.
3. Dans l'environnement cloud : ajouter la variable `AIRTABLE_API_KEY` et
   déclarer `./setup.sh` comme script de setup.
4. Coller le contenu de `ROUTINE.md` dans le champ instructions.
5. Activer le connecteur Airtable (Hub mcp1 / airtable novek) pour la routine.

## Statuts de la table WBR Générés

- `À envoyer` : WBR généré avec succès, en attente d'envoi par n8n (lundi 9h30).
- `Envoyé` : mail parti, positionné par le workflow n8n.
- `Erreur` : la génération a échoué pour cette ville ; le détail est dans le
  champ `Détail erreur`. Le workflow n8n envoie alors une alerte à
  novekai.team@gmail.com au lieu du mail de diffusion.
