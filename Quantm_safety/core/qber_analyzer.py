"""QBER (Quantum Bit Error Rate) analyzer with security threshold logic.

Computes QBER, secure key rate via the GLLP/decoy-state formula, and
implements the abort threshold logic used by the trust controller.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security constants
# ---------------------------------------------------------------------------

# BB84 abort threshold — above this QBER, information leakage to Eve
# exceeds the privacy amplification capacity.  Standard value from
# Shor-Preskill and MayMES analyses.
QBER_THRESHOLD_PERCENT = 11.0

# Channel loss threshold — if the channel transmittivity drops below
# this fraction, QKD is abandoned in favour of PQC-only mode.
CHANNEL_LOSS_THRESHOLD = 0.6

# Base secure key rate fraction at zero QBER (ideal BB84).
IDEAL_KEY_RATE_FRACTION = 0.5  # half the bits survive sifting

# Error correction efficiency factor (Cascade / LDPC).
ERROR_CORRECTION_EFFICIENCY = 1.16


@dataclass
class QBERResult:
    """Result of a QBER analysis.

    Attributes:
        qber:              Measured QBER percentage.
        secure_key_rate:   Estimated secure key rate as fraction of sifted bits.
        is_below_threshold: True if QBER < 11% threshold.
        should_abort:      True if QKD should be aborted.
        eve_information:   Estimated fraction of key known to Eve.
        checked_bits:      Number of bits compared for QBER.
        error_count:       Number of mismatched bits.
    """

    qber: float
    secure_key_rate: float
    is_below_threshold: bool
    should_abort: bool
    eve_information: float
    checked_bits: int
    error_count: int


class QBERAnalyzer:
    """Analyzes QBER and determines security posture.

    The analyzer implements:
      1. Direct QBER computation from Alice/Bob bit strings.
      2. Secure key rate estimation via the asymptotic formula:
            K = q * [1 - 2 * H2(Q)]
         where q = 0.5 (basis match fraction) and H2 is binary entropy.
      3. Eve's information estimation based on QBER and attack model.
    """

    @staticmethod
    def binary_entropy(p: float) -> float:
        """Compute binary entropy H2(p) = -p*log2(p) - (1-p)*log2(1-p).

        Args:
            p: Probability value in [0, 1].

        Returns:
            Binary entropy in bits.
        """
        if p <= 0.0 or p >= 1.0:
            return 0.0
        return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)

    def compute_qber(
        self,
        alice_bits: List[int],
        bob_bits: List[int],
        sample_size: Optional[int] = None,
    ) -> float:
        """Compute QBER from two bit strings.

        Args:
            alice_bits: Alice's key bits (post-sifting).
            bob_bits:   Bob's key bits (post-sifting).
            sample_size: If given, use only the first *sample_size* bits
                         for estimation (remaining bits stay in the key).

        Returns:
            QBER as a percentage.
        """
        if sample_size is not None:
            alice_bits = alice_bits[:sample_size]
            bob_bits = bob_bits[:sample_size]

        if len(alice_bits) == 0:
            return 0.0

        errors = sum(1 for a, b in zip(alice_bits, bob_bits) if a != b)
        return (errors / len(alice_bits)) * 100.0

    def estimate_eve_information(self, qber: float, attack_type: str = "intercept_resend") -> float:
        """Estimate the fraction of key bits Eve knows.

        For intercept-resend at QBER q, Eve knows ~2q fraction of bits.
        For PNS attacks, Eve's info is higher at low QBER.
        For detector blinding, Eve controls Bob fully.

        Args:
            qber:         Measured QBER percentage.
            attack_type:  Name of the attack model.

        Returns:
            Eve's information as a fraction in [0, 1].
        """
        q = qber / 100.0

        if attack_type == "intercept_resend":
            # Eve gets full info on ~2*q of sifted bits
            return min(2.0 * q, 1.0)
        elif attack_type == "pns":
            # PNS: high info leak even at low QBER
            return min(0.5 + 2.0 * q, 1.0)
        elif attack_type == "detector_blinding":
            # Full control — Eve knows everything
            return 1.0
        else:
            # General estimate from binary entropy
            return min(2.0 * q, 1.0)

    def analyze(
        self,
        alice_bits: List[int],
        bob_bits: List[int],
        channel_loss: float = 0.0,
        attack_type: str = "intercept_resend",
        sample_size: Optional[int] = None,
    ) -> QBERResult:
        """Full QBER analysis with abort logic.

        Args:
            alice_bits:   Alice's sifted key.
            bob_bits:     Bob's sifted key.
            channel_loss: Channel loss fraction [0, 1].
            attack_type:  Attack model for Eve info estimation.
            sample_size:  Optional subset size for QBER estimation.

        Returns:
            QBERResult with all metrics and security decision.
        """
        if sample_size is not None:
            check_alice = alice_bits[:sample_size]
            check_bob = bob_bits[:sample_size]
        else:
            check_alice = alice_bits
            check_bob = bob_bits

        checked_bits = len(check_alice)
        error_count = sum(1 for a, b in zip(check_alice, check_bob) if a != b)
        qber = (error_count / checked_bits * 100.0) if checked_bits > 0 else 0.0

        # Secure key rate: K = q * [1 - 2*H2(Q)]
        q_fraction = qber / 100.0
        h2 = self.binary_entropy(q_fraction)
        secure_key_rate = max(IDEAL_KEY_RATE_FRACTION * (1.0 - 2.0 * h2), 0.0)

        # Adjust for channel loss
        effective_rate = secure_key_rate * (1.0 - channel_loss)

        is_below = qber < QBER_THRESHOLD_PERCENT
        should_abort = qber >= QBER_THRESHOLD_PERCENT or channel_loss >= CHANNEL_LOSS_THRESHOLD

        eve_info = self.estimate_eve_information(qber, attack_type)

        return QBERResult(
            qber=qber,
            secure_key_rate=effective_rate,
            is_below_threshold=is_below,
            should_abort=should_abort,
            eve_information=eve_info,
            checked_bits=checked_bits,
            error_count=error_count,
        )


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    analyzer = QBERAnalyzer()

    # Simulate a clean channel
    alice = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0]
    bob_clean = alice.copy()
    bob_noisy = alice.copy()
    # Inject 3 errors out of 16 → 18.75% QBER
    for i in [2, 7, 11]:
        bob_noisy[i] ^= 1

    clean = analyzer.analyze(alice, bob_clean, attack_type="none")
    noisy = analyzer.analyze(alice, bob_noisy, attack_type="intercept_resend")

    print("=== Clean Channel ===")
    print(f"  QBER: {clean.qber:.2f}%  |  Key rate: {clean.secure_key_rate:.4f}")
    print(f"  Eve info: {clean.eve_information:.4f}  |  Abort: {clean.should_abort}")

    print("\n=== Noisy Channel (3 errors / 16) ===")
    print(f"  QBER: {noisy.qber:.2f}%  |  Key rate: {noisy.secure_key_rate:.4f}")
    print(f"  Eve info: {noisy.eve_information:.4f}  |  Abort: {noisy.should_abort}")
