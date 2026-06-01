from app.models.country import Country
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.models.tax_type import TaxType


def seed_source_version(db_session):
    country = Country(code="RW", name="Rwanda", status="active")
    db_session.add(country)
    db_session.flush()

    tax_type = TaxType(country_id=country.id, code="VAT", name="VAT", status="active")
    db_session.add(tax_type)
    db_session.flush()

    document = SourceDocument(
        country_id=country.id,
        tax_type_id=tax_type.id,
        source_type="law",
        authority_level="national",
        title="VAT Law",
        status="active",
    )
    db_session.add(document)
    db_session.flush()

    version = SourceVersion(
        source_document_id=document.id,
        version_label="v1",
        checksum_sha256="a" * 64,
        storage_path="rw/vat/v1.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )
    db_session.add(version)
    db_session.flush()
    return version
