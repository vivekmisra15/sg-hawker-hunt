"""
HygieneAgent — fetches NEA hygiene grades and closure status for a list of centres.
Single responsibility: given centre names, return structured HygieneResult per centre.
"""
import logging
from tools.nea_client import NEAClient, NEAClientError
from models.schemas import HygieneResult

logger = logging.getLogger(__name__)

_GRADE_ORDER = {"A": 4, "B": 3, "C": 2, "D": 1, "": 0, "UNKNOWN": 0}


def _best_grade(grades: list[str]) -> str:
    """Return the highest grade from a list."""
    return max(grades, key=lambda g: _GRADE_ORDER.get(g.upper(), 0), default="UNKNOWN")


class HygieneAgent:
    def __init__(self, nea_client: NEAClient | None = None):
        self._nea = nea_client or NEAClient()

    async def run(self, centre_names: list[str]) -> list[HygieneResult]:
        """
        Return one HygieneResult per centre name.
        Degrades gracefully on NEAClientError — returns UNKNOWN grade.
        """
        try:
            all_grades = await self._nea.get_hygiene_grades()
        except NEAClientError as e:
            logger.warning("NEA hygiene fetch failed: %s", e)
            all_grades = {}

        try:
            closed_centres = await self._nea.get_closure_dates()
            closed_upper = {c.upper() for c in closed_centres}
        except NEAClientError as e:
            logger.warning("NEA closure fetch failed: %s", e)
            closed_upper = set()

        results: list[HygieneResult] = []
        for centre_name in centre_names:
            centre_upper = centre_name.upper()
            is_closed = any(centre_upper in c or c in centre_upper for c in closed_upper)

            # Find all stall grades whose centre_name matches
            matching = [
                r for r in all_grades.values()
                if r.centre_name.upper() == centre_upper
                or centre_upper in r.centre_name.upper()
                or r.centre_name.upper() in centre_upper
            ]

            static_stalls: list[HygieneResult] = []

            if matching:
                grade = _best_grade([r.grade for r in matching])
                demerit = min(r.demerit_points for r in matching)
                suspended = any(r.suspended for r in matching)
                stall_name = matching[0].stall_name
                data_source = "live"
            else:
                # Live API had no match — try static grades from sfa_scraper output
                static_stalls = self._nea.get_static_hygiene_for_centre(centre_name)
                if static_stalls:
                    grade = _best_grade([r.grade for r in static_stalls])
                    demerit = min(r.demerit_points for r in static_stalls)
                    suspended = any(r.suspended for r in static_stalls)
                    stall_name = static_stalls[0].stall_name
                    data_source = "static"
                else:
                    grade = "UNKNOWN"
                    demerit = 0
                    suspended = False
                    stall_name = centre_name
                    data_source = "none"

            # Build enhanced reasoning trace
            # Reuse static_stalls from above — no second fetch needed
            if data_source == "static":
                total = len(static_stalls)
                grade_a_count = sum(1 for s in static_stalls if s.grade == "A")
                grade_summary = f"{grade_a_count}/{total} stalls Grade A" if total > 0 else f"Grade {grade}"
                parts = [f"{centre_name}: {grade_summary} (SFA data)"]
            else:
                parts = [f"{centre_name}: Grade {grade}, {demerit} demerit points"]
            if suspended:
                parts.append("⚠️ suspension on record")
            if is_closed:
                parts.append("🔒 closed for cleaning today")
            else:
                parts.append("open today")
            trace = ", ".join(parts) + "."

            results.append(
                HygieneResult(
                    stall_name=stall_name,
                    centre_name=centre_name,
                    grade=grade,
                    demerit_points=demerit,
                    suspended=suspended,
                    is_closed_today=is_closed,
                    reasoning_trace=trace,
                )
            )
        return results
