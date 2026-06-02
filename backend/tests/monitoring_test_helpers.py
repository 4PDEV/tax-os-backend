from app.models.country import Country
from app.models.source_document import SourceDocument
from app.models.tax_type import TaxType


def seed_source_document(db_session):
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
    return document
