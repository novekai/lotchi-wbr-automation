"""
generate_charts.py — MOTEUR DE GRAPHES v4 "Lotchi design" (dark, analytique).

Version design du skill wbr-airtable. Mêmes signatures que l'original (build_wbr.py
inchangé) mais rendu repensé pour l'analyse en réunion :
  - fond noir cinématique (#000000, = fond des slides du template) ;
  - orange #FF4200 en accent focal unique (la barre ou la ligne clé) ;
  - grille H+V discrète + graduations d'axes conservées ;
  - légende en bas, titre épuré seul en haut ;
  - deltas d'évolution vert/rouge entre semaines, dernière semaine mise en avant ;
  - combos : barres neutres calées en bas, ligne orange flottant au-dessus (jamais orange sur orange).

Fonts : Sora/Heebo si installées (rendu fidèle), sinon Montserrat/Carlito/DejaVu.
Les figsizes sont calées sur les ratios des zones du template design (voir BOX).
"""
import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as mticker
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import numpy as np

# --------------------------------------------------------------------------- #
# Palette & fonts                                                             #
# --------------------------------------------------------------------------- #
# Toggle de mode : WBR_CHART_MODE=dark pour la variante fond noir (defaut : light)
MODE = os.environ.get("WBR_CHART_MODE", "light").lower()
ACCENT = "#FF4200"
if MODE == "light":
    BG = "#F7F6F4"; FG = "#1A1A1A"; SEC = "#3D3D3D"; MUTED = "#8C8C8C"
    NEUTRAL = "#CFCDC8"; NEUTRAL2 = "#E4E2DE"; GRID = "#ECEAE6"; AXIS = "#6B6B6B"; BASE = "#C9C7C2"
    POS = "#16A34A"; NEG = "#DC2626"
    RAIL = "#E7E5E1"; CARD_HDR = "#F0EEEA"; CARD_R0 = "#FFFFFF"; CARD_R1 = "#F7F6F4"
    CARD_TXT = "#3D3D3D"; CARD_TXT_HI = "#1A1A1A"; CARD_HDR_TXT = "#1A1A1A"; CARD_BORD = "#DCDAD5"
else:
    BG = "#000000"; FG = "#FFFFFF"; SEC = "#BFBFBF"; MUTED = "#8C8C8C"
    NEUTRAL = "#6E6E6E"; NEUTRAL2 = "#454545"; GRID = "#242424"; AXIS = "#8C8C8C"; BASE = "#3D3D3D"
    POS = "#22C55E"; NEG = "#F0483E"
    RAIL = "#2A2A2A"; CARD_HDR = "#161616"; CARD_R0 = "#000000"; CARD_R1 = "#0D0D0D"
    CARD_TXT = "#E6E6E6"; CARD_TXT_HI = "#FFFFFF"; CARD_HDR_TXT = "#FFFFFF"; CARD_BORD = "#2A2A2A"

_AVAIL = {f.name for f in fm.fontManager.ttflist}
def _pick(cands):
    for c in cands:
        if c in _AVAIL:
            return c
    return "DejaVu Sans"
FD = _pick(["Century Gothic", "Sora", "Sora Medium", "Montserrat", "DejaVu Sans"])   # display
FB = _pick(["Heebo", "Heebo Light", "Carlito", "DejaVu Sans"])     # body

mpl.rcParams.update({"font.family": FB, "font.size": 9})

# Ratios des zones du template design (W/H en pouces) -> figsize
BOX = {
    "mkt":     (5.88, 1.799), "tickets": (5.906, 1.64),
    "meta":    (5.906, 3.602), "landing": (5.906, 3.584), "product": (5.88, 3.63),
    "soldout": (3.176, 2.242),
}
def _figsize(key, base_w=9.0):
    w, h = BOX[key]
    return (base_w, base_w * h / w)

