"""
Classification des créatives en clusters pour les slides 14-18 du WBR Full v2.

Règle cascade (priorité décroissante) — voir
`Donnees WBR - couverture actuelle et reliquat.md` :

    1. Campaign Objective == "REACH"                        → REACH
    2. Ad set name commence par "ac - influencers"
       (insensible à la casse)
       OU Creative name commence par "ugc "
       (insensible à la casse)
       OU Creative name contient "(inf) ugc"                → UGC
    3. Creative ID matche "MPM-ADE-"
       OU Ad set name commence par "AD - ADE"               → ADE
    4. Ad set name contient "rmkt" (insensible à la casse)
       OU Creative ID matche "MPM-SLRMKT-"                  → RMKT
    5. Creative ID matche "MPM-TOURIST-"
       OU (Ad set name commence par "AD - OG - "
           ET Campaign Objective == "CONV")                 → TOURIST
    6. Creative ID matche "MPM-WL-" OU Phase == "Waitlist"  → WL
    7. Creative ID matche "MPM-OG-"                         → OG
    8. Sinon                                                → OTHER

Les clusters REACH, UGC, ADE, RMKT, TOURIST sont les 5 qui alimentent les
slides 14, 15, 16, 17, 18. WL/OG/OTHER ne sont pas affichés dans les
campaign reviews mais alimentent les agrégats Big Picture (slide 13).
"""
from __future__ import annotations

import re
from typing import Iterable

# Ordre garanti des clusters affichés sur les slides 14-18 du template Full.
# TOURIST est splité par langue : FR / EN / ES (via suffixe Ad set name ou
# token langue dans creative_name : -FRE_, -ENG_, -SPA_).
DISPLAY_CLUSTERS = ["REACH", "UGC", "ADE", "RMKT", "TOURIST_FR", "TOURIST_EN", "TOURIST_ES"]
ALL_CLUSTERS = DISPLAY_CLUSTERS + ["TOURIST_OTHER", "WL", "OG", "OTHER"]

# Regex précompilés
RE_ADE_ID = re.compile(r"MPM-ADE-", re.IGNORECASE)
RE_RMKT_ID = re.compile(r"MPM-SLRMKT-", re.IGNORECASE)
RE_TOURIST_ID = re.compile(r"MPM-TOURIST-", re.IGNORECASE)
RE_WL_ID = re.compile(r"MPM-WL-", re.IGNORECASE)
RE_OG_ID = re.compile(r"MPM-OG-", re.IGNORECASE)

# Tokens langue présents dans le creative_name technique
# (ex: "OG MESSAGING ES STATIC P2 // SM-Luminiscence-MPM-OG-OGMessageStatic-P2-1x1-BIQ-SPA_xxx")
RE_LANG_FRE = re.compile(r"-FRE[_\b]", re.IGNORECASE)
RE_LANG_ENG = re.compile(r"-ENG[_\b]", re.IGNORECASE)
RE_LANG_SPA = re.compile(r"-SPA[_\b]", re.IGNORECASE)


def detect_language(adset: str, creative_name: str) -> str:
    """Détecte la langue d'une créa.

    Stratégie : suffixe Ad set name (AD - OG - FR/EN/ES) prioritaire, fallback
    sur le token langue du creative_name technique (-FRE_/-ENG_/-SPA_).

    Renvoie 'FR', 'EN', 'ES', ou '' si indéterminé.
    """
    # Suffixe ad set
    if adset.endswith(" - FR") or adset.endswith(" FR"):
        return "FR"
    if adset.endswith(" - EN") or adset.endswith(" EN"):
        return "EN"
    if adset.endswith(" - ES") or adset.endswith(" ES"):
        return "ES"
    # Token langue dans creative name
    if RE_LANG_FRE.search(creative_name):
        return "FR"
    if RE_LANG_ENG.search(creative_name):
        return "EN"
    if RE_LANG_SPA.search(creative_name):
        return "ES"
    return ""


