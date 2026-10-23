"""Tests for QBER analysis, BB84 protocol, and Q-SHIELD hybrid protocol.

Run with:
    python -m pytest tests/test_qber.py -v
or:
    python tests/test_qber.py
"""

from __future__ import annotations

import logging
import os
import sys
import unittest

# Ensure package root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qber_analyzer import QBERAnalyzer, QBERResult, QBER_THRESHOLD_PERCENT, CHANNEL_LOSS_THRESHOLD
from core.quantum_sim import BB84Simulator
from protocols.bb84 import BB84Protocol
from protocols.qshield_hybrid import QShieldHybrid, ProtocolMode
from attacks.intercept_resend import InterceptResendAttack
from attacks.pns_attack import PNSAttack
from attacks.detector_blinding import DetectorBlindingAttack

logging.basicConfig(level=logging.INFO)


class TestQBERAnalyzer(unittest.TestCase):
    """Tests for the QBER analyzer."""

    def setUp(self):
        self.analyzer = QBERAnalyzer()

    def test_binary_entropy_edges(self):
        """Binary entropy at 0 and 1 should be 0."""
        self.assertEqual(self.analyzer.binary_entropy(0.0), 0.0)
        self.assertEqual(self.analyzer.binary_entropy(1.0), 0.0)

    def test_binary_entropy_half(self):
        """H2(0.5) = 1.0 — maximum uncertainty."""
        self.assertAlmostEqual(self.analyzer.binary_entropy(0.5), 1.0, places=6)

    def test_qber_clean_channel(self):
        """QBER should be 0% when Alice and Bob have identical bits."""
        alice = [1, 0, 1, 1, 0, 1, 0, 0]
        bob = alice.copy()
        qber = self.analyzer.compute_qber(alice, bob)
        self.assertAlmostEqual(qber, 0.0, places=2)

    def test_qber_full_error(self):
        """QBER should be 100% when all bits differ."""
        alice = [1, 0, 1, 1, 0, 1, 0, 0]
        bob = [0, 1, 0, 0, 1, 0, 1, 1]
        qber = self.analyzer.compute_qber(alice, bob)
        self.assertAlmostEqual(qber, 100.0, places=2)

    def test_qber_partial_error(self):
        """QBER should be 25% when 2 of 8 bits differ."""
        alice = [1, 0, 1, 1, 0, 1, 0, 0]
        bob =   [1, 0, 0, 1, 1, 1, 0, 0]  # positions 2 and 4 differ
        qber = self.analyzer.compute_qber(alice, bob)
        self.assertAlmostEqual(qber, 25.0, places=2)

    def test_abort_threshold(self):
        """Should abort when QBER > 11%."""
        alice = [1] * 20
        bob = [1] * 17 + [0] * 3  # 3/20 = 15% QBER
        result = self.analyzer.analyze(alice, bob, attack_type="intercept_resend")
        self.assertTrue(result.should_abort)
        self.assertFalse(result.is_below_threshold)

    def test_no_abort_below_threshold(self):
        """Should NOT abort when QBER < 11%."""
        alice = [1] * 100
        bob = [1] * 99 + [0] * 1  # 1% QBER
        result = self.analyzer.analyze(alice, bob, attack_type="none")
        self.assertFalse(result.should_abort)
        self.assertTrue(result.is_below_threshold)

    def test_channel_loss_abort(self):
        """Should abort when channel loss >= 60%."""
        alice = [1] * 50
        bob = alice.copy()
        result = self.analyzer.analyze(alice, bob, channel_loss=0.7)
        self.assertTrue(result.should_abort)

    def test_eve_info_intercept_resend(self):
        """Eve info should be ~2*QBER for intercept-resend."""
        alice = [1] * 50
        bob = [1] * 43 + [0] * 7  # 14% QBER
        result = self.analyzer.analyze(alice, bob, attack_type="intercept_resend")
        self.assertAlmostEqual(result.eve_information, 0.28, places=1)

    def test_eve_info_detector_blinding(self):
        """Eve info should be 1.0 for detector blinding."""
        alice = [1] * 50
        bob = alice.copy()
        result = self.analyzer.analyze(alice, bob, attack_type="detector_blinding")
        self.assertEqual(result.eve_information, 1.0)


