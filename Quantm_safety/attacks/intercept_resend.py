"""Intercept-Resend Attack on BB84.

Eve intercepts a fraction of qubits en route from Alice to Bob, measures
them in a randomly chosen basis, and forwards the resulting state to Bob.

When Eve measures in the wrong basis (50% of the time), she disturbs the
qubit state.  This introduces errors in ~25% of the bits where Alice and
Bob used matching bases, raising QBER to 25% at full interception.

This is the most basic quantum attack and is easily detected by QBER
monitoring.
"""

from __future__ import annotations

import logging
import random
from typing import List, Tuple

from attacks.base import BaseAttack

logger = logging.getLogger(__name__)

# When Eve measures in the wrong basis and Bob measures in the correct
# basis, the probability of an error is 50% — but only half of Eve's
# wrong-basis measurements hit matched Alice-Bob bases, yielding ~25%
# overall QBER at full interception.
WRONG_BASIS_ERROR_PROB = 0.50


class InterceptResendAttack(BaseAttack):
    """Intercept-Resend attack against BB84.

    Args:
        intercept_rate: Fraction of qubits Eve intercepts [0, 1].
        seed:           Optional RNG seed.

    Example::

        attack = InterceptResendAttack(intercept_rate=0.8)
        bob_results, qber, eve_info = attack.launch(
            alice_bits, alice_basis, bob_basis
        )
        # Expected QBER at 80% intercept: ~20%
    """

    def __init__(self, intercept_rate: float = 1.0, seed: int = None) -> None:
        super().__init__(intercept_rate=intercept_rate, seed=seed)
        self.name = "Intercept-Resend"

    def launch(
        self,
        alice_bits: List[int],
        alice_basis: List[int],
        bob_basis: List[int],
    ) -> Tuple[List[int], float, float]:
        """Execute the intercept-resend attack.

        For each qubit:
          1. With probability *intercept_rate*, Eve intercepts.
          2. Eve chooses a random basis and measures.
          3. Eve forwards the measured state to Bob.
          4. Bob measures in his basis.

        When Eve's basis differs from Alice's, the qubit is projected
        into a random state, causing errors.

        Returns:
            Tuple of (bob_results, qber, eve_info).
        """
        n = len(alice_bits)
        bob_results: List[int] = []
        eve_known_bits = 0

        for i in range(n):
            if random.random() < self.intercept_rate:
                # Eve intercepts
                eve_basis = random.randint(0, 1)

                if eve_basis == alice_basis[i]:
                    # Eve measures correctly — knows the bit
                    eve_bit = alice_bits[i]
                    eve_known_bits += 1
                else:
                    # Eve measures in wrong basis — random result
                    eve_bit = random.randint(0, 1)

                # Eve forwards the state corresponding to her measurement
                # Bob now measures Eve's state in his basis
                if bob_basis[i] == eve_basis:
                    bob_bit = eve_bit
                else:
                    bob_bit = random.randint(0, 1)
            else:
                # Eve doesn't intercept — normal BB84
                if bob_basis[i] == alice_basis[i]:
                    bob_bit = alice_bits[i]
                else:
                    bob_bit = random.randint(0, 1)

            bob_results.append(bob_bit)

        qber = self._compute_qber(alice_bits, bob_results, alice_basis, bob_basis)

        # Eve knows bits where her basis matched Alice's
        eve_info = eve_known_bits / n if n > 0 else 0.0

        logger.info(
            f"Intercept-Resend: intercept_rate={self.intercept_rate:.0%}, "
            f"QBER={qber:.2f}%, Eve info={eve_info:.4f}"
        )

        return bob_results, qber, eve_info


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    random.seed(42)
    n = 200
    alice_bits = [random.randint(0, 1) for _ in range(n)]
    alice_basis = [random.randint(0, 1) for _ in range(n)]
    bob_basis = [random.randint(0, 1) for _ in range(n)]

    for rate in [0.0, 0.25, 0.5, 0.75, 1.0]:
        attack = InterceptResendAttack(intercept_rate=rate, seed=42)
        _, qber, eve_info = attack.launch(alice_bits, alice_basis, bob_basis)
        print(f"  Rate={rate:.0%}  |  QBER={qber:5.2f}%  |  Eve info={eve_info:.4f}")
