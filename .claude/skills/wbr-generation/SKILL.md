---
name: wbr-generation
description: >-
  Génère une Weekly Business Review (WBR) complète en PowerPoint pour une ville, à partir du
  datalake (schéma mart_wbr) et d'un service de génération distant. Utiliser dès qu'on demande de
  « générer / produire / faire le WBR » d'une ville, une « weekly business review », ou un deck de
  revue hebdo marketing (tickets, CA, spend, CTR, funnel, sold-out, campagnes Meta). Le skill
  récupère le deck (graphiques + vignettes), calcule les progressions et rédige les Key Metrics,
  les Action Plans et le « To do for next week ».
---

# Génération de WBR

Ce skill produit un `.pptx` de WBR pour une ville, prêt à présenter. La **génération lourde du deck
(graphiques, tables, vignettes des créas) est faite par un service distant** ; le skill est un
client léger qui télécharge le deck, calcule les progressions, rédige les textes et les injecte.

1. `wbr_metrics.py` — lit `mart_wbr` et calcule les progressions W-2 → W-1 (local).
2. **Endpoint distant** — renvoie le deck `WBR_<Ville>_W<sem>.pptx` (charts + vignettes), cellules
   de texte vides.
3. **rédaction** — Claude écrit Key Metrics, Action Plans, To do d'après les progressions.
4. `wbr_write_text.py` — pose les textes, nettoie les slides fantômes et vérifie l'intégrité.

## Pré-requis (à vérifier avant de lancer)

Les identifiants sont **fournis avec le skill** : le fichier **`<DIR>/.env.wbr.local`** est à la
racine du dossier du skill (`<DIR>` = dossier d'installation du skill, celui qui contient `SKILL.md`
et `scripts/`). Tu n'as rien à créer ni à demander à l'utilisateur — lis ce fichier directement. Il
contient :
- `WBR_ENDPOINT_URL` (déjà terminé par `/wbr`) et `WBR_ENDPOINT_TOKEN` — pour le service distant ;
- `WBR_DATABASE_URL` — pour `wbr_metrics.py` (rôle `analyst_wbr`, lecture seule).

Si `<DIR>/.env.wbr.local` est absent ou incomplet (moins de 3 variables), c'est le signe d'une
installation partielle : réinstalle le skill (voir préflight ci-dessous) avant de continuer.

Charge-les en **retirant d'éventuels retours chariot Windows** (`\r`), qui corrompraient l'en-tête
d'autorisation :

```bash
DB="$(grep -E '^WBR_DATABASE_URL='   <DIR>/.env.wbr.local | cut -d= -f2- | tr -d '\r\n')"
EPU="$(grep -E '^WBR_ENDPOINT_URL='  <DIR>/.env.wbr.local | cut -d= -f2- | tr -d '\r\n')"
EPT="$(grep -E '^WBR_ENDPOINT_TOKEN=' <DIR>/.env.wbr.local | cut -d= -f2- | tr -d '\r\n')"
export WBR_DATABASE_URL="$DB"
```

- **Dépendances Python** : `pip install -r <DIR>/requirements.txt --break-system-packages`.
- **Intégrité des scripts (préflight anti-troncature)** : `python -m py_compile <DIR>/scripts/*.py`.
  Si un script ne compile pas (fichier tronqué lors d'une réinstallation par-dessus une version plus
  courte), ré-extrais-le du `.skill` (`unzip -o <chemin_du_.skill> 'scripts/*' -d <DIR>`) **ou**
  désinstalle puis réinstalle le skill. Ne lance jamais un script qui ne compile pas.
- **Ville** : le nom exact attendu par le mart (minuscules, ex. `bayonne`, `reims`, `london`). En
  cas de doute : `SELECT city FROM mart_wbr.cities`.

## Procédure

`<DIR>` = dossier de ce skill. Charge d'abord les variables (voir pré-requis).

### Étape 1 — métriques

```bash
python <DIR>/scripts/wbr_metrics.py --city <ville> --out metrics.json
```

Chaque métrique porte `w1`, `w2`, `variation_str` (ex. `-6 %`, `+2 pt`) et `weeks.cover_week_label`
(ex. `W29`). C'est la source de tous les chiffres pour la rédaction.

