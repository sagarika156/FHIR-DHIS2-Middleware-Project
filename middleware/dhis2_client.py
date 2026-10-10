"""
dhis2_client.py
Sends computed ANC data values to a DHIS2 instance via the
dataValueSets API. Currently configured against the DHIS2 public
demo/play server for testing purposes - NOT Nepal's real instance.

IMPORTANT: the DHIS2 demo server resets its data every night
(per official DHIS2 documentation). This module is for proving the
client logic works end-to-end, not for storing real or permanent
data. Swap DHIS2_BASE_URL, DHIS2_USERNAME, DHIS2_PASSWORD, and the
UIDs in config.py once real Nepal DHIS2 credentials are available.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

import requests

# DHIS2 demo/play server - FOR TESTING ONLY, resets nightly.
DHIS2_BASE_URL = "https://play.im.dhis2.org/stable-2-43-1/api"
DHIS2_USERNAME = "admin"
DHIS2_PASSWORD = "district"


def post_data_values(payload):
    """
    POST a dataValueSets-style payload to DHIS2.

    payload: a dict shaped like {"dataValues": [...]},
             e.g. the output of dhis2_payload_preview.build_dhis2_payload()

    Returns the parsed JSON response from DHIS2, which includes an
    import summary (counts of imported/updated/ignored values, and
    any conflicts/errors per data value).
    """
    url = f"{DHIS2_BASE_URL}/dataValueSets"
    response = requests.post(
        url,
        json=payload,
        auth=(DHIS2_USERNAME, DHIS2_PASSWORD),
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return response.json()


def get_data_value(data_element_uid, period, org_unit_uid):
    """
    Fetch a single previously-submitted data value back from DHIS2,
    to verify a submission actually persisted correctly.
    """
    url = f"{DHIS2_BASE_URL}/dataValueSets"
    params = {
        "dataElement": data_element_uid,
        "period": period,
        "orgUnit": org_unit_uid,
    }
    response = requests.get(
        url,
        params=params,
        auth=(DHIS2_USERNAME, DHIS2_PASSWORD),
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Quick manual test: submit Hiramaya's computed ANC payload
    # to the DHIS2 demo server and print the import summary.
    import json
    from dhis2_payload_preview import build_dhis2_payload

    patient_id = "patient-pregnant"
    payload, patient = build_dhis2_payload(patient_id)

    print(f"Submitting payload for {patient['name'][0]['text']}...")
    print(f"Note: using PLACEHOLDER UIDs - rejection is expected.\n")

    try:
        result = post_data_values(payload)
        print("DHIS2 Response Summary:")
        print(json.dumps(result, indent=2))
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error occurred: {e}")
        try:
            print("DHIS2 Error Details:")
            print(json.dumps(e.response.json(), indent=2))
        except Exception:
            print(e.response.text)