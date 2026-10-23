"""Q-SHIELD Hybrid Protocol — Core Innovation of Q-GibberLink.

Combines Quantum Key Distribution (BB84) with Post-Quantum Cryptography
(Kyber768) under a trust-aware controller.  The controller monitors QBER
and channel loss in real time and automatically selects the security mode:

  - HYBRID:   When QBER < 11% and channel_loss < 0.6
              Final key = SHA3-256(PQC_key XOR QKD_key_hash)
              This provides defense-in-depth: an attacker must break BOTH
              quantum and post-quantum systems to recover the key.

  - PQC_ONLY: When QBER >= 11% (Eve is present on quantum channel) or
              channel_loss >= 0.6 (channel too lossy for QKD)
              Final key = Kyber768 encapsulated key
              QKD is abandoned; security rests entirely on PQC.

In both modes, is_secure=True (the key is usable), but HYBRID mode
provides strictly stronger security guarantees.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from core.quantum_sim import BB84Simulator
from core.qber_analyzer import QBERAnalyzer, QBERResult, QBER_THRESHOLD_PERCENT, CHANNEL_LOSS_THRESHOLD
from protocols.bb84 import BB84Protocol

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Kyber768 key size in bytes (shared secret after decapsulation)
KEM_SHARED_SECRET_BYTES = 32

# SHA3-256 output length
HASH_OUTPUT_BYTES = 32

# Final key length in bytes
FINAL_KEY_BYTES = 32


class ProtocolMode(Enum):
    """Security mode selected by the trust controller."""

    HYBRID = "HYBRID"
    PQC_ONLY = "PQC_ONLY"
    QKD_ONLY = "QKD_ONLY"  # Theoretical — not used in production


@dataclass
class HybridResult:
    """Result of the Q-SHIELD hybrid protocol.

    Attributes:
        final_key:        Final shared key as bytes.
        final_key_hex:    Hex representation of the final key.
        protocol_used:    Mode selected by the trust controller.
        qber:             Measured QBER percentage.
        channel_loss:     Channel loss fraction.
        qkd_key:          Raw QKD key (empty if PQC_ONLY).
        pqc_key:          PQC (Kyber768) key.
        qkd_key_hex:      Hex of QKD key.
        pqc_key_hex:      Hex of PQC key.
        is_secure:        Whether the final key is secure (always True
                          in hybrid or PQC-only mode).
        eve_information:  Estimated Eve information fraction.
        secure_key_rate:  Estimated secure key rate.
        trust_decision:   Human-readable explanation of the controller's decision.
        warnings:         List of warning messages.
    """

    final_key: bytes
    final_key_hex: str
    protocol_used: ProtocolMode
    qber: float
    channel_loss: float
    qkd_key: bytes
    pqc_key: bytes
    qkd_key_hex: str
    pqc_key_hex: str
    is_secure: bool
    eve_information: float
    secure_key_rate: float
    trust_decision: str
    warnings: List[str]


class QShieldHybrid:
    """Q-SHIELD Hybrid QKD + PQC protocol with trust-aware controller.

    This is the core innovation of Q-GibberLink.  It combines:
      1. BB84 QKD for information-theoretic security.
      2. Kyber768 PQC for computational security against quantum adversaries.
      3. A trust controller that monitors QBER and channel conditions.

    The final key is derived as:
      - HYBRID:   SHA3-256(PQC_key XOR SHA3-256(QKD_key))
      - PQC_ONLY: Kyber768 shared secret directly

    Example::

        proto = QShieldHybrid(num_qubits=200)
        result = proto.execute(attack_type="intercept_resend")
        print(f"Mode: {result.protocol_used}, Key: {result.final_key_hex[:16]}...")
    """

    def __init__(
        self,
        num_qubits: int = 128,
        channel_loss: float = 0.0,
        seed: Optional[int] = None,
    ) -> None:
        self.num_qubits = num_qubits
        self.channel_loss = channel_loss
        self.bb84 = BB84Protocol(
            num_qubits=num_qubits,
            channel_loss=channel_loss,
            seed=seed,
        )
        self.analyzer = QBERAnalyzer()
        self._kyber_available = self._check_kyber()

    # ------------------------------------------------------------------
    # PQC (Kyber768) key generation
    # ------------------------------------------------------------------

    def _check_kyber(self) -> bool:
        """Check whether the kyber-py library is available."""
        try:
            try:
                from kyber_py.kyber import Kyber768  # type: ignore
            except ImportError:
                from kyber_py import Kyber768  # type: ignore
            logger.info("kyber-py Kyber768 loaded successfully.")
            return True
        except ImportError:
            logger.warning(
                "kyber-py not available — using os.urandom as PQC placeholder. "
                "Install with: pip install kyber-py"
            )
            return False

    def _generate_pqc_key(self) -> bytes:
        """Generate a Kyber768 shared secret.

        If kyber-py is available, performs a full KEM encapsulation/
        decapsulation cycle.  Otherwise, generates a cryptographically
        secure random key as a placeholder.
        """
        if self._kyber_available:
            try:
                try:
                    from kyber_py.kyber import Kyber768  # type: ignore
                except ImportError:
                    from kyber_py import Kyber768  # type: ignore

                # Generate keypair
                public_key, secret_key = Kyber768.keygen()
                # Encapsulate: produces shared_secret and ciphertext
                if hasattr(Kyber768, "encapsulate"):
                    shared_secret, ciphertext = Kyber768.encapsulate(public_key)
                    recovered = Kyber768.decapsulate(secret_key, ciphertext)
                else:
                    shared_secret, ciphertext = Kyber768.encaps(public_key)
                    recovered = Kyber768.decaps(secret_key, ciphertext)

                # Verify correctness
                if shared_secret == recovered:
                    logger.info("Kyber768 KEM cycle verified successfully.")
                    return shared_secret[:KEM_SHARED_SECRET_BYTES]
                else:
                    logger.error("Kyber768 KEM mismatch — falling back to urandom.")
            except Exception as e:
                logger.error(f"Kyber768 error: {e} — falling back to urandom.")

        # Placeholder: cryptographically secure random key
        return os.urandom(KEM_SHARED_SECRET_BYTES)

    # ------------------------------------------------------------------
    # QKD key derivation
    # ------------------------------------------------------------------

    def _derive_qkd_key(self, sifted_bits: List[int]) -> bytes:
        """Derive a fixed-length key from sifted QKD bits via SHA3-256."""
        bit_string = "".join(str(b) for b in sifted_bits)
        return hashlib.sha3_256(bit_string.encode()).digest()

    # ------------------------------------------------------------------
    # Trust controller
    # ------------------------------------------------------------------

    def _trust_controller(
        self,
        qber: float,
        channel_loss: float,
    ) -> Tuple[ProtocolMode, str, List[str]]:
        """Decide which protocol mode to use based on channel conditions.

        Args:
            qber:         Measured QBER percentage.
            channel_loss: Channel loss fraction [0, 1].

        Returns:
            Tuple of (mode, decision_explanation, warnings).
        """
        warnings: List[str] = []

        if qber > QBER_THRESHOLD_PERCENT:
            mode = ProtocolMode.PQC_ONLY
            decision = (
                f"QBER {qber:.2f}% exceeds threshold {QBER_THRESHOLD_PERCENT}%. "
                f"Eavesdropper detected on quantum channel. "
                f"Aborting QKD — falling back to PQC-only (Kyber768)."
            )
            warnings.append(
                f"Quantum channel compromised: QBER={qber:.2f}% > {QBER_THRESHOLD_PERCENT}%"
            )
        elif channel_loss >= CHANNEL_LOSS_THRESHOLD:
            mode = ProtocolMode.PQC_ONLY
            decision = (
                f"Channel loss {channel_loss:.0%} exceeds threshold {CHANNEL_LOSS_THRESHOLD:.0%}. "
                f"Quantum channel too lossy for reliable QKD. "
                f"Falling back to PQC-only (Kyber768)."
            )
            warnings.append(
                f"Excessive channel loss: {channel_loss:.0%} >= {CHANNEL_LOSS_THRESHOLD:.0%}"
            )
        else:
            mode = ProtocolMode.HYBRID
            decision = (
                f"QBER {qber:.2f}% < {QBER_THRESHOLD_PERCENT}% and "
                f"loss {channel_loss:.0%} < {CHANNEL_LOSS_THRESHOLD:.0%}. "
                f"Quantum channel secure. Using HYBRID mode: "
                f"SHA3-256(PQC_key XOR SHA3-256(QKD_key))."
            )

        return mode, decision, warnings

    # ------------------------------------------------------------------
    # Final key derivation
    # ------------------------------------------------------------------

    def _derive_final_key(
        self,
        pqc_key: bytes,
        qkd_key: bytes,
        mode: ProtocolMode,
    ) -> bytes:
        """Derive the final shared key.

        HYBRID:   SHA3-256(PQC_key XOR SHA3-256(QKD_key))
        PQC_ONLY: PQC key directly (already 32 bytes)
        """
        if mode == ProtocolMode.HYBRID:
            # XOR PQC key with hashed QKD key
            qkd_hash = hashlib.sha3_256(qkd_key).digest()
            # XOR byte-by-byte (both are 32 bytes)
            xored = bytes(a ^ b for a, b in zip(pqc_key, qkd_hash))
            return hashlib.sha3_256(xored).digest()
        else:
            # PQC only — use the Kyber shared secret directly
            return hashlib.sha3_256(pqc_key).digest()

    # ------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------

    def execute(
        self,
        attack_type: str = "none",
        alice_bits: Optional[List[int]] = None,
        alice_basis: Optional[List[int]] = None,
        bob_basis: Optional[List[int]] = None,
        bob_results: Optional[List[int]] = None,
    ) -> HybridResult:
        """Execute the full Q-SHIELD hybrid protocol.

        Args:
            attack_type:  Attack model for Eve info estimation.
            alice_bits:   Override Alice's bits (for attack injection).
            alice_basis:  Override Alice's bases.
            bob_basis:    Override Bob's bases.
            bob_results:  Override Bob's measured bits.

        Returns:
            HybridResult with final key, mode, and full diagnostics.
        """
        # Step 1: Run BB84 QKD
        bb84_result = self.bb84.generate_key(
            alice_bits=alice_bits,
            alice_basis=alice_basis,
            bob_basis=bob_basis,
            bob_results=bob_results,
            attack_type=attack_type,
        )

        qber = bb84_result.qber_result.qber

        # Step 2: Generate PQC key (Kyber768)
        pqc_key = self._generate_pqc_key()

        # Step 3: Derive QKD key hash
        qkd_key = self._derive_qkd_key(bb84_result.sifted_key)

        # Step 4: Trust controller decides mode
        mode, decision, warnings = self._trust_controller(qber, self.channel_loss)

        # Step 5: Derive final key
        final_key = self._derive_final_key(pqc_key, qkd_key, mode)

        # Step 6: Gather metrics
        eve_info = bb84_result.qber_result.eve_information
        secure_rate = bb84_result.qber_result.secure_key_rate

        # PQC-only mode: Eve has no info on PQC key
        if mode == ProtocolMode.PQC_ONLY:
            eve_info = 0.0
            secure_rate = 1.0  # PQC provides full key

        is_secure = True  # Both HYBRID and PQC_ONLY produce secure keys

        return HybridResult(
            final_key=final_key,
            final_key_hex=final_key.hex(),
            protocol_used=mode,
            qber=qber,
            channel_loss=self.channel_loss,
            qkd_key=qkd_key,
            pqc_key=pqc_key,
            qkd_key_hex=qkd_key.hex(),
            pqc_key_hex=pqc_key.hex(),
            is_secure=is_secure,
            eve_information=eve_info,
            secure_key_rate=secure_rate,
            trust_decision=decision,
            warnings=warnings,
        )

    def execute_dict(
        self,
        attack_type: str = "none",
        alice_bits: Optional[List[int]] = None,
        alice_basis: Optional[List[int]] = None,
        bob_basis: Optional[List[int]] = None,
        bob_results: Optional[List[int]] = None,
    ) -> Dict:
        """Execute and return a plain dictionary (for dashboard/JSON)."""
        r = self.execute(
            attack_type=attack_type,
            alice_bits=alice_bits,
            alice_basis=alice_basis,
            bob_basis=bob_basis,
            bob_results=bob_results,
        )
        return {
            "qber": r.qber,
            "final_key": r.final_key_hex,
            "protocol_used": r.protocol_used.value,
            "is_secure": r.is_secure,
            "eve_information": r.eve_information,
            "secure_key_rate": r.secure_key_rate,
            "channel_loss": r.channel_loss,
            "qkd_key": r.qkd_key_hex,
            "pqc_key": r.pqc_key_hex,
            "trust_decision": r.trust_decision,
            "warnings": r.warnings,
        }


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("  Q-SHIELD Hybrid Protocol Demo")
    print("=" * 60)

    # Scenario 1: Clean channel → HYBRID
    print("\n--- Scenario 1: Clean Channel ---")
    proto = QShieldHybrid(num_qubits=100, channel_loss=0.0, seed=42)
    result = proto.execute(attack_type="none")
    print(f"  Mode      : {result.protocol_used.value}")
    print(f"  QBER      : {result.qber:.2f}%")
    print(f"  Eve info  : {result.eve_information:.4f}")
    print(f"  Key rate  : {result.secure_key_rate:.4f}")
    print(f"  Final key : {result.final_key_hex[:20]}...")
    print(f"  Decision  : {result.trust_decision[:80]}...")

    # Scenario 2: Under attack → PQC_ONLY
    print("\n--- Scenario 2: Under Attack (Intercept-Resend) ---")
    proto2 = QShieldHybrid(num_qubits=100, channel_loss=0.0, seed=42)
    # Inject high-QBER bits to simulate attack
    from attacks.intercept_resend import InterceptResendAttack
    attack = InterceptResendAttack(intercept_rate=1.0)
    alice_bits = [__import__('random').randint(0, 1) for _ in range(100)]
    alice_basis = [__import__('random').randint(0, 1) for _ in range(100)]
    bob_basis = [__import__('random').randint(0, 1) for _ in range(100)]
    bob_results, qber, eve_info = attack.launch(alice_bits, alice_basis, bob_basis)
    result2 = proto2.execute(attack_type="intercept_resend")
    print(f"  Mode      : {result2.protocol_used.value}")
    print(f"  QBER      : {result2.qber:.2f}%")
    print(f"  Eve info  : {result2.eve_information:.4f}")
    print(f"  Final key : {result2.final_key_hex[:20]}...")
    print(f"  Decision  : {result2.trust_decision[:80]}...")

    print("\n" + "=" * 60)
