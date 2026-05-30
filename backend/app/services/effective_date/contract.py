"""Effective-Date Resolver Contract (TASK-004B).

Deterministic resolution of which legal object versions apply on a given date.

This module performs NO legal interpretation, answer generation, citation assembly,
semantic search, embeddings, or AI retrieval.
"""

RESOLVER_CONTRACT_VERSION = "1.0.0"

PROHIBITED_RESOLVER_CAPABILITIES: tuple[str, ...] = (
    "answer_generation",
    "legal_interpretation",
    "authority_ranking",
    "citation_assembly",
    "embeddings",
    "pgvector",
    "semantic_search",
    "rag",
    "ai_retrieval",
)

__all__ = [
    "PROHIBITED_RESOLVER_CAPABILITIES",
    "RESOLVER_CONTRACT_VERSION",
]
