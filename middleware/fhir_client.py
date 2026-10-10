"""
fhir_client.py
Connects to the HAPI FHIR server and fetches resources needed
for ANC/PNC data element transformation.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

import requests

FHIR_BASE_URL = "http://localhost:8080/fhir"


def get_all_patients():
    """
    Fetch all Patient resources currently on the FHIR server.
    Returns a list of Patient resource dicts.
    """
    url = f"{FHIR_BASE_URL}/Patient"
    params = {"_count": 100}  # raise above HAPI's default page size
    response = requests.get(url, params=params)
    response.raise_for_status()
    bundle = response.json()
    return _extract_resources(bundle)

def get_patient(patient_id):
    """Fetch a single Patient resource by ID."""
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_encounters_for_patient(patient_id):
    """Fetch all Encounter resources linked to a patient."""
    url = f"{FHIR_BASE_URL}/Encounter"
    params = {"subject": f"Patient/{patient_id}"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    bundle = response.json()
    return _extract_resources(bundle)


def get_observations_for_patient(patient_id):
    """Fetch all Observation resources linked to a patient."""
    url = f"{FHIR_BASE_URL}/Observation"
    params = {"subject": f"Patient/{patient_id}"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    bundle = response.json()
    return _extract_resources(bundle)


def get_medication_dispenses_for_patient(patient_id):
    """Fetch all MedicationDispense resources linked to a patient."""
    url = f"{FHIR_BASE_URL}/MedicationDispense"
    params = {"subject": f"Patient/{patient_id}"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    bundle = response.json()
    return _extract_resources(bundle)


def get_procedures_for_patient(patient_id):
    """Fetch all Procedure resources linked to a patient."""
    url = f"{FHIR_BASE_URL}/Procedure"
    params = {"subject": f"Patient/{patient_id}"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    bundle = response.json()
    return _extract_resources(bundle)

def get_immunizations_for_patient(patient_id):
    """Fetch all Immunization resources linked to a patient."""
    url = f"{FHIR_BASE_URL}/Immunization"
    params = {"patient": f"Patient/{patient_id}"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    bundle = response.json()
    return _extract_resources(bundle)

def get_medication_administrations_for_patient(patient_id):
    """Fetch all MedicationAdministration resources linked to a patient."""
    url = f"{FHIR_BASE_URL}/MedicationAdministration"
    params = {"subject": f"Patient/{patient_id}"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    bundle = response.json()
    return _extract_resources(bundle)

def _extract_resources(bundle):
    """
    Helper: pull out the actual resource objects from a FHIR
    Bundle (searchset) response. Returns an empty list if there
    are no matching resources.
    """
    if bundle.get("total", 0) == 0:
        return []
    return [entry["resource"] for entry in bundle.get("entry", [])]


if __name__ == "__main__":
    # Quick manual test when running this file directly
    patient_id = "patient-pregnant"

    patient = get_patient(patient_id)
    print(f"Patient name: {patient['name'][0]['text']}")

    encounters = get_encounters_for_patient(patient_id)
    print(f"Encounters found: {len(encounters)}")

    observations = get_observations_for_patient(patient_id)
    print(f"Observations found: {len(observations)}")

    dispenses = get_medication_dispenses_for_patient(patient_id)
    print(f"MedicationDispenses found: {len(dispenses)}")

    procedures = get_procedures_for_patient(patient_id)
    print(f"Procedures found: {len(procedures)}")

    immunizations = get_immunizations_for_patient(patient_id)
    print(f"Immunizations found: {len(immunizations)}")

    medication_administrations = get_medication_administrations_for_patient(patient_id)
    print(f"MedicationAdministrations found: {len(medication_administrations)}")