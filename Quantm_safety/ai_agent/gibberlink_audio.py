"""GibberLink audio communication module for AI-to-AI data transfer.

Uses the GGWave library to encode/decode data as acoustic modem tones
(frequency-shift keying beeps).  Adds a quantum-secure layer that
AES-GCM encrypts data with a Q-SHIELD derived key before audio encoding.

If GGWave is not installed, falls back to a simulated audio representation
so the dashboard remains functional for demonstration.
"""

from __future__ import annotations

import logging
import os
import struct
import wave
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# AES-GCM parameters
AES_KEY_BYTES = 32       # 256-bit key
AES_NONCE_BYTES = 12     # 96-bit nonce (standard for GCM)
AES_TAG_BYTES = 16       # 128-bit authentication tag

# GGWave default parameters
GGWAVE_PROTOCOL = 1      # RX protocol index
GGWAVE_PAYLOAD_LENGTH = 16
GGWAVE_SAMPLE_RATE = 48000

# Fallback audio parameters
FALLBACK_DURATION_SEC = 2.0
FALLBACK_FREQUENCY = 1200  # Hz


class GibberLinkAudio:
    """GibberLink audio encoder/decoder with quantum-secure layer.

    Provides two modes:
      1. Plain:   encode_to_sound(data, file) -> decode_from_sound(file)
      2. Secure:  quantum_secure_encode(data, key, file)
                  -> quantum_secure_decode(key, file)

    The secure mode AES-GCM encrypts the data before GGWave encoding,
    ensuring confidentiality and integrity over the acoustic channel.

    Args:
        sample_rate: Audio sample rate in Hz (default 48000).

    Example::

        audio = GibberLinkAudio()
        audio.encode_to_sound("Hello Bob!", "output.wav")
        decoded = audio.decode_from_sound("output.wav")

        audio.quantum_secure_encode("Secret message", key_bytes, "secure.wav")
        plaintext = audio.quantum_secure_decode(key_bytes, "secure.wav")
    """

    def __init__(self, sample_rate: int = GGWAVE_SAMPLE_RATE) -> None:
        self.sample_rate = sample_rate
        self._ggwave_available = self._check_ggwave()
        self._crypto_available = self._check_crypto()

    # ------------------------------------------------------------------
    # Availability checks
    # ------------------------------------------------------------------

    def _check_ggwave(self) -> bool:
        """Check if the ggwave Python library is available."""
        try:
            import ggwave  # type: ignore
            logger.info("ggwave library loaded successfully.")
            return True
        except ImportError:
            logger.warning(
                "ggwave not available — using simulated audio fallback. "
                "Install with: pip install ggwave"
            )
            return False

    def _check_crypto(self) -> bool:
        """Check if pycryptodome is available for AES-GCM."""
        try:
            from Crypto.Cipher import AES  # type: ignore
            logger.info("pycryptodome AES loaded successfully.")
            return True
        except ImportError:
            logger.warning(
                "pycryptodome not available — using XOR cipher fallback. "
                "Install with: pip install pycryptodome"
            )
            return False

    # ------------------------------------------------------------------
    # Plain audio encode/decode
    # ------------------------------------------------------------------

    def encode_to_sound(self, data: str, filename: str) -> str:
        """Encode a string into a GGWave audio file.

        Args:
            data:     String to encode.
            filename: Output WAV file path.

        Returns:
            Path to the generated audio file.
        """
        if self._ggwave_available:
            return self._ggwave_encode(data, filename)
        else:
            return self._fallback_encode(data, filename)

    def decode_from_sound(self, filename: str) -> str:
        """Decode a GGWave audio file back to a string.

        Args:
            filename: WAV file path to decode.

        Returns:
            Decoded string.
        """
        if self._ggwave_available:
            return self._ggwave_decode(filename)
        else:
            return self._fallback_decode(filename)

    # ------------------------------------------------------------------
    # Quantum-secure encode/decode
    # ------------------------------------------------------------------

    def quantum_secure_encode(self, data: str, key: bytes, filename: str) -> str:
        """Encrypt data with AES-GCM and encode as GibberLink audio.

        The encryption uses the Q-SHIELD derived key (32 bytes).
        The output file contains the nonce + ciphertext + tag as audio.

        Args:
            data:     Plaintext string to encrypt and encode.
            key:      32-byte encryption key (from Q-SHIELD protocol).
            filename: Output WAV file path.

        Returns:
            Path to the generated audio file.
        """
        if len(key) < AES_KEY_BYTES:
            key = key.ljust(AES_KEY_BYTES, b'\x00')

        ciphertext = self._encrypt(data, key[:AES_KEY_BYTES])
        # Encode the ciphertext bytes as hex string for audio transport
        hex_payload = ciphertext.hex()
        return self.encode_to_sound(hex_payload, filename)

    def quantum_secure_decode(self, key: bytes, filename: str) -> Tuple[str, bool]:
        """Decode audio and decrypt with AES-GCM.

        Args:
            key:      32-byte decryption key.
            filename: WAV file path to decode.

        Returns:
            Tuple of (plaintext, is_secure).  If decryption fails (wrong
            key or tampered data), returns ("<gibberish>", False).
        """
        if len(key) < AES_KEY_BYTES:
            key = key.ljust(AES_KEY_BYTES, b'\x00')

        hex_payload = self.decode_from_sound(filename)
        try:
            ciphertext = bytes.fromhex(hex_payload)
        except ValueError:
            return "<gibberish: invalid audio payload>", False

        return self._decrypt(ciphertext, key[:AES_KEY_BYTES])

    # ------------------------------------------------------------------
    # Encryption / Decryption
    # ------------------------------------------------------------------

    def _encrypt(self, plaintext: str, key: bytes) -> bytes:
        """Encrypt plaintext with AES-GCM or XOR fallback."""
        if self._crypto_available:
            from Crypto.Cipher import AES  # type: ignore
            nonce = os.urandom(AES_NONCE_BYTES)
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
            return nonce + tag + ciphertext
        else:
            # XOR fallback (NOT secure — demo only)
            data = plaintext.encode('utf-8')
            return bytes(d ^ key[i % len(key)] for i, d in enumerate(data))

    def _decrypt(self, data: bytes, key: bytes) -> Tuple[str, bool]:
        """Decrypt AES-GCM ciphertext or XOR fallback."""
        if self._crypto_available:
            from Crypto.Cipher import AES  # type: ignore
            try:
                nonce = data[:AES_NONCE_BYTES]
                tag = data[AES_NONCE_BYTES:AES_NONCE_BYTES + AES_TAG_BYTES]
                ciphertext = data[AES_NONCE_BYTES + AES_TAG_BYTES:]
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                plaintext = cipher.decrypt_and_verify(ciphertext, tag)
                return plaintext.decode('utf-8'), True
            except (ValueError, KeyError):
                return "<gibberish: decryption failed — wrong key or tampered>", False
        else:
            # XOR fallback
            try:
                decrypted = bytes(d ^ key[i % len(key)] for i, d in enumerate(data))
                return decrypted.decode('utf-8'), True
            except Exception:
                return "<gibberish: decryption failed>", False

    # ------------------------------------------------------------------
    # GGWave implementation
    # ------------------------------------------------------------------

    def _ggwave_encode(self, data: str, filename: str) -> str:
        """Encode using the ggwave library."""
        import ggwave  # type: import ggwave (type: ignore)
        import numpy as np

        instance = ggwave.init(
            sampleRate=self.sample_rate,
            protocol=GGWAVE_PROTOCOL,
            payloadLength=GGWAVE_PAYLOAD_LENGTH,
        )
        waveform = ggwave.encode(data, protocol=GGWAVE_PROTOCOL, payloadLength=GGWAVE_PAYLOAD_LENGTH)
        ggwave.free(instance)

        # Convert to numpy array and save as WAV
        samples = np.frombuffer(waveform, dtype=np.int8).astype(np.int16)
        self._save_wav(filename, samples, self.sample_rate)
        return filename

    def _ggwave_decode(self, filename: str) -> str:
        """Decode using the ggwave library."""
        import ggwave  # type: ignore
        import numpy as np

        samples, sr = self._load_wav(filename)
        instance = ggwave.init(
            sampleRate=sr,
            protocol=GGWAVE_PROTOCOL,
            payloadLength=GGWAVE_PAYLOAD_LENGTH,
        )
        # ggwave.decode expects raw bytes
        raw = samples.astype(np.int8).tobytes()
        result = ggwave.decode(instance, raw)
        ggwave.free(instance)

        if result is not None:
            return result.decode('utf-8', errors='replace')
        return ""

    # ------------------------------------------------------------------
    # Fallback (no ggwave) — simulate audio with tones
    # ------------------------------------------------------------------

    def _fallback_encode(self, data: str, filename: str) -> str:
        """Simulate audio encoding with simple frequency tones."""
        import numpy as np

        # Each character -> a short tone at a frequency derived from its ASCII value
        char_duration = FALLBACK_DURATION_SEC / max(len(data), 1)
        total_samples = int(self.sample_rate * FALLBACK_DURATION_SEC)
        samples = np.zeros(total_samples, dtype=np.int16)

        for i, char in enumerate(data[:100]):  # Cap at 100 chars
            freq = FALLBACK_FREQUENCY + ord(char) * 10
            start = int(i * char_duration * self.sample_rate)
            end = min(start + int(char_duration * self.sample_rate), total_samples)
            t = np.arange(end - start) / self.sample_rate
            samples[start:end] = (np.sin(2 * np.pi * freq * t) * 16000).astype(np.int16)

        self._save_wav(filename, samples, self.sample_rate)
        sidecar = filename.replace('.wav', '.payload')
        with open(sidecar, 'w', encoding='utf-8') as sf:
            sf.write(data)
        logger.info(f"Fallback audio encoded {len(data)} chars -> {filename}")
        return filename

    def _fallback_decode(self, filename: str) -> str:
        """Simulate audio decoding — reads back the stored payload.

        In fallback mode, we store the payload in a sidecar file alongside
        the WAV so decode can recover it (simulating successful audio decode).
        """
        sidecar = filename.replace('.wav', '.payload')
        if os.path.exists(sidecar):
            with open(sidecar, 'r') as f:
                return f.read()
        return ""

    # ------------------------------------------------------------------
    # WAV utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _save_wav(filename: str, samples, sample_rate: int) -> None:
        """Save a numpy array as a 16-bit PCM WAV file."""
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(samples.tobytes())

    @staticmethod
    def _load_wav(filename: str) -> Tuple[any, int]:
        """Load a WAV file into a numpy array."""
        import numpy as np

        with wave.open(filename, 'rb') as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sample_width == 2:
            samples = np.frombuffer(raw, dtype=np.int16)
        elif sample_width == 1:
            samples = np.frombuffer(raw, dtype=np.int8).astype(np.int16) * 256
        else:
            samples = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)

        if n_channels > 1:
            samples = samples[::n_channels]

        return samples, framerate


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    audio = GibberLinkAudio()

    # Plain mode
    print("=== Plain GibberLink ===")
    audio.encode_to_sound("HELLO_BOB_AI", "demo_plain.wav")
    decoded = audio.decode_from_sound("demo_plain.wav")
    print(f"  Encoded -> demo_plain.wav")
    print(f"  Decoded: '{decoded}'")

    # Secure mode
    print("\n=== Quantum-Secure GibberLink ===")
    key = os.urandom(32)
    audio.quantum_secure_encode("TOP_SECRET_KEY_12345", key, "demo_secure.wav")
    plaintext, secure = audio.quantum_secure_decode(key, "demo_secure.wav")
    print(f"  Encrypted -> demo_secure.wav")
    print(f"  Decrypted: '{plaintext}' (secure: {secure})")

    # Wrong key
    wrong_key = os.urandom(32)
    bad_text, bad_secure = audio.quantum_secure_decode(wrong_key, "demo_secure.wav")
    print(f"  Wrong key -> '{bad_text[:40]}' (secure: {bad_secure})")
