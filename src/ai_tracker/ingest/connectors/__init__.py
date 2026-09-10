from .anthropic_ei import AnthropicEi
from .bls import Bls
from .census_btos import CensusBtos
from .epoch import Epoch
from .fred import Fred
from .manual import Manual
from .metr import Metr
from .sec_xbrl import SecXbrl

CONNECTORS = {c.source_id: c for c in (Metr, SecXbrl, Manual, Bls, Epoch, Fred, CensusBtos, AnthropicEi)}
