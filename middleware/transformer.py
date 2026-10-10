"""
transformer.py
Applies Nepal MNCH mapping rules (Spec v4.0, Section 6) to FHIR
resources, computing the 7 ANC data element values.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

from datetime import datetime

def calculate_age_at_date(patient, reference_date):
    """
    Calculate a patient's age in completed years as of a given
    reference date (e.g. their first ANC visit), using
    Patient.birthDate. Returns None if birthDate is missing.
    """
    birth_date_str = patient.get("birthDate")
    if not birth_date_str:
        return None

    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    ref_date = reference_date.date() if isinstance(reference_date, datetime) else reference_date

    age = ref_date.year - birth_date.year
    # Subtract 1 if the birthday hasn't occurred yet this year
    if (ref_date.month, ref_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def age_band(age):
    """Classify an age into Nepal HMIS's standard <20 / >=20 bands."""
    if age is None:
        return "UNKNOWN"
    return "UNDER20" if age < 20 else "20PLUS"


def get_observation_value(observations, loinc_code):
    """
    Find an Observation by LOINC code and return its numeric value.
    Returns None if not found.
    """
    for obs in observations:
        codings = obs.get("code", {}).get("coding", [])
        for coding in codings:
            if coding.get("code") == loinc_code:
                return obs.get("valueQuantity", {}).get("value")
    return None


def get_gestational_age_for_encounter(observations, encounter_id):
    """
    Find the gestational age Observation (LOINC 11884-4) that is
    linked to a specific Encounter.
    """
    for obs in observations:
        codings = obs.get("code", {}).get("coding", [])
        is_gest_age = any(c.get("code") == "11884-4" for c in codings)
        if not is_gest_age:
            continue

        encounter_ref = obs.get("encounter", {}).get("reference", "")
        # Use endswith() to guard against absolute vs relative reference
        # strings (e.g. a full URI vs "Encounter/{id}").
        if encounter_ref.endswith(f"Encounter/{encounter_id}"):
            return obs.get("valueQuantity", {}).get("value")
    return None

def sort_encounters_by_date(encounters):
    """Sort ANC encounters chronologically by period.start."""
    def get_start(enc):
        start_str = enc.get("period", {}).get("start", "")
        if not start_str:
            return datetime.min
        # Normalize trailing 'Z' (UTC shorthand) to an explicit offset,
        # since fromisoformat() doesn't accept bare 'Z' in all versions.
        if start_str.endswith("Z"):
            start_str = start_str.replace("Z", "+00:00")
        return datetime.fromisoformat(start_str)

    return sorted(encounters, key=get_start)

def sort_immunizations_by_date(immunizations):
    """Sort Td Immunization records chronologically by occurrenceDateTime."""
    def get_occurrence(imm):
        occurrence_str = imm.get("occurrenceDateTime", "")
        if not occurrence_str:
            return datetime.min
        if occurrence_str.endswith("Z"):
            occurrence_str = occurrence_str.replace("Z", "+00:00")
        return datetime.fromisoformat(occurrence_str)
    return sorted(immunizations, key=get_occurrence)

def has_snomed_code(resource, code, field_path="medicationCodeableConcept"):
    """
    Check if a resource (MedicationDispense or Procedure) contains
    a specific SNOMED code, in either medicationCodeableConcept
    (MedicationDispense) or code (Procedure).
    """
    concept = resource.get(field_path, resource.get("code", {}))
    codings = concept.get("coding", [])
    return any(c.get("code") == code for c in codings)


