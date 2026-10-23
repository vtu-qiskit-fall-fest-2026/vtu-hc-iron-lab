"""Detector Blinding Attack on BB84.

Eve uses bright laser light to "blind" Bob's single-photon detectors,
forcing them into a classical (linear) mode.  In this state, Eve can
control Bob's detection outcomes by sending carefully calibrated pulses
that trigger clicks only in the detector of her choosing.

This results in 0% QBER — Eve's bits perfectly match Alice's — because
Eve is effectively choosing Bob's measurement results.  However, the
key is completely compromised: Eve knows every bit.

This attack highlights a critical limitation of QBER-only monitoring:
zero QBER does NOT guarantee security.  Side-channel attacks on the
hardware can bypass the quantum protocol entirely.

Defense: Detector watchdogs, optical isolators, and monitoring of
detector bias current.
"""

from __future__ import annotations

import logging
import random
from typing import List, Tuple

from attacks.base import BaseAttack

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# QBER under detector blinding — Eve controls Bob perfectly, so errors
# are only from Eve's own measurement noise (near zero).
DETECTOR_BLIND_QBER_PERCENT = 0.0

# Eve's information — she knows every bit she forces.
DETECTOR_BLIND_EVE_INFO = 1.0


class DetectorBlindingAttack(BaseAttack):
    """Detector Blinding attack against BB84.

    Eve blinds Bob's detectors and controls his measurement outcomes
    directly.  QBER remains ~0% but Eve knows the entire key.

    Args:
        intercept_rate: Fraction of qubits where Eve controls Bob's
                        detector (default 1.0 = full control).
        seed:           Optional RNG seed.

    Example::

        attack = DetectorBlindingAttack(intercept_rate=1.0)
        bob_results, qber, eve_info = attack.launch(
            alice_bits, alice_basis, bob_basis
        )
        # Expected: QBER ~0%, Eve info = 1.0 — key fully compromised!
    """

    def __init__(self, intercept_rate: float = 1.0, seed: int = None) -> None:
        super().__init__(intercept_rate=intercept_rate, seed=seed)
        self.name = "Detector Blinding"

    def launch(
        self,
        alice_bits: List[int],
        alice_basis: List[int],
        bob_basis: List[int],
    ) -> Tuple[List[int], float, float]:
        """Execute the detector blinding attack.

        For intercepted qubits, Eve:
          1. Measures Alice's qubit in Alice's basis (she knows it
             after basis announcement, or uses bright pulse to read it).
          2. Forces Bob's blinded detector to report her measured bit.

        For non-intercepted qubits, normal BB84 applies.

        Returns:
            Tuple of (bob_results, qber, eve_info).
        """
        n = len(alice_bits)
        bob_results: List[int] = []
        eve_controlled = 0

        for i in range(n):
            if random.random() < self.intercept_rate:
                # Eve controls Bob's detector — forces her desired result
                # Eve knows Alice's bit (she reads it before basis reconciliation
                # using the bright pulse attack, or she measures in Alice's basis)
                bob_bit = alice_bits[i]
                eve_controlled += 1
            else:
                # Normal BB84 for non-intercepted qubits
                if bob_basis[i] == alice_basis[i]:
                    bob_bit = alice_bits[i]
                else:
                    bob_bit = random.randint(0, 1)

            bob_results.append(bob_bit)

        qber = self._compute_qber(alice_bits, bob_results, alice_basis, bob_basis)

        # Eve's information proportional to controlled fraction
        eve_info = eve_controlled / n if n > 0 else 0.0

        logger.warning(
            f"Detector Blinding: intercept_rate={self.intercept_rate:.0%}, "
            f"QBER={qber:.2f}% (DECEPTIVELY LOW!), "
            f"Eve info={eve_info:.4f} — KEY COMPROMISED"
        )

        return bob_results, qber, eve_info


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    random.seed(42)
    n = 200
    alice_bits = [random.randint(0, 1) for _ in range(n)]
    alice_basis = [random.randint(0, 1) for _ in range(n)]
    bob_basis = [random.randint(0, 1) for _ in range(n)]

    attack = DetectorBlindingAttack(intercept_rate=1.0, seed=42)
    _, qber, eve_info = attack.launch(alice_bits, alice_basis, bob_basis)
    print(f"Detector Blinding Attack on {n} qubits:")
    print(f"  QBER      : {qber:.2f}%  (ZERO — bypasses QBER monitoring!)")
    print(f"  Eve info  : {eve_info:.4f}  (FULL KEY COMPROMISE)")
    print(f"  Detection : Requires hardware-level countermeasures,")
    print(f"              not just QBER analysis.")
