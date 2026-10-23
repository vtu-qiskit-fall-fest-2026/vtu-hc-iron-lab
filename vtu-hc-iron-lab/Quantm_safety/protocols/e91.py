"""E91 Entanglement-Based Quantum Key Distribution protocol.

The E91 protocol (Ekert 1991) uses Bell pairs shared between Alice and
Bob, with security rooted in the violation of Bell's inequality.  This
implementation provides a simplified simulation suitable for comparison
with BB84 in the Q-GibberLink platform.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.qber_analyzer import QBERAnalyzer, QBERResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# E91 uses three measurement settings per party
# Alice: a1=0, a2=pi/4, a3=pi/2
# Bob:   b1=pi/4, b2=pi/2, b3=3*pi/4
ALICE_ANGLES = [0.0, math.pi / 4, math.pi / 2]
BOB_ANGLES = [math.pi / 4, math.pi / 2, 3 * math.pi / 4]

# Classical correlation threshold for Bell inequality (CHSH form)
# S > 2 indicates quantum entanglement; max is 2*sqrt(2) ≈ 2.828
CHSH_CLASSICAL_BOUND = 2.0
CHSH_QUANTUM_BOUND = 2.0 * math.sqrt(2)

DEFAULT_ENTANGLED_PAIRS = 128


@dataclass
class E91Result:
    """Result of an E91 protocol run.

    Attributes:
        sifted_key:       Final key bits from entangled pairs.
        qber:             QBER percentage.
        bell_parameter:   CHSH Bell parameter S.
        is_entangled:     True if Bell inequality is violated.
        secure_key_rate:  Estimated secure key rate.
        is_secure:        Overall security assessment.
    """

    sifted_key: List[int]
    qber: float
    bell_parameter: float
    is_entangled: bool
    secure_key_rate: float
    is_secure: bool


class E91Protocol:
    """Simplified E91 entanglement-based QKD protocol.

    In the ideal case, Alice and Bob share maximally entangled Bell pairs
    (|Phi+> = (|00> + |11>)/sqrt(2)).  When they measure in the same basis,
    their results are perfectly correlated.

    Security comes from Bell inequality violation — an eavesdropper would
    necessarily disturb the entanglement, reducing S below 2.

    Example::

        proto = E91Protocol(num_pairs=100)
        result = proto.run()
        print(f"S = {result.bell_parameter:.3f}, secure: {result.is_secure}")
    """

    def __init__(self, num_pairs: int = DEFAULT_ENTANGLED_PAIRS, seed: Optional[int] = None) -> None:
        self.num_pairs = num_pairs
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.analyzer = QBERAnalyzer()

    def run(self, noise_level: float = 0.0) -> E91Result:
        """Execute the E91 protocol.

        Args:
            noise_level: Fraction of pairs affected by depolarising noise [0, 1].

        Returns:
            E91Result with key, QBER, and Bell parameter.
        """
        alice_results: List[int] = []
        bob_results: List[int] = []

        # For Bell test: use settings a2/b1 and a3/b2 for key, others for CHSH
        bell_correlations: List[float] = []

        for _ in range(self.num_pairs):
            # Simulate measurement of a |Phi+> Bell pair
            # In the ideal case, both parties get the same bit
            bit = random.randint(0, 1)

            # Apply noise
            if random.random() < noise_level:
                bob_bit = 1 - bit
            else:
                bob_bit = bit

            alice_results.append(bit)
            bob_results.append(bob_bit)

        # Compute QBER
        errors = sum(1 for a, b in zip(alice_results, bob_results) if a != b)
        qber = (errors / self.num_pairs) * 100.0 if self.num_pairs > 0 else 0.0

        # Estimate Bell parameter (CHSH)
        # For ideal entanglement: S = 2*sqrt(2); noise reduces it
        # S ≈ 2*sqrt(2) * (1 - 2*Q) where Q is QBER fraction
        q_fraction = qber / 100.0
        bell_s = CHSH_QUANTUM_BOUND * (1.0 - 2.0 * q_fraction)
        bell_s = max(bell_s, 0.0)

        is_entangled = bell_s > CHSH_CLASSICAL_BOUND

        # Secure key rate for E91: proportional to Bell violation
        if bell_s > CHSH_CLASSICAL_BOUND:
            secure_rate = 1.0 - self.analyzer.binary_entropy(q_fraction)
        else:
            secure_rate = 0.0

        is_secure = is_entangled and qber < 11.0

        return E91Result(
            sifted_key=alice_results,
            qber=qber,
            bell_parameter=bell_s,
            is_entangled=is_entangled,
            secure_key_rate=max(secure_rate, 0.0),
            is_secure=is_secure,
        )

    @staticmethod
    def _bits_to_hex(bits: List[int]) -> str:
        """Convert a list of bits to a hex string."""
        if not bits:
            return "0x00"
        padded = bits + [0] * ((8 - len(bits) % 8) % 8)
        value = 0
        for bit in padded:
            value = (value << 1) | bit
        return hex(value)


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    proto = E91Protocol(num_pairs=100, seed=42)
    clean = proto.run(noise_level=0.0)
    noisy = proto.run(noise_level=0.15)

    print("=== E91 Clean Channel ===")
    print(f"  QBER: {clean.qber:.2f}%  |  S: {clean.bell_parameter:.3f}  |  Secure: {clean.is_secure}")

    print("\n=== E91 Noisy Channel (15% noise) ===")
    print(f"  QBER: {noisy.qber:.2f}%  |  S: {noisy.bell_parameter:.3f}  |  Secure: {noisy.is_secure}")
