import io
import json
import zipfile
from datetime import date, datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.formd import FormD, norm

ISS = (
    "ACCESSIONNUMBER\tIS_PRIMARYISSUER_FLAG\tISSUER_SEQ_KEY\tCIK\tENTITYNAME\n"
    "A1\tYES\t1\t1865393\tBaseten Labs, Inc.\n"
    "A2\tYES\t1\t999\tHII Baseten SPV, a Series of HII LLC\n"
    "A3\tYES\t1\t888\tHarvey AI Corp\n"
    "A4\tYES\t1\t777\tSurgery Center of Wasilla, LLC\n"
    "A5\tYES\t1\t2104151\tFluidstack Ltd\n"
)
OFF = (
    "ACCESSIONNUMBER\tINDUSTRYGROUPTYPE\tISAMENDMENT\tSALE_DATE\tYETTOOCCUR\tISEQUITYTYPE\tISDEBTTYPE\tISPOOLEDINVESTMENTFUNDTYPE\tTOTALOFFERINGAMOUNT\tTOTALAMOUNTSOLD\n"
    "A1\tOther Technology\tfalse\t2026-06-15\tfalse\ttrue\t\tfalse\t1499995892\t1096448855\n"
    "A2\tPooled Investment Fund\tfalse\t2026-06-01\tfalse\ttrue\t\ttrue\tIndefinite\t5000000\n"
    "A3\tOther Technology\tfalse\t2026-03-24\tfalse\ttrue\t\tfalse\tIndefinite\t200009773\n"
    "A4\tCommercial\tfalse\t2026-02-01\tfalse\ttrue\t\tfalse\t1000000\t1000000\n"
    "A5\tOther Technology\tfalse\t2026-01-10\tfalse\t\ttrue\tfalse\t850000000\t842478689\n"
)
SUB = "ACCESSIONNUMBER\tFILING_DATE\nA1\t2026-06-30\nA2\t2026-06-02\nA3\t2026-04-06\nA4\t2026-02-05\nA5\t2026-05-12\n"


def _zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("2026Q2_d/ISSUERS.tsv", ISS)
        z.writestr("2026Q2_d/OFFERING.tsv", OFF)
        z.writestr("2026Q2_d/FORMDSUBMISSION.tsv", SUB)
    return buf.getvalue()


def test_form_d_maps_by_cik_only_and_drops_spvs():
    rows = FormD().extract(
        [
            RawItem(
                "https://www.sec.gov/x/2026q2_d.zip",
                _zip(),
                200,
                datetime(2026, 9, 11, tzinfo=timezone.utc),
                "h",
                None,
            )
        ]
    )
    by = {(r.series_key, r.as_of_date): r for r in rows}
    b = by[("formd.baseten.amount_sold_usd.pt", date(2026, 6, 15))]
    assert (
        b.value_numeric == 1096448855
        and b.published_date == date(2026, 6, 30)
        and b.tier == 4
        and b.entity_id == "baseten"
    )
    assert ("formd.baseten.offering_amount_usd.pt", date(2026, 6, 15)) in by
    assert not any(
        k[0].startswith("formd.harvey") for k in by
    )  # a name match alone never makes a row (CIK 888 is not Harvey's)
    c = FormD().candidates(
        [
            RawItem(
                "https://www.sec.gov/x/2026q2_d.zip",
                _zip(),
                200,
                datetime(2026, 9, 11, tzinfo=timezone.utc),
                "h",
                None,
            )
        ]
    )
    assert [(x["entity"], x["cik"]) for x in c] == [("harvey", "0000000888")]
    assert ("formd.fluidstack.debt_sold_usd.pt", date(2026, 1, 10)) in by  # debt-only offering
    assert not any("surge" in k[0] or "hii" in k[0] for k in by)  # the surgery centre and the SPV never map
    assert json.loads(b.raw_snippet)["accession"] == "A1"
    assert norm("Baseten Labs, Inc.") == norm("Baseten") == "baseten"
