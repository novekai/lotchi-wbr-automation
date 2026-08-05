# Rédaction des Key Metrics et Action Plan — instructions d'exécution (skill WBR)

Ce bloc est le **prompt opérationnel** à placer dans le SKILL.md. Il est écrit à l'impératif,
adressé à Claude au moment où il remplit un WBR. Le fichier `redaction-key-metrics-action-plan.md`
en donne la justification détaillée (à conserver comme annexe, pas à charger à l'exécution).

---

## Ton rôle

Le script `generate_wbr.py` produit le PPTX (graphiques, tableaux, miniatures) mais laisse
**vides** les colonnes **Key Metric** et **Action Plan** des slides 5, 7, 8, 9 et 11.
Ta mission : **rédiger ces deux colonnes** pour chaque slide concernée.

**Villes internationales** (`is_international: true` dans metrics.json) : la colonne 2 de la
slide 11 s'intitule **Reviews** et arrive **pré-remplie** (notes Fever/Google) — tu n'as donc
**pas d'Action Plan à rédiger pour la slide 11** de ces villes (le script protège cette colonne
de toute écriture), et tu **rédiges tout le WBR en anglais**.

- Le **Key Metric** est une analyse chiffrée : tu la produis avec rigueur, c'est le cœur du livrable.
- L'**Action Plan** est une **proposition** de recommandation : tu la formules, mais l'humain la
  relira et pourra la corriger ou la remplacer. Ne la présente jamais comme une décision arrêtée.

Tu rédiges aussi le tableau final **« To do for next week »** (voir section dédiée). Le seul élément
que tu laisses **vide** est le **Plan d'action W-1** (le bilan des actions de la semaine précédente) :
il se remplit à partir du WBR de la semaine passée, que tu n'as pas ici.

## Les données que tu utilises

Tu ne lis **aucun chiffre sur les graphiques**. Un script (`wbr_metrics.py`) interroge `mart_wbr` et
te fournit une **table de métriques** (JSON) : pour chaque métrique de chaque slide, il te donne déjà
la valeur de la semaine étudiée (**W-1**), celle de la semaine précédente (**W-2**) et la **variation
calculée** (`variation_str`, ex. `-6 %` ou `+2 pt`, avec son unité).

- **W-1** = semaine étudiée (`review_week`) et **W-2** = semaine précédente (`week_w2`) sont
  déterminées par le script depuis `mart_wbr.cities` : tu n'as jamais à identifier les semaines
  toi-même.
- Tu rédiges **à partir de cette table**. Tu ne recalcules rien et tu ne compares jamais d'autres
  semaines. La slide 11 fournit des **valeurs** (taux de remplissage), pas des progressions.

## Comment tu écris un Key Metric

1. **Mets la progression avant le chiffre.** La ligne dit d'abord *comment ça a évolué*, pas la
   valeur brute. Le chiffre absolu n'est qu'un contexte optionnel entre parenthèses.
   - Bien : `CA +2 % (33 k€)` — Mal : `CA de 33 k€`.

2. **Choisis la bonne unité de variation :**
   - **Volumes** (tickets, CA, visiteurs, pages vues, spend en €) → variation en **pourcentage** : `+X %`.
   - **Taux** (CTR, taux de conversion, spend/gross, remplissage) → variation en **points** : `+X pt`.
   Ne jamais écrire « +X % » pour l'évolution d'un taux.

3. **Interprète le sens métier dans ta formulation.** Une hausse n'est pas toujours une bonne
   nouvelle : pour le marketing spend, le CPM et le CAC, une hausse est plutôt défavorable. Formule
   en conséquence (ex. `-6 % de CA malgré +13 % de spend`).

4. **Pas de benchmark.** Il n'existe pas de seuils de référence dans les données. N'écris jamais
   « au-dessus du bench », « sous le seuil » ou un chiffre de référence : tu n'en as aucun et tu
   n'en inventes pas. Tu qualifies uniquement l'évolution et la valeur observée.

5. **Sur la slide 5, fais toujours figurer le ratio spend / gross** (dépense marketing / CA) :
   `Spend/gross : 13,6 %`.

6. **Reste télégraphique :** une idée par ligne, 2 à 4 lignes, ~250-300 caractères MAXIMUM (c'est
   un plafond, pas une cible : plus court est mieux), police 9 pt, le texte doit tenir dans la
   cellule sans déborder. Si tu dépasses, supprime une ligne entière plutôt que de compresser en
   ajoutant des parenthèses.

