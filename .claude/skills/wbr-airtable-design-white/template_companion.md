# Template WBR Full v2 — Fiche compagnon

Référence opérationnelle du template `WBR_Template_v2_Full.pptx`, dérivé du format Paris Full (21 slides) et utilisé comme base unique pour les deux skills de génération du WBR (variante Airtable et variante navigateur).

## 1. Pourquoi un template Full

Le template précédent (`Template WBR Claude v6.pptx`) couvrait la version *Light* en 14 slides — sans les revues de campagne par cluster. Le format *Full* ajoute 7 slides supplémentaires (Big Picture CTR/CPM + 5 cluster reviews + 1 divider) et fixe la maille de l'analyse au cluster créa, ce qui correspond à la maille effective utilisée en réunion. Travailler à partir d'un seul template Full pour les deux pipelines garantit que l'évaluation comparative porte uniquement sur la stratégie d'extraction, pas sur la mise en page.

## 2. Conventions du template

Le template applique trois règles internes :

- **Noms de shapes** en `snake_case` explicite. Plus aucun `Image 4` ou `Tableau 30` ambigu. Les noms reflètent la fonction (`chart_landing_page`, `km_ap_table_s7`, `soldout_wminus1`).
- **Placeholders** `{{VILLE_UPPER}}`, `{{ANNEE}}`, `{{DATE_MERCREDI}}` sur la couverture et les tags année-ville. Tout remplacement de chaîne se fait via `text_frame.paragraphs[i].runs[0].text` pour préserver le formatage.
- **Tables vidées** des valeurs métier (chiffres Paris, commentaires, libellés W-1) tout en conservant les en-têtes et, là où c'est structurel, les libellés statiques (Meta/Google, nom de cluster).

Les images résiduelles (charts, captures sold-out, tableaux de créas) sont **conservées** en tant que repères dimensionnels. Le skill les remplace en runtime via la mécanique `pic._element.getparent().remove(...)` + `slide.shapes.add_picture(path, left, top, width, height)`.

## 3. Cartographie slide par slide

### Section 1 — Cover et sommaire

#### Slide 1 — Cover

| Shape | Type | Rôle | Contenu attendu |
|---|---|---|---|
| `bg_cover` | Image | Fond dégradé Lotchi | Statique |
| `logo_lotchi_big` | Image | Logo grand format | Statique |
| `cover_textbox` | Texte | 3 lignes empilées | Ligne 1 : `Business Review` (statique). Ligne 2 : `{{VILLE_UPPER}}`. Ligne 3 : `{{DATE_MERCREDI}}` (format `JJ/MM/AAAA`). |

#### Slide 2 — Summary

Statique. Six numéros de section avec leurs intitulés (General Highlights, Acquisition Funnel, Top Funnel, Action Plan, Check List W-1, Sold Out Rates). À noter : l'ordre des numéros sur cette slide ne suit pas l'ordre des slides du deck — c'est un parti pris du template Paris, conservé tel quel.

#### Slide 3 — Check List W-1

| Shape | Type | Contenu attendu |
|---|---|---|
| `title_slide3` | Texte | Statique : `Check List actions W-1.` |
| `year_city_tag_s3` | Texte | `{{VILLE_UPPER}} {{ANNEE}}` |
| `checklist_w1_table` | Table 4 colonnes × N lignes | Header conservé (`Actions / Done by Lotchi / Done by Fever / Ongoing`). Lignes data à remplir par le skill : action en col 0, croix en col 1/2/3 selon le statut. |
| `logo_small_s3` | Image | Statique |

### Section 2 — General Highlights

#### Slide 4 — Divider GH

Statique. `divider_title_s4`, `bg_divider_s4`, `logo_small_s4`. Aucune variable.

#### Slide 5 — General Highlights

