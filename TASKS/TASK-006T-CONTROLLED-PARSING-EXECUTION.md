# TASK-006T — Controlled Parsing Execution

## Status

**Complete**

## Objective

Controlled structural parsing from `extracted_text` into `parsed_structures` without legal interpretation.

## Delivered

| Area | Location |
|------|----------|
| Provider | `ControlledStructuralParsingProvider` |
| Segmentation | `backend/app/workers/parsing/structural.py` |
| Runner | `run_controlled_structural_parsing()` — requires `controlled_structural=True` |
| Persistence | `persist_parsed_structure()` with optional `structure_json_extra` envelope |

## Doctrine

`parsed_structure` ≠ legal meaning — structural units only.

## Final principle

Controlled parsing produces structural evidence. It does not produce legal meaning.