class TestBB84Simulator(unittest.TestCase):
    """Tests for the BB84 quantum simulator."""

    def test_simulation_returns_correct_length(self):
        """Simulation should return results for all qubits."""
        sim = BB84Simulator(num_qubits=50, seed=42)
        result = sim.run()
        self.assertEqual(len(result.alice_bits), 50)
        self.assertEqual(len(result.bob_results), 50)

    def test_sifted_key_subset(self):
        """Sifted key should only contain matched-basis bits."""
        sim = BB84Simulator(num_qubits=50, seed=42)
        result = sim.run()
        self.assertEqual(len(result.sifted_key), len(result.matched_indices))

    def test_qber_zero_without_attack(self):
        """Without an attack, QBER should be near 0% (mathematical model)."""
        sim = BB84Simulator(num_qubits=100, seed=42)
        result = sim.run()
        # Mathematical model: 0% QBER without noise
        # Qiskit: small quantum noise possible
        self.assertLess(result.qber, 5.0)

    def test_invalid_qubit_count(self):
        """Should raise ValueError for num_qubits < 2."""
        with self.assertRaises(ValueError):
            BB84Simulator(num_qubits=0)


class TestBB84Protocol(unittest.TestCase):
    """Tests for the BB84 protocol wrapper."""

    def test_key_generation(self):
        """Should generate a non-empty key."""
        proto = BB84Protocol(num_qubits=50, seed=42)
        result = proto.generate_key()
        self.assertGreater(len(result.sifted_key), 0)
        self.assertTrue(result.key_hex.startswith("0x"))

    def test_security_flag(self):
        """is_secure should reflect QBER threshold."""
        proto = BB84Protocol(num_qubits=100, seed=42)
        result = proto.generate_key(attack_type="none")
        # Clean channel → secure
        self.assertTrue(result.is_secure)


class TestInterceptResendAttack(unittest.TestCase):
    """Tests for the intercept-resend attack."""

    def test_full_intercept_raises_qber(self):
        """Full interception should raise QBER above 11%."""
        import random
        random.seed(42)
        n = 500
        alice_bits = [random.randint(0, 1) for _ in range(n)]
        alice_basis = [random.randint(0, 1) for _ in range(n)]
        bob_basis = [random.randint(0, 1) for _ in range(n)]

        attack = InterceptResendAttack(intercept_rate=1.0, seed=42)
        _, qber, _ = attack.launch(alice_bits, alice_basis, bob_basis)
        self.assertGreater(qber, QBER_THRESHOLD_PERCENT)

    def test_zero_intercept_no_error(self):
        """Zero interception should result in near-zero QBER."""
        import random
        random.seed(42)
        n = 200
        alice_bits = [random.randint(0, 1) for _ in range(n)]
        alice_basis = [random.randint(0, 1) for _ in range(n)]
        bob_basis = [random.randint(0, 1) for _ in range(n)]

        attack = InterceptResendAttack(intercept_rate=0.0, seed=42)
        _, qber, _ = attack.launch(alice_bits, alice_basis, bob_basis)
        self.assertLess(qber, 5.0)

    def test_invalid_intercept_rate(self):
        """Should reject intercept_rate outside [0, 1]."""
        with self.assertRaises(ValueError):
            InterceptResendAttack(intercept_rate=1.5)


class TestPNSAttack(unittest.TestCase):
    """Tests for the PNS attack."""

    def test_low_qber_high_info(self):
        """PNS should have low QBER but significant Eve info."""
        import random
        random.seed(42)
        n = 500
        alice_bits = [random.randint(0, 1) for _ in range(n)]
        alice_basis = [random.randint(0, 1) for _ in range(n)]
        bob_basis = [random.randint(0, 1) for _ in range(n)]

        attack = PNSAttack(seed=42)
        _, qber, eve_info = attack.launch(alice_bits, alice_basis, bob_basis)
        # QBER should be low (stealthy)
        self.assertLess(qber, QBER_THRESHOLD_PERCENT)
        # But Eve should have meaningful info
        self.assertGreater(eve_info, 0.0)


