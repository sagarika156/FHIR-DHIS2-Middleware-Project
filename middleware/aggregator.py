"""
aggregator.py
Loops through all patients on the FHIR server, computes their
individual ANC/PNC results using the existing, tested transformer.py
functions, and sums them into facility-level monthly aggregate
counts - the actual output a real DHIS2 submission needs.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

from fhir_client import (
    get_all_patients,
    get_encounters_for_patient,
    get_observations_for_patient,
    get_medication_dispenses_for_patient,
    get_procedures_for_patient,
    get_immunizations_for_patient,
    get_medication_administrations_for_patient,
)
from transformer import transform_anc_elements, transform_pnc_elements


def compute_all_patient_results():
    """
    Runs the full ANC + PNC transformation for every patient on the
    server. Returns a list of dicts, one per patient, each combining
    their ANC results, PNC results, and identifying info.
    """
    patients = get_all_patients()
    all_results = []

    for patient in patients:
        patient_id = patient.get("id")
        name = patient.get("name", [{}])[0].get("text", "Unknown")

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

        combined = {"patient_id": patient_id, "name": name}
        combined.update(anc_results)
        combined.update(pnc_results)
        all_results.append(combined)

    return all_results


def aggregate_facility_totals(all_results):
    """
    Sums individual patient results into facility-level totals for
    each ANC/PNC element, plus a breakdown by age band.

    Returns a dict like:
        {"ANC_4_VISITS": {"total": 2, "UNDER20": 0, "20PLUS": 2}, ...}
    """
    # Element keys to aggregate (everything except identifying/text fields)
    element_keys = [
        "ANC_1ST_ANY", "ANC_1ST_PROTOCOL_12WK", "ANC_4_VISITS", "ANC_8_VISITS",
        "IFA_180", "DEWORMING", "CALCIUM_180",
        "TD_1ST_DOSE", "TD_2ND_DOSE", "TD_2PLUS_DOSE",
        "PNC_1ST_24HR", "PNC_2ND_DAY3", "PNC_3RD_7TO14DAY", "PNC_4_CONTACTS",
        "PNC_2_HOME_VISITS", "PNC_IFA_45DAY", "PNC_VITAMIN_A",
    ]

    totals = {key: {"total": 0, "UNDER20": 0, "20PLUS": 0, "UNKNOWN": 0} for key in element_keys}
    totals["_patient_count"] = len(all_results)

    for patient_result in all_results:
        age_band = patient_result.get("AGE_BAND", "UNKNOWN")
        for key in element_keys:
            value = patient_result.get(key, 0)
            if value == 1:
                totals[key]["total"] += 1
                totals[key][age_band] += 1

    return totals


if __name__ == "__main__":
    print("Fetching and computing results for all patients...\n")
    all_results = compute_all_patient_results()

    print(f"Found {len(all_results)} patients:\n")
    for r in all_results:
        print(f"  {r['name']} (AGE_BAND: {r.get('AGE_BAND', 'UNKNOWN')})")

    print("\nAggregating facility totals...\n")
    totals = aggregate_facility_totals(all_results)

    print(f"Facility Monthly Totals (n={totals['_patient_count']} patients):\n")
    for element, breakdown in totals.items():
        if element == "_patient_count":
            continue
        print(f"  {element}: {breakdown['total']} total  (<20: {breakdown['UNDER20']}, ≥20: {breakdown['20PLUS']})")