# --------------------------------------------------------------------------- #
# Formatters                                                                  #
# --------------------------------------------------------------------------- #
def _sp(v):  return f"{v:,.0f}".replace(",", " ")
def _pct1(v): return f"{v:.1f}%".replace(".", ",")
def _pct2(v): return f"{v:.2f}%".replace(".", ",")
def _kcur(v, cur="€"): return f"{v/1000:.1f}k{cur}".replace(".", ",")

# --------------------------------------------------------------------------- #
# Primitives de rendu                                                         #
# --------------------------------------------------------------------------- #
def _fig(key):
    fig = plt.figure(figsize=_figsize(key), dpi=190)
    fig.patch.set_facecolor(BG)
    return fig

def _style(ax):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=AXIS, labelsize=9)
    for lb in ax.get_xticklabels() + ax.get_yticklabels():
        lb.set_fontfamily(FB)

def _grid(ax, vertical=True):
    ax.set_axisbelow(True)
    ax.grid(True, axis="y", color=GRID, lw=0.8, zorder=0)
    if vertical:
        ax.grid(True, axis="x", color=GRID, lw=0.8, zorder=0)

def _title(fig, title, x=0.075, y=0.9):
    fig.text(x, y, title, family=FD, fontsize=15, color=FG, weight="bold", va="center")

def _legend_bottom(fig, items, y=0.055):
    widths = [0.02 + 0.0092 * len(l) + 0.03 for _, l in items]
    x = 0.5 - sum(widths) / 2
    for (c, l), w in zip(items, widths):
        fig.add_artist(Line2D([x], [y], marker="s", ms=8, color=c, ls="none",
                              transform=fig.transFigure))
        fig.text(x + 0.017, y, l, family=FB, fontsize=8.5, color=SEC, va="center")
        x += w

def _save(fig, out_path):
    fig.savefig(out_path, facecolor=BG, dpi=fig.dpi)
    plt.close(fig)
    return Path(out_path)

def _layout(key):
    """(title_y, rect, legend_y) selon zone haute (tall) ou large-courte (wide)."""
    w, h = BOX[key]
    if w / h < 2.4:   # tall
        return 0.93, (0.085, 0.15, 0.83, 0.70), 0.05
    return 0.89, (0.085, 0.22, 0.83, 0.52), 0.075   # wide-court

def _deltas(ax, x, values, ymax):
    for i in range(1, len(values)):
        if not values[i-1]:
            continue
        d = (values[i] - values[i-1]) / values[i-1] * 100
        up = d >= 0
        col = POS if up else NEG
        xm = (x[i] + x[i-1]) / 2
        ax.plot([xm - 0.16], [ymax * 0.93], marker="^" if up else "v", ms=6,
                color=col, clip_on=False, zorder=6)
        ax.text(xm - 0.08, ymax * 0.93, f"{d:+.0f}%".replace(".", ","), ha="left",
                va="center", family=FB, fontsize=8.5, color=col, weight="bold")

