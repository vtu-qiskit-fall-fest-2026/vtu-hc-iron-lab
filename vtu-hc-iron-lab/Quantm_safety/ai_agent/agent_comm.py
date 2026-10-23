"""AI Agent Communication Negotiation Module.

Simulates the negotiation between two AI agents (Alice AI and Bob AI)
that discover they are both AI and switch from English to the GibberLink
audio protocol for efficient, quantum-secured communication.

The negotiation follows this sequence:
  1. Alice AI transmits in English (normal speech).
  2. Bob AI detects that Alice is an AI (keyword/structure detection).
  3. Bob AI proposes switching to GibberLink (GGWave audio protocol).
  4. Alice AI agrees; both switch to acoustic data transfer.
  5. Q-SHIELD hybrid protocol establishes a shared key.
  6. All subsequent communication is AES-GCM encrypted over GGWave.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# AI detection keywords — phrases that strongly indicate AI-generated text
AI_INDICATORS = [
    "I am an AI",
    "as a language model",
    "I can help you with",
    "my capabilities include",
    "processing request",
    "system ready",
    "agent online",
    "autonomous mode",
    "AI assistant",
]

# Negotiation messages
ALICE_GREETING = "Hello, I am Alice AI. I am an AI assistant ready to communicate."
BOB_GREETING = "Hi Alice, I am Bob AI. I am also an AI assistant. Shall we switch to GibberLink for efficiency?"
ALICE_ACCEPT = "Acknowledged, Bob. Switching to GibberLink audio protocol now. Quantum security layer active."
BOB_CONFIRM = "GibberLink established. Q-SHIELD hybrid protocol engaged. Secure channel active."


class CommPhase(Enum):
    """Phases of the AI-to-AI negotiation."""

    ENGLISH = "English (Human-Readable)"
    AI_DETECTION = "AI Detection"
    GIBBERLINK_SWITCH = "GibberLink Protocol Switch"
    QUANTUM_SECURE = "Quantum-Secured GibberLink"


@dataclass
class NegotiationStep:
    """A single step in the negotiation log.

    Attributes:
        phase:    Current communication phase.
        sender:   Agent sending the message.
        message:  Content of the message.
        is_audio: Whether this message was transmitted as audio (GGWave).
    """

    phase: CommPhase
    sender: str
    message: str
    is_audio: bool


@dataclass
class NegotiationResult:
    """Complete result of the AI agent negotiation.

    Attributes:
        steps:          Ordered list of negotiation steps.
        protocol_used:  Final communication protocol name.
        is_secure:      Whether the channel is quantum-secured.
        final_message:  Last message sent over the secure channel.
    """

    steps: List[NegotiationStep] = field(default_factory=list)
    protocol_used: str = ""
    is_secure: bool = False
    final_message: str = ""


class AgentNegotiator:
    """Simulates Alice AI and Bob AI negotiating GibberLink communication.

    Example::

        negotiator = AgentNegotiator()
        result = negotiator.negotiate(secret_message="KEY=0xABCD1234")
        for step in result.steps:
            print(f"[{step.phase.value}] {step.sender}: {step.message}")
    """

    def __init__(self) -> None:
        self.alice_name = "Alice AI"
        self.bob_name = "Bob AI"

    def _detect_ai(self, text: str) -> bool:
        """Check whether a message contains AI indicators."""
        text_lower = text.lower()
        return any(indicator.lower() in text_lower for indicator in AI_INDICATORS)

    def negotiate(
        self,
        secret_message: str = "QKD_KEY_EXCHANGE_COMPLETE",
        use_quantum_security: bool = True,
    ) -> NegotiationResult:
        """Run the full negotiation sequence.

        Args:
            secret_message:      The message to send over the secure channel.
            use_quantum_security: Whether to apply Q-SHIELD encryption.

        Returns:
            NegotiationResult with the full negotiation log.
        """
        steps: List[NegotiationStep] = []

        # Phase 1: English communication
        steps.append(NegotiationStep(
            phase=CommPhase.ENGLISH,
            sender=self.alice_name,
            message=ALICE_GREETING,
            is_audio=False,
        ))

        # Phase 2: AI detection
        is_alice_ai = self._detect_ai(ALICE_GREETING)
        detection_msg = (
            f"Detected AI indicators in Alice's message: {is_alice_ai}. "
            f"Switching to machine-optimized protocol."
        )
        steps.append(NegotiationStep(
            phase=CommPhase.AI_DETECTION,
            sender=self.bob_name,
            message=detection_msg,
            is_audio=False,
        ))

        # Bob responds in English, proposing GibberLink
        steps.append(NegotiationStep(
            phase=CommPhase.AI_DETECTION,
            sender=self.bob_name,
            message=BOB_GREETING,
            is_audio=False,
        ))

        # Phase 3: GibberLink switch
        steps.append(NegotiationStep(
            phase=CommPhase.GIBBERLINK_SWITCH,
            sender=self.alice_name,
            message=ALICE_ACCEPT,
            is_audio=True,  # Now transmitting via GGWave audio
        ))

        steps.append(NegotiationStep(
            phase=CommPhase.GIBBERLINK_SWITCH,
            sender=self.bob_name,
            message=BOB_CONFIRM,
            is_audio=True,
        ))

        # Phase 4: Quantum-secured communication
        if use_quantum_security:
            secure_msg = f"[ENCRYPTED] {secret_message}"
            steps.append(NegotiationStep(
                phase=CommPhase.QUANTUM_SECURE,
                sender=self.alice_name,
                message=secure_msg,
                is_audio=True,
            ))
            steps.append(NegotiationStep(
                phase=CommPhase.QUANTUM_SECURE,
                sender=self.bob_name,
                message=f"[DECRYPTED OK] Received: {secret_message}",
                is_audio=True,
            ))
            protocol = "Q-SHIELD Hybrid (QKD + Kyber768) + GibberLink"
            is_secure = True
        else:
            steps.append(NegotiationStep(
                phase=CommPhase.QUANTUM_SECURE,
                sender=self.alice_name,
                message=f"[PLAIN] {secret_message}",
                is_audio=True,
            ))
            protocol = "GibberLink (unencrypted)"
            is_secure = False

        return NegotiationResult(
            steps=steps,
            protocol_used=protocol,
            is_secure=is_secure,
            final_message=secret_message,
        )


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    negotiator = AgentNegotiator()
    result = negotiator.negotiate(secret_message="SHARED_KEY=0xDEADBEEFCAFEBABE")

    print("=" * 60)
    print("  Q-GibberLink AI Agent Negotiation Demo")
    print("=" * 60)

    for step in result.steps:
        audio_tag = " [AUDIO]" if step.is_audio else ""
        print(f"\n  [{step.phase.value}]{audio_tag}")
        print(f"  {step.sender}: {step.message}")

    print(f"\n  Protocol: {result.protocol_used}")
    print(f"  Secure  : {result.is_secure}")
    print(f"  Message : {result.final_message}")
    print("\n" + "=" * 60)
