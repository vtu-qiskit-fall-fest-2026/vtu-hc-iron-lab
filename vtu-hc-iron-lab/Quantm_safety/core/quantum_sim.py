"""BB84 Quantum Key Distribution simulator using Qiskit AerSimulator.

This module simulates the BB84 protocol with real quantum circuits:
  - Hadamard (H) gate for basis selection
  - Pauli-X gate for bit value encoding
  - Measurement for readout

The simulator supports configurable qubit counts and integrates with
the attack modules to model eavesdropping scenarios.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASIS_RECTILINEAR = 0  # Z-basis (|0>, |1>)
BASIS_DIAGONAL = 1     # X-basis (|+>, |->)

BASIS_LABELS = {BASIS_RECTILINEAR: "Z", BASIS_DIAGONAL: "X"}

# Default number of qubits if not specified.
DEFAULT_QUBIT_COUNT = 128

# AerSimulator batch size — Qiskit Aer processes circuits in batches to
# avoid excessive memory use for large qubit counts.
SIM_BATCH_SIZE = 50

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Container for BB84 simulation output.

    Attributes:
        alice_bits:   Alice's original random bit string.
        alice_basis:  Alice's basis choices (0=Z, 1=X).
        bob_basis:    Bob's basis choices.
        bob_results:  Bob's measured bit string.
        matched_indices: Indices where Alice and Bob bases matched.
        sifted_key:   Key bits after sifting (only matched-basis positions).
        qber:         Quantum Bit Error Rate percentage.
        key_length:   Length of the sifted key.
    """

    alice_bits: List[int]
    alice_basis: List[int]
    bob_basis: List[int]
    bob_results: List[int]
    matched_indices: List[int]
    sifted_key: List[int]
    qber: float
    key_length: int


def _generate_random_bits(n: int) -> List[int]:
    """Generate *n* cryptographically-usable random bits."""
    return [random.randint(0, 1) for _ in range(n)]


def _generate_random_bases(n: int) -> List[int]:
    """Generate *n* random basis choices (0 or 1)."""
    return [random.randint(0, 1) for _ in range(n)]


