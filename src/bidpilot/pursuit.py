"""Tender-to-Bid-Room decisions independent of the UI and storage backend."""

from __future__ import annotations

from dataclasses import dataclass, replace

from bidpilot.policy import pursue_status


class PursuitInputError(ValueError):
    """Raised when a tender or supplier cannot enter the pursuit policy."""


@dataclass(frozen=True)
class ProofCard:
    label: str
    kind: str
    detail: str


@dataclass(frozen=True)
class WinPosition:
    title: str
    statement: str
    target_criteria: tuple[str, ...]
    proof_cards: tuple[ProofCard, ...]
    weakness: str | None
    mitigation: str | None


@dataclass(frozen=True)
class BlueprintSection:
    criterion: str
    weight: int
    claim: str
    assets: tuple[str, ...]
    owner: str


@dataclass(frozen=True)
class PursuitBrief:
    opportunity_id: str
    supplier_profile_id: str
    status: str
    buyer_objective: str
    missing_eligibility: tuple[str, ...]
    capacity_gap_hours: int
    score_map: tuple[dict, ...]
    win_positions: tuple[WinPosition, ...]
    proposal_blueprint: tuple[BlueprintSection, ...]
    next_actions: tuple[str, ...]
    selected_position_index: int = 0

    @property
    def can_generate_proposal(self) -> bool:
        return self.status == "PURSUE"


def _matches(tender: dict, supplier: dict) -> list[dict]:
    tender_tags = set(tender["tags"])
    return [
        project
        for project in supplier["past_projects"]
        if tender_tags.intersection(project["tags"])
    ]


def _proof_cards(supplier: dict, projects: list[dict]) -> tuple[ProofCard, ...]:
    cards: list[ProofCard] = [
        ProofCard(project["title"], "Past project", project["outcome"])
        for project in projects[:2]
    ]
    cards.extend(
        ProofCard(credential, "Credential", "Available in the selected supplier profile")
        for credential in supplier["credentials"][: 3 - len(cards)]
    )
    cards.extend(
        ProofCard(person["name"], "Delivery lead", person["role"])
        for person in supplier["people"][: 3 - len(cards)]
    )
    return tuple(cards[:3])


def _position(title: str, tender: dict, supplier: dict, projects: list[dict], criteria: list[dict]) -> WinPosition:
    ranked_projects = list(projects)
    if title == "Operational continuity":
        ranked_projects.sort(key=lambda item: "api-operations" in item.get("tags", ()), reverse=True)
    proof_cards = _proof_cards(supplier, ranked_projects)
    target = tuple(criterion["name"] for criterion in criteria[:2])
    proof_names = ", ".join(card.label for card in proof_cards[:2]) or "the selected delivery team"
    statement = (
        f"Win {title.lower()} with {proof_names}: {supplier['name']} will deliver "
        f"{tender['promised_outcome'].lower()}."
    )
    weakness = None
    mitigation = None
    if len(projects) < 2:
        weakness = "Limited directly comparable delivery history"
        mitigation = "Confirm an additional reference and assign an executive delivery reviewer before pursuing."
    return WinPosition(title, statement, target, proof_cards, weakness, mitigation)


def _blueprint(tender: dict, supplier: dict, position: WinPosition, projects: list[dict]) -> tuple[BlueprintSection, ...]:
    sections: list[BlueprintSection] = []
    continuity = position.title == "Operational continuity"
    strategy_method = (
        "a phased transition, service checkpoints, and an explicit rollback owner"
        if continuity
        else "recorded delivery outcomes, criterion-level acceptance checks, and traceable evidence owners"
    )
    for criterion in sorted(tender["evaluation_criteria"], key=lambda item: item["weight"], reverse=True):
        name = criterion["name"].lower()
        if "team" in name:
            asset_names = tuple(person["name"] for person in supplier["people"]) or tuple(supplier["credentials"])
            evidence = f"the named {supplier['people'][0]['role']}" if supplier["people"] else "the credentialed delivery team"
        elif "price" in name or "commercial" in name:
            asset_names = (f"{supplier['available_hours']} available hours",)
            evidence = f"a delivery envelope backed by {supplier['available_hours']} available hours"
        elif "delivery" in name or "experience" in name:
            asset_names = tuple(project["title"] for project in projects) or tuple(card.label for card in position.proof_cards)
            evidence = f"{len(projects)} comparable delivery record(s)"
        else:
            asset_names = tuple(project["title"] for project in projects[:2]) or tuple(card.label for card in position.proof_cards)
            outcomes = [project["outcome"] for project in projects[:2]]
            evidence = outcomes[0] if outcomes else tender["promised_outcome"]
        claim = (
            f"{position.title}: {supplier['name']} will address {name} through {strategy_method}, backed by {evidence}. "
            f"This {criterion['weight']}-point response targets {tender['promised_outcome'].lower()}."
        )
        owner = ("Operations lead" if continuity else "Solution lead") if criterion["weight"] >= 30 else "Bid manager"
        sections.append(BlueprintSection(criterion["name"], criterion["weight"], claim, asset_names, owner))
    return tuple(sections)


def _is_record_list(value: object) -> bool:
    return isinstance(value, (list, tuple)) and all(isinstance(item, dict) for item in value)


def _is_text_list(value: object) -> bool:
    return isinstance(value, (list, tuple)) and all(isinstance(item, str) and item.strip() for item in value)


