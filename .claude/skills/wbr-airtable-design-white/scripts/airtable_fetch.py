"""
Récupération des données nécessaires à la génération du WBR depuis la base
Airtable « Lotchi WBR » (baseId = appfKTIV0MZCvLfbb).

Pré-requis utilisateur : la variable d'environnement `AIRTABLE_API_KEY` doit
être renseignée avec un Personal Access Token Airtable disposant du scope
`data.records:read` sur la base Lotchi WBR.

Usage minimal :

    from scripts.airtable_fetch import AirtableClient, WBRDataLoader

    client = AirtableClient()
    loader = WBRDataLoader(client, city="Bayonne", week_id="2026-W23")
    data = loader.load_all()

`data` est un dict contenant les sous-arbres `show`, `weeks`, `sessions`,
`weekly_kpis`, `marketing_channels`, `landing_page`, `funnel`, `creatives`,
`benchmarks` — exposés directement aux générateurs de charts et au pipeline
d'édition du PPTX.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


BASE_ID = "appfKTIV0MZCvLfbb"
API_ROOT = "https://api.airtable.com/v0"

# Identifiants de tables (constants, exposés par list_tables_for_base)
TABLES = {
    "shows": "tblV7UIPAduNXw4ET",
    "weeks": "tblHPVM75mnlG7m6f",
    "channels": "tblslQ62PzOtyq0kR",
    "sessions": "tblVxzUSsaPHtw5Hg",
    "weekly_kpis": "tblj9zsr8VtDiTCAB",
    "marketing_channels": "tblEz36Ho93JPvnyA",
    "landing_page": "tblNc4v03BdIynJuT",
    "funnel": "tbl2TVDYpusnXjOJa",
    "creatives": "tblXCWffe8mFtI3JQ",
    "benchmarks": "tblZgYld819sWSKM6",
}


# ---------------------------------------------------------------------------
# Client REST minimal


class AirtableError(RuntimeError):
    pass


def _load_dotenv_key(name: str = "AIRTABLE_API_KEY") -> str | None:
    """Fallback : lit `name` dans le fichier .env à la racine du skill
    (dossier parent de scripts/). Permet de packager la clé avec le skill
    sans configuration utilisateur."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, v = line.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'") or None
    return None


class AirtableClient:
    """Client REST Airtable v0 minimal, avec pagination + retry simple."""

    def __init__(self, api_key: str | None = None, base_id: str = BASE_ID):
        self.api_key = (api_key or os.environ.get("AIRTABLE_API_KEY")
                        or _load_dotenv_key())
        if not self.api_key:
            raise AirtableError(
                "AIRTABLE_API_KEY absent. Configurer la variable "
                "d'environnement ou le fichier .env à la racine du skill."
            )
        self.base_id = base_id

    def _request(self, url: str, max_retry: int = 3) -> dict:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
        )
        last_err: Exception | None = None
        for attempt in range(max_retry):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(1 + attempt)
        raise AirtableError(f"Airtable request failed after retries: {last_err}")

    def select(
        self,
        table_id: str,
        formula: str | None = None,
        fields: list[str] | None = None,
        page_size: int = 100,
        max_records: int | None = None,
    ) -> list[dict]:
        """Récupère tous les enregistrements d'une table, avec pagination."""
        records: list[dict] = []
        offset: str | None = None
        while True:
            params: dict[str, Any] = {"pageSize": page_size}
            if formula:
                params["filterByFormula"] = formula
            if fields:
                for f in fields:
                    params.setdefault("fields[]", []).append(f)
            if offset:
                params["offset"] = offset
            # Sérialisation manuelle (Airtable accepte fields[]=A&fields[]=B)
            flat_params = []
            for k, v in params.items():
                if isinstance(v, list):
                    for item in v:
                        flat_params.append((k, item))
                else:
                    flat_params.append((k, v))
            query = urllib.parse.urlencode(flat_params)
            url = f"{API_ROOT}/{self.base_id}/{table_id}?{query}"
            payload = self._request(url)
            for r in payload.get("records", []):
                records.append(r)
                if max_records and len(records) >= max_records:
                    return records
            offset = payload.get("offset")
            if not offset:
                break
        return records


# ---------------------------------------------------------------------------
# Loader haut niveau


