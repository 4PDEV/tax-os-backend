"""Citation Candidate Contract (TASK-004C).

Deterministic preparation of citation-ready candidate DTOs from retrieval/resolution results.

No final citation formatting, answer generation, AI, embeddings, or persistence.
"""

CITATION_CANDIDATE_CONTRACT_VERSION = "1.0.0"

PROHIBITED_CITATION_CANDIDATE_CAPABILITIES: tuple[str, ...] = (
    "final_citation_formatting",
    "citation_style_rules",
    "answer_generation",
    "authority_hierarchy_weighting",
    "legal_interpretation",
    "ai",
    "rag",
    "embeddings",
    "semantic_retrieval",
    "candidate_persistence",
)

__all__ = [
    "CITATION_CANDIDATE_CONTRACT_VERSION",
    "PROHIBITED_CITATION_CANDIDATE_CAPABILITIES",
]
