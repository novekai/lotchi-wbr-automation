# DESIGN_CHANGES — ce qui change vs `wbr-airtable`

Version **design** du skill. Le pipeline données (Airtable), l'orchestration
(`build_wbr.py`, `inject_metrics.py`) et les **signatures de fonctions** sont
**inchangés**. Seule la couche visuelle a été refondue.

## 1. Moteur de graphes — `scripts/generate_charts.py` (réécrit)

Style **Lotchi dark analytique**, pensé pour l'analyse en réunion :

- Fond noir `#000000` (= fond des slides du template) : les graphes se fondent, plus de rectangle blanc.
- Orange `#FF4200` en **accent focal unique** (la barre ou la ligne clé).
- **Grille H+V discrète** (`#242424`) + **graduations d'axes conservées** (lecture des niveaux).
- **Légende en bas**, titre épuré seul en haut (pas de sous-titre ni de source).
- **Deltas d'évolution** vert/rouge entre semaines (barres) ; **dernière semaine** mise en avant (barre orange ou bande).
- **Combos** (CA+ROI, LP, PP) : barres neutres calées en bas, **ligne orange flottant au-dessus** — jamais orange sur orange.
- **Sold-out** (slide 11) : converti de tableau rouge/vert en **barres de remplissage** (rail + fill orange = sold-out).
- **Tableaux créas** (slides 14-18) : **recolorés en dark** (header `#161616`, lignes noires alternées, texte clair). Vignettes conservées.
- Fonts : Sora/Heebo si installées (rendu fidèle), sinon Montserrat/Carlito/DejaVu.

Les `figsize` sont calés sur les ratios des zones du template (constante `BOX`).
Si tu modifies la géométrie d'une zone dans le template, ajuste `BOX` en conséquence.

## 2. Template — `wbr_template.pptx` (zones agrandies)

Fond déjà noir dans l'original. Zones de graphes **agrandies** pour respirer :

| Slide | Zone | Avant (WxH po) | Après (WxH po) |
|---|---|---|---|
| 7 | chart_top_funnel_meta | 5,78 × 1,36 | 5,82 × 3,55 |
| 8 | chart_landing_page | 5,93 × 1,41 | 5,85 × 3,55 |
| 9 | chart_product_page | 5,72 × 1,84 | 5,75 × 3,55 |
| 5 | chart_mkt / tickets | 5,95×1,84 / 5,97×1,45 | 5,95×1,82 / 5,97×1,66 |
| 11 | soldout_* | ~3,2 × 1,0-1,6 | 3,2-3,5 × 1,45 (recalé) |

Les tableaux Key Metric/Action Plan et résumé/commentaires (slides 5, 7-9, 11, 13, 14-18)
sont des **tables PowerPoint natives** encore en orange/rose : non traitées ici
(harmonisation dark à faire dans un second temps en éditant les styles de cellules du template).

## 3. Avant de lancer

1. Ajouter le fichier `.env` avec `AIRTABLE_API_KEY=...` à la racine du skill (cf. `.env.example`).
2. Lancer comme le skill d'origine : `python3 scripts/build_wbr.py --city ... --week ... --template wbr_template.pptx --out ...`.

## 4. Variante fond clair (toggle `WBR_CHART_MODE`)

