"""
dhis2_payload_preview.py
Combines fhir_client + transformer + bs_converter to preview what
the final DHIS2 dataValueSets payload will look like, BEFORE
actually submitting anything to DHIS2.

Uses verified demo-server UIDs from config.py for structural
testing. NOT Nepal's actual production identifiers - see config.py
for details.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

import json

from fhir_client import (
    get_patient,
    get_encounters_for_patient,
    get_observations_for_patient,
    get_medication_dispenses_for_patient,
    get_procedures_for_patient,
    get_immunizations_for_patient,
     get_medication_administrations_for_patient,
)
from transformer import transform_anc_elements, transform_pnc_elements, transform_delivery_elements, sort_encounters_by_date
from bs_converter import fhir_datetime_to_bs_period, fhir_datetime_to_gregorian_period
from config import DHIS2_DATA_ELEMENT_UIDS, DHIS2_ORG_UNIT_UID


def build_dhis2_payload(patient_id):
    """
    Fetches a patient's FHIR data, computes ANC element values,
    determines the reporting period (Gregorian) from their first
    ANC encounter, and assembles a DHIS2 dataValueSets-style
    payload.
    """
    patient = get_patient(patient_id)
    encounters = get_encounters_for_patient(patient_id)
    observations = get_observations_for_patient(patient_id)
    dispenses = get_medication_dispenses_for_patient(patient_id)
    procedures = get_procedures_for_patient(patient_id)
    immunizations = get_immunizations_for_patient(patient_id)
    medication_administrations = get_medication_administrations_for_patient(patient_id)

    anc_results = transform_anc_elements(
        patient, encounters, observations, dispenses, procedures, immunizations
    )
    pnc_results = transform_pnc_elements(
        patient, encounters, dispenses, medication_administrations, procedures
    )
    delivery_results = transform_delivery_elements(procedures)

    # Exclude PNC_2_HOME_VISITS (no demo UID available - value is 0
    # for Hiramaya anyway, so omitting it doesn't lose a meaningful
    # test case) and INSTITUTIONAL_DELIVERY (deliberately not
    # submitted to DHIS2 this round - see lab notes).
    pnc_results_for_dhis2 = {
        k: v for k, v in pnc_results.items() if k != "PNC_2_HOME_VISITS"
    }
    
    # DELIVERY_MODE excluded too: the demo server's matching element
    # (MCH Mode of Delivery) is a Tracker-type data element, not
    # Aggregate, and triggers the same E8020 dataset-mismatch error
    # as Calcium did earlier. Tracker elements use a fundamentally
    # different DHIS2 data model (per-patient program enrollment)
    # than the Aggregate monthly-count elements used everywhere else
    # in this payload, so they cannot be mixed in one dataValueSets
    # submission. Both Delivery-related elements remain computed
    # locally (see transform_delivery_elements) but are not submitted
    # to DHIS2 in this structural test.
    delivery_results_for_dhis2 = {}

    results = {**anc_results, **pnc_results_for_dhis2, **delivery_results_for_dhis2}

    # TEMPORARY TEST-ONLY EXCLUSION: the demo server's Calcium data
    # element (PKZPVfAJfHD) belongs to a different dataset than the
    # other elements, causing DHIS2 error E8020 ("Data set ... not
    # usable with data element"). This is a demo-database
    # organisation quirk specific to the Sierra Leone sandbox, not
    # a real concern for Nepal's actual DHIS2 instance. Excluded
    # here only to complete a successful structural happy-path test.
    results = {k: v for k, v in results.items() if k != "CALCIUM_180"}

    # Use the first ANC encounter's date to determine reporting period
    sorted_encounters = sort_encounters_by_date(encounters)
    first_encounter_date = sorted_encounters[0]["period"]["start"]
    period = fhir_datetime_to_gregorian_period(first_encounter_date)

    # Some internal elements intentionally reuse the same demo-server
    # UID (no closer match was available - see config.py comments).
    # DHIS2's dataValueSets API treats one dataElement+period+orgUnit
    # +categoryOptionCombo combination as a single cell, so submitting
    # the same UID twice in one payload would just overwrite itself,
    # not test two distinct values. Deduplicate here, keeping the
    # FIRST value seen for each unique UID+combo pair.
    seen_cells = set()
    data_values = []
    for element_name, value in results.items():
        uid, combo = DHIS2_DATA_ELEMENT_UIDS.get(element_name, ("UNKNOWN_UID", None))
        cell_key = (uid, combo)
        if cell_key in seen_cells:
            continue
        seen_cells.add(cell_key)

        data_value = {
            "dataElement": uid,
            "period": period,
            "orgUnit": DHIS2_ORG_UNIT_UID,
            "value": str(value),
        }
        if combo is not None:
            data_value["categoryOptionCombo"] = combo
        data_values.append(data_value)

    payload = {"dataValues": data_values}
    return payload, patient


if __name__ == "__main__":
    patient_id = "patient-pregnant"
    payload, patient = build_dhis2_payload(patient_id)

    print(f"\nDHIS2 Payload Preview for {patient['name'][0]['text']}:\n")
    print(json.dumps(payload, indent=2))
    print("\n⚠️  NOTE: dataElement/orgUnit/categoryOptionCombo values above are")
    print("    REAL DHIS2 demo-server UIDs used for structural testing only,")
    print("    NOT Nepal's actual production values. Replace in config.py")
    print("    once real UIDs are received from IHIMS.")