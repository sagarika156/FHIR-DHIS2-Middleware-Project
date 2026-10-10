# FHIR-to-DHIS2 Middleware (Project Phase)

Interoperability middleware for automated Safe Motherhood (ANC/PNC) reporting in Nepal.
It reads maternal health data from a HAPI FHIR R4 server, transforms it into DHIS2
aggregate data values, and submits them to DHIS2.

M.Sc. Health Informatics project, Kathmandu University School of Medical Sciences.

## Status
Project-phase prototype, validated on a 7-patient synthetic cohort against the public
DHIS2 demo server (period 202505): 17 indicators, 11 of 12 submitted values verified.
All data is synthetic. No real patient data is used.

## Architecture
HAPI FHIR R4 + PostgreSQL (Docker) -> Python middleware -> DHIS2 (dataValueSets)

| Module | Role |
|---|---|
| `fhir_client.py` | Reads resources from the FHIR server |
| `transformer.py` | Maps FHIR data to ANC/PNC indicators |
| `aggregator.py` | Aggregates indicator counts |
| `aggregate_payload.py` | Builds the DHIS2 dataValueSets payload |
| `dhis2_payload_preview.py` | Previews the final payload before submission |
| `submit_aggregate.py` | Submits the aggregate payload to DHIS2 |
| `dhis2_client.py` | Communicates with the DHIS2 API |
| `bs_converter.py` | Bikram Sambat / Gregorian date conversion |
| `config.py` | Configuration and UID mappings |

## Setup
1. Start the FHIR server and database: `docker compose up -d`
2. Create the Python environment:
   `cd middleware && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

## Known limitations
- Uses demo-server UIDs, not Nepal's production identifiers.
- Single reporting period and single facility.
- One demo-server UID is shared by two PNC elements, which caused the one unverified value.

## Author
Sagarika Thapa
