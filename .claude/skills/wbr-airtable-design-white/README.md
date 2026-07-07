# wbr-airtable — mode d'emploi rapide

Skill Cowork qui produit le WBR Full v2 (21 slides) d'une ville Luminiscence pour une semaine donnée, à partir de la base Airtable Lotchi WBR.

## Pré-requis

- Variable d'environnement `AIRTABLE_API_KEY` configurée avec un PAT Airtable (`data.records:read` sur `appfKTIV0MZCvLfbb`).
- Python 3.10+ avec `python-pptx`, `matplotlib`, `Pillow`, `numpy`.

## Installation (une fois)

Demandez à Claude : « Installe le skill `wbr-airtable.skill` ». Une fois validé, le skill devient disponible dans toutes les conversations Cowork du projet.

## Usage type

```bash
# Étape 1 — build PPTX brut
python3 scripts/build_wbr.py \
  --city Bayonne --week 2026-W23 \
  --template wbr_template.pptx \
  --out output/BAYONNE_WBR_2026-W23.pptx \
  --tmp-dir output/tmp \
  --report-json output/report.json

# Étape 2 — rédiger metrics.json (KM/AP/Comments) à la main ou via LLM,
# puis injecter dans le PPTX
python3 scripts/inject_metrics.py \
  --pptx output/BAYONNE_WBR_2026-W23.pptx \
  --metrics metrics.json \
  --out output/BAYONNE_WBR_2026-W23_final.pptx
```

## Format `metrics.json`

Voir `SKILL.md` section « Étape 2 » + l'exemple `_runs/metrics_bayonne_w23.json` qui couvre toutes les slides (Check List, KM/AP slides 5-13, Comments cluster slides 14-18, Action Plan slide 20).

## Convention semaines

`--week 2026-W23` désigne **Current week**. Donc W-1 = W22, W-2 = W21, W-3 = W20, W+1 = W24.

## Limites connues (cf. SKILL.md)

- Tableau créa vide pour les clusters qui démarrent en Current week (UGC sur Bayonne).
- TOURIST_ES non affiché sur slide 18.
- Slide 3 et Slide 20 limitées par le template (2 et 1 lignes respectivement).
- Col Bench slide 13 vide tant que la table `Benchmarks` est vide.

## Documentation

- `SKILL.md` : description du skill, workflow détaillé, sources.
- `template_companion.md` : spec slide par slide du template Full v2 (shapes nommées, placeholders, dimensions).
- `playbook_decisions.md` : seuils d'alerte business pour la rédaction des Key Metrics.

## Si quelque chose se passe mal

| Symptôme | Cause probable | Solution |
|---|---|---|
| `AirtableError: AIRTABLE_API_KEY absent` | Variable d'env non chargée | Charger le `.env.local` ou exporter manuellement |
| `Semaine inconnue dans la base : 2026-WXX` | La **ligne** de semaine n'existe pas encore (≠ valeur 0) | Tolérable pour W+1 (placeholder). Pour W-1/Current : vérifier la sync. Un KPI à 0 sur une semaine présente est une valeur réelle, pas ce cas. |
| KPI summary slide 14/15 à « — » | Cluster vide sur la semaine W-1 | Comportement attendu si le cluster démarre plus tard |
| Tableau créa vide « Aucune créa » | Idem | Le Comment rédigé en regard explique |
| Vignettes absentes sur certaines créas 