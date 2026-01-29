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
        Convert speech to text (STT) using 3-Layer Failover.
        Layer 1: OpenAI Whisper (Primary)
        Layer 2: Google Gemini Flash (Native Audio Support)
        Layer 3: Error/Mock
        """
        errors = []
        
        # --- Layer 1: OpenAI Whisper ---
        try:
            if not self.client:
                # Try lazy init
                self.api_key = os.getenv("OPENAI_API_KEY")
                if self.api_key:
                    self.client = OpenAI(api_key=self.api_key)
            
            if self.client:
                from io import BytesIO
                audio_file = BytesIO(audio_bytes)
                audio_file.name = filename
                
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                logger.info(f"AudioService: OpenAI Transcription successful.")
                return transcript.text
            else:
                errors.append("OpenAI client not initialized")
        except Exception as e:
            logger.warning(f"AudioService: OpenAI Whisper failed: {e}")
            errors.append(f"OpenAI: {str(e)}")

        # --- Layer 2: Google Gemini (Native Audio) ---
        try:
            google_key = os.getenv("GOOGLE_API_KEY")
            if google_key:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=google_key)
                
                # Gemini 2.0 Flash or 1.5 Flash supports native audio
                # Using 1.5 Flash as stable fallback for multimodal
                model_id = 'gemini-1.5-flash'
                
                logger.info("AudioService: Attempting Google Gemini failover for audio...")
                
                response = client.models.generate_content(
                    model=model_id,
                    contents=[
                        "Transcribe this audio file exactly.",
                        types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3")
                    ]
                )
                
                if response.text:
                    logger.info("AudioService: Google Gemini transcription successful.")
                    return response.text
            else:
                errors.append("Google API key not found")
        except Exception as e:
            logger.warning(f"AudioService: Google Gemini failed: {e}")
            errors.append(f"Google: {str(e)}")

        # --- Layer 3: Failure ---
        logger.error(f"AudioService: All transcription layers failed. Errors: {errors}")
        return f"[Error: Audio transcription unavailable. Details: {'; '.join(errors)}]"

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
