from .anthropic_ei import AnthropicEi
from .artificial_analysis import ArtificialAnalysis
from .bls import Bls
from .cait import Cait
from .canaries import Canaries, CanariesAge
from .census_btos import CensusBtos
from .epoch import Epoch
from .epoch_tables import (
    EpochBench,
    EpochChips,
    EpochComponents,
    EpochDataCenters,
    EpochHardware,
    EpochModels,
    EpochPrices,
)
from .feeds import Feeds
from .formd import FormD
from .fred import Fred, FredOfficial
from .hal_reliability import HalReliability
from .manual import Manual
from .metr import Metr
from .openrouter import OpenRouter
from .openrouter_rankings import OpenRouterRankings
from .ramp import Ramp
from .regulatory import FdaDevices, Ncsl, Owid, RlList
from .sec_segments import SecSegments
from .sec_xbrl import SecXbrl
from .yale import YaleDissimilarity

CONNECTORS = {
    c.source_id: c
    for c in (
        Metr,
        HalReliability,
        Ramp,
        Canaries,
        CanariesAge,
        Cait,
        YaleDissimilarity,
        OpenRouterRankings,
        ArtificialAnalysis,
        SecXbrl,
        Manual,
        Bls,
        Epoch,
        Fred,
        FredOfficial,
        CensusBtos,
        AnthropicEi,
        SecSegments,
        Feeds,
        OpenRouter,
        FormD,
        EpochModels,
        EpochHardware,
        EpochPrices,
        EpochBench,
        EpochChips,
        EpochComponents,
        EpochDataCenters,
        FdaDevices,
        Ncsl,
        RlList,
        Owid,
    )
}
