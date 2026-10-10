"""
bs_converter.py
Converts Gregorian dates (as found in FHIR resources, e.g.
Encounter.period.start) into Bikram Sambat (BS) dates and DHIS2
monthly period codes.

Uses the third-party 'nepali-datetime' library, since BS month
lengths vary year to year (not a fixed offset from Gregorian) and
a vetted library is safer than hand-rolled conversion logic.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

from datetime import datetime
import nepali_datetime


def parse_fhir_datetime(fhir_datetime_str):
    """
    Parse a FHIR dateTime string (e.g. '2026-04-08T09:30:00+05:45')
    into a Python datetime.date object.
    """
    # FHIR dateTime strings can include a timezone offset; we only
    # need the date portion for BS conversion.
    date_part = fhir_datetime_str[:10]  # 'YYYY-MM-DD'
    return datetime.strptime(date_part, "%Y-%m-%d").date()


def gregorian_to_bs(gregorian_date):
    """
    Convert a Python datetime.date (Gregorian/AD) into a BS date.
    Returns a nepali_datetime.date object.
    """
    return nepali_datetime.date.from_datetime_date(gregorian_date)


def fhir_datetime_to_bs_period(fhir_datetime_str):
    """
    Convert a FHIR dateTime string directly into a DHIS2 monthly
    period code in BS, e.g. '2083-03-04' -> '208303'.

    DHIS2 monthly period format: YYYYMM (BS year + BS month, zero-padded)
    """
    gregorian_date = parse_fhir_datetime(fhir_datetime_str)
    bs_date = gregorian_to_bs(gregorian_date)
    period_code = f"{bs_date.year}{bs_date.month:02d}"
    return period_code

def fhir_datetime_to_gregorian_period(fhir_datetime_str):
    """
    Convert a FHIR dateTime string directly into a DHIS2 monthly
    period code in Gregorian/AD, e.g. '2026-04-08' -> '202604'.

    Per DHIS2 community findings (Nepal implementers, Oct 2024):
    the dataValueSets API expects Gregorian periods even when the
    UI displays BS dates. BS conversion (above) remains useful for
    human-readable reports/dashboards, but NOT for API submission.
    """
    gregorian_date = parse_fhir_datetime(fhir_datetime_str)
    period_code = f"{gregorian_date.year}{gregorian_date.month:02d}"
    return period_code
    
if __name__ == "__main__":
    # Quick manual test
    test_dates = [
        "2026-04-08T09:30:00+05:45",  # encounter-anc-001
        "2026-05-27T10:00:00+05:45",  # encounter-anc-002
        "2026-07-08T10:00:00+05:45",  # encounter-anc-003
        "2026-09-16T10:00:00+05:45",  # encounter-anc-004
    ]

    for dt_str in test_dates:
        bs_date = gregorian_to_bs(parse_fhir_datetime(dt_str))
        period = fhir_datetime_to_bs_period(dt_str)
        print(f"{dt_str}  ->  BS: {bs_date}  ->  DHIS2 period: {period}")