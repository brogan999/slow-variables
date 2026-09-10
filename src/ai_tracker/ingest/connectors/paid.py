"""Stubs for paid sources (P1 §5.4). Each connector refuses to run unless PAID_SOURCES=true and its key is set, and
says exactly which key it needs. Nothing here fetches anything today; the stubs exist so the registry, the sources
page and the nightly summary show the paid tier as a deliberate gap rather than an omission.
"""

from __future__ import annotations

import os
from datetime import date

from ...schema import Observation
from ..base import Connector, RawItem


class _Paid(Connector):
    key_env: str = ""
    optional = True

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        if os.environ.get("PAID_SOURCES", "").lower() != "true":
            raise PermissionError(
                f"{self.source_id}: paid source; set PAID_SOURCES=true and {self.key_env} to enable"
            )
        if not os.environ.get(self.key_env):
            raise PermissionError(f"{self.source_id}: {self.key_env} is not set")
        raise NotImplementedError(
            f"{self.source_id}: paid connector not implemented; budget not approved (docs/plan.md §5)"
        )

    def extract(self, items: list[RawItem]) -> list[Observation]:
        return []


class PitchBook(_Paid):
    source_id, key_env = "pitchbook", "PITCHBOOK_API_KEY"


class Crunchbase(_Paid):
    source_id, key_env = "crunchbase", "CRUNCHBASE_API_KEY"


class SemiAnalysis(_Paid):
    source_id, key_env = "semianalysis", "SEMIANALYSIS_API_KEY"


class TheInformation(_Paid):
    source_id, key_env = "the_information", "THE_INFORMATION_API_KEY"


class Dealroom(_Paid):
    source_id, key_env = "dealroom", "DEALROOM_API_KEY"


class CbInsights(_Paid):
    source_id, key_env = "cb_insights", "CB_INSIGHTS_API_KEY"


class Sacra(_Paid):
    source_id, key_env = "sacra", "SACRA_API_KEY"


class Caplight(_Paid):
    source_id, key_env = "caplight", "CAPLIGHT_API_KEY"


PAID = (PitchBook, Crunchbase, SemiAnalysis, TheInformation, Dealroom, CbInsights, Sacra, Caplight)
