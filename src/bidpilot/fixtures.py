"""Synthetic, contest-safe RFP and company records."""

COMPANY = {
    "capabilities": ["cloud_migration", "data_engineering", "security_review"],
    "available_hours": 980,
    "loaded_hourly_cost": 82,
    "minimum_margin_rate": 0.22,
    "minimum_lead_days": 8,
}

RFPS = [
    {
        "id": "RFP-ORBIT",
        "title": "Public-sector data platform modernization",
        "contract_value": 210_000,
        "required_hours": 1_050,
        "estimated_delivery_cost": 248_000,
        "required_capabilities": ["cloud_migration", "data_engineering", "public_sector_clearance"],
        "deadline_days": 6,
        "delivery_risk": "high",
        "incumbent_competitor": True,
        "summary": "The largest opportunity fails mandatory qualification, capacity, and margin gates.",
    },
    {
        "id": "RFP-NORTHSTAR",
        "title": "Analytics migration and governance delivery",
        "contract_value": 182_000,
        "required_hours": 840,
        "estimated_delivery_cost": 122_000,
        "required_capabilities": ["cloud_migration", "data_engineering", "security_review"],
        "deadline_days": 12,
        "delivery_risk": "medium",
        "incumbent_competitor": False,
        "summary": "A viable opportunity that becomes the next action after the high-value RFP is rejected.",
    },
]
