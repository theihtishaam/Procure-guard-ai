from __future__ import annotations

from app.models import VendorCase


SAMPLE_CASES: list[VendorCase] = [
    VendorCase(
        case_id="case-vectorcrm",
        requester="Maya Patel",
        department="Revenue Operations",
        vendor_name="VectorCRM",
        product="CRM enrichment and lead routing",
        requested_amount_usd=42000,
        renewal_or_new="new",
        business_need=(
            "Sales wants automated account enrichment, lead prioritization, and routing "
            "to reduce manual research time before a Q3 enterprise pipeline push."
        ),
        data_access=["customer contacts", "opportunity notes", "email metadata"],
        integrations=["Salesforce", "HubSpot", "Slack"],
        timeline="launch before Q3 pipeline review",
        notes="Vendor claims SOC 2 Type II is available under NDA. DPA not yet reviewed.",
    ),
    VendorCase(
        case_id="case-ledgerflow",
        requester="Owen Hughes",
        department="Finance",
        vendor_name="LedgerFlow",
        product="AP invoice automation and approval routing",
        requested_amount_usd=88000,
        renewal_or_new="new",
        business_need=(
            "Finance wants to reduce invoice processing time and enforce purchase-order "
            "matching for a growing vendor base."
        ),
        data_access=["supplier bank details", "invoice PDFs", "purchase orders"],
        integrations=["NetSuite", "Okta", "Google Drive"],
        timeline="pilot this quarter",
        notes="Would handle sensitive payment data and needs segregation-of-duties review.",
    ),
    VendorCase(
        case_id="case-mediclaim",
        requester="Nadia Romero",
        department="Operations",
        vendor_name="MediClaim Assist",
        product="Claims document classification workflow",
        requested_amount_usd=125000,
        renewal_or_new="new",
        business_need=(
            "Operations needs to classify claim packets and route exceptions to reviewers "
            "while preserving auditability for regulated customer files."
        ),
        data_access=["regulated customer files", "medical notes", "claim attachments"],
        integrations=["SFTP", "ServiceNow", "Snowflake"],
        timeline="urgent, executive sponsor requested 30-day review",
        notes="High-stakes workflow. Requires legal, privacy, and human-in-the-loop controls.",
    ),
]


def get_case(case_id: str) -> VendorCase:
    for case in SAMPLE_CASES:
        if case.case_id == case_id:
            return case
    raise KeyError(case_id)
