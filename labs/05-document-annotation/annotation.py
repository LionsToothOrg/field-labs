"""Synthetic annotation anchoring model for Lab 05."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Annotation:
    selected_text: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class ResolvedAnchor:
    start_offset: int
    end_offset: int


def create_annotation(document: str, selected_text: str) -> Annotation:
    """Capture one uniquely identifiable synthetic selection."""
    first = document.find(selected_text)
    if first < 0:
        raise ValueError("selected text is not present in document")
    if document.find(selected_text, first + 1) >= 0:
        raise ValueError("selected text must be unique when annotation is created")
    return Annotation(
        selected_text=selected_text,
        start_offset=first,
        end_offset=first + len(selected_text),
    )


def resolve_by_offsets(document: str, annotation: Annotation) -> str:
    """Return what the original offsets point at after a document revision."""
    return document[annotation.start_offset : annotation.end_offset]


def resolve_by_unique_text(document: str, annotation: Annotation) -> ResolvedAnchor | None:
    """Re-anchor only when the exact selected text has one unambiguous match."""
    first = document.find(annotation.selected_text)
    if first < 0:
        return None
    if document.find(annotation.selected_text, first + 1) >= 0:
        return None
    return ResolvedAnchor(first, first + len(annotation.selected_text))
