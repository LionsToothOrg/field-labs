from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    max_load_kg: int
    indoor_only: bool
    stock_count: int


@dataclass(frozen=True)
class Candidate:
    product_id: str
    semantic_score: float


@dataclass(frozen=True)
class Constraints:
    category: str
    minimum_load_kg: int
    require_outdoor: bool = False
    require_in_stock: bool = False


@dataclass(frozen=True)
class QualificationEvidence:
    requirement: str
    catalog_field: str
    observed_value: str


@dataclass(frozen=True)
class DiscoveryResult:
    product: Product
    evidence: tuple[QualificationEvidence, ...]


def _qualification_evidence(
    product: Product, constraints: Constraints
) -> tuple[QualificationEvidence, ...]:
    evidence = [
        QualificationEvidence("category", "category", product.category),
        QualificationEvidence(
            "minimum_load_kg", "max_load_kg", str(product.max_load_kg)
        ),
    ]
    if constraints.require_outdoor:
        evidence.append(
            QualificationEvidence(
                "outdoor_use", "indoor_only", str(product.indoor_only).lower()
            )
        )
    if constraints.require_in_stock:
        evidence.append(
            QualificationEvidence("in_stock", "stock_count", str(product.stock_count))
        )
    return tuple(evidence)


def discover(
    catalog: dict[str, Product],
    candidates: Iterable[Candidate],
    constraints: Constraints,
) -> list[DiscoveryResult]:
    """Return eligible catalog products with evidence for each applied requirement."""
    eligible: list[tuple[float, Product]] = []

    for candidate in candidates:
        product = catalog.get(candidate.product_id)
        if product is None:
            continue
        if product.category != constraints.category:
            continue
        if product.max_load_kg < constraints.minimum_load_kg:
            continue
        if constraints.require_outdoor and product.indoor_only:
            continue
        if constraints.require_in_stock and product.stock_count <= 0:
            continue
        eligible.append((candidate.semantic_score, product))

    eligible.sort(key=lambda item: (-item[0], item[1].product_id))
    return [
        DiscoveryResult(product, _qualification_evidence(product, constraints))
        for _, product in eligible
    ]
