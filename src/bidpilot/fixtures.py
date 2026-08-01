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


TENDERS = [
    {
        "id": "G2B-REPLAY-DATA-QUALITY",
        "title": "Public data quality and API continuity service",
        "buyer_objective": "Improve public-data reliability while keeping citizen-facing APIs stable.",
        "promised_outcome": "a measured data-quality improvement and a maintained API operating model",
        "tags": ["public-data", "data-quality", "api-operations"],
        "eligibility_requirements": ["SME confirmation", "Information-system maintenance certificate"],
        "delivery_hours": 720,
        "evaluation_criteria": [
            {"name": "Technical approach", "weight": 40},
            {"name": "Comparable delivery", "weight": 30},
            {"name": "Delivery team", "weight": 20},
            {"name": "Price", "weight": 10},
        ],
    },
    {
        "id": "G2B-REPLAY-ANALYTICS",
        "title": "Municipal analytics governance service",
        "buyer_objective": "Give policy teams governed analytics they can operate after handoff.",
        "promised_outcome": "a governed analytics service with a practical operating handoff",
        "tags": ["analytics", "governance", "public-sector"],
        "eligibility_requirements": ["SME confirmation"],
        "delivery_hours": 520,
        "evaluation_criteria": [
            {"name": "Comparable delivery", "weight": 45},
            {"name": "Team capability", "weight": 25},
            {"name": "Operating handoff", "weight": 20},
            {"name": "Price", "weight": 10},
        ],
    },
]


SUPPLIER_PROFILES = [
    {
        "id": "supplier-northstar",
        "name": "Northstar Systems",
        "credentials": ["SME confirmation", "Information-system maintenance certificate"],
        "available_hours": 900,
        "people": [
            {"name": "Mina Lee", "role": "Public data delivery lead"},
            {"name": "Jun Park", "role": "API operations architect"},
        ],
        "past_projects": [
            {"title": "City Open Data Reliability Program", "tags": ["public-data", "data-quality", "api-operations"], "outcome": "Reduced recurring data defects and introduced API change control."},
            {"title": "Regional Analytics Governance Rollout", "tags": ["analytics", "governance", "public-sector"], "outcome": "Handed governed dashboards to policy teams with an operating playbook."},
            {"title": "Citizen API Service Transition", "tags": ["api-operations", "public-sector"], "outcome": "Transferred API support without a public-service interruption."},
        ],
    },
    {
        "id": "supplier-atlas",
        "name": "Atlas Advisory",
        "credentials": ["SME confirmation"],
        "available_hours": 560,
        "people": [{"name": "Dana Cho", "role": "Analytics strategy lead"}],
        "past_projects": [
            {"title": "Commercial Analytics Modernization", "tags": ["analytics", "governance"], "outcome": "Established a commercial analytics governance model."},
        ],
    },
]