def transform_anc_elements(patient, encounters, observations, dispenses, procedures, immunizations):
    """
    Computes all 7 ANC data elements (Mapping Spec v4.0, Section 6)
    for a single patient. Returns a dictionary of results.
    """
    results = {
        "ANC_1ST_ANY": 0,
        "ANC_1ST_PROTOCOL_12WK": 0,
        "ANC_4_VISITS": 0,
        "ANC_8_VISITS": 0,
        "IFA_180": 0,
        "DEWORMING": 0,
        "CALCIUM_180": 0,
        "TD_1ST_DOSE": 0,
        "TD_2ND_DOSE": 0,
        "TD_2PLUS_DOSE": 0,
    }

    sorted_encounters = sort_encounters_by_date(encounters)
    anc_visit_count = len(sorted_encounters)

    # Determine age band at first ANC visit, for HMIS-standard
    # <20 / >=20 disaggregation, used by the aggregation layer.
    if sorted_encounters:
        first_visit_date = sort_encounters_by_date(encounters)[0].get("period", {}).get("start", "")
        if first_visit_date:
            if first_visit_date.endswith("Z"):
                first_visit_date = first_visit_date.replace("Z", "+00:00")
            first_visit_datetime = datetime.fromisoformat(first_visit_date)
            age_at_first_visit = calculate_age_at_date(patient, first_visit_datetime)
            results["AGE_BAND"] = age_band(age_at_first_visit)
        else:
            results["AGE_BAND"] = "UNKNOWN"
    else:
        results["AGE_BAND"] = "UNKNOWN"

    # --- Element #1: ANC 1st visit, any time ---
    if anc_visit_count >= 1:
        results["ANC_1ST_ANY"] = 1

        # --- Element #2: ANC 1st visit <= 12 weeks ---
        first_encounter = sorted_encounters[0]
        first_gest_age = get_gestational_age_for_encounter(
            observations, first_encounter["id"]
        )
        if first_gest_age is not None and first_gest_age <= 12:
            results["ANC_1ST_PROTOCOL_12WK"] = 1

    # --- Element #3: ANC 4 visits ---
    if anc_visit_count >= 4:
        results["ANC_4_VISITS"] = 1

    # --- Element #4: ANC 8 visits ---
    if anc_visit_count >= 8:
        results["ANC_8_VISITS"] = 1

    # --- Element #5 & #7: IFA and Calcium (MedicationDispense) ---
    # Sum quantities across ALL matching dispenses, since IFA/Calcium
    # may be dispensed in smaller batches across multiple visits
    # rather than all 180 tablets in a single record.
    total_ifa = sum(
        d.get("quantity", {}).get("value", 0)
        for d in dispenses
        if has_snomed_code(d, "438641000124100")
    )
    if total_ifa >= 180:
        results["IFA_180"] = 1

    total_calcium = sum(
        d.get("quantity", {}).get("value", 0)
        for d in dispenses
        if has_snomed_code(d, "5540006")
    )
    if total_calcium >= 180:
        results["CALCIUM_180"] = 1

    # --- Element #6: Deworming (MedicationDispense - Albendazole) ---
    # Corrected from Procedure to MedicationDispense after checking
    # against the official Nepal IG example instance
    # (medication-dispense-albendazole), which confirmed Albendazole
    # is dispensed, not administered as a procedure. Uses the
    # specific drug product SNOMED code (Albendazole 400mg tablet),
    # not the generic substance code.
    for disp in dispenses:
        is_deworming = has_snomed_code(disp, "1193657004")
        if is_deworming:
            results["DEWORMING"] = 1
    
    # --- Element #8: Immunization: Td1 / Td2 / Td2+ doses (per HMIS 3.6 register: 3 separate
    # rows, distinguished purely by chronological order of dose) ---
    sorted_immunizations = sort_immunizations_by_date(immunizations)
    td_dose_count = len(sorted_immunizations)

    if td_dose_count >= 1:
        results["TD_1ST_DOSE"] = 1
    if td_dose_count >= 2:
        results["TD_2ND_DOSE"] = 1
    if td_dose_count >= 3:
        results["TD_2PLUS_DOSE"] = 1

    return results

def get_delivery_datetime(procedures):
    """
    Find the delivery Procedure (SNOMED 22633006 or related delivery
    codes) and return its performedDateTime as a datetime object.
    Returns None if no delivery procedure is found.
    """
    delivery_codes = {"22633006", "11466000", "177184002", "236973005"}
    for proc in procedures:
        codings = proc.get("code", {}).get("coding", [])
        is_delivery = any(c.get("code") in delivery_codes for c in codings)
        if not is_delivery:
            continue

        performed_str = proc.get("performedDateTime", "")
        if not performed_str:
            continue
        if performed_str.endswith("Z"):
            performed_str = performed_str.replace("Z", "+00:00")
        return datetime.fromisoformat(performed_str)
    return None


def days_since_delivery(encounter, delivery_datetime):
    """
    Calculate how many calendar days after delivery a given Encounter
    occurred, comparing dates only (not exact times), since HMIS
    paper registers record dates, not precise timestamps - a "day 3"
    visit in the morning should count as day 3, even if delivery
    happened later the same evening 3 days prior.

    Returns None if the encounter has no valid start date or if
    delivery_datetime is None.
    """
    if delivery_datetime is None:
        return None

    start_str = encounter.get("period", {}).get("start", "")
    if not start_str:
        return None
    if start_str.endswith("Z"):
        start_str = start_str.replace("Z", "+00:00")

    encounter_datetime = datetime.fromisoformat(start_str)
    delta = encounter_datetime.date() - delivery_datetime.date()
    return delta.days