def _validate_pursuit_inputs(tender: dict, supplier: dict) -> None:
    """Fail with one stable domain error before policy code reads nested input."""
    if not _is_text_list(tender["tags"]):
        raise PursuitInputError("tender.tags must be a non-empty list of scope labels.")
    if not _is_text_list(tender["eligibility_requirements"]):
        raise PursuitInputError("tender.eligibility_requirements must be a list of requirement labels.")
    if not isinstance(tender["delivery_hours"], int) or isinstance(tender["delivery_hours"], bool):
        raise PursuitInputError("tender.delivery_hours must be a positive integer.")
    if tender["delivery_hours"] <= 0:
        raise PursuitInputError("tender.delivery_hours must be a positive integer.")
    if not _is_record_list(tender["evaluation_criteria"]):
        raise PursuitInputError("tender.evaluation_criteria must be a list of score-map rows.")

    if not _is_text_list(supplier["credentials"]):
        raise PursuitInputError("supplier.credentials must be a list of credential labels.")
    if not isinstance(supplier["available_hours"], int) or isinstance(supplier["available_hours"], bool):
        raise PursuitInputError("supplier.available_hours must be a non-negative integer.")
    if supplier["available_hours"] < 0:
        raise PursuitInputError("supplier.available_hours must be a non-negative integer.")
    if not _is_record_list(supplier["past_projects"]):
        raise PursuitInputError("supplier.past_projects must be a list of project records.")
    for project in supplier["past_projects"]:
        if not isinstance(project.get("title"), str) or not project["title"].strip():
            raise PursuitInputError("supplier.past_projects requires a title for every project.")
        if not _is_text_list(project.get("tags")):
            raise PursuitInputError("supplier.past_projects requires scope tags for every project.")
        if not isinstance(project.get("outcome"), str) or not project["outcome"].strip():
            raise PursuitInputError("supplier.past_projects requires an outcome for every project.")
    if not _is_record_list(supplier["people"]):
        raise PursuitInputError("supplier.people must be a list of delivery-team records.")
    for person in supplier["people"]:
        if not isinstance(person.get("name"), str) or not person["name"].strip():
            raise PursuitInputError("supplier.people requires a name for every person.")
        if not isinstance(person.get("role"), str) or not person["role"].strip():
            raise PursuitInputError("supplier.people requires a role for every person.")


def build_pursuit_brief(tender: dict, supplier: dict) -> PursuitBrief:
    """Return a reproducible bid decision and strategy from structured input."""
    required_tender = ("id", "buyer_objective", "promised_outcome", "tags", "eligibility_requirements", "delivery_hours", "evaluation_criteria")
    required_supplier = ("id", "name", "credentials", "available_hours", "past_projects", "people")
    missing_tender = [key for key in required_tender if key not in tender]
    missing_supplier = [key for key in required_supplier if key not in supplier]
    if missing_tender or missing_supplier:
        raise PursuitInputError(
            "Pursuit input is incomplete: "
            + ", ".join(f"tender.{key}" for key in missing_tender)
            + ("; " if missing_tender and missing_supplier else "")
            + ", ".join(f"supplier.{key}" for key in missing_supplier)
        )
    _validate_pursuit_inputs(tender, supplier)
    criteria = tender["evaluation_criteria"]
    if not criteria:
        raise PursuitInputError("Pursuit input needs a reviewed evaluation score map.")
    names = [str(item.get("name") or "").strip() for item in criteria]
    weights = [float(item.get("weight") or 0) for item in criteria]
    if any(not name for name in names) or any(weight <= 0 for weight in weights):
        raise PursuitInputError("Every score-map row needs a name and positive weight.")
    if len({name.casefold() for name in names}) != len(names):
        raise PursuitInputError("Score-map criterion names must be unique.")
    if abs(sum(weights) - 100.0) > 0.01:
        raise PursuitInputError(f"Score-map weights must total 100; current total is {sum(weights):g}.")
    missing = tuple(sorted(set(tender["eligibility_requirements"]) - set(supplier["credentials"])))
    capacity_gap = max(0, tender["delivery_hours"] - supplier["available_hours"])
    projects = _matches(tender, supplier)
    score_map = tuple(sorted(tender["evaluation_criteria"], key=lambda item: item["weight"], reverse=True))
    positions = (
        _position(score_map[0]["name"], tender, supplier, projects, list(score_map)),
        _position("Operational continuity", tender, supplier, projects, list(score_map)[1:] + list(score_map)[:1]),
    )

    status = pursue_status(len(missing), capacity_gap, len(projects))
    if status == "NO-GO":
        status = "NO-GO"
        next_actions = ("Do not generate a proposal.", "Resolve eligibility or delivery capacity before reopening this opportunity.")
    elif status == "REVIEW":
        next_actions = ("Validate the comparable-project gap.", "Add a delivery reference before authoring a proposal.")
    else:
        status = "PURSUE"
        next_actions = ("Select a Win Position.", "Assign the proposal blueprint owners.")

    return PursuitBrief(
        opportunity_id=tender["id"],
        supplier_profile_id=supplier["id"],
        status=status,
        buyer_objective=tender["buyer_objective"],
        missing_eligibility=missing,
        capacity_gap_hours=capacity_gap,
        score_map=score_map,
        win_positions=positions,
        proposal_blueprint=_blueprint(tender, supplier, positions[0], projects),
        next_actions=next_actions,
        selected_position_index=0,
    )


def select_win_position(brief: PursuitBrief, tender: dict, supplier: dict, index: int) -> PursuitBrief:
    """Bind the selected win position to every proposal-blueprint claim."""
    if index < 0 or index >= len(brief.win_positions):
        raise IndexError("Selected win position is outside the pursuit brief.")
    projects = _matches(tender, supplier)
    position = brief.win_positions[index]
    return replace(
        brief,
        proposal_blueprint=_blueprint(tender, supplier, position, projects),
        selected_position_index=index,
    )
