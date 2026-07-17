# Instructions de la routine (à coller dans le champ prompt)

Tu génères chaque lundi les WBR de toutes les villes actives en utilisant exclusivement le skill **wbr-generation** (ne pas confondre avec wbr-airtable, wbr-lotchi ou wbr-airtable-design-white, obsolètes), puis tu archives les résultats dans Airtable. Le skill se trouve dans ce dépôt cloné, à l'emplacement `.claude/skills/wbr-generation/` (noté `<DIR>` ci-dessous). Lis d'abord son SKILL.md. Le script de setup a déjà installé les dépendances et écrit `<DIR>/.env.wbr.local` à partir des variables d'environnement WBR_DATABASE_URL, WBR_ENDPOINT_URL et WBR_ENDPOINT_TOKEN ; si le fichier est absent, écris-le toi-même depuis ces variables avant toute génération. Ne demande aucune confirmation à aucune étape.

## 0. Préflight (une seule fois, avant toute ville)
Vérifie que `<DIR>/.env.wbr.local` existe et contient les 3 variables ; charge-les en retirant les retours chariot `\r` comme indiqué dans le SKILL.md. Vérifie que les dépendances sont installées (`pip install -r <DIR>/requirements.txt` au besoin) et l'intégrité des scripts (`python3 -m py_compile <DIR>/scripts/*.py`). Si le préflight échoue, n'essaie aucune génération : passe directement à l'étape 4 en mode échec global.

## 1. Identifier les villes
La liste des villes à traiter est le résultat de `SELECT city FROM mart_wbr.cities`, exécutée via WBR_DATABASE_URL (lecture seule). Traite toutes les villes retournées, une par une. Si cette requête échoue, c'est un échec global : applique l'étape 4 en mode échec global.

## 2. Générer les WBR (pour chaque ville de la liste)
Déroule le skill wbr-generation de bout en bout, en suivant son SKILL.md :
a. Métriques : `wbr_metrics.py --city <ville> --out metrics.json`.
b. Deck : téléchargement depuis le service distant (curl authentifié ; lance-le en arrière-plan si la génération dépasse 45 s).
c. Rédaction : produis `textes.json` (Key Metrics, Action Plans, To do, commentaires de campagne) en suivant strictement `PROMPT-key-metrics-action-plan.md`. N'invente jamais de chiffre ; donnée absente = `N/A`.
d. Injection : `wbr_write_text.py --deck ... --texts textes.json` (le script supprime les slides fantômes et échoue si l'intégrité du PPTX n'est pas garantie).
e. Vérification du contenu : relis le deck final (aucun chiffre inventé, textes qui tiennent, To do cohérent, Plan d'action W-1 vide).

La **Semaine** d'un WBR est celle des données, pas celle du calendrier : reconstruis le format `YYYY-Wnn` (ex. 2026-W28) à partir de la semaine étudiée (W-1) fournie par `metrics.json` — jamais à partir de la date d'exécution.

Si une étape échoue pour une ville (mart non rafraîchi, erreur script, endpoint indisponible, échec d'intégrité du PPTX), n'interromps pas la routine : note précisément le message d'erreur et la cause probable pour cette ville, puis continue avec la ville suivante.

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
d. **Mode échec global** (préflight ou requête des villes en échec) : enregistre une ligne Erreur, avec la cause commune, pour chaque ville de la semaine la plus récente déjà présente dans "WBR Générés" (à défaut : Bayonne et Reims). La Semaine de ces lignes est alors la semaine ISO précédant la date d'exécution (W-1 calendaire), faute de mieux.

Ne laisse jamais un échec sans enregistrement : c'est ce statut qui déclenche l'alerte mail du workflow n8n.

## 5. Livrer
Dépose les PPTX finaux générés dans le dossier de sortie et termine par un court récapitulatif : semaine traitée, liste des villes détectées, statut par ville (À envoyer / Erreur + cause), lien vers les enregistrements Airtable.

## Garde-fous
- Ne jamais exposer le contenu de `.env.wbr.local` ni la valeur des variables WBR_* ou AIRTABLE_API_KEY (ni dans le récapitulatif, ni dans Airtable, ni dans les logs).
- Accès base strictement en lecture seule (rôle analyst_wbr) : aucune écriture dans le datalake.
- Aucun chiffre inventé : toutes les valeurs viennent de `metrics.json`.
