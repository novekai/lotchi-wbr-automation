#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wbr_metrics.py — calcule les progressions W-2 -> W-1 d'un WBR et les sort en JSON.

But : fournir a Claude une table de metriques prete a rediger (Key Metrics), pour qu'il
n'ait JAMAIS a lire les chiffres sur les graphiques ni a deviner les semaines.

Source unique : schema mart_wbr, lu via le role analyst_wbr (lecture seule), exactement
comme generate_wbr.py. Les identifiants de semaines viennent de mart_wbr.cities :
  - review_week_id  = W-1 (semaine etudiee)
  - week_w2_id      = W-2 (semaine precedente)
  - week_w3_id      = W-3
  - review_week_start = lundi ISO de W-1 (cle de jointure des tables en serie temporelle)

Usage :
  WBR_DATABASE_URL=postgresql://analyst_wbr:...@host:5432/db?sslmode=require \
  python wbr/wbr_metrics.py --city bayonne [--out metrics_bayonne.json]

Sortie : JSON sur stdout (ou --out). Aucune ecriture dans la base.

Conventions de variation :
  - volume / money -> variation en POURCENTAGE : (w1 - w2) / w2 * 100
  - rate (CTR, conversion : stockes en fraction 0.0097) -> variation en POINTS : (w1 - w2) * 100
  - ratio spend/gross -> valeur en %, variation en points
  - donnee absente ou w2 nul -> variation = null (Claude ecrira N/A)
  - PAS de benchmark (il n'en existe pas) : le script n'en fournit aucun.

Dependances : psycopg2 (uniquement).
"""
import os, sys, json, argparse, datetime as dt
import psycopg2, psycopg2.extras

WEEKEND = {5, 6}  # samedi, dimanche (date.weekday())


# -- helpers de calcul --------------------------------------------------------
def num(x):
    return float(x) if x is not None else None


def var_pct(w1, w2):
    """Variation en % pour volumes / montants. None si non calculable."""
    if w1 is None or w2 in (None, 0):
        return None
    return (w1 - w2) / w2 * 100.0


def var_points(w1, w2):
    """Variation en points pour un taux stocke en fraction (0.0097 -> 0.97 %)."""
    if w1 is None or w2 is None:
        return None
    return (w1 - w2) * 100.0


def fr(v, decimals=0):
    """Formatage francais : separateur milliers = espace, decimale = virgule."""
    if v is None:
        return None
    s = f"{v:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return s


def variation_str(value, unit, decimals):
    """'+6 %' / '-1,8 pt' ... ; None -> None."""
    if value is None:
        return None
    sign = "+" if value >= 0 else "-"
    return f"{sign}{fr(abs(value), decimals)} {unit}"


def metric(label, key, mtype, w1, w2, higher_is_better):
    """Construit l'entree d'une metrique avec sa variation formatee."""
    w1, w2 = num(w1), num(w2)
    if mtype in ("volume", "money"):
        v = var_pct(w1, w2)
        unit, dec = "%", 0
    elif mtype == "rate":
        v = var_points(w1, w2)
        unit, dec = "pt", 2
    elif mtype == "ratio":  # w1/w2 deja en % (valeur), variation en points
        v = None if (w1 is None or w2 is None) else (w1 - w2)
        unit, dec = "pt", 1
    else:
        v, unit, dec = None, "", 0
    return {
        "label": label,
        "key": key,
        "type": mtype,
        "w1": w1,
        "w2": w2,
        "variation": v,
        "unit": unit if v is not None else None,
        "variation_str": variation_str(v, unit, dec),
        "higher_is_better": higher_is_better,
    }


# -- acces mart_wbr -----------------------------------------------------------
def load(url, city):
    conn = psycopg2.connect(url)
    conn.set_client_encoding("UTF8")
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def q(sql, *a):
        cur.execute(sql, a)
        return [dict(r) for r in cur.fetchall()]

    d = {"city": q("SELECT * FROM mart_wbr.cities WHERE city=%s", city)[0]}
    for t in ("mkt_performance", "tickets_sold", "landing_page", "product_page"):
        d[t] = q(f"SELECT * FROM mart_wbr.{t} WHERE city=%s ORDER BY date", city)
    d["big"] = q(
        "SELECT * FROM mart_wbr.big_picture WHERE city=%s AND wbr_label IS NOT NULL "
        "ORDER BY wbr_label, week_id",
        city,
    )
    d["soldout"] = q(
        "SELECT * FROM mart_wbr.soldout WHERE city=%s ORDER BY event_date, start_time", city
    )
    conn.close()
    return d


def by_date(rows):
    return {r["date"]: r for r in rows if r.get("date")}


def big_index(rows):
    return {(r["wbr_label"], r["week_id"]): r for r in rows}


# -- construction des metriques par slide -------------------------------------
def build(d):
    c = d["city"]
    rev, w2 = c["review_week_id"], c["week_w2_id"]
    rws = c["review_week_start"]
    rws2 = rws - dt.timedelta(days=7)

    mkt = by_date(d["mkt_performance"])
    tic = by_date(d["tickets_sold"])
    lp = by_date(d["landing_page"])
    pp = by_date(d["product_page"])
    big = big_index(d["big"])

    def g(idx, date, field):
        r = idx.get(date)
        return r.get(field) if r else None

    # slide 5 - General Highlights
    inv1, inv2 = g(mkt, rws, "mkt_investment"), g(mkt, rws2, "mkt_investment")
    gr1, gr2 = g(mkt, rws, "gross_revenue"), g(mkt, rws2, "gross_revenue")
    sg1 = (num(inv1) / num(gr1) * 100.0) if (inv1 is not None and gr1) else None
    sg2 = (num(inv2) / num(gr2) * 100.0) if (inv2 is not None and gr2) else None
    slide5 = [
        metric("Tickets vendus", "tickets", "volume", g(tic, rws, "tickets"), g(tic, rws2, "tickets"), True),
        metric("Chiffre d'affaires", "gross_revenue", "money", gr1, gr2, True),
        metric("Marketing spend", "mkt_investment", "money", inv1, inv2, False),
        metric("Spend / gross", "spend_gross_ratio", "ratio", sg1, sg2, False),
    ]

    # slide 7 - Top Funnel : CTR Meta & Google (uniquement)
    slide7 = [
        metric("CTR Meta", "ctr_meta", "rate", g(big, ("Meta", rev), "ctr"), g(big, ("Meta", w2), "ctr"), True),
        metric("CTR Google Search", "ctr_google", "rate", g(big, ("Google", rev), "ctr"), g(big, ("Google", w2), "ctr"), True),
    ]

    # slide 8 - Landing page : visiteurs & CTR
    slide8 = [
        metric("Visiteurs", "visitors", "volume", g(lp, rws, "visitors"), g(lp, rws2, "visitors"), True),
        metric("CTR landing", "ctr_landing", "rate", g(lp, rws, "ctr"), g(lp, rws2, "ctr"), True),
    ]

    # slide 9 - Product page : pages vues & taux de conversion
    slide9 = [
        metric("Pages vues", "page_views", "volume", g(pp, rws, "estimated_page_views"), g(pp, rws2, "estimated_page_views"), True),
        metric("Taux de conversion", "conversion_rate", "rate", g(pp, rws, "conversion_rate"), g(pp, rws2, "conversion_rate"), True),
    ]

    # slide 13 - Big Picture : CTR & CPM, Meta & Google
    slide13 = [
        metric("CTR Meta", "ctr_meta", "rate", g(big, ("Meta", rev), "ctr"), g(big, ("Meta", w2), "ctr"), True),
        metric("CTR Google", "ctr_google", "rate", g(big, ("Google", rev), "ctr"), g(big, ("Google", w2), "ctr"), True),
        metric("CPM Meta", "cpm_meta", "money", g(big, ("Meta", rev), "cpm"), g(big, ("Meta", w2), "cpm"), False),
        metric("CPM Google", "cpm_google", "money", g(big, ("Google", rev), "cpm"), g(big, ("Google", w2), "cpm"), False),
    ]

    # slide 11 - Sold-out : VALEURS (taux de remplissage), pas de progression
    slide11 = build_soldout(d["soldout"], rws)

    # semaine de couverture (mercredi de presentation = review_week_start + 9 j) : info pour la redaction.
    # Le NOM DU FICHIER est gere par generate_wbr.py (WBR_<Ville>_W<sem>.pptx), pas ici.
    merc = rws + dt.timedelta(days=9)
    week_label = f"W{merc.isocalendar()[1]:02d}"

    return {
        "city": c["city"],
        "weeks": {
            "review_week_id": rev,
            "week_w2_id": w2,
            "week_w3_id": c.get("week_w3_id"),
            "review_week_start": rws.isoformat(),
            "presentation_date": merc.isoformat(),
            "cover_week_label": week_label,
        },
        "slides": {
            "5": {"title": "General Highlights", "metrics": slide5},
            "7": {"title": "Top Funnel: Meta Ads", "metrics": slide7},
            "8": {"title": "Mid Funnel: Landing page", "metrics": slide8},
            "9": {"title": "Low Funnel: Product page", "metrics": slide9},
            "11": {"title": "Sold-out", **slide11},
            "13": {"title": "Big Picture", "metrics": slide13},
        },
    }


def build_soldout(rows, rws):
    """Fenetres relatives a review_week_start : W-1 [0,6], en cours [7,13], W+1 [14,20]."""
    windows = [("W-1", 0, 6), ("Semaine en cours", 7, 13), ("W+1", 14, 20)]
    out = []
    for name, a0, a1 in windows:
        lo, hi = rws + dt.timedelta(days=a0), rws + dt.timedelta(days=a1)
        seg = [r for r in rows if r.get("event_date") and lo <= r["event_date"] <= hi]
        cap = sum(num(r["capacity"]) or 0 for r in seg)
        tot = sum(num(r["total_tickets"]) or 0 for r in seg)
        fill = (tot / cap) if cap else None
        we = [r for r in seg if r["event_date"].weekday() in WEEKEND]
        wd = [r for r in seg if r["event_date"].weekday() not in WEEKEND]

        def wfill(s):
            cc = sum(num(r["capacity"]) or 0 for r in s)
            tt = sum(num(r["total_tickets"]) or 0 for r in s)
            return (tt / cc) if cc else None

        graded = []
        for r in seg:
            try:
                p = float(r["sold_out"]) if r.get("sold_out") is not None else None
            except (TypeError, ValueError):
                p = None
            graded.append(
                {
                    "date": r["event_date"].isoformat(),
                    "start_time": r.get("start_time"),
                    "fill_rate": p,
                    "fill_pct": round(p * 100) if p is not None else None,
                }
            )
        worst = sorted([x for x in graded if x["fill_rate"] is not None], key=lambda x: x["fill_rate"])[:3]
        out.append(
            {
                "window": name,
                "fill_rate": fill,
                "fill_pct": round(fill * 100) if fill is not None else None,
                "weekend_fill_pct": round(wfill(we) * 100) if wfill(we) is not None else None,
                "weekday_fill_pct": round(wfill(wd) * 100) if wfill(wd) is not None else None,
                "n_sessions": len(seg),
                "worst_sessions": worst,
            }
        )
    return {"windows": out, "note": "Valeurs de remplissage, pas de progression."}


# -- main ---------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True)
    ap.add_argument("--url", default=os.environ.get("WBR_DATABASE_URL"))
    ap.add_argument("--out", default=None, help="fichier JSON de sortie (defaut : stdout)")
    a = ap.parse_args()
    if not a.url:
        sys.exit("WBR_DATABASE_URL manquant")
    data = build(load(a.url, a.city))
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"OK -> {a.out} | ville={data['city']} W-1={data['weeks']['review_week_id']} "
              f"W-2={data['weeks']['week_w2_id']}")
    else:
        print(text)


if __name__ == "__main__":
    main()
