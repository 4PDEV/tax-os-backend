"""Citation Assembly Contract (TASK-004D).

Deterministic assembly of source-backed citations from legal objects and versioned sources.

No answer generation, authority ranking, legal interpretation, AI, or persistence.
"""

CITATION_ASSEMBLY_CONTRACT_VERSION = "1.0.0"
ASSEMBLER_VERSION = "1.0.0"

PROHIBITED_CITATION_ASSEMBLY_CAPABILITIES: tuple[str, ...] = (
    "answer_generation",
    "citation_ranking",
    "authority_weighting",
    "legal_reasoning",
    "ai",
    "semantic_search",
    "retrieval",
    "topic_classification",
    "cross_regime_analysis",
    "citation_persistence",
)

__all__ = [
    "ASSEMBLER_VERSION",
    "CITATION_ASSEMBLY_CONTRACT_VERSION",
    "PROHIBITED_CITATION_ASSEMBLY_CAPABILITIES",
]
