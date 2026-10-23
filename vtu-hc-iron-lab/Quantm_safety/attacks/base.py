"""Base class for all quantum attack modules.

Every attack implements the common interface:

    launch(alice_bits, alice_basis, bob_basis) -> AttackResult

This allows the dashboard and protocol layer to swap attacks
interchangeably.
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# When Eve measures in the wrong basis, the qubit state is disturbed.
# The error rate among correctly-basis-matched bits rises to ~25%.
INTERCEPT_RESEND_WRONG_BASIS_ERROR_RATE = 0.25


@dataclass
class AttackResult:
    """Standardised result from any attack module.

    Attributes:
        bob_results: Bob's measurement results after the attack.
        qber:        Resulting QBER percentage.
        eve_info:    Fraction of the key Eve has learned [0, 1].
        attack_name: Human-readable attack identifier.
        details:     Dict of attack-specific diagnostic data.
    """

    bob_results: List[int]
    qber: float
    eve_info: float
    attack_name: str
    details: dict


class BaseAttack(ABC):
    """Abstract base class for quantum attacks.

    Subclasses must implement :meth:`launch`.

    Args:
        intercept_rate: Fraction of qubits Eve intercepts [0, 1].
        seed:           Optional RNG seed for reproducibility.
    """

    def __init__(self, intercept_rate: float = 1.0, seed: int = None) -> None:
        if not 0.0 <= intercept_rate <= 1.0:
            raise ValueError("intercept_rate must be in [0, 1]")
        self.intercept_rate = intercept_rate
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.name: str = self.__class__.__name__

    @abstractmethod
    def launch(
        self,
        alice_bits: List[int],
        alice_basis: List[int],
        bob_basis: List[int],
    ) -> Tuple[List[int], float, float]:
        """Execute the attack.

        Args:
            alice_bits:  Alice's original bit string.
            alice_basis: Alice's basis choices.
            bob_basis:   Bob's basis choices.

        Returns:
            Tuple of (bob_results, qber, eve_info).
        """
        ...

    @staticmethod
    def _compute_qber(
        alice_bits: List[int],
        bob_results: List[int],
        alice_basis: List[int],
        bob_basis: List[int],
    ) -> float:
        """Compute QBER from matched-basis positions only."""
        matched = [
            i for i in range(len(alice_bits))
            if alice_basis[i] == bob_basis[i]
        ]
        if not matched:
            return 0.0
        errors = sum(1 for i in matched if alice_bits[i] != bob_results[i])
        return (errors / len(matched)) * 100.0