| Shape | Type | Contenu attendu |
|---|---|---|
| `title_slide5` | Texte | Statique : `General Highlights.` |
| `year_city_tag_s5` | Texte | `{{VILLE_UPPER}} {{ANNEE}}` |
| `chart_mkt_performance` | Image | Chart matplotlib : Spend journalier + revenu marketing + ROAS sur ~12 semaines glissantes. Source : table `Weekly KPIs` filtrée sur le show, ou capture Fever Zone (selon variante). |
| `chart_tickets_sold` | Image | Chart matplotlib : tickets vendus cumulés + sold-out rate journalier. Même fenêtre temporelle. |
| `km_ap_table_s5` | Table 2 colonnes (Key Metric / Action Plan) | À remplir : une ligne de Key Metric + Action Plan rédigée par le skill, fondée sur l'évolution semaine sur semaine. |
| `logo_small_s5` | Image | Statique |

Les 4 résidus ZoneTexte avec des pourcentages Paris en dur ont été supprimés dans cette version du template.

### Section 3 — Acquisition Funnel

#### Slide 6 — Divider Funnel

Statique. `divider_title_s6`, `bg_divider_s6`, `logo_small_s6`.

#### Slide 7 — Top Funnel : Meta Ads

| Shape | Type | Contenu attendu |
|---|---|---|
| `title_slide7` | Texte | Statique : `Top Funnel: Meta Ads.` |
| `year_city_tag_s7` | Texte | `{{VILLE_UPPER}} {{ANNEE}}` |
| `chart_top_funnel_meta` | Image | Chart matplotlib : impressions Meta hebdo + CTR par phase (WL/SL). Données : table `Marketing Channel Performance` filtrée canal = Meta. |
| `km_ap_table_s7` | Table 2 col | Key Metric + Action Plan. |

#### Slide 8 — Mid Funnel : Landing Page

Mêmes conventions que slide 7 :
- `chart_landing_page` : LP views hebdo + CTR.
- `km_ap_table_s8` : Key Metric + Action Plan.
- Source données : table `Landing Page Traffic` ou capture Fever Zone.

#### Slide 9 — Low Funnel : Product Page

Mêmes conventions :
- `chart_product_page` : PP traffic hebdo + CR.
- `km_ap_table_s9` : Key Metric + Action Plan.
- Source : table `Funnel Conversion` ou capture Fever Zone.

### Section 4 — Sold Out

#### Slide 10 — Divider Sold Out

Statique.

#### Slide 11 — Sold Out Rates

| Shape | Type | Contenu attendu |
|---|---|---|
| `title_slide11` | Texte | Statique : `Sold out rates.` |
| `year_city_tag_s11` | Texte | `{{VILLE_UPPER}} {{ANNEE}}` |
| `label_wminus1` | Texte | Statique : `W-1` |
| `label_current` | Texte | Statique : `Current week` |
| `label_wplus1` | Texte | Statique : `W+1` |
| `soldout_wminus1` | Image | Capture du tableau sold-out par session pour la semaine N-1. |
| `soldout_current` | Image | Capture sold-out semaine en cours. |
| `soldout_wplus1` | Image | Capture sold-out semaine N+1. |
| `km_ap_table_s11` | Table 2 col | Key Metric + Action Plan. |

Source données : table `Sessions` filtrée par show + plage de dates, jointure capacity de la table `Shows`. Le skill calcule `taux_remplissage = tickets_sold / capacity` par session et génère 3 mini-tableaux en PNG via matplotlib.

### Section 5 — Top Funnel détaillé

#### Slide 12 — Divider Top Funnel

Statique.

#### Slide 13 — Top funnel : Big Picture

| Shape | Type | Contenu attendu |
|---|---|---|
| `title_slide13` | Texte | Statique : `Top funnel: Big Picture.` |
| `bigpicture_ctr_table` | Table 7 cols × 3 lignes | Header (`CTR / W-3 / Evol / W-2 / Evol / W-1 / Bench`). Col 0 conservée (`Meta`, `Google`). Skill remplit les colonnes W-3, Evol, W-2, Evol, W-1 (CTR moyen pondéré par les impressions, en %), et la colonne Bench (benchmark marché, donnée externe à fournir manuellement). |
| `bigpicture_cpm_table` | Idem | Idem pour CPM (en €). Bench Google reste vide à ce jour (pas exposé). |
| `km_ap_table_s13` | Table 2 col | Key Metric + Action Plan sur la performance Big Picture. |