def transform_pnc_elements(patient, encounters, dispenses, medication_administrations, procedures):
    """
    Computes all 7 PNC data elements (per HMIS 9.3 / 3.5 / 3.6)
    for a single patient. Returns a dictionary of results.
    """
    results = {
        "PNC_1ST_24HR": 0,
        "PNC_2ND_DAY3": 0,
        "PNC_3RD_7TO14DAY": 0,
        "PNC_4_CONTACTS": 0,
        "PNC_2_HOME_VISITS": 0,
        "PNC_IFA_45DAY": 0,
        "PNC_VITAMIN_A": 0,
    }

    delivery_datetime = get_delivery_datetime(procedures)
    if delivery_datetime is None:
        # No delivery recorded - PNC elements cannot be computed
        return results

    # Identify which encounters are PNC contacts (linked to delivery
    # via diagnosis.condition) and calculate days-since-delivery for each
    # Find the actual delivery Procedure's own ID dynamically (not
    # hardcoded), so this works correctly for any patient, not just
    # the one whose delivery happened to be named "procedure-delivery-001".
    delivery_codes = {"22633006", "11466000", "177184002", "236973005"}
    delivery_procedure_id = None
    for proc in procedures:
        codings = proc.get("code", {}).get("coding", [])
        if any(c.get("code") in delivery_codes for c in codings):
            delivery_procedure_id = proc.get("id")
            break

    pnc_encounters = []
    for enc in encounters:
        diagnoses = enc.get("diagnosis", [])
        is_pnc = any(
            d.get("condition", {}).get("reference", "").endswith(
                f"Procedure/{delivery_procedure_id}"
            )
            for d in diagnoses
        ) if delivery_procedure_id else False
        if is_pnc:
            days = days_since_delivery(enc, delivery_datetime)
            pnc_encounters.append((enc, days))

    pnc_contact_count = len(pnc_encounters)

    # --- Elements #1-3: specific contact windows ---
    for enc, days in pnc_encounters:
        if days is None:
            continue
        if 0 <= days <= 1:
            results["PNC_1ST_24HR"] = 1
        if days == 3:
            results["PNC_2ND_DAY3"] = 1
        if 7 <= days <= 14:
            results["PNC_3RD_7TO14DAY"] = 1

    # --- Element #4: 4 contacts as per full protocol ---
    if pnc_contact_count >= 4:
        results["PNC_4_CONTACTS"] = 1

    # --- Element #5: 2 home visits (2nd and 3rd contacts at home) ---
    home_visit_count = 0
    for enc, days in pnc_encounters:
        is_home = enc.get("class", {}).get("code") != "AMB"
        if is_home and days is not None and 3 <= days <= 14:
            home_visit_count += 1
    if home_visit_count >= 2:
        results["PNC_2_HOME_VISITS"] = 1

    # --- Element #6: 45-day IFA supply postpartum ---
    total_pnc_ifa = sum(
        d.get("quantity", {}).get("value", 0)
        for d in dispenses
        if has_snomed_code(d, "438641000124100")
        and d.get("whenHandedOver", "") >= delivery_datetime.isoformat()
    )
    if total_pnc_ifa >= 45:
        results["PNC_IFA_45DAY"] = 1

    # --- Element #7: Vitamin A given postpartum ---
    for admin in medication_administrations:
        if has_snomed_code(admin, "438501000124103"):
            results["PNC_VITAMIN_A"] = 1

    return results

def transform_delivery_elements(procedures):
    """
    Computes 2 new Delivery-related elements: mode of delivery
    (text classification) and institutional delivery status
    (facility vs home), both read directly from the delivery
    Procedure resource already used to anchor PNC timing.

    Added as a deliberate, bounded scope extension (19-20 June
    2026 sessions), grounded in HMIS 9.3 Section 7's facility/home
    delivery tracking, separate from the original 14 ANC/PNC
    elements.
    """
    results = {
        "DELIVERY_MODE": None,
        "INSTITUTIONAL_DELIVERY": 0,
    }

    delivery_codes = {"22633006", "11466000", "177184002", "236973005"}
    for proc in procedures:
        codings = proc.get("code", {}).get("coding", [])
        is_delivery = any(c.get("code") in delivery_codes for c in codings)
        if not is_delivery:
            continue

        # Mode of delivery - just record the SNOMED display text
        # for now, since DHIS2 demo element has no value-set
        # disaggregation to map against.
        if codings:
            results["DELIVERY_MODE"] = codings[0].get("display", "Unknown")

        # Institutional delivery - if Procedure.location is present
        # (vs absent for a home delivery), count as institutional.
        if proc.get("location"):
            results["INSTITUTIONAL_DELIVERY"] = 1

        break  # only one delivery expected per patient

    return results

if __name__ == "__main__":
    # Quick manual test using fhir_client.py
    from fhir_client import (
        get_patient,
        get_encounters_for_patient,
        get_observations_for_patient,
        get_medication_dispenses_for_patient,
        get_procedures_for_patient,
        get_immunizations_for_patient,
        get_medication_administrations_for_patient,
    )

    patient_id = "patient-pregnant"

    patient = get_patient(patient_id)
    encounters = get_encounters_for_patient(patient_id)
    observations = get_observations_for_patient(patient_id)
    dispenses = get_medication_dispenses_for_patient(patient_id)
    procedures = get_procedures_for_patient(patient_id)
    immunizations = get_immunizations_for_patient(patient_id)

    results = transform_anc_elements(
        patient, encounters, observations, dispenses, procedures, immunizations
    )

    print(f"\nANC Data Element Results for {patient['name'][0]['text']}:\n")
    for element, value in results.items():
        print(f"  {element}: {value}")
    
    medication_administrations = get_medication_administrations_for_patient(patient_id)

    pnc_results = transform_pnc_elements(
        patient, encounters, dispenses, medication_administrations, procedures
    )

    print(f"\nPNC Data Element Results for {patient['name'][0]['text']}:\n")
    for element, value in pnc_results.items():
        print(f"  {element}: {value}")