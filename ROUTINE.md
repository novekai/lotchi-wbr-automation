# Instructions de la routine (à coller dans le champ prompt)

Tu génères chaque lundi les WBR de toutes les villes actives en utilisant exclusivement le skill **wbr-generation** (ne pas confondre avec wbr-airtable, wbr-lotchi ou wbr-airtable-design-white, obsolètes), puis tu déposes les fichiers dans Google Drive. Le skill se trouve dans ce dépôt cloné, à l'emplacement `.claude/skills/wbr-generation/` (noté `<DIR>` ci-dessous). Lis d'abord son SKILL.md. Ne demande aucune confirmation à aucune étape.

**Particularité cloud — pas d'accès Postgres.** L'environnement de la routine ne laisse sortir que du HTTPS : n'essaie jamais de te connecter à la base (`wbr_metrics.py` direct, psql…). Tout passe par le service WBR distant. `WBR_ENDPOINT_URL` (fournie en variable d'environnement, terminée par `/wbr`) donne l'URL du deck ; l'URL de base du service est `WBR_ENDPOINT_URL` **sans** le suffixe `/wbr` (ex. `https://<hote>`), et expose aussi `GET /cities` et `GET /metrics?city=<ville>`, avec la même authentification `Authorization: Bearer $WBR_ENDPOINT_TOKEN`.

## 0. Préflight (une seule fois, avant toute ville)
Le script de setup a installé les dépendances et écrit `<DIR>/.env.wbr.local` depuis les variables d'environnement. Vérifie que WBR_ENDPOINT_URL et WBR_ENDPOINT_TOKEN sont disponibles (fichier ou environnement ; retire les retours chariot `\r`). Vérifie l'intégrité des scripts (`python3 -m py_compile <DIR>/scripts/*.py`). Vérifie que le service répond : `GET /cities` doit renvoyer HTTP 200. Si le préflight échoue, n'essaie aucune génération : passe directement à l'étape 4 en mode échec global.

## 1. Identifier les villes
La liste des villes à traiter est le champ `cities` de la réponse de `GET /cities`. Traite toutes les villes retournées, une par une. Si l'appel échoue, c'est un échec global : applique l'étape 4 en mode échec global.

## 2. Générer les WBR (pour chaque ville de la liste)
Déroule le skill wbr-generation en remplaçant son étape 1 par l'endpoint distant :
a. Métriques : `curl -sS -H "Authorization: Bearer $EPT" "<base>/metrics?city=<ville>" -o metrics.json` — ce JSON est identique à la sortie de `wbr_metrics.py` ; ne lance PAS le script (pas d'accès Postgres ici).
b. Deck : téléchargement depuis `$WBR_ENDPOINT_URL?city=<ville>` (curl authentifié `-OJ` ; lance-le en arrière-plan si la génération dépasse 45 s).
c. Rédaction : produis `textes.json` (Key Metrics, Action Plans, To do, commentaires de campagne) en suivant strictement `PROMPT-key-metrics-action-plan.md`. N'invente jamais de chiffre ; donnée absente = `N/A`.
d. Injection : `python3 <DIR>/scripts/wbr_write_text.py --deck ... --texts textes.json` (le script supprime les slides fantômes et échoue si l'intégrité du PPTX n'est pas garantie).
e. Vérification du contenu : relis le deck final (aucun chiffre inventé, textes qui tiennent, To do cohérent, Plan d'action W-1 vide).

La **Semaine** d'un run est la semaine de présentation (celle de la couverture du deck, `weeks.cover_week_label`), au format `AAAA-Wnn`. Calcule-la comme la semaine ISO de `weeks.presentation_date` de `metrics.json` (ex. `2026-07-15` → `2026-W29`, cohérent avec `cover_week_label: "W29"`) — ne prends jamais `review_week_id` (semaine des données, décalée d'une semaine) ni la date d'exécution.

Si une étape échoue pour une ville (métriques en erreur, endpoint indisponible, échec d'intégrité du PPTX), n'interromps pas la routine : note précisément le message d'erreur et la cause probable pour cette ville, puis continue avec la ville suivante.

## 3. Dépôt dans Drive — via le webhook d'upload
Le dépôt dans Google Drive passe par un webhook n8n (le workflow « WBR - Réception upload Drive » crée/réutilise le dossier de la semaine dans le dossier parent et gère les remplacements — la routine n'appelle jamais Drive directement). Les variables d'environnement `WBR_UPLOAD_URL` et `WBR_UPLOAD_SECRET` sont fournies.

- **Déposer un fichier** (un appel par fichier) :
  `curl -sS -X POST -H "x-wbr-secret: $WBR_UPLOAD_SECRET" "$WBR_UPLOAD_URL?week=<Semaine>" -F "file=@<fichier>"`
- **Supprimer un fichier** :
  `curl -sS -X POST -H "x-wbr-secret: $WBR_UPLOAD_SECRET" "$WBR_UPLOAD_URL?week=<Semaine>&action=delete&filename=<nom>"`
- **Vérifier chaque réponse** : le corps doit contenir `"status":"ok"`. Un HTTP 200 avec un corps vide ou différent est un ÉCHEC de l'appel (le webhook renvoie 200 même quand son traitement échoue en amont) — retente une fois, puis traite comme un échec.

## 4. Enregistrer les résultats
Tous les dépôts se font via le webhook (étape 3), avec `week=<Semaine>` :
a. Pour chaque ville réussie : dépose le PPTX final (nom du fichier tel que renvoyé par le service, ex. `WBR_Bayonne_W30.pptx`). Le webhook remplace automatiquement un fichier du même nom (re-run) — jamais de doublon.
b. Si au moins une ville a échoué : rédige un fichier `ERREURS.md` et dépose-le. Pour chaque ville en échec : l'étape en échec, le message d'erreur et la cause probable, de façon claire et actionnable. N'y recopie jamais de credentials ni d'URL avec token.
c. Si toutes les villes ont réussi : supprime un éventuel `ERREURS.md` obsolète laissé par un run précédent de la même semaine (`action=delete&filename=ERREURS.md` — répond ok même si le fichier n'existe pas). Un `ERREURS.md` présent déclenche l'alerte du workflow n8n : il ne doit refléter que l'état du dernier run.
d. **Mode échec global** (préflight ou `/cities` en échec) : dépose uniquement un `ERREURS.md` expliquant la cause commune, avec `week` = semaine ISO de la date d'exécution (faute de metrics.json — même convention que la semaine de présentation).

Ne laisse jamais un échec sans trace dans Drive : c'est la présence d'`ERREURS.md` qui déclenche l'alerte mail du workflow n8n (et l'absence totale du dossier de la semaine signale une panne complète de la routine).

## 5. Livrer
Termine par un court récapitulatif : semaine traitée, liste des villes détectées, statut par ville (Déposé / Erreur + cause), et le lien du dossier Drive de la semaine.

## Garde-fous
- Ne jamais exposer la valeur de WBR_ENDPOINT_TOKEN, WBR_UPLOAD_SECRET ni le contenu de `.env.wbr.local` (ni dans le récapitulatif, ni dans ERREURS.md, ni dans les logs).
- Aucune connexion directe à la base de données depuis la routine : uniquement les endpoints HTTPS du service WBR.
- Aucun chiffre inventé : toutes les valeurs viennent de `metrics.json`.
