"""Conservative two-substrate feeding with an explicit processing tradeoff."""
from dataclasses import dataclass

RESOURCE_RULES = 'v3-resources-1'


@dataclass(frozen=True)
class Feeding:
    remaining_a: int
    remaining_b: int
    consumed_a: int
    consumed_b: int
    energy_gain: int
    released_b: int
    dissipated: int


def feed(a: int, b: int, capacity: int, allocation_a: int, limit: int = 8,
         recycle: bool = True) -> Feeding:
    """Process old substrates simultaneously; newly released B waits until later.

    allocation_a in0..16 partitions a fixed processing budget. Half of each
    consumed substrate becomes energy (integer floor). A's remainder becomes B
    when recycling is enabled, subject to capacity; all other loss dissipates.
    Unused processing allocation is not transferred between substrate types.
    """
    if any(type(v) is not int or v < 0 for v in (a, b, capacity, allocation_a, limit)):
        raise ValueError('nonnegative integer resource and processing values required')
    if a > capacity or b > capacity or allocation_a > 16 or type(recycle) is not bool:
        raise ValueError('invalid capacity, allocation or recycling switch')
    quota_a = limit * allocation_a // 16
    consumed_a, consumed_b = min(a, quota_a), min(b, limit - quota_a)
    energy = consumed_a // 2 + consumed_b // 2
    waste_a = consumed_a - consumed_a // 2
    available_b = b - consumed_b
    released = min(waste_a, capacity - available_b) if recycle else 0
    loss = consumed_a + consumed_b - energy - released
    return Feeding(a - consumed_a, available_b + released, consumed_a, consumed_b,
                   energy, released, loss)