#### Slides 14 à 18 — Campaign reviews par cluster

Chaque slide suit le même squelette : un titre, une table KPI agrégée pour le cluster, une table de commentaires, une capture du tableau de créas Fever Zone du cluster. La classification des créatives dans les 5 clusters utilise la règle cascade définie dans `Donnees WBR - couverture actuelle et reliquat.md` (priorité : Objective REACH → AC-Influencers/UGC → MPM-ADE/AD-ADE → MPM-SLRMKT/RMKT → MPM-TOURIST → autres).

| Slide | Cluster | Shape KPI | Shape commentaires | Shape créa |
|---|---|---|---|---|
| 14 | **REACH** | `reach_kpi_summary_table` (IMP W-2/W-1, CTR W-2/W-1, ROAS W-2/W-1, CPM W-2/W-1) | `reach_comments_table` (Campaign / CTRs / Comments) | `chart_reach_assets` |
| 15 | **UGC** | `ugc_kpi_summary_table` (mêmes 8 colonnes) | `ugc_comments_table` (Campaign / CTRs / ROAS / Comments) | `chart_ugc_assets` |
| 16 | **ADE** | (pas de table KPI dédiée) | `ade_comments_table` | `chart_ade_assets` |
| 17 | **RMKT** | (pas de table KPI dédiée) | `rmkt_comments_table` | `chart_rmkt_assets` |
| 18 | **TOURIST FR + EN** | (pas de table KPI dédiée) | `tourist_fr_comments_table` et `tourist_en_comments_table` | `chart_tourist_fr_assets` et `chart_tourist_en_assets` |

Pour les KPI tables (slides 14-15), le skill agrège les lignes `Creative Performance` du cluster (scope `weekly` ou `weekly_datacloud` selon variante) sur les deux dernières semaines. Pour les commentaires, le skill rédige 1 à 3 lignes synthétiques par cluster en suivant le `Playbook de decisions WBR.md`.

Les images de créas (`chart_X_assets`) sont des captures du tableau de créas trié par impressions décroissantes côté Fever Zone, filtré sur le cluster. Pour la variante Airtable, le skill génère ces tableaux en matplotlib à partir des lignes `Creative Performance` correspondantes.

### Section 6 — Action Plan et clôture

#### Slide 19 — Divider Action Plan

Statique.

#### Slide 20 — To do for next week

| Shape | Type | Contenu attendu |
|---|---|---|
| `title_slide20` | Texte | Statique : `To do for next week.` |
| `year_city_tag_s20` | Texte | `{{VILLE_UPPER}} {{ANNEE}}` |
| `actionplan_table` | Table 4 cols (`Actions / To be done by Lotchi / To be done by Fever / Deadline`) | Skill agrège les Action Plans des slides précédentes, en déduit qui fait quoi et fixe une échéance par défaut à `W+1`. |

#### Slide 21 — Merci

Statique. `merci_text` peut accueillir une signature ou un mot de remerciement personnalisé, mais reste générique par défaut.

## 4. Variables et liste de remplacements

Le skill exécute en début de génération un balayage `find_replace` sur toutes les shapes texte du deck, pour les jetons suivants :

| Jeton | Exemple de valeur | Format |
|---|---|---|
| `{{VILLE}}` | Bayonne | Capitalisation normale |
| `{{VILLE_UPPER}}` | BAYONNE | Tout majuscules |
| `{{ANNEE}}` | 2026 | Année de la session de référence |
| `{{DATE_MERCREDI}}` | 03/06/2026 | Mercredi de la semaine WBR en cours |

Les autres champs (chiffres, commentaires, tables) sont remplis par accès direct aux shapes nommées, pas par substitution de jetons. Cela évite tout risque de collision et permet d'écrire des nombres formatés (`€`, `%`, `M`) sans souci d'échappement.