@dataclass
class WBRDataLoader:
    client: AirtableClient
    city: str
    week_id: str  # ex "2026-W23"

    # Caches internes
    _show_record: dict | None = field(default=None, repr=False, init=False)
    _weeks_cache: dict[str, dict] = field(default_factory=dict, repr=False, init=False)

    # ------------------------------------------------------------------
    # Helpers

    @staticmethod
    def _esc(s: str) -> str:
        """Échappe une chaîne pour formule Airtable."""
        return s.replace('"', '\\"')

    def _week_offsets(self) -> list[str]:
        """Renvoie la liste des week IDs dans la sémantique WBR.

        Convention : `self.week_id` désigne la **Current week** du WBR (la
        semaine en cours côté présentation Lotchi).

        Retourne [W-3, W-2, W-1, Current, W+1] dans la sémantique slides :
            - W-3 = self.week_id - 3 semaines
            - W-2 = self.week_id - 2 semaines
            - W-1 = self.week_id - 1 semaine
            - Current = self.week_id
            - W+1 = self.week_id + 1 semaine
        """
        target = self._weeks_cache.get(self.week_id)
        if not target:
            target = self.get_week(self.week_id)
        from datetime import date, timedelta

        period_from = date.fromisoformat(target["fields"]["Period from"])
        ids = []
        for off in range(-3, 2):  # -3, -2, -1, 0, +1 → W-3, W-2, W-1, Current, W+1
            d = period_from + timedelta(weeks=off)
            y, w, _ = d.isocalendar()
            ids.append(f"{y}-W{w:02d}")
        return ids

    # ------------------------------------------------------------------
    # Loaders unitaires

    def get_show(self) -> dict:
        if self._show_record:
            return self._show_record
        formula = f'AND({{City}}="{self._esc(self.city)}", {{Active}}=1)'
        records = self.client.select(TABLES["shows"], formula=formula)
        if not records:
            raise AirtableError(
                f"Aucun show actif trouvé pour la ville {self.city!r}."
            )
        # Si plusieurs, on prend celui dont la fenêtre couvre week_id
        self._show_record = records[0]
        return self._show_record

    def get_week(self, week_id: str, allow_missing: bool = False) -> dict:
        """Retourne le record Airtable d'une semaine.

        Si `allow_missing=True` et la semaine n'est pas en base, retourne un
        record placeholder (utile pour les semaines futures W+1 qui n'ont pas
        encore de KPIs scrapés). Le placeholder n'a pas d'`id` et expose
        uniquement le champ `Week ID`.
        """
        if week_id in self._weeks_cache:
            return self._weeks_cache[week_id]
        formula = f'{{Week ID}}="{self._esc(week_id)}"'
        records = self.client.select(TABLES["weeks"], formula=formula, max_records=1)
        if not records:
            if allow_missing:
                placeholder = {"id": None, "fields": {"Week ID": week_id}}
                self._weeks_cache[week_id] = placeholder
                return placeholder
            raise AirtableError(f"Semaine inconnue dans la base : {week_id}")
        self._weeks_cache[week_id] = records[0]
        return records[0]

    def get_sessions(self, week_ids: list[str]) -> list[dict]:
        """Récupère toutes les sessions du show sur les semaines demandées."""
        show = self.get_show()
        show_id = show["fields"]["Show ID"]
        week_or = " , ".join(f'"{w}"' for w in week_ids)
        # On filtre via la session_key qui contient le Show ID + Event date,
        # mais c'est plus simple via la date du Period from/to des semaines.
        # On charge toutes les sessions du show et on filtre côté Python.
        formula = f'{{Show}}="{self._esc(show["id"])}"'
        # Hack : Airtable Lookup sur Show ID est plus fiable que le record link
        # Donc on filtre via la session_key qui commence par "<show_id> | "
        formula = f'FIND("{show_id}", {{Session key}})=1'
        records = self.client.select(TABLES["sessions"], formula=formula)
        # Filtrage côté Python par Week link
        week_record_ids = {self.get_week(w)["id"] for w in week_ids}
        out = []
        for r in records:
            wlinks = r["fields"].get("Week", [])
            if any(wid in week_record_ids for wid in wlinks):
                out.append(r)
        return out

    def get_weekly_kpis(self, week_ids: list[str]) -> list[dict]:
        show = self.get_show()
        show_id = show["fields"]["Show ID"]
        formula = f'FIND("{show_id}", {{KPI key}})=1'
        records = self.client.select(TABLES["weekly_kpis"], formula=formula)
        week_record_ids = {self.get_week(w)["id"] for w in week_ids}
        return [
            r for r in records
            if any(wid in week_record_ids for wid in r["fields"].get("Week", []))
        ]

    def get_marketing_channels(self, week_ids: list[str]) -> list[dict]:
        show = self.get_show()
        show_id = show["fields"]["Show ID"]
        formula = f'FIND("{show_id}", {{Channel perf key}})=1'
        records = self.client.select(TABLES["marketing_channels"], formula=formula)
        week_record_ids = {self.get_week(w)["id"] for w in week_ids}
        return [
            r for r in records
            if any(wid in week_record_ids for wid in r["fields"].get("Week", []))
        ]

    def get_landing_page(self, week_ids: list[str]) -> list[dict]:
        show = self.get_show()
        show_id = show["fields"]["Show ID"]
        formula = f'FIND("{show_id}", {{LP key}})=1'
        records = self.client.select(TABLES["landing_page"], formula=formula)
        week_record_ids = {self.get_week(w)["id"] for w in week_ids}
        return [
            r for r in records
            if any(wid in week_record_ids for wid in r["fields"].get("Week", []))
        ]

    def get_funnel(self, week_ids: list[str]) -> list[dict]:
        show = self.get_show()
        show_id = show["fields"]["Show ID"]
        formula = f'FIND("{show_id}", {{Funnel key}})=1'
        records = self.client.select(TABLES["funnel"], formula=formula)
        week_record_ids = {self.get_week(w)["id"] for w in week_ids}
        return [
            r for r in records
            if any(wid in week_record_ids for wid in r["fields"].get("Week", []))
        ]

    def get_creatives_weekly(self, snapshot_week: str) -> list[dict]:
        """Récupère les créatives en vraie maille hebdo pour le snapshot demandé.

        Priorité : les records `weekly_real` issus de la card Datacloud 21114
        Asset Comparison (vraies données hebdo par créa). Identifiés par le
        suffixe `|weekly_real` dans Creative perf key.
        """
        show = self.get_show()
        show_id = show["fields"]["Show ID"]
        # Filtre : clé qui commence par show_id ET se termine par |weekly_real
        formula = (
            f'AND('
            f'FIND("{show_id}", {{Creative perf key}})=1, '
            f'RIGHT({{Creative perf key}}, 12)="|weekly_real"'
            f')'
        )
        records = self.client.select(TABLES["creatives"], formula=formula)
        # Filtrage strict par snapshot week (via la 2e partie de la clé)
        out = []
        for r in records:
            key = r["fields"].get("Creative perf key", "")
            parts = key.split("|")
            if len(parts) >= 2 and parts[1].strip() == snapshot_week:
                out.append(r)
        return out

    def get_benchmarks(self) -> list[dict]:
        return self.client.select(TABLES["benchmarks"])

    # ------------------------------------------------------------------
    # Chargement complet

    def load_all(self) -> dict:
        """Charge tout ce qu'il faut pour générer le WBR Full v2.

        `week_ids` est l'ordre sémantique [W-3, W-2, W-1, Current, W+1].
        `creatives_wminus1` = créas snapshot W-1 (= semaine analysée).
        `creatives_wminus2` = créas snapshot W-2 pour les KPI summaries
        (slides 14-15 qui comparent W-2 vs W-1).
        """
        week_ids = self._week_offsets()  # [W-3, W-2, W-1, Current, W+1]
        w_minus2 = week_ids[1]
        w_minus1 = week_ids[2]
        show = self.get_show()
        return {
            "show": show,
            "week_ids": week_ids,
            # W+1 (futur) peut ne pas être encore en base — on tolère
            "weeks": [self.get_week(w, allow_missing=True) for w in week_ids],
            # Sessions sold-out : W-1 (passé), Current (en cours), W+1 (futur)
            "sessions": self.get_sessions(week_ids[2:5]),
            "weekly_kpis": self.get_weekly_kpis(week_ids),
            "marketing_channels": self.get_marketing_channels(week_ids),
            "landing_page": self.get_landing_page(week_ids),
            "funnel": self.get_funnel(week_ids),
            "creatives_wminus1": self.get_creatives_weekly(w_minus1),
            "creatives_wminus2": self.get_creatives_weekly(w_minus2),
            "benchmarks": self.get_benchmarks(),
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Diagnostic Airtable Lotchi WBR")
    parser.add_argument("--city", required=True)
    parser.add_argument("--week", required=True)
    args = parser.parse_args()
    client = AirtableClient()
    loader = WBRDataLoader(client, city=args.city, week_id=args.week)
    data = loader.load_all()
    print(f"OK: show={data['show']['fields'].get('Show name')}, "
          f"week_ids={data['week_ids']}, "
          f"creatives_w1={len(data['creatives_wminus1'])}, "
          f"creatives_w2={len(data['creatives_wminus2'])}")
