"""
config.py
Configuration values for the DHIS2 submission step, including
data element UIDs and their associated category option combos.

TEMPORARY STRUCTURAL TEST CONFIGURATION (as of 20 June 2026):
All UIDs below are REAL, valid DHIS2 identifiers, each individually
verified by the user directly via the DHIS2 demo server's
Maintenance app and/or live data-entry network requests
(https://play.im.dhis2.org/stable-2-43-1/). They do NOT correspond
to Nepal's actual ANC/PNC data elements - they are real but
unrelated/loosely-thematic demo data elements, used purely to test
that the DHIS2 client correctly handles a SUCCESSFUL submission.
This is a structural/mechanical test only, not a submission of
real or meaningful ANC data.

Official Nepal DHIS2 dataElement UIDs are still pending a formal
request (university letter to IHIMS, Management Division, MoHP).
Once received, replace ALL values below. No other code needs to
change when this happens.

Nepal MNCH FHIR-to-DHIS2 Middleware | Sagarika Thapa | KU
"""

# Maps internal element names (from transformer.py) to a tuple of
# (dataElement UID, categoryOptionCombo UID or None).
#
# A combo of None means: omit the categoryOptionCombo field entirely
# for this element, letting DHIS2 apply its own default - used where
# the demo data element has no disaggregation at all (e.g. Calcium).
#
# All verified directly against the live demo server by the user.
DHIS2_DATA_ELEMENT_UIDS = {
    # --- Original 7 ANC elements ---
    "ANC_1ST_ANY": ("fbfJHSPpUQD", "pq2XI5kz2BY"),            # demo: "ANC 1st visit" (Fixed)
    "ANC_1ST_PROTOCOL_12WK": ("cYeuwXTCPkU", "pq2XI5kz2BY"),  # demo: "ANC 2nd visit" (Fixed)
    "ANC_4_VISITS": ("Jtf34kNZhzP", "pq2XI5kz2BY"),           # demo: "ANC 3rd visit" (Fixed)
    "ANC_8_VISITS": ("hfdmMSPBgLG", "pq2XI5kz2BY"),           # demo: "ANC 4th or more visits" (Fixed)
    "IFA_180": ("rbkr8PL0rwM", "pq2XI5kz2BY"),                # demo: "Iron Folate given at ANC 3rd" (Fixed)
    "DEWORMING": ("hCVSHjcml9g", "pq2XI5kz2BY"),              # demo: "Albendazole given at ANC (2nd trimester)" (Fixed)
    "CALCIUM_180": ("PKZPVfAJfHD", None),                     # demo: "WHOMCH Calcium supplements given" (no combo - "None" on demo)

    # --- Td (Tetanus-diphtheria) elements, added 20 June 2026 ---
    # Demo server has "TT" (Tetanus Toxoid) elements, not "Td" -
    # closely related but not an exact vaccine match; used as a
    # thematic stand-in for structural testing only, same as Iron
    # Folate standing in for IFA above. Uses a DIFFERENT combo than
    # the other elements (Pregnant + Fixed, a two-dimensional
    # disaggregation - Pregnant/Non-pregnant x Fixed/Outreach/School)
    # rather than the simple Fixed/Outreach combo used above.
    "TD_1ST_DOSE": ("DUTSJE8MGCw", "dcguXUTwenI"),    # demo: "TT1 doses given" (Pregnant, Fixed)
    "TD_2ND_DOSE": ("zzHwXqxKYy1", "dcguXUTwenI"),    # demo: "TT2 doses given" (Pregnant, Fixed)
    "TD_2PLUS_DOSE": ("jWaNoH0X0Am", "dcguXUTwenI"),  # demo: "TT3 doses given" (Pregnant, Fixed),

   
    # --- PNC elements (added 24 June 2026) ---
    # Demo server only had 3 distinct PNC-related elements; several
    # internal elements below intentionally REUSE the same demo UID,
    # clearly marked, since no closer match existed. PNC_2_HOME_VISITS
    # is excluded entirely - no UID needed, see dhis2_payload_preview.py.
    "PNC_1ST_24HR": ("LhoRsqtRn4r", "pq2XI5kz2BY"),            # demo: "Postnatal 1st contact (within 1 week)"
    "PNC_2ND_DAY3": ("LhoRsqtRn4r", "pq2XI5kz2BY"),            # REUSED - same demo element as above
    "PNC_3RD_7TO14DAY": ("k1vnEuKnRYE", "pq2XI5kz2BY"),        # demo: "Postnatal 2nd contact (at 6 weeks)"
    "PNC_4_CONTACTS": ("k1vnEuKnRYE", "pq2XI5kz2BY"),          # REUSED - same demo element as above
    "PNC_IFA_45DAY": ("btSSE4w61kd", "pq2XI5kz2BY"),           # REUSED - demo: "Vitamin A given at postnatal"
    "PNC_VITAMIN_A": ("btSSE4w61kd", "pq2XI5kz2BY"),           # demo: "Vitamin A given at postnatal"

    # --- Delivery elements (added 20 June 2026, deliberate scope extension) ---
    "DELIVERY_MODE": ("fIy3fOtkbdS", None),                    # demo: "MCH Mode of Delivery" (no combo - "None" on demo)


}

# DHIS2 organisation unit UID for the facility submitting data.
# Verified real org unit from the demo server (Sierra Leone,
# country-level org unit) - confirmed via the data entry app.
DHIS2_ORG_UNIT_UID = "ImspTQPwCqd"