# --------------------------------------------------------------------------- #
# Cœur combo (barres neutres bas + ligne orange haut, double axe)             #
# --------------------------------------------------------------------------- #
def _render_combo(key, weeks, bar_series, bar_names, bar_fmt, line, line_name,
                  line_fmt, laxis_fmt, raxis_fmt, title, out_path,
                  line2=None, line2_name=None, line2_fmt=None,
                  line_left=None, line_left_name=None, line_left_fmt=None):
    if MODE == "light":
        YEL = "#334155"    # ardoise : ligne axe gauche (Gross - Mkt value, en €)
        ACC2 = "#8C8C8C"   # gris : 2e ligne pointillee (Acc ROI cumule)
    else:
        YEL = "#FFC400"    # jaune : ligne axe gauche (Gross - Mkt value, en €)
        ACC2 = "#FF8A5B"   # orange clair : 2e ligne (Acc ROI cumule)
    ty, rect, ly = _layout(key)
    fig = _fig(key); ax = fig.add_axes(rect); ax.set_facecolor(BG)
    _style(ax); _grid(ax, vertical=True)
    x = np.arange(len(weeks)); nb = len(bar_series)
    bw = 0.6 / nb
    bar_cols = [NEUTRAL, NEUTRAL2, MUTED]
    for bi, s in enumerate(bar_series):
        off = (bi - (nb - 1) / 2) * bw
        ax.bar(x + off, s, width=bw * 0.9, color=bar_cols[bi % 3], zorder=3)
    ax.axhline(0, color=BASE, lw=1.0, zorder=2)
    ax.set_xticks(x); ax.set_xticklabels(weeks)
    maxbar = max(max(s) for s in bar_series)
    ax.set_ylim(0, maxbar / 0.55)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(5))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: laxis_fmt(v)))
    ax.margins(x=0.06)
    if bar_fmt:
        for bi, s in enumerate(bar_series):
            off = (bi - (nb - 1) / 2) * bw
            for xi, v in zip(x, s):
                ax.text(xi + off, v + maxbar * 0.03, bar_fmt(v), ha="center",
                        va="bottom", family=FB, fontsize=8, color=SEC, zorder=9,
                        path_effects=[pe.withStroke(linewidth=3.0, foreground=BG)])
    if line_left is not None:
        llf = line_left_fmt or (lambda v: f"{v:.0f}")
        ax.plot(x, line_left, color=YEL, lw=2.2, marker="o", ms=4, mfc=BG,
                mec=YEL, mew=1.4, zorder=5)
        for xi, v in zip(x, line_left):
            ax.annotate(llf(v), (xi, v), textcoords="offset points", xytext=(0, -13),
                        ha="center", va="top", fontsize=8, family=FB, color=YEL,
                        weight="bold", bbox=dict(boxstyle="round,pad=0.15", fc=BG, ec="none", alpha=0.6), zorder=7)
    ax2 = ax.twinx(); ax2.set_facecolor("none")
    for s in ax2.spines.values():
        s.set_visible(False)
    ax2.tick_params(length=0, colors=AXIS, labelsize=9)
    for lb in ax2.get_yticklabels():
        lb.set_fontfamily(FB)
    ax2.yaxis.set_major_locator(mticker.MaxNLocator(4))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: raxis_fmt(v)))
    all_line = list(line) + (list(line2) if line2 is not None else [])
    lmin, lmax = min(all_line), max(all_line)
    span = (lmax - lmin) or (lmax or 1.0)
    d = span / 0.26
    ax2.set_ylim(lmin - 0.66 * d, lmin + 0.42 * d)
    ax2.plot(x, line, color=ACCENT, lw=2.6, marker="o", ms=5, mfc=BG,
             mec=ACCENT, mew=1.6, zorder=6)
    for xi, v in zip(x, line):
        ax2.annotate(line_fmt(v), (xi, v), textcoords="offset points", xytext=(0, 11),
                     ha="center", va="bottom", fontsize=8.5, family=FB, color=ACCENT,
                     weight="bold", bbox=dict(boxstyle="round,pad=0.15", fc=BG, ec="none", alpha=0.6), zorder=8)
    if line2 is not None:
        f2 = line2_fmt or line_fmt
        ax2.plot(x, line2, color=ACC2, lw=2.2, ls="--", marker="o", ms=4, mfc=BG,
                 mec=ACC2, mew=1.4, zorder=5)
        for xi, v in zip(x, line2):
            ax2.annotate(f2(v), (xi, v), textcoords="offset points", xytext=(0, -18),
                         ha="center", va="top", fontsize=8, family=FB, color=ACC2,
                         weight="bold", bbox=dict(boxstyle="round,pad=0.15", fc=BG, ec="none", alpha=0.6), zorder=7)
    _title(fig, title, y=ty)
    items = [(bar_cols[i % 3], bar_names[i]) for i in range(nb)]
    if line_left is not None:
        items.append((YEL, line_left_name))
    items.append((ACCENT, line_name))
    if line2 is not None:
        items.append((ACC2, line2_name))
    _legend_bottom(fig, items, y=ly)
    return _save(fig, out_path)