class TestDetectorBlindingAttack(unittest.TestCase):
    """Tests for the detector blinding attack."""

    def test_zero_qber_full_compromise(self):
        """Detector blinding: 0% QBER but Eve knows everything."""
        import random
        random.seed(42)
        n = 200
        alice_bits = [random.randint(0, 1) for _ in range(n)]
        alice_basis = [random.randint(0, 1) for _ in range(n)]
        bob_basis = [random.randint(0, 1) for _ in range(n)]

        attack = DetectorBlindingAttack(intercept_rate=1.0, seed=42)
        _, qber, eve_info = attack.launch(alice_bits, alice_basis, bob_basis)
        self.assertAlmostEqual(qber, 0.0, places=1)
        self.assertAlmostEqual(eve_info, 1.0, places=2)


class TestQShieldHybrid(unittest.TestCase):
    """Tests for the Q-SHIELD hybrid protocol."""

    def test_hybrid_mode_clean_channel(self):
        """Clean channel should use HYBRID mode."""
        proto = QShieldHybrid(num_qubits=100, channel_loss=0.0, seed=42)
        result = proto.execute(attack_type="none")
        self.assertEqual(result.protocol_used, ProtocolMode.HYBRID)
        self.assertTrue(result.is_secure)

    def test_pqc_only_on_high_qber(self):
        """High QBER should trigger PQC_ONLY fallback."""
        proto = QShieldHybrid(num_qubits=100, channel_loss=0.0, seed=42)
        # Inject attack to raise QBER
        import random
        random.seed(42)
        n = 100
        alice_bits = [random.randint(0, 1) for _ in range(n)]
        alice_basis = [random.randint(0, 1) for _ in range(n)]
        bob_basis = [random.randint(0, 1) for _ in range(n)]

        attack = InterceptResendAttack(intercept_rate=1.0, seed=42)
        bob_results, _, _ = attack.launch(alice_bits, alice_basis, bob_basis)

        result = proto.execute(attack_type="intercept_resend")
        self.assertEqual(result.protocol_used, ProtocolMode.PQC_ONLY)
        self.assertTrue(result.is_secure)  # Still secure via PQC

    def test_pqc_only_on_high_loss(self):
        """High channel loss should trigger PQC_ONLY."""
        proto = QShieldHybrid(num_qubits=100, channel_loss=0.7, seed=42)
        result = proto.execute(attack_type="none")
        self.assertEqual(result.protocol_used, ProtocolMode.PQC_ONLY)

    def test_final_key_is_32_bytes(self):
        """Final key should be 32 bytes (SHA3-256 output)."""
        proto = QShieldHybrid(num_qubits=100, seed=42)
        result = proto.execute()
        self.assertEqual(len(result.final_key), 32)

    def test_final_key_hex_format(self):
        """Final key hex should be 64 characters (32 bytes = 64 hex chars)."""
        proto = QShieldHybrid(num_qubits=50, seed=42)
        result = proto.execute()
        self.assertEqual(len(result.final_key_hex), 64)

    def test_dict_output(self):
        """execute_dict should return a plain dict with expected keys."""
        proto = QShieldHybrid(num_qubits=50, seed=42)
        d = proto.execute_dict()
        self.assertIn("qber", d)
        self.assertIn("final_key", d)
        self.assertIn("protocol_used", d)
        self.assertIn("is_secure", d)
        self.assertIn("trust_decision", d)

    def test_hybrid_key_differs_from_pqc_only(self):
        """HYBRID key should differ from PQC_ONLY key (different derivation)."""
        proto_clean = QShieldHybrid(num_qubits=100, channel_loss=0.0, seed=42)
        result_clean = proto_clean.execute()

        proto_lossy = QShieldHybrid(num_qubits=100, channel_loss=0.8, seed=42)
        result_lossy = proto_lossy.execute()

        # Different modes → different key derivation
        if result_clean.protocol_used != result_lossy.protocol_used:
            self.assertNotEqual(result_clean.final_key_hex, result_lossy.final_key_hex)


if __name__ == "__main__":
    unittest.main(verbosity=2)
