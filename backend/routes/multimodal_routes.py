"""
Multimodal API Routes - PRODUCTION VERSION
------------------------------------------
Exposes Audio, Video, and Document processing capabilities.
"""
import logging
from flask import Blueprint, request, jsonify
from backend.auth.api_decorators import api_login_required
from backend.services.audio_service import audio_service
from backend.services.video_service import video_service
from backend.services.document_processor import document_processor

multimodal_bp = Blueprint('multimodal_api', __name__, url_prefix='/api/v1/multimodal')
logger = logging.getLogger(__name__)

@multimodal_bp.route('/audio/transcribe', methods=['POST'])
@api_login_required
async def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    audio_file = request.files['file']
    audio_bytes = audio_file.read()
    
    try:
        text = await audio_service.transcribe(audio_bytes, filename=audio_file.filename)
        return jsonify({"success": True, "text": text})
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return jsonify({"error": str(e)}), 500

@multimodal_bp.route('/audio/synthesize', methods=['POST'])
@api_login_required
async def synthesize_speech():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        audio_bytes = await audio_service.synthesize(data['text'], voice=data.get('voice', 'alloy'))
        # In a real app, you might save to cloud storage and return a URL
        # For now, we return a success indicator
        return jsonify({"success": True, "message": "Speech synthesized successfully", "size": len(audio_bytes)})
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return jsonify({"error": str(e)}), 500

@multimodal_bp.route('/video/analyze', methods=['POST'])
@api_login_required
async def analyze_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    video_file = request.files['file']
    video_bytes = video_file.read()
    
    try:
        analysis = await video_service.analyze_video(video_bytes)
        return jsonify({"success": True, "analysis": analysis})
    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        return jsonify({"error": str(e)}), 500

@multimodal_bp.route('/document/process', methods=['POST'])
@api_login_required
def process_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    doc_file = request.files['file']
    doc_bytes = doc_file.read()
    mime_type = doc_file.content_type
    
    try:
        result = document_processor.process_file(doc_bytes, doc_file.filename, mime_type)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        return jsonify({"error": str(e)}), 500
