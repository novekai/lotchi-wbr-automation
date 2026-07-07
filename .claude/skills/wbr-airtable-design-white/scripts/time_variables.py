"""
Calcul automatique des variables temporelles de la WBR.

Convention Lotchi : la WBR est présentée le mercredi, et porte sur la semaine
ISO précédente (lundi à dimanche).

Usage minimal :
    from scripts.time_variables import compute_dates
    dates = compute_dates()             # depuis la date du jour
    dates = compute_dates(today=...)    # ou explicitement
"""
from datetime import date, timedelta
from dataclasses import dataclass


@dataclass
class WbrDates:
    """Toutes les dates utiles pour générer la WBR."""
    today: date
    lundi_w: date            # lundi de la semaine analysée (W-1 par rapport au jour de présentation)
    dimanche_w: date         # dimanche de la semaine analysée
    mercredi_presentation: date  # mercredi de présentation
    week_id: str             # ex : "2026-W22"
    week_id_minus1: str      # ex : "2026-W21"
    week_id_minus2: str      # ex : "2026-W20"
    week_id_plus1: str       # ex : "2026-W23"

    @property
    def date_mercredi(self) -> str:
        """Format DD/MM/YYYY pour insertion dans le cover_textbox."""
        return self.mercredi_presentation.strftime("%d/%m/%Y")


def compute_dates(today: date | None = None) -> WbrDates:
    """
    Calcule toutes les dates à partir d'une date d'exécution.

    Règle :
    - La WBR est présentée le mercredi de la semaine courante.
    - Elle porte sur la semaine ISO précédente (lundi à dimanche).

    Si le run a lieu un mercredi, on prend la semaine précédente.
    Si le run a lieu un autre jour, on prend la semaine en cours OU précédente
    selon que dimanche est passé.

    Heuristique simple : on prend le mercredi le plus proche dans le futur
    (ou aujourd'hui si on est mercredi) comme date de présentation.
    """
    if today is None:
        today = date.today()

    # Mercredi de présentation = mercredi le plus proche dans le futur (ou aujourd'hui).
    # weekday() : lundi=0, mardi=1, mercredi=2, ...
    days_to_wednesday = (2 - today.weekday()) % 7
    mercredi = today + timedelta(days=days_to_wednesday)

    # Dimanche W = dimanche précédant le mercredi de présentation
    # mercredi.weekday() == 2 → dimanche est 3 jours avant
    dimanche_w = mercredi - timedelta(days=3)
    lundi_w = dimanche_w - timedelta(days=6)

    iso_year, iso_week, _ = lundi_w.isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"

    def offset_week(weeks: int) -> str:
        d = lundi_w + timedelta(weeks=weeks)
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"

    return WbrDates(
        today=today,
        lundi_w=lundi_w,
        dimanche_w=dimanche_w,
        mercredi_presentation=mercredi,
        week_id=week_id,
        week_id_minus1=offset_week(-1),
        week_id_minus2=offset_week(-2),
        week_id_plus1=offset_week(1),
    )


def ville_upper(name: str) -> str:
    """Capitalisation safe pour la cover (accents conservés)."""
    return name.strip().upper()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Format YYYY-MM-DD
        d = date.fromisoformat(sys.argv[1])
    else:
        d = date.today()
    dates = compute_dates(d)
    print(f"Today               : {dates.today}")
    print(f"Lundi W             : {dates.lundi_w} ({dates.week_id})")
    print(f"Dimanche W          : {dates.dimanche_w}")
    print(f"Mercredi présentation: {dates.mercredi_presentation}")
    print(f"date_mercredi (cover): {dates.date_mercredi}")
    print(f"Comparatives        : {dates.week_id_minus2} | {dates.week_id_minus1} | {dates.week_id}")
    print(f"W+1                 : {dates.week_id_plus1}")
