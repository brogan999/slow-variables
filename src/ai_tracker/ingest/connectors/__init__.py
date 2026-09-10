from .bls import Bls
from .epoch import Epoch
from .manual import Manual
from .metr import Metr
from .sec_xbrl import SecXbrl

CONNECTORS = {c.source_id: c for c in (Metr, SecXbrl, Manual, Bls, Epoch)}
