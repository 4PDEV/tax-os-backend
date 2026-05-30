from uuid import uuid4

from app.services.extraction.enums import ExtractionStatus
from app.services.extraction.extractors.txt import TxtExtractor
from app.services.extraction.hashing import sha256_text


def test_txt_extractor_returns_text_exactly_as_extracted():
    content = b"Article 1.\nThe rate is 18%.\n\nArticle 2.\n"
    result = TxtExtractor().extract(source_version_id=uuid4(), content=content)

    assert result.raw_text == content.decode("utf-8")
    assert result.extraction_status is ExtractionStatus.SUCCESS
    assert result.extractor_name == "txt"
    assert result.extractor_version == "1.0.0"


def test_txt_extractor_generates_sha256_of_raw_text():
    content = b"deterministic content"
    result = TxtExtractor().extract(source_version_id=uuid4(), content=content)

    assert result.content_hash == sha256_text("deterministic content")
    assert len(result.content_hash) == 64


def test_txt_extractor_is_deterministic_across_runs():
    content = b"same input -> same hash"
    version_id = uuid4()

    first = TxtExtractor().extract(source_version_id=version_id, content=content)
    second = TxtExtractor().extract(source_version_id=version_id, content=content)

    assert first.raw_text == second.raw_text
    assert first.content_hash == second.content_hash


def test_txt_extractor_populates_metadata():
    content = b"line one\nline two\nline three"
    result = TxtExtractor().extract(source_version_id=uuid4(), content=content)

    assert result.metadata.encoding == "utf-8"
    assert result.metadata.char_count == len(content.decode("utf-8"))
    assert result.metadata.byte_count == len(content)
    assert result.metadata.line_count == 3
    assert result.metadata.partial is False
    assert result.metadata.duration_ms is not None and result.metadata.duration_ms >= 0


def test_txt_extractor_handles_empty_file():
    result = TxtExtractor().extract(source_version_id=uuid4(), content=b"")

    assert result.raw_text == ""
    assert result.extraction_status is ExtractionStatus.SUCCESS
    assert result.metadata.line_count == 0
    assert result.content_hash == sha256_text("")


def test_txt_extractor_degrades_to_partial_on_invalid_utf8():
    content = b"valid text \xff\xfe invalid bytes"
    result = TxtExtractor().extract(source_version_id=uuid4(), content=content)

    assert result.extraction_status is ExtractionStatus.PARTIAL
    assert result.metadata.partial is True
    assert result.metadata.warnings
    assert result.content_hash == sha256_text(result.raw_text)


def test_txt_extractor_does_not_transform_whitespace():
    content = b"  leading and trailing  \n\ttabbed\n"
    result = TxtExtractor().extract(source_version_id=uuid4(), content=content)

    assert result.raw_text == content.decode("utf-8")
