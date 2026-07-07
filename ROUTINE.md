# Instructions de la routine (à coller dans le champ prompt)

Tu génères chaque lundi les WBR des villes Bayonne et Reims en utilisant exclusivement le skill wbr-airtable-design-white (version design fond clair — ne pas confondre avec wbr-airtable ni wbr-lotchi), puis tu les archives dans Airtable. Le skill se trouve dans ce dépôt cloné, à l'emplacement `.claude/skills/wbr-airtable-design-white/`. Lis d'abord son SKILL.md. Le script de setup a déjà installé les dépendances et écrit le `.env` du skill à partir de la variable d'environnement AIRTABLE_API_KEY ; si le `.env` est absent, écris-le toi-même depuis cette variable avant tout build. Suis exactement ces étapes.

## 1. Déterminer la semaine
Calcule la semaine ISO du jour d'exécution (ce lundi), au format YYYY-Wnn (ex. 2026-W28). C'est la "Current week" au sens du skill : les données analysées seront celles de W-1, la semaine qui vient de se clore. Ne demande aucune confirmation.

## 2. Générer les WBR (pour chaque ville : Bayonne, puis Reims)
Utilise le skill wbr-airtable-design-white, de bout en bout :
a. Étape 1 (build) : lance `python3 .claude/skills/wbr-airtable-design-white/scripts/build_wbr.py` avec --city [VILLE] --week [CURRENT_WEEK], --template pointant vers le wbr_template.pptx du skill, sortie dans output/[VILLE]_WBR_[SEMAINE]_Airtable.pptx, avec --report-json.
b. Rédaction : rédige toi-même le metrics.json (Key Metrics, Action Plans, Comments par cluster) à partir des chiffres réels extraits du pipeline, en suivant playbook_decisions.md, le gabarit KM/AP du SKILL.md et les longueurs maximales anti-débordement. N'invente jamais de chiffres ; un 0 réel se rédige tel quel.
c. Étape 2 (injection) : lance inject_metrics.py pour produire le PPTX final [VILLE]_WBR_[SEMAINE]_Airtable_final.pptx.
Si une étape échoue pour une ville (données absentes dans Bilan-ville, erreur script, dépendance manquante), n'interromps pas la routine : note précisément le message d'erreur et la cause probable pour cette ville, puis continue avec l'autre ville.

## 3. Table Airtable "WBR Générés"
Utilise exclusivement le connecteur Airtable novek du Hub (outils Hub mcp1:airtable_novek__*), base Lotchi WBR (appfKTIV0MZCvLfbb).
a. Vérifie si la table "WBR Générés" existe déjà. Si oui, ne la recrée pas. Si l'option "Erreur" ou le champ "Détail erreur" manquent dans une table existante, ajoute-les sans toucher au reste du schéma.
b. Si elle n'existe pas, crée-la une seule fois avec ces champs :
   - Semaine (texte, ex. 2026-W28)
   - Ville (sélection unique : Bayonne, Reims)
   - Fichier (pièce jointe)
   - Statut (sélection unique : À envoyer, Envoyé, Erreur)
   - Détail erreur (texte long)

## 4. Enregistrer les résultats
Pour chaque ville, sans exception (succès comme échec) :
a. Vérifie s'il existe déjà un enregistrement pour cette Semaine + Ville. Si oui, mets-le à jour au lieu de créer un doublon.
b. Si le WBR a été généré avec succès : Statut = "À envoyer", Détail erreur vidé, et attache le PPTX final dans le champ Fichier en uploadant le fichier lui-même (endpoint Airtable uploadAttachment sur le record), pas une URL. Si l'upload échoue (taille, endpoint), traite ce cas comme un échec : Statut = "Erreur" avec le détail.
c. Si la génération a échoué : Statut = "Erreur" et renseigne le champ Détail erreur avec un résumé clair et actionnable (étape en échec, message d'erreur, cause probable), en 500 caractères maximum. Ne laisse jamais un échec sans enregistrement : c'est ce statut qui déclenche l'alerte mail du workflow n8n.

## 5. Livrer
Dépose les PPTX finaux générés dans le dossier de sortie et termine par un court récapitulatif : semaine traitée, statut par ville (À envoyer / Erreur + cause), lien vers les enregistrements Airtable.