# --------------------------------------------------------------------------- #
# Slide 5 haut — Mkt performance (CA + spend + ROI)                           #
# --------------------------------------------------------------------------- #
def chart_mkt_performance(weeks, revenue, spend, roas, *, currency_revenue="€",
                          currency_spend="$", country_5kpi=True, out_path, acc_roas=None):
    _r = lambda v: f"{v:.1f}".replace(".", ",")
    net = [rv - sp for rv, sp in zip(revenue, spend)]
    return _render_combo(
        "mkt", weeks, [revenue, spend], ["CA brut", "Marketing value"],
        lambda v: _kcur(v, currency_revenue), roas, "ROI", _r,
        laxis_fmt=lambda v: _kcur(v, currency_revenue) if v else "0",
        raxis_fmt=lambda v: f"{v:.0f}",
        title="Chiffre d'affaires brut & ROI", out_path=out_path,
        line2=acc_roas, line2_name="Acc ROI", line2_fmt=_r,
        line_left=net, line_left_name="Gross - Mkt value",
        line_left_fmt=lambda v: _kcur(v, currency_revenue))

# --------------------------------------------------------------------------- #
# Slide 5 bas — Tickets sold                                                  #
# --------------------------------------------------------------------------- #
def chart_tickets_sold(weeks, tickets, out_path):
    ty, rect, ly = _layout("tickets")
    fig = _fig("tickets"); ax = fig.add_axes(rect); ax.set_facecolor(BG)
    _style(ax); _grid(ax, vertical=True)
    hi = len(tickets) - 1
    cols = [ACCENT if i == hi else NEUTRAL for i in range(len(tickets))]
    x = np.arange(len(tickets))
    ax.bar(x, tickets, color=cols, width=0.6, zorder=3)
    ax.axhline(0, color=BASE, lw=1.1, zorder=2)
    ax.set_xticks(x); ax.set_xticklabels(weeks)
    ax.set_ylim(0, max(tickets) * 1.22)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(5))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: _sp(v)))
    ax.margins(x=0.06)
    for i, v in enumerate(tickets):
        ax.text(i, v + max(tickets) * 0.03, _sp(v), ha="center", va="bottom",
                family=FB, fontsize=9.5, color=FG if i == hi else SEC,
                weight="bold" if i == hi else "normal")
    _deltas(ax, x, tickets, max(tickets) * 1.22)
    _title(fig, "Tickets vendus par semaine", y=ty)
    _legend_bottom(fig, [(NEUTRAL, "Semaines precedentes"), (ACCENT, "Derniere semaine")], y=ly)
    return _save(fig, out_path)

