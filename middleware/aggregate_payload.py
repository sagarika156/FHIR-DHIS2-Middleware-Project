"""
aggregate_payload.py
Builds a DHIS2 dataValueSets payload from facility-level aggregated
totals (via aggregator.py), submitting one TOTAL count per element
- not split by age band, since the demo server's category option
combos do not support age-band disaggregation (confirmed directly
by checking the Maintenance app). Age-band breakdowns remain
available locally via aggregator.py's output, for future use once
Nepal's real DHIS2 configuration is known.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

import json

from aggregator import compute_all_patient_results, aggregate_facility_totals
from config import DHIS2_DATA_ELEMENT_UIDS, DHIS2_ORG_UNIT_UID


# Fixed reporting period for this test run, matching the cohort's
# shared first-ANC-visit month. In production this would be
# determined dynamically (e.g. "last calendar month").
REPORTING_PERIOD = "202505"


def build_aggregate_dhis2_payload():
    """
    Computes facility-wide totals across all patients and builds a
    DHIS2 dataValueSets payload, one data value per element
    (TOTAL count only, not age-band split).
    """
    all_results = compute_all_patient_results()
    totals = aggregate_facility_totals(all_results)

    # Same exclusions as dhis2_payload_preview.py: CALCIUM_180 belongs
    # to a different dataset on the demo server (E8020 error), and
    # PNC_2_HOME_VISITS has no matching demo UID at all (config.py
    # intentionally omits it).
    EXCLUDED_ELEMENTS = {"CALCIUM_180", "PNC_2_HOME_VISITS"}

    seen_cells = set()
    data_values = []
    for element_name, breakdown in totals.items():
        if element_name == "_patient_count" or element_name in EXCLUDED_ELEMENTS:
            continue

        uid, combo = DHIS2_DATA_ELEMENT_UIDS.get(element_name, ("UNKNOWN_UID", None))
        cell_key = (uid, combo)
        if cell_key in seen_cells:
            continue
        seen_cells.add(cell_key)

        data_value = {
            "dataElement": uid,
            "period": REPORTING_PERIOD,
            "orgUnit": DHIS2_ORG_UNIT_UID,
            "value": str(breakdown["total"]),
        }
        if combo is not None:
            data_value["categoryOptionCombo"] = combo
        data_values.append(data_value)

    payload = {"dataValues": data_values}
    return payload, totals["_patient_count"]


if __name__ == "__main__":
    payload, patient_count = build_aggregate_dhis2_payload()

    print(f"\nFacility Aggregate DHIS2 Payload Preview (n={patient_count} patients, period {REPORTING_PERIOD}):\n")
    print(json.dumps(payload, indent=2))
    print("\n⚠️  NOTE: Using real demo-server UIDs for structural testing only.")
    print("    Values are TOTAL counts only - age-band breakdown is computed")
    print("    locally (see aggregator.py) but not submitted, since the demo")
    print("    server has no age-band category combo to test against.")