from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.services.extraction import (
    BaseExtractor,
    ExtractionMetadata,
    ExtractionResult,
    ExtractionStatus,
    HtmlExtractor,
    PdfExtractor,
    TxtExtractor,
    sha256_text,
)
from app.core.datetime_utils import utc_now


def test_extraction_status_has_only_permitted_values():
    assert {s.value for s in ExtractionStatus} == {
        "pending",
        "success",
        "failed",
        "partial",
    }


def test_extraction_result_requires_core_fields():
    result = ExtractionResult(
        source_version_id=uuid4(),
        extraction_status=ExtractionStatus.SUCCESS,
        extractor_name="txt",
        extractor_version="1.0.0",
        extracted_at=utc_now(),
        content_hash=sha256_text("hello"),
        raw_text="hello",
    )
    assert result.extraction_status is ExtractionStatus.SUCCESS
    assert isinstance(result.metadata, ExtractionMetadata)
    assert result.metadata.partial is False


def test_extraction_result_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        ExtractionResult(
            source_version_id=uuid4(),
            extraction_status=ExtractionStatus.PENDING,
            extractor_name="txt",
            extractor_version="1.0.0",
            extracted_at=utc_now(),
            interpretation="not allowed",
        )


def test_extraction_metadata_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        ExtractionMetadata(summary="forbidden")


def test_pdf_and_html_extractors_are_skeletons():
    for extractor in (PdfExtractor(), HtmlExtractor()):
        assert isinstance(extractor, BaseExtractor)
        with pytest.raises(NotImplementedError):
            extractor.extract(source_version_id=uuid4(), content=b"data")


def test_extractors_inherit_base_contract():
    for extractor in (TxtExtractor(), PdfExtractor(), HtmlExtractor()):
        assert isinstance(extractor, BaseExtractor)
        assert extractor.name
        assert extractor.version


def test_can_handle_routing_by_mime_and_extension():
    txt = TxtExtractor()
    assert txt.can_handle(mime_type="text/plain", filename=None) is True
    assert txt.can_handle(mime_type="text/plain; charset=utf-8", filename=None) is True
    assert txt.can_handle(mime_type=None, filename="law.txt") is True
    assert txt.can_handle(mime_type="application/pdf", filename="law.pdf") is False

    pdf = PdfExtractor()
    assert pdf.can_handle(mime_type="application/pdf", filename=None) is True
    assert pdf.can_handle(mime_type="text/plain", filename=None) is False

    html = HtmlExtractor()
    assert html.can_handle(mime_type="text/html", filename=None) is True
    assert html.can_handle(mime_type=None, filename="page.htm") is True
