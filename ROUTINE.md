# Instructions de la routine (à coller dans le champ prompt)

Tu génères chaque lundi les WBR de toutes les villes actives en utilisant exclusivement le skill **wbr-generation** (ne pas confondre avec wbr-airtable, wbr-lotchi ou wbr-airtable-design-white, obsolètes), puis tu archives les résultats dans Airtable. Le skill se trouve dans ce dépôt cloné, à l'emplacement `.claude/skills/wbr-generation/` (noté `<DIR>` ci-dessous). Lis d'abord son SKILL.md. Ne demande aucune confirmation à aucune étape.

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

La **Semaine** d'un WBR est la semaine de présentation (celle de la couverture du deck, `weeks.cover_week_label`), au format `YYYY-Wnn`. Calcule-la comme la semaine ISO de `weeks.presentation_date` de `metrics.json` (ex. `2026-07-15` → `2026-W29`, cohérent avec `cover_week_label: "W29"`) — ne prends jamais `review_week_id` (semaine des données, décalée d'une semaine) ni la date d'exécution.

Si une étape échoue pour une ville (métriques en erreur, endpoint indisponible, échec d'intégrité du PPTX), n'interromps pas la routine : note précisément le message d'erreur et la cause probable pour cette ville, puis continue avec la ville suivante.

## 3. Table Airtable "WBR Générés"
Utilise exclusivement le connecteur Airtable novek du Hub (outils Hub mcp1:airtable_novek__*), base Lotchi WBR (appfKTIV0MZCvLfbb).
a. Vérifie si la table "WBR Générés" existe déjà. Si oui, ne la recrée pas. Si l'option "Erreur" ou le champ "Détail erreur" manquent dans une table existante, ajoute-les sans toucher au reste du schéma.
b. Si elle n'existe pas, crée-la une seule fois avec ces champs :
   - Semaine (texte, ex. 2026-W28)
   - Ville (sélection unique)
   - Fichier (pièce jointe)
   - Statut (sélection unique : À envoyer, Envoyé, Erreur)
   - Détail erreur (texte long)
c. Si une ville détectée à l'étape 1 n'existe pas encore dans les options du champ Ville, ajoute l'option (première lettre en majuscule, ex. `bayonne` → `Bayonne`).

## 4. Enregistrer les résultats
Pour chaque ville, sans exception (succès comme échec) :
a. Vérifie s'il existe déjà un enregistrement pour cette Semaine + Ville. Si oui, mets-le à jour au lieu de créer un doublon.
b. Si le WBR a été généré avec succès : Statut = "À envoyer", Détail erreur vidé, et attache le PPTX final dans le champ Fichier en uploadant le fichier lui-même (endpoint Airtable uploadAttachment sur le record, avec AIRTABLE_API_KEY), pas une URL. Si l'upload échoue (taille, endpoint), traite ce cas comme un échec : Statut = "Erreur" avec le détail.
c. Si la génération a échoué : Statut = "Erreur" et renseigne le champ Détail erreur avec un résumé clair et actionnable (étape en échec, message d'erreur, cause probable), en 500 caractères maximum, sans jamais y recopier de credentials.
d. **Mode échec global** (préflight ou `/cities` en échec) : enregistre une ligne Erreur, avec la cause commune, pour chaque ville de la semaine la plus récente déjà présente dans "WBR Générés" (à défaut : Bayonne et Reims). La Semaine de ces lignes est alors la semaine ISO de la date d'exécution (même convention que la semaine de présentation), faute de metrics.json.

Ne laisse jamais un échec sans enregistrement : c'est ce statut qui déclenche l'alerte mail du workflow n8n.

## 5. Livrer
Dépose les PPTX finaux générés dans le dossier de sortie et termine par un court récapitulatif : semaine traitée, liste des villes détectées, statut par ville (À envoyer / Erreur + cause), lien vers les enregistrements Airtable.

## Garde-fous
- Ne jamais exposer la valeur de WBR_ENDPOINT_TOKEN, AIRTABLE_API_KEY ni le contenu de `.env.wbr.local` (ni dans le récapitulatif, ni dans Airtable, ni dans les logs).
- Aucune connexion directe à la base de données depuis la routine : uniquement les endpoints HTTPS du service WBR.
- Aucun chiffre inventé : toutes les valeurs viennent de `metrics.json`.