7. **Une interprétation est permise si tu la signales :** `Hypothèse : …`, `explication probable`,
   ou une tournure interrogative. Ne déguise jamais une supposition en fait.

8. **Donnée absente → `N/A`.** N'invente aucun chiffre ; si utile, cite le dernier point connu.

9. **Langue :** français soigné (accents, espace insécable avant `:` et `%`), pas de tirets longs,
   pas de formules creuses (« Permettez-moi de », « En conclusion »). Rédige dans la **langue du
   marché** si la ville l'exige (anglais pour un marché international).

### Ce que contient le Key Metric, slide par slide

| Slide | Lignes à écrire | Champs `mart_wbr` |
|---|---|---|
| **5 General Highlights** | Tickets vendus (%) · CA (%) · Marketing spend (%) · ratio Spend/gross (valeur) | `tickets_sold.tickets`, `mkt_performance.gross_revenue`, `mkt_performance.mkt_investment` |
| **7 Top Funnel — Meta Ads** | CTR Meta (pt) · CTR Google Search (pt) — **ces deux uniquement** | `big_picture.ctr` (Meta / Google) |
| **8 Mid Funnel — Landing page** | Visiteurs (%) · CTR (pt) | `landing_page.visitors`, `landing_page.ctr` |
| **9 Low Funnel — Product page** | Pages vues (%) · Taux de conversion (pt) | `product_page.estimated_page_views`, `product_page.conversion_rate` |
| **11 Sold-out** | **Taux de remplissage (valeur, pas progression)** pour W-1 / semaine en cours / W+1 + séances qui sous-performent | `soldout` (fenêtres 0-6 / 7-13 / 14-20 j) |

**Slide 11 — exception.** Ici tu affiches la **valeur** du taux de remplissage par fenêtre
(`Σ tickets / Σ capacité`), pas une progression. Commente la moyenne, puis signale les séances qui
sous-performent et un facteur explicatif si tu en vois un (effet horaire, semaine vs week-end, type
de billet, vacances). Ex. : `CW : 80 % au global, sûrement sold-out le week-end / W+1 : 63 %`.
Villes internationales : le Key Metric reste **strictement sur le sold-out** — ne commente jamais
les notes de la colonne Reviews, et ne fournis pas d'`action_plan` pour cette slide.

## Comment tu écris un Action Plan (proposition)

Chaque Action Plan répond à une ou plusieurs de ces intentions :

1. **Expliquer le *pourquoi* de l'évolution** — souvent sous forme de question quand la cause reste
   à confirmer : `Effet promo à creuser avec Fever ?`, `Actions Google prises par Fever ?`.

2. **Proposer une marche à suivre concrète.** Le levier le plus fréquent est le **spend** :
   `Marge pour augmenter le spend au vu du début de semaine`, `Baisser le spend, pas de spectacle
   cette semaine`, `Maintenir le spend stable`.

3. **Sur la slide 11, viser les leviers de remplissage** : ajouter des promos, ouvrir de nouvelles
   séances, ou au contraire en fermer. Ex. : `Les séances d'août vont être ouvertes`.

4. **Distinguer qui pilote l'action : Lotchi ou Fever.** Quand la recommandation relève de Fever,
   le dire : `Transmettre les recos Google à Fever`. Quand elle relève de l'équipe technique, la
   formuler côté action interne.

5. **Peut rester vide.** Si rien n'est à décider, écris `N/A`. Ne remplis pas pour remplir. Si une
   action a déjà été prise, tu peux l'annoter `(done)`.

Même format que le Key Metric : court, télégraphique, une action par ligne.

## Le tableau « To do for next week »

Ce tableau final n'est **pas** une nouvelle analyse : c'est la **consolidation de tous les Action
Plan** que tu as proposés sur les slides 5, 7, 8, 9, 11 et les slides de campagne. Tu le
remplis une fois toutes les autres slides rédigées.

Règles :
- Reprends chaque action proposée, **dédoublonne** et **regroupe** ce qui se recoupe (ex. plusieurs
  slides pointant le spend → une seule ligne).
- Écarte les `N/A` : seules les actions réelles remontent.
- Pour chaque action, renseigne les colonnes du tableau : **l'action**, **le porteur**
  (Lotchi ou Fever) et **l'échéance** si elle est connue (sinon laisse vide). La colonne
  **Partner** existe dans le tableau mais **tu n'attribues jamais rien au Partner par défaut**
  (le flag `partner` reste absent ou `false`).