`generate_charts.py` lit la variable d'environnement `WBR_CHART_MODE` :
- `dark` (défaut) : fond noir cinématique.
- `light` : fond clair (#FFFFFF / #F7F6F4), texte foncé, orange en accent — comme les propositions initiales.

```bash
WBR_CHART_MODE=light python3 scripts/build_wbr.py --city Bayonne --week 2026-W25 ...
```

Note : le template `wbr_template.pptx` est **dark**. En mode `light`, les graphes apparaissent
en cartes claires sur les slides noires (effet "interlude clair"). Pour un deck **entièrement
clair** (slides + tables + titres + logo noir), un template light dédié est nécessaire (non fourni ici, à demander).

## 5. Harmonisation des tables

Les 18 tables PowerPoint natives (Key Metric/Action Plan, résumés, commentaires, Big Picture,
checklist, action plan) ont été recolorées en dark directement dans le template (fills explicites
qui overrident le style). `set_cell_text` (dans `pptx_utils.py`) force désormais le texte injecté
en clair (#E6E6E6) pour rester lisible.


---

## v3 — Rebranchement sur le template v2 finalisé d'Alex (2026-07-01)

- **Template verrouillé** : `wbr_template.pptx` = template v2 refondu par Alex (21 slides), 32 noms de shapes verrouillés. ⚠️ Ne pas ré-exporter via Google Slides (efface tous les noms → casse le ciblage). Re-mapper par position au besoin.
- **Charts sans bandeau orange** : suppression de l'`axvspan` (surlignage dernière semaine, alpha 0.06) dans `_render_combo`. mkt / landing / product sur fond noir pur.
- **BOX** recalé sur les zones exactes du template v2 : mkt 5.88×1.80, tickets 5.906×1.64, meta 5.906×3.60, landing 5.906×3.58, product 5.88×3.63, soldout 3.176×2.242.
- **Sold-out en carte blanche zébrée** : `soldout_table()` réécrit — fond blanc, header gris, zébrage #F3F3F3, bordures claires, rouge/vert conservé sur Sold-out %. Colonnes Date / Capacité / Billets totaux / Disponibles / Sold-out. (Remplace les barres de remplissage.)
- **Assets créas en carte blanche** : `creative_assets_table()` recoloré blanc (header gris, texte foncé, zébrage) + paramètre `aspect` pour rendre au ratio exact de chaque boîte (REACH/UGC 4.37, ADE/RMKT 3.09, TOURIST 7.60) → aucune distorsion à l'injection.
- **Police charts** : Century Gothic en tête de cascade (cohérence deck), fallback Sora / Montserrat / DejaVu.
- **Fix `set_cell`** : force un texte clair (#E6E6E6) sur les cellules de données remplies. Corrige le « texte noir sur cellule noire » (invisible) survenu car Google Slides avait supprimé les runs blancs des cellules vides.
- **UGC comments 2×4** : colonne ROAS rétablie (retirée par erreur). `build_wbr` re-remplit CTR + ROAS.
- **Injection de data** : `build(..., data=...)` accepte un dict pré-chargé → test du pipeline hors Airtable (validé sur données Bayonne factices, 21 slides OK).


---

## v3.1 — Retours Alex (2026-07-01, 2e passe)

- **Chart mkt (S5) — 4 séries** : ajout de la 2e ligne **Acc ROI** (ROI cumulé = revenu cumulé / spend cumulé sur la fenêtre) en plus de ROI. Rendu : 2 barres (CA brut, Marketing value) + 2 lignes (ROI orange plein, Acc ROI orange clair pointillé). `_render_combo` accepte `line2/line2_name/line2_fmt` ; `build_wbr` calcule `acc_roas_3`.
- **Chart Meta (S7) — multi-courbes** : `chart_top_funnel_ctrs` passe des barres groupées à 2 courbes (Meta accent + Google neutre) sur les semaines.
- **Saisie manuelle des tables (S13+)** : les cellules body des tables créées (bigpicture, km/ap S13, kpi summary, comments, actionplan) reçoivent un `endParaRPr` blanc + `sz=1000` (modèle km_ap_table_s9). Corrige le texte noir/mauvaise taille lors du remplissage manuel. `set_cell` aligné : texte blanc, taille lue depuis run ou endParaRPr, défaut 10 pt.


## v3.2 — Chart S5 : 5e série (Gross - Mkt value)

- Ajout de la ligne **Gross - Mkt value** (= CA brut − Marketing value, la marge nette en €) en **jaune** (#FFC400) sur l'axe de gauche (échelle argent, aux côtés des barres). `_render_combo` accepte désormais `line_left/line_left_name/line_left_fmt` ; `chart_mkt_performance` calcule net = revenue − spend. Le chart S5 affiche donc 5 séries : CA brut, Marketing value, Gross - Mkt value (jaune), ROI (orange plein), Acc ROI (orange pointillé).


## v3.3 — Chart S5 : anti-collision des étiquettes

- Étiquettes de valeurs des lignes placées en offsets opposés systématiques : ROI au-dessus du point, Acc ROI et Gross - Mkt value en dessous → plus de superposition quand les courbes se croisent/convergent (ex : ROI = Acc ROI en dernière semaine).
- Léger fond sombre semi-transparent (bbox alpha 0.6) derrière chaque valeur de ligne : reste lisible même par-dessus une barre ou une autre courbe.
- Marge haute de l'axe droit élargie (0.42) pour loger l'étiquette ROI du haut.


## v3.4 — Étape 2 (inject_metrics) + .env prêt à l'emploi

- **Fix `inject_metrics.set_cell`** : même correctif que `build_wbr` — texte forcé en blanc (#FFFFFF), taille lue depuis run/endParaRPr (défaut 10 pt). Sans ça, tout le contenu rédigé (Key Metric, Action Plan, Comments, Check List, Action Plan S20) sortait en noir sur noir = invisible. Étape 2 testée de bout en bout (KM/AP + checklist + actionplan lisibles).
- **`.env` inclus** à la racine du skill (au lieu de seulement `.env.example`) : y coller le PAT Airtable une fois → skill prêt à l'emploi.
- **Parité fichiers** vérifiée : les 15 fichiers de la 1re version sont tous présents.


## v3.5 — .env avec la clé (prêt à l'emploi)

- Clé Airtable copiée depuis le skill de référence `wbr-airtable` dans le `.env` à la racine. Le skill tourne sans configuration. ⚠️ Le `.skill` contient une clé vive : ne pas diffuser hors équipe.


## v3.6 — Chart S7 : étiquettes toujours au-dessus des lignes

- Labels de valeurs avec zorder élevé + fond sombre (comme S5) : toujours devant les courbes, jamais derrière.
- Placement adaptatif par point : la courbe la plus haute a son label au-dessus, la plus basse en dessous → aucune collision même au croisement Meta/Google.


## v3.7 — Chart S7 : garde anti-collision avec l'axe X

- Un point trop proche du bas de l'axe voit son label forcé au-dessus (évite le chevauchement avec les libellés de semaines de l'axe X). Utile quand une courbe est écrasée en bas (ex : outlier Google). Le cas normal reste en placement adaptatif haut/bas.
