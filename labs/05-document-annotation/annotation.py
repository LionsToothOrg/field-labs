"""Synthetic annotation anchoring model for Lab 05."""

from dataclasses import dataclass


CONTEXT_WINDOW = 16


@dataclass(frozen=True)
class Annotation:
    selected_text: str
    start_offset: int
    end_offset: int
    prefix_context: str
    suffix_context: str


@dataclass(frozen=True)
class ResolvedAnchor:
    start_offset: int
    end_offset: int


def create_annotation(document: str, selected_text: str) -> Annotation:
    """Capture one uniquely identifiable synthetic selection and its neighborhood."""
    first = document.find(selected_text)
    if first < 0:
        raise ValueError("selected text is not present in document")
    if document.find(selected_text, first + 1) >= 0:
        raise ValueError("selected text must be unique when annotation is created")
    end = first + len(selected_text)
    return Annotation(
        selected_text=selected_text,
        start_offset=first,
        end_offset=end,
        prefix_context=document[max(0, first - CONTEXT_WINDOW) : first],
        suffix_context=document[end : end + CONTEXT_WINDOW],
    )


def resolve_by_offsets(document: str, annotation: Annotation) -> str:
    """Return what the original offsets point at after a document revision."""
    return document[annotation.start_offset : annotation.end_offset]


def _matching_offsets(document: str, selected_text: str) -> list[int]:
    matches: list[int] = []
    start = 0
    while True:
        match = document.find(selected_text, start)
        if match < 0:
            return matches
        matches.append(match)
        start = match + 1


def resolve_by_unique_text(document: str, annotation: Annotation) -> ResolvedAnchor | None:
    """Re-anchor only when the exact selected text has one unambiguous match."""
    matches = _matching_offsets(document, annotation.selected_text)
    if len(matches) != 1:
        return None
    start = matches[0]
    return ResolvedAnchor(start, start + len(annotation.selected_text))


def resolve_by_context(document: str, annotation: Annotation) -> ResolvedAnchor | None:
    """Disambiguate exact quote matches only when one retains the captured neighborhood."""
    candidates: list[ResolvedAnchor] = []
    for start in _matching_offsets(document, annotation.selected_text):
        end = start + len(annotation.selected_text)
        prefix_start = max(0, start - len(annotation.prefix_context))
        prefix = document[prefix_start:start]
        suffix = document[end : end + len(annotation.suffix_context)]
        if prefix == annotation.prefix_context and suffix == annotation.suffix_context:
            candidates.append(ResolvedAnchor(start, end))

    if len(candidates) != 1:
        return None
    return candidates[0]
