---
name: wbr-airtable-design-white
description: Version DESIGN WHITE du skill wbr-airtable (graphes Lotchi sur fond clair #F7F6F4, orange focal #FF4200 : grille légère, grille légère, graduations conservées, légende en bas, deltas vert/rouge, semaine courante mise en avant, zones agrandies). Génère automatiquement la Weekly Business Review (WBR) Luminiscence version Full (21 slides) à partir de la base Airtable Lotchi WBR. Use when un utilisateur demande de produire le WBR d'une ville pour une semaine donnée et préfère la voie data (Airtable + scraper en amont) plutôt que la navigation Fever Zone. Les seuls inputs utilisateur attendus sont le nom de la ville et la semaine ISO de référence (la "Current week"). Tout le reste — dates, charts, classification des créatives, mise en page, KPI summaries — est résolu par le skill.
---

# Skill `wbr-airtable-design-white` — WBR Lotchi Full, rendu design fond clair (voie Airtable)

> **Version design.** Identique à `wbr-airtable` côté données et pipeline (Airtable → build → injection) : mêmes scripts, mêmes signatures. Seuls changent le moteur de graphes `scripts/generate_charts.py` (style Lotchi **fond clair** par défaut) et le template v2 verrouillé d'Alex (dividers aurora, titres Century Gothic, tables dark gris/orange, sold-out et tableaux de créas en **cartes blanches** lisibles). Voir `DESIGN_CHANGES.md`. ⚠️ **Ne jamais ré-ouvrir/ré-exporter `wbr_template.pptx` via Google Slides** : cela efface les 32 noms de shapes et casse le ciblage du skill. Le `.env` (AIRTABLE_API_KEY) est **embarqué** dans ce skill (cf. aussi `.env.example`).
>
> **Défaut fond clair.** Les graphes sont clairs par défaut (`WBR_CHART_MODE=light`). Pour retrouver le rendu fond noir, lancer avec `WBR_CHART_MODE=dark`.

## Quand invoquer ce skill

Quand l'utilisateur (Aurel, Delphine, Sofia, ou tout membre habilité) demande de produire le WBR Full d'une ville Lotchi pour une semaine donnée, en utilisant la base Airtable Lotchi WBR comme source de vérité. Exemples : « Génère le WBR Full Bayonne semaine W23 », « Produis la WBR Manchester W22 », « WBR Paris cette semaine ».

À ne pas confondre avec le skill `wbr-lotchi` qui produit la version Light (14 slides) en passant par Claude in Chrome sur Fever Zone.

> Note : la clé Airtable est déjà dans le `.env` du skill et chargée
> automatiquement. Ne jamais la demander à l'utilisateur — lancer le build directement.

## Ce que le skill produit

Un fichier `[VILLE]_WBR_[SEMAINE]_Airtable.pptx` éditable, 21 slides, charte Lotchi respectée, déposé dans le dossier projet Cowork. Inclut :

- Charts hebdo (Marketing performance, Tickets sold, Top Funnel Meta, Landing Page, Product Page) reconstruits en matplotlib à partir des données Airtable.
- Tables sold-out par session pour W-1, Current, W+1.
- Tables Big Picture CTR + CPM par canal × semaine avec colonnes Evol.
- KPI summaries cluster (REACH, UGC) avec vraies valeurs hebdo W-2 vs W-1.
- Tableaux de créas par cluster (REACH, UGC, ADE, RMKT, TOURIST FR, TOURIST EN), 8 colonnes (Vignette, Publicité, Date début, Date fin, Impressions, CTR, ROAS, CPC, CPM).
- Vignettes téléchargées en parallèle depuis `Preview URL`.
- Key Metrics / Action Plans / Comments injectés via un `metrics.json` rédigé en amont (étape 2 du pipeline).

Durée typique : 30 à 45 s côté build, plus quelques minutes côté rédaction LLM/humaine.

## Pré-requis utilisateur

Avant d'invoquer le skill :

1. **Clé Airtable dans `.env`.** Un fichier `.env` est fourni à la racine du skill ; il
   suffit d'y coller **une fois** le Personal Access Token Airtable (PAT, scope
   `data.records:read` sur `appfKTIV0MZCvLfbb`) après la ligne `AIRTABLE_API_KEY=`.
   `airtable_fetch.py` le charge automatiquement (`_load_dotenv_key`). Une fois la clé
   en place, Claude lance `build_wbr.py` directement sans jamais redemander la clé.
