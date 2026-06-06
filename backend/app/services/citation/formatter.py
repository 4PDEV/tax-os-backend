"""Display formatting for assembled citations — separate from assembly logic."""

from datetime import date

from app.services.citation.models import AuthorityType


def _format_date(value: date) -> str:
    return f"{value.day} {value.strftime('%B %Y')}"


class CitationFormatter:
    """Convert structured citation fields into deterministic display text."""

    def format(
        self,
        *,
        source_title: str,
        location_reference: str,
        authority_type: AuthorityType,
        version_label: str | None = None,
        effective_from: date | None = None,
        source_version_effective_from: date | None = None,
        source_version_effective_to: date | None = None,
        official_reference: str | None = None,
    ) -> str:
        lines: list[str] = [source_title.rstrip(".") + ",", location_reference + ","]

        version_line = self._version_line(
            authority_type=authority_type,
            version_label=version_label,
            effective_from=effective_from,
            official_reference=official_reference,
        )
        if version_line:
            lines.append(version_line)

        lines.extend(
            self._source_metadata_lines(
                source_version_effective_from=source_version_effective_from,
                source_version_effective_to=source_version_effective_to,
            )
        )

        return "\n".join(lines)

    def _source_metadata_lines(
        self,
        *,
        source_version_effective_from: date | None,
        source_version_effective_to: date | None,
    ) -> list[str]:
        lines: list[str] = []
        if source_version_effective_from is not None:
            lines.append(
                "Source version metadata: effective from "
                f"{_format_date(source_version_effective_from)}."
            )
        if source_version_effective_to is not None:
            lines.append(
                "Source version metadata: effective to "
                f"{_format_date(source_version_effective_to)}."
            )
        return lines

    def _version_line(
        self,
        *,
        authority_type: AuthorityType,
        version_label: str | None,
        effective_from: date | None,
        official_reference: str | None,
    ) -> str:
        if version_label and version_label.strip():
            label = version_label.strip()
            if not label.lower().endswith("version"):
                label = f"{label} Version"
            return f"{label}."

        if effective_from is not None:
            return f"Version effective {_format_date(effective_from)}."

        if official_reference and official_reference.strip():
            return f"{official_reference.strip()}."

        authority_name = authority_type.value.replace("_", " ").title()
        return f"{authority_name}."
