from .anthropic_ei import AnthropicEi
from .bls import Bls
from .census_btos import CensusBtos
from .clouded_judgment import CloudedJudgment
from .epoch import Epoch
from .feeds import Feeds
from .fred import Fred
from .manual import Manual
from .metr import Metr
from .openrouter import OpenRouter
from .sec_segments import SecSegments
from .sec_xbrl import SecXbrl

CONNECTORS = {
    c.source_id: c
    for c in (
        Metr,
        SecXbrl,
        Manual,
        Bls,
        Epoch,
        Fred,
        CensusBtos,
        AnthropicEi,
        SecSegments,
        Feeds,
        CloudedJudgment,
        OpenRouter,
    )
}
