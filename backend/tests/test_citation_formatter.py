from datetime import date

from app.services.citation.formatter import CitationFormatter
from app.services.citation.models import AuthorityType


def test_format_with_version_label():
    text = CitationFormatter().format(
        source_title="Value Added Tax Act",
        location_reference="Section 15",
        authority_type=AuthorityType.STATUTE,
        version_label="Finance Act 2024 Amendment",
    )
    assert text == (
        "Value Added Tax Act,\n"
        "Section 15,\n"
        "Finance Act 2024 Amendment Version."
    )


def test_format_with_effective_from():
    text = CitationFormatter().format(
        source_title="Value Added Tax Act",
        location_reference="Section 15",
        authority_type=AuthorityType.STATUTE,
        effective_from=date(2024, 7, 1),
    )
    assert "Version effective 1 July 2024." in text
    assert text.startswith("Value Added Tax Act,")


def test_format_income_tax_example():
    text = CitationFormatter().format(
        source_title="Income Tax Act",
        location_reference="Section 63(2)",
        authority_type=AuthorityType.STATUTE,
        version_label="Finance Act 2025",
    )
    assert "Income Tax Act," in text
    assert "Section 63(2)," in text
    assert "Finance Act 2025 Version." in text


def test_formatting_consistency():
    formatter = CitationFormatter()
    kwargs = {
        "source_title": "VAT Law",
        "location_reference": "Article 8",
        "authority_type": AuthorityType.STATUTE,
        "version_label": "v1",
    }
    assert formatter.format(**kwargs) == formatter.format(**kwargs)