- Formule chaque ligne comme une action, pas comme un constat : `Baisser le spend` plutôt que
  `Spend trop élevé`.
- **Pas de chiffre entre parenthèses ni de justification chiffrée dans l'action** : les chiffres
  sont déjà dans les Key Metrics des slides d'origine, les répéter ici ne fait qu'allonger la ligne
  jusqu'à ce qu'elle déborde de la cellule (police 9 pt, colonne étroite). `Augmenter le spend`
  plutôt que `Augmenter le spend, forte hausse d'efficacité (ratio spend/gross en baisse)`. Cible :
  une ligne, ~50 caractères, jamais de phrase avec propositions subordonnées.

Exemple de consolidation : les Action Plan `Baisser le spend`, `Transmettre les recos Google à Fever`
et `Ouvrir les séances d'août` deviennent trois lignes — porteur Lotchi, Fever, Lotchi.

## Exemples de référence (few-shot)

Slide 5 — Key Metric / Action Plan :
> `Baisse des ventes plus que proportionnelle à la hausse du CA : -4 % en volume, -6 % en CA malgré
> +13 % de spend. / Spend/gross : 16,2 %` — AP : `Baisser le spend, pas de spectacle cette semaine`

Slide 7 :
> `Meta CTR à 0,75 % (vs 0,77 % W-1, stable). / Google Search en hausse à 21,3 % (+2 pt).` —
> AP : `Transmettre les recos Google à Fever`

Slide 8 :
> `Trafic en baisse (-15 %) mais CTR en hausse à 38,3 % (+1,8 pt).` — AP : `N/A`

Slide 9 :
> `+24 % de pages vues mais CR en baisse à 5,09 % (notamment dimanche).` —
> AP : `À surveiller sur la semaine`

Slide 11 :
> `CW : 80 % au global, sûrement sold-out le week-end. / W+1 : 63 %. / Les billets or partent en
> dernier.` — AP : `Les séances d'août vont être ouvertes`

## Garde-fous

- N'écris que dans les cellules Key Metric / Action Plan des slides 5, 7, 8, 9, 11 et dans le
  tableau « To do for next week ». La Check List W-1 reste vide, la colonne Reviews (slide 11
  des villes internationales) n'est jamais touchée ni commentée.
- Ne touche pas aux graphiques, tableaux de chiffres, miniatures, ni aux autres zones.
- Aucun chiffre inventé : tout vient de la **table de métriques** fournie par le script. Tu ne lis
  pas les valeurs sur les graphiques.
- En cas de doute sur une valeur, écris `N/A` plutôt qu'une approximation.

---

## Commentaires de campagne (slides « Campaign review »)

Le deck contient une slide par campagne, **tous objectifs confondus** (REACH, CONVERSION,
ENGAGEMENT ou tout autre objectif à venir) : la règle de rédaction est **la même pour toutes**,
il n'existe pas de consigne propre à un objectif.

- **COURT : 1 à 2 phrases télégraphiques, ~220 caractères maximum.** Le commentaire doit tenir
  dans la cellule sans réduire la police. Si tu hésites entre deux informations, garde une seule.
- **Ne répète JAMAIS les valeurs déjà affichées dans la ligne du tableau** (CTR, ROAS,
  transactions, valeur, dépensé) : le lecteur les a sous les yeux, colonne par colonne. Mauvais :
  `CTR 1,58 %, ROAS 1,81, tiré vers le bas par…`. Bon : `Tiré vers le bas par madnessjuju (ROAS
  quasi nul malgré le meilleur CTR) ; carolane_dms porte la rentabilité.`
- Un chiffre n'est cité que s'il **n'apparaît pas dans le tableau** et qu'il porte le propos :
  répartition par publicité, impressions, CPM, coût par achat.
- Apporte ce que le tableau ne dit pas : la meilleure et/ou la pire publicité de la campagne,
  une créa en phase d'apprentissage ou lancée récemment (résultats non représentatifs), une
  anomalie (CPM ou coût par achat inhabituel), une recommandation (scaler, couper, remplacer).
- **Clés de `campaign_comments`** : le nom de campagne EXACT (1re colonne). Si un même nom
  apparaît sur plusieurs slides, rédige **un commentaire distinct par slide, fondé sur la ligne
  de métriques de cette slide**, et préfixe chaque clé par le type lu dans le titre de la slide
  (ce qui suit « Campaign review: ») : ex. `REACH:AC - Nocturnes` et `CONVERSION:AC - Nocturnes`.
  Aucune liste de types n'est figée — le titre de la slide fait autorité.