# --------------------------------------------------------------------------- #
# Slide 7 — CTRs Meta + Google (groupées)                                     #
# --------------------------------------------------------------------------- #
def chart_top_funnel_ctrs(weeks, meta_ctr_pct, google_ctr_pct, out_path):
    """Multi-courbes : CTR Meta (accent) + CTR Google (neutre) sur les semaines."""
    ty, rect, ly = _layout("meta")
    fig = _fig("meta"); ax = fig.add_axes(rect); ax.set_facecolor(BG)
    _style(ax); _grid(ax, vertical=True)
    x = np.arange(len(weeks))
    ax.set_xticks(x); ax.set_xticklabels(weeks)
    ymax = max(max(meta_ctr_pct), max(google_ctr_pct))
    ymin = min(min(meta_ctr_pct), min(google_ctr_pct))
    pad = (ymax - ymin) or ymax or 1.0
    ax.set_ylim(max(0, ymin - pad*0.35), ymax + pad*0.45)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(5))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: _pct1(v)))
    ax.margins(x=0.06)
    ax.plot(x, google_ctr_pct, color=NEUTRAL, lw=2.4, marker="o", ms=5, mfc=BG,
            mec=NEUTRAL, mew=1.4, zorder=4)
    ax.plot(x, meta_ctr_pct, color=ACCENT, lw=2.8, marker="o", ms=6, mfc=ACCENT,
            mec=BG, mew=1.2, zorder=6)
    # Étiquettes toujours par-dessus les lignes (zorder haut + fond sombre) et
    # placement adaptatif : à chaque point, la courbe la plus haute a son label
    # au-dessus, la plus basse en dessous -> jamais de collision, même au croisement.
    _bb = dict(boxstyle="round,pad=0.15", fc=BG, ec="none", alpha=0.6)
    _ylo, _yhi = ax.get_ylim(); _yr = (_yhi - _ylo) or 1.0
    for xi, m, g in zip(x, meta_ctr_pct, google_ctr_pct):
        m_up = m >= g
        g_up = not m_up
        # garde : un point trop proche du bas met son label au-dessus (évite l'axe X)
        if m - _ylo < _yr * 0.12: m_up = True
        if g - _ylo < _yr * 0.12: g_up = True
        ax.annotate(_pct2(m), (xi, m), textcoords="offset points",
                    xytext=(0, 11 if m_up else -16), ha="center",
                    va="bottom" if m_up else "top", fontsize=8.5, family=FB,
                    color=FG, weight="bold", bbox=_bb, zorder=11)
        ax.annotate(_pct2(g), (xi, g), textcoords="offset points",
                    xytext=(0, 11 if g_up else -16), ha="center",
                    va="bottom" if g_up else "top", fontsize=8, family=FB,
                    color=SEC, bbox=_bb, zorder=10)
    _title(fig, "CTR par canal", y=ty)
    _legend_bottom(fig, [(NEUTRAL, "Google Search"), (ACCENT, "Meta (FB+IG)")], y=ly)
    return _save(fig, out_path)

# --------------------------------------------------------------------------- #
# Slide 8 — Landing page (visiteurs + clics + CTR)                            #
# --------------------------------------------------------------------------- #
def chart_landing_page(weeks, visitors, cta_clicks, ctr_pct, out_path):
    return _render_combo(
        "landing", weeks, [visitors, cta_clicks], ["Visiteurs", "Clics CTA"],
        _sp, ctr_pct, "CTR", _pct1,
        laxis_fmt=lambda v: f"{v/1000:.0f}k" if v else "0",
        raxis_fmt=lambda v: _pct1(v),
        title="Visiteurs sur le site & CTR", out_path=out_path)

# --------------------------------------------------------------------------- #
# Slide 9 — Product page (pages vues + CR)                                    #
# --------------------------------------------------------------------------- #
def chart_product_page(weeks, pp_views, cr_pct, out_path):
    return _render_combo(
        "product", weeks, [pp_views], ["Pages vues"],
        _sp, cr_pct, "Taux de conversion", _pct1,
        laxis_fmt=lambda v: f"{v/1000:.0f}k" if v else "0",
        raxis_fmt=lambda v: _pct1(v),
        title="Pages vues & taux de conversion", out_path=out_path)

