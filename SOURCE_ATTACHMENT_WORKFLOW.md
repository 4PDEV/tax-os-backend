# Source Version File Attachment Workflow

Internal workflow for attaching raw legal source files to `source_versions` (TASK-001J, TASK-001K).

## Lifecycle States

| `attachment_status` | Meaning |
|---------------------|---------|
| `pending` | Version registered; file not yet attached or metadata incomplete |
| `attached` | All attachment metadata present and file exists in storage |
| `inconsistent` | Partial metadata or storage/metadata mismatch |

API field `file_attached` is `true` only when status is `attached`.

## Attachment Requirements

A version is **attached** only when all are present:

- `storage_path`
- `checksum_sha256`
- `file_size`
- `mime_type`

Plus the file must exist under `STORAGE_ROOT` at `storage_path`.

## Workflow

1. Create `source_document`.
2. Create `source_version` with declared `checksum_sha256` and `storage_path` (checksum is pre-declared; verified on upload).
3. `POST /source-versions/{id}/upload` with multipart field `file`.
4. System verifies checksum, writes file once, sets `file_size` and non-empty `mime_type` (uses client `Content-Type` when provided, otherwise `application/octet-stream`), updates `retrieved_at`.
5. Re-upload returns **409** (`source version file is already attached`).

## Governance Rules

- No silent overwrite (`overwrite=False` in storage layer).
- No general PUT on `source_versions` (405).
- Partial `file_size` / `mime_type` without the other → **422** inconsistent state.
- Successful upload always persists non-empty `mime_type`.
- Binary content is never stored in PostgreSQL.

## Example

```bash
# Create version (checksum must match file bytes you will upload)
curl -s -X POST http://localhost:8000/source-versions \
  -H "Content-Type: application/json" \
  -d '{
    "source_document_id": "<uuid>",
    "version_label": "v1",
    "checksum_sha256": "<sha256-hex>",
    "storage_path": "rw/vat/v1/statute.pdf"
  }'

# Upload file
curl -s -X POST "http://localhost:8000/source-versions/<version-id>/upload" \
  -F "file=@./statute.pdf;type=application/pdf"
```

## Service Helpers

- `has_attached_file(source_version, storage)` — attached check
- `validate_attachment_state(source_version, storage)` — consistency validation
- `get_attachment_status(source_version, storage)` — status for API responses

Located in `backend/app/services/source_attachment.py`.
