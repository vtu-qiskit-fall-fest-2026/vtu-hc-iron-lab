"""BB84 Quantum Key Distribution protocol.

Pure BB84 implementation using the BB84Simulator for quantum circuit
execution, with integrated QBER analysis and key sifting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from core.quantum_sim import BB84Simulator, SimulationResult
from core.qber_analyzer import QBERAnalyzer, QBERResult

logger = logging.getLogger(__name__)

# Default parameters
DEFAULT_QUBITS = 128
DEFAULT_CHANNEL_LOSS = 0.0


@dataclass
class BB84KeyResult:
    """Result of a BB84 key generation round.

    Attributes:
        simulation:     Raw BB84 simulation data.
        qber_result:    QBER analysis result.
        sifted_key:     Final sifted key bits.
        key_hex:        Hex representation of the sifted key.
        is_secure:      Whether the key is secure (QBER below threshold).
    """

    simulation: SimulationResult
    qber_result: QBERResult
    sifted_key: List[int]
    key_hex: str
    is_secure: bool


class BB84Protocol:
    """High-level BB84 protocol wrapper.

    Combines quantum simulation, sifting, and QBER analysis into a
    single ``generate_key`` call.

    Example::

        proto = BB84Protocol(num_qubits=200)
        result = proto.generate_key()
        print(f"Key secure: {result.is_secure}, QBER: {result.qber_result.qber:.2f}%")
    """

    def __init__(
        self,
        num_qubits: int = DEFAULT_QUBITS,
        channel_loss: float = DEFAULT_CHANNEL_LOSS,
        seed: Optional[int] = None,
    ) -> None:
        self.num_qubits = num_qubits
        self.channel_loss = channel_loss
        self.seed = seed
        self.simulator = BB84Simulator(num_qubits=num_qubits, seed=seed)
        self.analyzer = QBERAnalyzer()

    def generate_key(
        self,
        alice_bits: Optional[List[int]] = None,
        alice_basis: Optional[List[int]] = None,
        bob_basis: Optional[List[int]] = None,
        bob_results: Optional[List[int]] = None,
        attack_type: str = "none",
    ) -> BB84KeyResult:
        """Execute a full BB84 key generation round.

        Args:
            alice_bits:  Override Alice's bits (used by attack modules).
            alice_basis: Override Alice's bases.
            bob_basis:   Override Bob's bases.
            bob_results: Override Bob's measurement results.
            attack_type: Attack model name for simulation and Eve info estimation.

        Returns:
            BB84KeyResult with key, QBER, and security assessment.
        """
        sim_result = self.simulator.run(
            alice_bits=alice_bits,
            alice_basis=alice_basis,
            bob_basis=bob_basis,
        )

        final_bob_results = bob_results if bob_results is not None else list(sim_result.bob_results)

        if bob_results is None and attack_type and attack_type != "none":
            if attack_type == "intercept_resend":
                from attacks.intercept_resend import InterceptResendAttack
                attack = InterceptResendAttack(intercept_rate=1.0, seed=self.seed)
                final_bob_results, _, _ = attack.launch(
                    sim_result.alice_bits, sim_result.alice_basis, sim_result.bob_basis
                )
            elif attack_type == "pns":
                from attacks.pns_attack import PNSAttack
                attack = PNSAttack(seed=self.seed)
                final_bob_results, _, _ = attack.launch(
                    sim_result.alice_bits, sim_result.alice_basis, sim_result.bob_basis
                )
            elif attack_type == "detector_blinding":
                from attacks.detector_blinding import DetectorBlindingAttack
                attack = DetectorBlindingAttack(seed=self.seed)
                final_bob_results, _, _ = attack.launch(
                    sim_result.alice_bits, sim_result.alice_basis, sim_result.bob_basis
                )

        sim_result.bob_results = final_bob_results

        qber_result = self.analyzer.analyze(
            alice_bits=sim_result.sifted_key,
            bob_bits=[final_bob_results[i] for i in sim_result.matched_indices],
            channel_loss=self.channel_loss,
            attack_type=attack_type,
        )
        sim_result.qber = qber_result.qber

        # Convert sifted key to hex
        key_hex = self._bits_to_hex(sim_result.sifted_key)

        is_secure = qber_result.is_below_threshold and not qber_result.should_abort

        return BB84KeyResult(
            simulation=sim_result,
            qber_result=qber_result,
            sifted_key=sim_result.sifted_key,
            key_hex=key_hex,
            is_secure=is_secure,
        )

    @staticmethod
    def _bits_to_hex(bits: List[int]) -> str:
        """Convert a list of bits to a hex string."""
        if not bits:
            return "0x00"
        # Pad to multiple of 8
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
    proto = BB84Protocol(num_qubits=100, seed=42)
    result = proto.generate_key()
    print(f"BB84 Protocol Result")
    print(f"  QBER        : {result.qber_result.qber:.2f}%")
    print(f"  Key rate    : {result.qber_result.secure_key_rate:.4f}")
    print(f"  Eve info    : {result.qber_result.eve_information:.4f}")
    print(f"  Secure      : {result.is_secure}")
    print(f"  Key (hex)   : {result.key_hex[:20]}...")