# --------------------------------------------------------------------------- #
# Slide 11 — Sold-out : barres de remplissage (remplace le tableau)           #
# --------------------------------------------------------------------------- #
def soldout_table(sessions, out_path, *, width_in=3.176, height_in=2.242):
    """Tableau sold-out par seance, fond BLANC + zebrage gris leger.
    Colonnes : Date | Capacite | Billets totaux | Disponibles | Sold-out.
    Rouge/vert conserve sur la colonne Sold-out. sessions : [{date,time,cap,sold,fill}]."""
    from matplotlib.table import Table as _Table
    W_BG="#F7F6F4"; HDR="#434343"; HDR_TXT="#FFFFFF"; ZEB="#FFFFFF"
    TXTC="#1A1A1A"; BORDC="#DCDAD5"; VERT="#16A34A"; ROUGE="#DC2626"
    rows=[x for x in sessions if x.get("cap",0)>0]
    rows.sort(key=lambda r:(r.get("date",""), r.get("time","")))
    ratio=height_in/width_in
    fig=plt.figure(figsize=(6.0, 6.0*ratio), dpi=200); fig.patch.set_facecolor(W_BG)
    ax=fig.add_axes([0,0,1,1]); ax.axis("off"); ax.set_facecolor(W_BG)
    if not rows:
        ax.text(0.5,0.5,"Aucune seance\navec capacite",ha="center",va="center",
                family=FB, fontsize=9, color="#8C8C8C")
        fig.savefig(out_path, facecolor=W_BG, dpi=fig.dpi); plt.close(fig); return Path(out_path)
    headers=["Date","Capacite","Billets totaux","Disponibles","Sold-out"]
    cw=[0.20,0.18,0.24,0.20,0.18]; n=len(rows); rh=1.0/(n+1); fs=6.8
    tbl=_Table(ax,bbox=[0,0,1,1])
    for j,h in enumerate(headers):
        c=tbl.add_cell(0,j,cw[j],rh,text=h,loc="center"); c.set_facecolor(ACCENT if j==0 else HDR)
        c.get_text().set_color(HDR_TXT); c.get_text().set_fontsize(fs); c.get_text().set_fontweight("bold")
        c.set_edgecolor(BORDC); c.set_linewidth(0.8)
    for i,sx in enumerate(rows,start=1):
        cap=int(sx.get("cap",0)); sold=int(sx.get("sold",0)); fill=sx.get("fill",0.0)
        dispo=max(cap-sold,0); soldpct=(fill*100) if fill else ((sold/cap*100) if cap else 0)
        dt=("%s %s"%(str(sx.get("date",""))[-5:], sx.get("time",""))).strip()
        vals=[dt,str(cap),str(cap),str(dispo),"%.1f%%"%soldpct]
        bg=ZEB if i%2==0 else W_BG
        for j,v in enumerate(vals):
            c=tbl.add_cell(i,j,cw[j],rh,text=v,loc="center"); c.set_facecolor(bg)
            c.set_edgecolor(BORDC); c.set_linewidth(0.8); c.get_text().set_fontsize(fs)
            if j==4:
                c.get_text().set_color(VERT if soldpct>=99.9 else ROUGE); c.get_text().set_fontweight("bold")
            else:
                c.get_text().set_color(TXTC)
    ax.add_table(tbl)
    fig.savefig(out_path, facecolor=W_BG, dpi=fig.dpi); plt.close(fig); return Path(out_path)

def soldout_placeholder(text, out_path, *, width_in=3.176, height_in=2.242):
    W_BG="#F7F6F4"; ratio=height_in/width_in
    fig=plt.figure(figsize=(6.0,6.0*ratio),dpi=200); fig.patch.set_facecolor(W_BG)
    ax=fig.add_axes((0.05,0.05,0.90,0.90)); ax.set_facecolor(W_BG); ax.axis("off")
    ax.text(0.5,0.5,text,ha="center",va="center",family=FB,fontsize=10,color="#8C8C8C",wrap=True)
    fig.savefig(out_path, facecolor=W_BG, dpi=fig.dpi); plt.close(fig); return Path(out_path)

import io
import urllib.request
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

def _fetch_thumbnail(url, timeout_s=1.5):
    if not url or "facebook.com/ads/image" in url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (wbr thumbnail)"})
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = resp.read()
        from PIL import Image
        img = Image.open(io.BytesIO(data)); img.thumbnail((80, 80))
        return img
    except Exception:
        return None

def _fetch_thumbnails_parallel(urls, max_workers=16):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(_fetch_thumbnail, urls))