## 5. Différences avec le template Light précédent

- **Big Picture** (slide 13) : nouvelle slide, table CTR + CPM par canal avec W-3/W-2/W-1 + bench.
- **Cluster reviews** (slides 14-18) : remplacent les 2 slides agrégées par cluster du Light, avec un tableau de créas dédié.
- **Sold Out** (slide 11) : 3 captures (W-1 / current / W+1) au lieu d'une seule.
- **Bench** : nouvelle colonne dans Big Picture, à remplir à partir de sources externes (eMarketer, Statista, benchmarks marché internes Lotchi).
- **Cluster classification** : règle cascade obligatoire pour produire les slides 14-18, à partir des champs `Campaign Objective`, `Phase WL/SL`, `Ad set name`, `Creative ID`.

## 6. Limitations connues du template

- Les images résiduelles (charts et captures Paris) ne sont pas vidées par défaut. Si le template est ouvert sans skill, les visuels Paris restent visibles. C'est volontaire pour garder les dimensions de chaque image facile à inspecter.
- La box `year_city_tag_sX` a été élargie à 1,9 pouce pour accepter des noms longs (`SAO PAULO 2026`, `MANCHESTER 2026`). Au-delà de ~14 caractères, prévoir une ligne supplémentaire.
- Les colonnes 0 des `*_comments_table` (slides 14-18) conservent un libellé Paris (`AD/FOMO`, `UGC`, `ADE`, etc.). Le skill peut les écraser au runtime selon les besoins ; la classification cluster produit toujours le bon libellé.

## 7. Liste des shapes nommées (récapitulatif)

```
Slide 1  : bg_cover, logo_lotchi_big, cover_textbox
Slide 2  : (statique, logo_small_s2 renommé)
Slide 3  : title_slide3, year_city_tag_s3, checklist_w1_table, logo_small_s3
Slide 4  : bg_divider_s4, logo_small_s4, divider_title_s4
Slide 5  : title_slide5, year_city_tag_s5, chart_mkt_performance,
           chart_tickets_sold, km_ap_table_s5, logo_small_s5
Slide 6  : bg_divider_s6, logo_small_s6, divider_title_s6
Slide 7  : title_slide7, year_city_tag_s7, chart_top_funnel_meta,
           km_ap_table_s7
Slide 8  : title_slide8, year_city_tag_s8, chart_landing_page,
           km_ap_table_s8, logo_small_s8
Slide 9  : title_slide9, year_city_tag_s9, chart_product_page,
           km_ap_table_s9, logo_small_s9
Slide 10 : bg_divider_s10, logo_small_s10, divider_title_s10
Slide 11 : title_slide11, year_city_tag_s11, label_wminus1, label_current,
           label_wplus1, soldout_wminus1, soldout_current, soldout_wplus1,
           km_ap_table_s11, logo_small_s11
Slide 12 : bg_divider_s12, logo_small_s12, divider_title_s12
Slide 13 : title_slide13, bigpicture_ctr_table, bigpicture_cpm_table,
           km_ap_table_s13, logo_small_s13
Slide 14 : title_slide14, reach_kpi_summary_table, reach_comments_table,
           chart_reach_assets, logo_small_s14
Slide 15 : title_slide15, ugc_kpi_summary_table, ugc_comments_table,
           chart_ugc_assets, logo_small_s15
Slide 16 : title_slide16, ade_comments_table, chart_ade_assets,
           logo_small_s16
Slide 17 : title_slide17, rmkt_comments_table, chart_rmkt_assets,
           logo_small_s17
Slide 18 : title_slide18, tourist_fr_comments_table,
           tourist_en_comments_table, chart_tourist_fr_assets,
           chart_tourist_en_assets, logo_small_s18
Slide 19 : bg_divider_s19, logo_small_s19, divider_title_s19
Slide 20 : title_slide20, year_city_tag_s20, actionplan_table,
           logo_small_s20
Slide 21 : merci_text
```
