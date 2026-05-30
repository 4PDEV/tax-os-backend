"""Legal Object Retrieval Contract (TASK-004A).

Deterministic, auditable, source-backed retrieval of persisted legal objects.

This module performs NO answer generation, semantic search, embeddings, ranking,
citation assembly, or AI retrieval.
"""

RETRIEVAL_CONTRACT_VERSION = "1.0.0"

PROHIBITED_RETRIEVAL_CAPABILITIES: tuple[str, ...] = (
    "embeddings",
    "pgvector",
    "semantic_similarity",
    "rag",
    "ai_retrieval",
    "bm25",
    "answer_generation",
    "citation_assembly",
    "topic_scoring",
    "nlp",
)

DETERMINISTIC_ORDER_FIELDS: tuple[str, ...] = (
    "effective_from",
    "object_identifier",
    "created_at",
)

__all__ = [
    "DETERMINISTIC_ORDER_FIELDS",
    "PROHIBITED_RETRIEVAL_CAPABILITIES",
    "RETRIEVAL_CONTRACT_VERSION",
]