def classify_creative(fields: dict) -> str:
    """Retourne le cluster d'une créative à partir de ses champs Airtable.

    `fields` est attendu sous la forme `record["fields"]` côté Airtable.
    Les champs lus :
    - Campaign Objective
    - Phase WL/SL
    - Ad set name
    - Creative ID
    - Creative name
    """
    objective = (fields.get("Campaign Objective") or "").strip().upper()
    phase = (fields.get("Phase WL/SL") or "").strip()
    adset = (fields.get("Ad set name") or "").strip()
    creative_id = (fields.get("Creative ID") or "").strip()
    creative_name = (fields.get("Creative name") or "").strip()

    # Versions lower-case pour des comparaisons insensibles à la casse :
    # certaines villes utilisent "AC - INFLUENCERS" en majuscules (Reims),
    # d'autres "AC - Influencers" (Bayonne). Idem pour les variantes RMKT.
    adset_l = adset.lower()
    cname_l = creative_name.lower()

    # 1. REACH par objectif de campagne (prioritaire)
    if objective == "REACH":
        return "REACH"

    # 2. UGC élargi : ad set Influencers insensible à la casse,
    #    OU creative_name commençant par "UGC ",
    #    OU présence du tag "(inf) ugc" dans le creative_name (convention
    #    Lotchi pour les créas influenceurs).
    if (
        adset_l.startswith("ac - influencers")
        or cname_l.startswith("ugc ")
        or "(inf) ugc" in cname_l
    ):
        return "UGC"

    # 3. ADE par Creative ID OU Ad set name
    if RE_ADE_ID.search(creative_id) or adset.startswith("AD - ADE"):
        return "ADE"

    # 4. RMKT élargi : tout ad set contenant "RMKT" (insensible à la casse),
    #    ce qui capture "RMKT - SL", "RMKT - WL", "ADE - RMKT", etc. ;
    #    OU Creative ID matching MPM-SLRMKT-.
    if "rmkt" in adset_l or RE_RMKT_ID.search(creative_id):
        return "RMKT"

    # 5. TOURIST split par langue : Creative ID OU (AD - OG - ... ET CONV)
    is_tourist = RE_TOURIST_ID.search(creative_id) or (
        adset.startswith("AD - OG - ") and objective == "CONV"
    )
    if is_tourist:
        lang = detect_language(adset, creative_name)
        if lang == "FR":
            return "TOURIST_FR"
        if lang == "EN":
            return "TOURIST_EN"
        if lang == "ES":
            return "TOURIST_ES"
        return "TOURIST_OTHER"

    # 6. WL par Creative ID OU Phase
    if RE_WL_ID.search(creative_id) or phase == "Waitlist":
        return "WL"

    # 7. OG par Creative ID
    if RE_OG_ID.search(creative_id):
        return "OG"

    return "OTHER"


def group_by_cluster(records: Iterable[dict]) -> dict[str, list[dict]]:
    """Groupe les enregistrements Airtable Creative Performance par cluster.

    `records` est une liste d'enregistrements bruts Airtable (avec `fields`).
    Renvoie un dict {cluster: [records, ...]}.
    """
    out: dict[str, list[dict]] = {c: [] for c in ALL_CLUSTERS}
    for r in records:
        cluster = classify_creative(r.get("fields", {}))
        out.setdefault(cluster, []).append(r)
    return out


def aggregate_cluster_kpis(records: Iterable[dict]) -> dict:
    """Agrégat pondéré par impressions sur une liste de créatives d'un cluster.

    Renvoie : impressions totales, clics totaux, spend total, CTR moyen
    pondéré, CPM moyen pondéré, ROAS moyen pondéré.
    """
    imps_total = 0
    clicks_total = 0
    spend_total = 0.0
    revenue_total = 0.0  # estimé via ROAS × spend

    for r in records:
        f = r.get("fields", {})
        imps = int(f.get("Impressions") or 0)
        clicks = int(f.get("Clicks") or 0)
        spend = float(f.get("Spend") or 0.0)
        roas = float(f.get("ROAS") or 0.0)
        imps_total += imps
        clicks_total += clicks
        spend_total += spend
        revenue_total += spend * roas if roas else 0.0

    ctr = (clicks_total / imps_total) if imps_total else 0.0
    cpm = (spend_total / imps_total * 1000) if imps_total else 0.0
    roas = (revenue_total / spend_total) if spend_total else 0.0
    return {
        "impressions": imps_total,
        "clicks": clicks_total,
        "spend": spend_total,
        "revenue": revenue_total,
        "ctr": ctr,
        "cpm": cpm,
        "roas": roas,
    }
