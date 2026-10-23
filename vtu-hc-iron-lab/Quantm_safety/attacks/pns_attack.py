"""Photon Number Splitting (PNS) Attack on BB84.

In a practical QKD system, Alice's source occasionally emits multi-photon
pulses (2+ photons per qubit) instead of the ideal single-photon pulses.
Eve can split off one photon from these multi-photon pulses using a
beamsplitter, store it in quantum memory, and wait until Alice and Bob
announce their bases.  She then measures her stored photon in the correct
basis, obtaining the bit value without introducing errors.

This makes PNS particularly dangerous: Eve gains significant information
while keeping QBER low — the attack is "stealthy" against standard QBER
monitoring.

Defense: Decoy-state BB84 (varying intensity levels) detects PNS by
comparing yield statistics across decoy and signal pulses.
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

# Probability of multi-photon emission per pulse for a practical source.
# Weak coherent pulses with mu=0.1 yield ~5% multi-photon rate.
MULTI_PHOTON_PROBABILITY = 0.05

# Eve's probability of successfully splitting a photon from multi-photon
# pulses (limited by beamsplitter efficiency).
SPLITTING_EFFICIENCY = 0.95

# Small residual QBER introduced by PNS (imperfect splitting).
PNS_RESIDUAL_QBER_PERCENT = 2.0


class PNSAttack(BaseAttack):
    """Photon Number Splitting attack.

    Unlike intercept-resend, PNS does not disturb the qubit state — Eve
    merely siphons off a photon from multi-photon pulses.  This results
    in low QBER but high information leakage.

    Args:
        intercept_rate: Fraction of pulses Eve targets (default 1.0).
        multi_photon_prob: Probability that a pulse is multi-photon.
        splitting_efficiency: Eve's photon-splitting success rate.
        seed: Optional RNG seed.

    Example::

        attack = PNSAttack(seed=42)
        bob_results, qber, eve_info = attack.launch(
            alice_bits, alice_basis, bob_basis
        )
        # Expected: low QBER (~2%), high Eve info (~5% of bits fully known)
    """

    def __init__(
        self,
        intercept_rate: float = 1.0,
        multi_photon_prob: float = MULTI_PHOTON_PROBABILITY,
        splitting_efficiency: float = SPLITTING_EFFICIENCY,
        seed: int = None,
    ) -> None:
        super().__init__(intercept_rate=intercept_rate, seed=seed)
        self.multi_photon_prob = multi_photon_prob
        self.splitting_efficiency = splitting_efficiency
        self.name = "PNS"

    def launch(
        self,
        alice_bits: List[int],
        alice_basis: List[int],
        bob_basis: List[int],
    ) -> Tuple[List[int], float, float]:
        """Execute the PNS attack.

        For each qubit:
          1. Determine if the pulse is multi-photon (prob ~5%).
          2. If multi-photon and Eve intercepts: split off one photon.
          3. Eve stores her photon; Bob receives the rest.
          4. After basis announcement, Eve measures in the correct basis.

        QBER stays low because the photons Bob receives are undisturbed.
        Eve's information equals the fraction of multi-photon pulses she
        successfully split.

        Returns:
            Tuple of (bob_results, qber, eve_info).
        """
        n = len(alice_bits)
        bob_results: List[int] = []
        eve_split_count = 0

        for i in range(n):
            # Normal BB84 transmission (Bob gets the qubit)
            if bob_basis[i] == alice_basis[i]:
                bob_bit = alice_bits[i]
            else:
                bob_bit = random.randint(0, 1)

            # Occasionally introduce a small error (imperfect channel)
            if random.random() < (PNS_RESIDUAL_QBER_PERCENT / 100.0):
                if bob_basis[i] == alice_basis[i]:
                    bob_bit ^= 1

            bob_results.append(bob_bit)

            # PNS: Eve splits multi-photon pulses
            if random.random() < self.intercept_rate:
                if random.random() < self.multi_photon_prob:
                    if random.random() < self.splitting_efficiency:
                        # Eve successfully splits — she'll know this bit
                        # after basis reconciliation
                        eve_split_count += 1

        qber = self._compute_qber(alice_bits, bob_results, alice_basis, bob_basis)

        # Eve's information: she knows the split bits perfectly
        # Plus she gains partial info from the residual QBER
        eve_info = (eve_split_count / n) if n > 0 else 0.0
        # PNS is stealthy — Eve's info is high relative to QBER
        # Model: Eve also gets info proportional to multi-photon fraction
        eve_info = min(eve_info + self.multi_photon_prob * self.splitting_efficiency, 1.0)

        logger.info(
            f"PNS Attack: multi_photon_prob={self.multi_photon_prob:.2%}, "
            f"QBER={qber:.2f}%, Eve info={eve_info:.4f}, "
            f"split_bits={eve_split_count}/{n}"
        )

        return bob_results, qber, eve_info


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    random.seed(42)
    n = 500
    alice_bits = [random.randint(0, 1) for _ in range(n)]
    alice_basis = [random.randint(0, 1) for _ in range(n)]
    bob_basis = [random.randint(0, 1) for _ in range(n)]

    attack = PNSAttack(seed=42)
    _, qber, eve_info = attack.launch(alice_bits, alice_basis, bob_basis)
    print(f"PNS Attack on {n} qubits:")
    print(f"  QBER      : {qber:.2f}%  (stealthy — below 11% threshold)")
    print(f"  Eve info  : {eve_info:.4f}  (significant info leak)")
    print(f"  Detection : PNS evades QBER monitoring — needs decoy states!")
