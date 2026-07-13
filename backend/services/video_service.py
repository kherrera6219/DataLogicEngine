"""
Video Service - PRODUCTION VERSION
----------------------------------
Handles video analysis and frame extraction using OpenCV and Vision LLMs.
"""
import importlib
import logging
import os
import sys
import tempfile
from typing import Dict, Any, List
import base64
from flask import current_app, has_app_context
from werkzeug.local import LocalProxy

logger = logging.getLogger(__name__)


def _load_cv2():
    """Load OpenCV lazily so optional native dependencies do not break app startup."""
    preserved_modules = {name: sys.modules.get(name) for name in ("config", "utils")}
    try:
        return importlib.import_module("cv2")
    except Exception as exc:
        for module_name, preserved_module in preserved_modules.items():
            if preserved_module is None:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = preserved_module
        logger.warning("OpenCV is unavailable; video analysis features will be disabled", exc_info=exc)
        return None


CV2 = None

class VideoService:
    """
    Manages video processing pipelines using CV2 and Vision AI.
    """
    
    def __init__(self, llm_gateway=None):
        if llm_gateway:
            self.llm_gateway = llm_gateway
        else:
            # Lazy import to avoid circular dependency
            from backend.llm_gateway.gateway import LLMGateway
            self.llm_gateway = LLMGateway()
            
        logger.info("VideoService initialized (PRODUCTION MODE).")

    async def analyze_video(self, video_bytes: bytes) -> Dict[str, Any]:
        """
        Perform complete analysis of a video file by extracting keyframes 
        and sending them to a Vision LLM.
        """
        logger.info("Starting production video analysis...")
        
        # 1. Extract Frames
        frames = self.extract_frames_sync(video_bytes, interval_sec=10, max_frames=5)
        if not frames:
            return {"error": "Failed to extract frames from video"}
        
        # 2. Vision Analysis via Gateway
        try:
            # We use the existing LLM gateway if available, or fallback to direct OpenAI if needed
            # For this implementation, we'll assume a vision-capable model is used
            summary = await self._analyze_frames_with_llm(frames)
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            summary = "Error performing visual analysis."
            
        return {
            "duration_estimated": len(frames) * 10,
            "frame_count": len(frames),
            "summary": summary,
            "status": "completed",
            "metadata": {
                "engine": "OpenCV + VisionLLM",
                "extracted_frames": len(frames)
            }
        }

    def extract_frames_sync(self, video_bytes: bytes, interval_sec: int = 10, max_frames: int = 5) -> List[bytes]:
        """
        Extract keyframes from video bytes using OpenCV.
        """
        global CV2
        if CV2 is None:
            CV2 = _load_cv2()

        if CV2 is None:
            logger.warning("Video frame extraction requested but OpenCV is not available")
            return []

        frames_bytes = []
        
        # CV2 needs a file path, so we use a temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tfile:
            tfile.write(video_bytes)
            temp_path = tfile.name

        try:
            cap = CV2.VideoCapture(temp_path)
            fps = cap.get(CV2.CAP_PROP_FPS)
            if fps == 0:
                fps = 30 # Fallback
            
            frame_interval = int(fps * interval_sec)
            count = 0
            success, image = cap.read()
            
            while success and len(frames_bytes) < max_frames:
                if count % frame_interval == 0:
                    # Resize to stay within tool/LLM limits
                    image = CV2.resize(image, (640, 480))
                    # Encode to jpg
                    is_success, buffer = CV2.imencode(".jpg", image)
                    if is_success:
                        frames_bytes.append(buffer.tobytes())
                
                success, image = cap.read()
                count += 1
                
            cap.release()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        return frames_bytes

    async def _analyze_frames_with_llm(self, frames_bytes: List[bytes]) -> str:
        """
        Sends extracted frames to a vision model via the LLM Gateway.
        """
        if not self.llm_gateway:
            logger.warning("LLM Gateway not provided to VideoService, returning mock summary.")
            return f"Video Analysis: Found {len(frames_bytes)} frames. (Gateway not connected)"

        logger.info(f"Analyzing {len(frames_bytes)} frames with Vision LLM via Gateway...")
        
        # Format content for Vision API (OpenAI style)
        content = [
            {"type": "text", "text": "Analyze these sequence of frames from a video. Describe the key actions, objects, and any text visible. Focus on compliance and security risks if any."}
        ]
        
        for frame in frames_bytes:
            b64_frame = base64.b64encode(frame).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64_frame}"
                }
            })

        from backend.llm_gateway.gateway import GatewayRequest
        from backend.llm_gateway.model_defaults import OPENAI_LATEST_MODEL
        request = GatewayRequest(
            messages=[{"role": "user", "content": content}],
            model=OPENAI_LATEST_MODEL,  # current OpenAI model (gpt-5.5; multimodal/vision-capable)
            run_ukg_pipeline=False, # Direct vision call usually better than overlay for raw frames
            meta={"task": "video_analysis", "priority": "high"}
        )

        try:
            response = await self.llm_gateway.process(request)
            if response.ok:
                return response.content
            else:
                logger.error(f"Gateway video analysis failed: {response.error}")
                return f"Vision analysis error: {response.error}"
        except Exception as e:
            logger.error(f"Exception during gateway video analysis: {e}")
            return f"Vision analysis exception: {str(e)}"

_fallback_video_service: VideoService | None = None


def get_video_service() -> VideoService:
    """Return a video service owned by the active application."""
    if has_app_context():
        service = current_app.extensions.get("dle_video_service")
        if service is None:
            service = VideoService()
            current_app.extensions["dle_video_service"] = service
        return service
    global _fallback_video_service
    if _fallback_video_service is None:
        _fallback_video_service = VideoService()
    return _fallback_video_service


video_service = LocalProxy(get_video_service)