2. **Données scrapées à jour** dans la base Airtable. La voie est : scrapers Fever Zone + Datacloud → Postgres → sync Airtable.
3. **Pour les rédactions** (Key Metric / Action Plan / Comments), un fichier `metrics.json` rédigé manuellement ou via LLM en se basant sur les chiffres extraits par le pipeline (cf. `playbook_decisions.md` pour les seuils d'alerte).

## Workflow en 2 étapes

### Étape 1 — Build (auto)

```bash
python3 scripts/build_wbr.py \
  --city Bayonne \
  --week 2026-W23 \
  --template wbr_template.pptx \
  --out output/BAYONNE_WBR_2026-W23_Airtable.pptx \
  --tmp-dir output/tmp \
  --report-json output/run_report.json
```

Le script charge depuis Airtable, calcule les agrégats, génère 11 charts PNG, édite le template Full v2 (21 slides), sauvegarde avec déduplication zip XML.

### Étape 2 — Inject rédactions (semi-auto)

Préparer un `metrics.json` (cf. `_runs/metrics_bayonne_w23.json` pour un exemple complet) avec les KM/AP/Comments, puis :

```bash
python3 scripts/inject_metrics.py \
  --pptx output/BAYONNE_WBR_2026-W23_Airtable.pptx \
  --metrics metrics.json \
  --out output/BAYONNE_WBR_2026-W23_Airtable_final.pptx
```

Le script injecte :
- Check List W-1 (slide 3, jusqu'à 2 actions)
- Key Metric + Action Plan (slides 5, 7, 8, 9, 11, 13)
- Comments par cluster (slides 14-18)
- Action Plan W+1 (slide 20, 1 ligne actuellement, à étendre)

### Rédaction du `metrics.json` (KM / AP / Comments)

Modèle de référence complet : `_runs/metrics_bayonne_w23.json` (toutes les slides
remplies). Seuils business : `playbook_decisions.md`. Schéma des clés attendues :

- `slide_3_checklist` : liste d'actions W-1, chacune `{action, lotchi, fever, ongoing}` (booléens).
- `slide_5_gh`, `slide_7_top_funnel_meta`, `slide_8_mid_funnel_lp`,
  `slide_9_low_funnel_pp`, `slide_11_soldout`, `slide_13_bigpicture` : chacune `{km, ap}`.
- `slide_14_reach_comment` … `slide_18_tourist_en_comment` : chaînes (commentaire cluster).
- `slide_20_actionplan` : liste `{action, lotchi, fever, deadline}` (`lotchi`/`fever` = "x" ou "").

**Gabarit Key Metric (`km`)** : 1 à 2 KPI clés de la slide, avec la valeur W-1 et
son évolution (W/W et, si pertinent, sur 3 semaines), terminés par un signal court.
Uniquement des chiffres réels issus d'Airtable — ne jamais inventer ni arrondir
abusivement. Un 0 réel se rédige tel quel (cf. anti-patterns du playbook).

**Gabarit Action Plan (`ap`)** : 1 phrase orientée action qui découle du KM —
verbe à l'infinitif + levier/canal + cible ou objectif (ex. « Maintenir le spend
Meta à $4-5k pour W+1 », « Étendre l'UGC le plus performant »).

**Commentaires cluster (slides 14-18)** : citer la meilleure créa du cluster
(nom + IMP/CTR/ROAS) puis une recommandation. Pour REACH (slide 14), séparer
`Videos : … | Statics : …`. Si le cluster n'a aucune créa en W-1, l'indiquer
explicitement plutôt que laisser vide.

Respecter les longueurs max ci-dessous pour éviter tout débordement de table.

### Longueurs maximales des rédactions (anti-débordement)

PowerPoint agrandit les lignes d'un tableau quand le texte wrappe : un texte trop
long fait déborder la table hors de la slide (cas observé : KM de 142 caractères
sur la slide 13 → tableau coupé en bas). Respecter ces plafonds lors de la
rédaction du `metrics.json` :

| Champ | Slides | Largeur colonne | Max caractères |
|---|---|---|---|
| `km` / `ap` | 5, 7, 8, 9, 13 | ~2 po | **110** chacun |
| `km` / `ap` | 11 | ~3 / ~2,5 po | **150** / **120** |
| `*_comment` (REACH) | 14 | ~6,5 po | **350** |
| `*_comment` (UGC/ADE/RMKT/TOURIST) | 15-18 | ~5,2-5,8 po | **300** |
| `action` (checklist / actionplan) | 3, 20 | ~3 po | **90** |

Un garde-fou automatique (`fit_all_tables` dans `scripts/pptx_utils.py`, appelé
par `build_wbr.py` et `inject_metrics.py` avant sauvegarde) réduit la police
(10 → 9 → 8 pt) puis remonte la table si un texte dépasse malgré tout. Mais c'est
un filet de sécurité : viser les plafonds ci-dessus pour rester lisible à 10 pt.

## Convention sémantique des semaines

`--week 2026-W23` désigne **Current week** (la semaine de présentation), pas W-1.

| Slot | Semaine ISO si `--week 2026-W23` |
|---|---|
| W-3 | 2026-W20 |
| W-2 | 2026-W21 |
| W-1 | 2026-W22 (la semaine analysée) |
| Current | 2026-W23 |
| W+1 | 2026-W24 |

Les charts hebdo affichent W-3 / W-2 / W-1 (= les 3 dernières semaines closes), les tableaux Sold Out affichent W-1 / Current / W+1, les KPI summaries cluster affichent W-2 vs W-1.

## Sources de données

Voir `template_companion.md` pour la spec du template, `playbook_decisions.md` pour les seuils d'alerte business, et le doc projet `Mapping WBR vers Datacloud - strict v6 final.md` pour la table complète des sources par shape.

En bref :
- **Slides 5-13** : champs `Weekly KPIs`, `Marketing Channel Performance`, `Landing Page Traffic`, `Funnel Conversion`, `Sessions` — alimentés par le scraper Fever Zone.
- **Slides 14-18** : champs `Creative Performance` filtrés sur la suffixe `weekly_real` (vraies données hebdo par créa) — alimentés par le scraper Datacloud sur la card 21114 « Asset Comparison ».

## Limites connues

- **Tableau créa vide pour les clusters qui démarrent en Current week** : si UGC ou TOURIST n'a aucune créa active en W-1, le tableau de la slide est vide. Le Comment rédigé en regard explique la situation.
- **TOURIST_ES** non affiché : le template Paris ne prévoit que FR / EN. Les créas espagnoles sont classifiées mais ignorées sur la slide 18.
- **Slide 3 et Slide 20** : le template Paris n'a respectivement que 2 et 1 data row(s). Au-delà, les actions rédigées dans `metrics.json` ne s'affichent pas (à corriger en étendant dynamiquement les tables).
- **Col Bench slide 13** : reste vide tant que la table `Benchmarks` Airtable est vide.

## Fichiers fournis

```
wbr-airtable/
├── SKILL.md                      # Ce fichier
├── README.md                     # Mode d'emploi rapide
├── playbook_decisions.md         # Seuils d'alerte business pour rédiger KM/AP
├── template_companion.md         # Spec du template (21 slides, shapes nommées)
├── wbr_template.pptx             # Template Full v2 (21 slides, shapes en snake_case)
└── scripts/
    ├── airtable_fetch.py         # Client REST Airtable + loader haut niveau
    ├── build_wbr.py              # Orchestrateur étape 1 (build PPTX brut)
    ├── cluster_classifier.py     # Cascade pour classer les créas en cluster
    ├── generate_charts.py        # Fonctions matplotlib pour les 11 visuels
    ├── inject_metrics.py         # Orchestrateur étape 2 (injection rédactions)
    ├── pptx_utils.py             # Utilitaires partagés (replace_picture, set_cell, dedupe_zip_xml)
    └── time_variables.py         # Calcul des dates ISO selon la convention WBR
```