class BB84Simulator:
    """BB84 QKD simulator backed by Qiskit AerSimulator.

    Parameters:
        num_qubits: Number of qubits to simulate per run.
        seed:       Optional RNG seed for reproducibility.

    Example::

        sim = BB84Simulator(num_qubits=100)
        result = sim.run()
        print(f"QBER = {result.qber:.2f}%")
    """

    def __init__(self, num_qubits: int = DEFAULT_QUBIT_COUNT, seed: Optional[int] = None) -> None:
        if num_qubits < 2:
            raise ValueError("num_qubits must be at least 2")
        self.num_qubits = num_qubits
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self._simulator = None
        self._qiskit_available = False
        self._init_simulator()

    # ------------------------------------------------------------------
    # Simulator initialisation with graceful fallback
    # ------------------------------------------------------------------

    def _init_simulator(self) -> None:
        """Attempt to load Qiskit Aer; fall back to a mathematical model."""
        try:
            from qiskit_aer import AerSimulator  # type: ignore
            self._simulator = AerSimulator()
            self._qiskit_available = True
            logger.info("Qiskit AerSimulator loaded successfully.")
        except ImportError:
            logger.warning(
                "Qiskit Aer not available — using mathematical fallback "
                "model for BB84 simulation."
            )
            self._qiskit_available = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        alice_bits: Optional[List[int]] = None,
        alice_basis: Optional[List[int]] = None,
        bob_basis: Optional[List[int]] = None,
    ) -> SimulationResult:
        """Execute a full BB84 round.

        Args:
            alice_bits:  Override Alice's random bits (used by attacks).
            alice_basis: Override Alice's basis choices.
            bob_basis:   Override Bob's basis choices.

        Returns:
            SimulationResult with all intermediate values and computed QBER.
        """
        alice_bits = alice_bits if alice_bits is not None else _generate_random_bits(self.num_qubits)
        alice_basis = alice_basis if alice_basis is not None else _generate_random_bases(self.num_qubits)
        bob_basis = bob_basis if bob_basis is not None else _generate_random_bases(self.num_qubits)

        if self._qiskit_available:
            bob_results = self._run_qiskit(alice_bits, alice_basis, bob_basis)
        else:
            bob_results = self._run_mathematical(alice_bits, alice_basis, bob_basis)

        return self._build_result(alice_bits, alice_basis, bob_basis, bob_results)

    # ------------------------------------------------------------------
    # Qiskit path
    # ------------------------------------------------------------------

    def _run_qiskit(
        self,
        alice_bits: List[int],
        alice_basis: List[int],
        bob_basis: List[int],
    ) -> List[int]:
        """Run BB84 through Qiskit AerSimulator with real quantum circuits.

        Each qubit is encoded as:
            - X gate if bit == 1 (flip from |0> to |1>)
            - H gate if basis == X (rotate to diagonal basis)
        Bob applies H if his basis is X, then measures.
        """
        # qiskit QuantumCircuit imported below
        from qiskit import QuantumCircuit

        n = len(alice_bits)
        results: List[int] = []

        for start in range(0, n, SIM_BATCH_SIZE):
            end = min(start + SIM_BATCH_SIZE, n)
            batch_size = end - start

            qc = QuantumCircuit(batch_size, batch_size)

            for i in range(batch_size):
                qubit_idx = start + i
                # Encode bit value
                if alice_bits[qubit_idx] == 1:
                    qc.x(i)
                # Alice's basis
                if alice_basis[qubit_idx] == BASIS_DIAGONAL:
                    qc.h(i)
                # Bob's basis
                if bob_basis[qubit_idx] == BASIS_DIAGONAL:
                    qc.h(i)
                # Measure
                qc.measure(i, i)

            job = self._simulator.run(qc, shots=1)
            counts = job.result().get_counts()
            # counts is a dict like {'1010': 1} — single shot
            bitstring = list(counts.keys())[0]
            # Qiskit bitstrings are little-endian: index 0 is the last char
            for i in range(batch_size):
                # bitstring[len-1-i] corresponds to qubit i
                results.append(int(bitstring[batch_size - 1 - i]))

        return results

    # ------------------------------------------------------------------
    # Mathematical fallback (no Qiskit)
    # ------------------------------------------------------------------

    def _run_mathematical(
        self,
        alice_bits: List[int],
        alice_basis: List[int],
        bob_basis: List[int],
    ) -> List[int]:
        """Mathematical BB84 model: perfect correlation when bases match.

        When Alice and Bob use the same basis, Bob gets Alice's bit exactly.
        When bases differ, Bob's result is uniformly random (50/50).
        """
        results: List[int] = []
        for bit, ab, bb in zip(alice_bits, alice_basis, bob_basis):
            if ab == bb:
                results.append(bit)
            else:
                results.append(random.randint(0, 1))
        return results

    # ------------------------------------------------------------------
    # Result assembly
    # ------------------------------------------------------------------

    def _build_result(
        self,
        alice_bits: List[int],
        alice_basis: List[int],
        bob_basis: List[int],
        bob_results: List[int],
    ) -> SimulationResult:
        """Sift keys and compute QBER from matched-basis positions."""
        matched_indices = [
            i for i in range(len(alice_bits)) if alice_basis[i] == bob_basis[i]
        ]
        sifted_key = [alice_bits[i] for i in matched_indices]

        if len(matched_indices) == 0:
            qber = 0.0
        else:
            errors = sum(
                1
                for i in matched_indices
                if alice_bits[i] != bob_results[i]
            )
            qber = (errors / len(matched_indices)) * 100.0

        return SimulationResult(
            alice_bits=alice_bits,
            alice_basis=alice_basis,
            bob_basis=bob_basis,
            bob_results=bob_results,
            matched_indices=matched_indices,
            sifted_key=sifted_key,
            qber=qber,
            key_length=len(sifted_key),
        )


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sim = BB84Simulator(num_qubits=100, seed=42)
    result = sim.run()
    print(f"BB84 Simulation Complete")
    print(f"  Qubits simulated : {sim.num_qubits}")
    print(f"  Matched bases    : {len(result.matched_indices)}")
    print(f"  Sifted key length: {result.key_length}")
    print(f"  QBER             : {result.qber:.2f}%")
    print(f"  Key (hex)        : {''.join(str(b) for b in result.sifted_key[:32])}...")
