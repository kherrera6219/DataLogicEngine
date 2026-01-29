"""
Audio Service - PRODUCTION VERSION
----------------------------------
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) operations using OpenAI.
"""
import logging
import os
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class AudioService:
    """
    Manages audio processing pipelines using production-grade LLM services.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("AudioService: OPENAI_API_KEY not found in environment.")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        logger.info("AudioService initialized (PRODUCTION MODE).")

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Convert speech to text (STT) using OpenAI Whisper.
        """
        if not self.client:
            logger.error("AudioService: OpenAI client not initialized.")
            return "[Error: Audio transcription service unavailable]"

        try:
            # Whisper requires a file-like object with a name
            from io import BytesIO
            audio_file = BytesIO(audio_bytes)
            audio_file.name = filename
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            
            logger.info(f"Successfully transcribed {len(audio_bytes)} bytes.")
            return transcript.text
        except Exception as e:
            logger.error(f"AudioService transcription failed: {e}")
            return f"[Error: {str(e)}]"

    async def synthesize(self, text: str, voice: str = "alloy") -> bytes:
        """
        Convert text to speech (TTS) using OpenAI TTS.
        """
        if not self.client:
            logger.error("AudioService: OpenAI client not initialized.")
            return b""

        try:
            logger.info(f"Synthesizing speech for text: {text[:50]}...")
            
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # response.content is the raw bytes
            return response.content
        except Exception as e:
            logger.error(f"AudioService synthesis failed: {e}")
            return b""

# Global Instance
audio_service = AudioService()
