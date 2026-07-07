# Playbook de décisions — WBR Lotchi

> Inspiré du `fever-wbr` MES (page Notion « WBR Fever — Weekly Business Review automatisé »).
> Sert à orienter la rédaction des Key Metrics : Claude doit signaler les seuils franchis.

## Seuils d'alerte par KPI

| KPI | Seuil | Niveau | Action recommandée (Key Metric) |
|---|---|---|---|
| Fill rate < 60 % à J-7 d'une séance | < 60 % | 🔴 Alerte | Signaler la séance, suggérer push Ads ou opération CRM |
| Fill rate < 40 % à J-3 | < 40 % | 🔴 Alerte critique | Mention explicite, séance à risque |
| Fill rate ≥ 95 % | ≥ 95 % | 🟢 Sold-out imminent | Saluer la dynamique, surveiller la levée de quota |
| ROAS hebdo | < 3× | 🟡 Attention | Suggérer audit créas |
| ROAS hebdo | > 6× | 🟢 Très bon | Suggérer envisager d'augmenter le spend |
| Spend / Gross | > 25 % | 🟡 Attention | Ratio élevé, surveiller la rentabilité marketing |
| Spend / Gross | < 12 % | 🟢 Excellent | Bonne efficacité marketing |
| Variation CA W vs W-1 | < -20 % | 🔴 Alerte | Demander investigation |
| Variation CA W vs W-1 | > +20 % | 🟢 Reprise notable | Saluer si confirmation tendance |
| CAC par billet | > 12 € | 🟡 Attention | Optimiser targeting |
| CAC par billet | < 5 € | 🟢 Excellent | Saluer l'efficience d'acquisition |
| CTR Meta | < 0,4 % | 🟡 Attention | Sous-performance par rapport au benchmark marché (0,61 %) |
| CTR Meta | > 1,5 % | 🟢 Très bon | Au-dessus du benchmark, signaler |
| CTR Google Search | < 8 % | 🟡 Attention | Sous-performance par rapport au benchmark marché (13 %) |
| CTR Google Search | > 15 % | 🟢 Très bon | Au-dessus du benchmark, signaler |
| CR funnel global | < 4 % | 🟡 Attention | Qualité du trafic à interroger |
| CR funnel global | > 8 % | 🟢 Très bon | Trafic très qualifié |

## Règles de lecture

1. **Toujours comparer** sur deux horizons : W vs W-1 (variation hebdo) et W vs W-2 (tendance courte). Si la W-1 raconte une histoire différente de la tendance longue, le signaler.
2. **Signaler les changements significatifs même positifs** — les bons signaux servent à confirmer une stratégie qui marche.
3. **Pas de drame** sur les variations inférieures à ± 5 % — bruit normal.
4. **Caveat « données partielles » réservé à la Current week en cours de semaine.**
   Préciser que ROAS/CAC sont biaisés par la baisse mécanique du spend uniquement
   pour la semaine en cours non clôturée. Ne jamais appliquer ce caveat à une
   semaine close (W-1, W-2…) ni l'utiliser pour justifier un zéro.

## Structure type d'une Key Metric

```
[KPI 1] : valeur W (variation vs W-1, variation vs W-2).
[KPI 2] : valeur W (variation vs W-1).
[Signal qualitatif en 1 mot ou 1 demi-phrase].
```

Exemple Rennes W22 (slide 5) :

```
Revenue W22 : 36 311 € (+24 % vs W21, +11 % vs W20).
Tickets vendus : 1 391 (+30 % vs W21).
Spend / Gross : 11,96 % (vs 26,4 % W21), forte amélioration.
```

## Anti-patterns

- Ne pas extrapoler une tendance sur 1 seule semaine.
- Ne pas affirmer une causalité (« la baisse Meta a causé X ») sans preuve directe.
- Ne pas mettre des recommandations vagues type « à surveiller » sans préciser quoi.
- **Un 0 (ou une cellule vide) dans Airtable est une valeur réelle.** La base est
  synchronisée quotidiennement avec Fever : un zéro signifie « vraiment zéro », pas
  un défaut technique. Ne JAMAIS attribuer un 0 à une « synchro non consolidée »,
  un « scraper non lancé » ou une « donnée manquante », et ne pas le signaler dans
  un Key Metric ou la checklist. Reporter la valeur telle quelle.
