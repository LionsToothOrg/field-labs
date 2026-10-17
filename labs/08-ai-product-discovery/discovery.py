from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    max_load_kg: int
    indoor_only: bool


@dataclass(frozen=True)
class Candidate:
    product_id: str
    semantic_score: float


@dataclass(frozen=True)
class Constraints:
    category: str
    minimum_load_kg: int
    require_outdoor: bool = False


def discover(
    catalog: dict[str, Product],
    candidates: Iterable[Candidate],
    constraints: Constraints,
) -> list[Product]:
    """Hydrate retrieval candidates from the authoritative catalog, then apply hard constraints."""
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
        eligible.append((candidate.semantic_score, product))

    eligible.sort(key=lambda item: (-item[0], item[1].product_id))
    return [product for _, product in eligible]
