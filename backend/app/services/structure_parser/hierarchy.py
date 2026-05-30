from app.services.structure_parser.enums import StructuralUnitType
from app.services.structure_parser.patterns import STRUCTURAL_RANK


def assign_hierarchy(
    units: list,
) -> None:
    """Resolve parent_unit_id and hierarchy_level using structural ranks.

    Mutates units in place. Purely structural — no legal or semantic hierarchy.
    """
    stack: list[tuple[str, int, int]] = []  # unit_id, rank, hierarchy_level

    for unit in units:
        rank = STRUCTURAL_RANK.get(unit.unit_type, STRUCTURAL_RANK[StructuralUnitType.UNKNOWN])

        while len(stack) > 0 and stack[-1][1] >= rank:
            stack.pop()

        if stack:
            unit.parent_unit_id = stack[-1][0]
            unit.hierarchy_level = stack[-1][2] + 1
        else:
            unit.parent_unit_id = None
            unit.hierarchy_level = 0

        stack.append((unit.unit_id, rank, unit.hierarchy_level))