def creative_assets_table(creatives, out_path, *, max_rows=8, aspect=None):
    """Tableau d'inventaire de creas, fond BLANC + zebrage gris leger, texte fonce.
    `aspect` = W/H de la boite cible (pour rendre au bon ratio, sans distorsion)."""
    W_BG="#F7F6F4"; HDR="#434343"; HDR_TXT="#FFFFFF"; BORDC="#DCDAD5"
    R0="#FFFFFF"; R1="#F7F6F4"; TXTC="#1A1A1A"; TXT_HI="#1A1A1A"; THUMB_BG="#EFEFEF"
    rows = sorted(creatives, key=lambda c: c.get("impressions") or 0, reverse=True)[:max_rows]
    urls = [c.get("preview_url") or "" for c in rows]
    thumbs = _fetch_thumbnails_parallel(urls)
    fig_w = 13.0
    fig_h = (fig_w/aspect) if aspect else max(2.0, 0.40*(len(rows)+1)+0.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor(W_BG); ax.set_facecolor(W_BG); ax.axis("off")
    headers = ["", "Publicite", "Date debut", "Date fin", "Impressions", "CTR", "ROAS", "CPC", "CPM"]
    rows_data = []
    for c in rows:
        imps=c.get("impressions") or 0; ctr=c.get("ctr") or 0.0
        roas=c.get("roas_utm") or c.get("roas") or 0.0; cpc=c.get("cpc") or 0.0; cpm=c.get("cpm") or 0.0
        dp=c.get("date_posted") or "-"
        rows_data.append(["", (c.get("creative_name") or "-")[:50], str(dp)[:10] if dp!="-" else "-", "-",
            ("%s"%f"{imps:,}").replace(","," "),
            (f"{ctr*100:.2f}%" if ctr<=1 else f"{ctr:.2f}%"),
            (f"{roas:.2f}" if roas else "-"), (f"{cpc:.2f} $" if cpc else "-"), f"{cpm:.2f} $"])
    if not rows_data:
        ax.text(0.5,0.5,"Aucune crea dans ce cluster sur la fenetre demandee.",
                ha="center",va="center",family=FB,fontsize=10,color="#8C8C8C")
        plt.tight_layout(); plt.savefig(out_path,dpi=150,bbox_inches="tight",facecolor=W_BG); plt.close()
        return Path(out_path)
    col_widths=[0.09,0.32,0.08,0.08,0.12,0.08,0.08,0.08,0.09]
    table=ax.table(cellText=rows_data,colLabels=headers,loc="center",cellLoc="center",colWidths=col_widths)
    table.auto_set_font_size(False); table.set_fontsize(8); table.scale(1,1.7)
    for j in range(len(headers)):
        c=table[(0,j)]; c.set_facecolor(ACCENT if j==1 else HDR); c.set_text_props(weight="bold",color=HDR_TXT); c.set_edgecolor(BORDC)
    for i in range(1,len(rows_data)+1):
        for j in range(len(headers)):
            cell=table[(i,j)]; cell.set_facecolor(R1 if i%2 else R0)
            cell.set_text_props(color=TXTC); cell.set_edgecolor(BORDC)
            if j==0: cell.set_facecolor(THUMB_BG)
            if j==len(headers)-1 or j==6: cell.set_text_props(color=TXT_HI)
    fig.canvas.draw()
    for i,thumb in enumerate(thumbs,start=1):
        if thumb is None: continue
        cell=table[(i,0)]; bbox=cell.get_window_extent(fig.canvas.get_renderer())
        inv=ax.transAxes.inverted(); ba=inv.transform(bbox)
        xc=(ba[0][0]+ba[1][0])/2; yc=(ba[0][1]+ba[1][1])/2
        ab=AnnotationBbox(OffsetImage(thumb,zoom=0.22),(xc,yc),xycoords="axes fraction",frameon=False,pad=0)
        ax.add_artist(ab)
    plt.tight_layout(); plt.savefig(out_path,dpi=160,bbox_inches="tight",facecolor=W_BG); plt.close()
    return Path(out_path)
