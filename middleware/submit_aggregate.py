"""
submit_aggregate.py
Submits the facility-level aggregate DHIS2 payload (built by
aggregate_payload.py) to the DHIS2 demo server, reusing the same
authenticated POST logic already proven in dhis2_client.py.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

import json

from aggregate_payload import build_aggregate_dhis2_payload
from dhis2_client import post_data_values

if __name__ == "__main__":
    payload, patient_count = build_aggregate_dhis2_payload()

    print(f"Submitting facility aggregate payload (n={patient_count} patients)...\n")

    try:
        result = post_data_values(payload)
        print("DHIS2 Response Summary:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        try:
            print("DHIS2 Error Details:")
            print(json.dumps(e.response.json(), indent=2))
        except Exception:
            pass