from fastapi import APIRouter

from app.api.routes import (
    countries,
    source_documents,
    source_processing_jobs,
    source_versions,
    tax_types,
)

api_router = APIRouter()

api_router.include_router(countries.router, prefix="/countries", tags=["countries"])
api_router.include_router(tax_types.router, prefix="/tax-types", tags=["tax-types"])
api_router.include_router(source_documents.router, prefix="/source-documents", tags=["source-documents"])
api_router.include_router(source_versions.router, prefix="/source-versions", tags=["source-versions"])
api_router.include_router(
    source_processing_jobs.router,
    prefix="/source-processing-jobs",
    tags=["source-processing-jobs"],
)