### Étape 2 — télécharger le deck depuis le service distant

```bash
curl -sS -H "Authorization: Bearer $EPT" "$EPU?city=<ville>" -OJ
```

`WBR_ENDPOINT_URL` inclut déjà le chemin `/wbr` : on ajoute seulement `?city=<ville>`. Le `-OJ`
enregistre le fichier sous le nom fourni par le serveur, `WBR_<Ville>_W<sem>.pptx` (le n° de semaine
est géré côté serveur). La réponse doit être **HTTP 200** avec le type
`application/vnd.openxmlformats-officedocument.presentationml.presentation`. La génération prend
généralement quelques dizaines de secondes ; si l'appel dépasse la limite de 45 s par commande,
lance le `curl` en arrière-plan et sonde la présence du `.pptx`.

Le deck arrive avec graphiques, sold-out, Big Picture, vignettes des créas et tables de campagne,
mais les cellules Key Metric / Action Plan / To do **vides**.

### Étape 3 — rédaction (Claude)

Lis **`PROMPT-key-metrics-action-plan.md`** (dans ce dossier) : règles de rédaction et exemples. À
partir de `metrics.json`, produis `textes.json` :

```json
{
  "key_metrics": {
    "5":  {"key_metric": "...", "action_plan": "..."},
    "7":  {"key_metric": "...", "action_plan": "N/A"},
    "8": {"...": "..."}, "9": {"...": "..."}, "11": {"...": "..."}, "13": {"...": "..."}
  },
  "todo": [
    {"action": "Baisser le spend", "lotchi": true, "fever": false, "deadline": ""},
    {"action": "Transmettre les recos Google", "lotchi": false, "fever": true, "deadline": "W30"}
  ],
  "campaign_comments": { "<nom de campagne exact>": "commentaire ..." }
}
```

Règles clés (le prompt fait foi) : la progression avant le chiffre ; `%` pour les volumes, `pt` pour
les taux ; slide 11 = valeurs de remplissage (pas de progression) ; **aucun benchmark** ; `N/A` si la
donnée manque. Le **To do** consolide et dédoublonne tous les Action Plans. Le **Plan d'action W-1**
(`checklist_w1_table`) reste **vide**.

Pour les `campaign_comments` : lis les tables des slides « Campaign review » du deck téléchargé (nom
de campagne, CTR, ROAS, lignes d'annonces) et rédige un commentaire par campagne selon la section
« Commentaires de campagne » du prompt. La clé doit être le **nom de campagne EXACT** de la 1re
colonne (l'appariement approximatif n'est utilisé qu'en dernier recours, et seulement s'il est non
ambigu).

### Étape 4 — injection des textes

```bash
python <DIR>/scripts/wbr_write_text.py --deck WBR_<Ville>_W<sem>.pptx --texts textes.json
```

Le script écrit dans `km_ap_table_s5/s7/s8/s9/s11/s13`, `actionplan_table` (une ligne par action) et
les `*_comments_table`. Il ne touche jamais à `checklist_w1_table` ni aux graphiques/chiffres. Il
**supprime d'abord les slides fantômes** (parts orphelines laissées par la génération) et **vérifie
qu'aucun nom de part n'est dupliqué** — sinon il échoue au lieu de livrer un fichier que PowerPoint
refuserait d'ouvrir. La sortie indique `orphelines_supprimees=N`.

### Étape 5 — vérification

L'intégrité du conteneur (zéro doublon) est garantie par l'étape 4. Vérifie ici le **contenu** :
rouvre le deck, relis les cellules remplies (aucun chiffre inventé, `N/A` là où la donnée manquait,
texte qui tient, To do cohérent, Plan d'action W-1 vide), puis livre le `.pptx`.

## Garde-fous

- Accès base en **lecture seule** via `analyst_wbr` : le skill lit uniquement `mart_wbr`, il n'écrit
  jamais dans la base.
- Claude ne lit jamais les chiffres sur les graphiques : les valeurs viennent de `metrics.json`.
- Ne jamais inventer de benchmark ni de chiffre absent.
- Les identifiants embarqués (`.env.wbr.local` : token endpoint + accès base lecture seule) ne
  doivent jamais être exposés.
