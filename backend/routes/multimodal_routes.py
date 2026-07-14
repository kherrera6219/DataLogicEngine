"""
Multimodal API Routes - PRODUCTION VERSION
------------------------------------------
Exposes Audio, Video, and Document processing capabilities.
"""
import asyncio
import logging
from dataclasses import dataclass
from flask import Blueprint, request, jsonify
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from backend.auth.api_decorators import api_login_required
from backend.services.audio_service import AudioCapabilityUnavailable, audio_service
from backend.services.video_service import video_service
from backend.services.document_processor import document_processor
from backend.utils.error_normalization import normalize_public_error_message

multimodal_bp = Blueprint('multimodal_api', __name__, url_prefix='/api/v1/multimodal')
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadPolicy:
    max_bytes: int
    extensions: frozenset[str]
    signatures: tuple[bytes, ...]
    mime_by_extension: dict[str, str]


AUDIO_UPLOAD_POLICY = UploadPolicy(
    max_bytes=25 * 1024 * 1024,
    extensions=frozenset({".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}),
    signatures=(b"ID3", b"RIFF", b"OggS", b"fLaC", b"\x1aE\xdf\xa3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"),
    mime_by_extension={
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
    },
)
VIDEO_UPLOAD_POLICY = UploadPolicy(
    max_bytes=50 * 1024 * 1024,
    extensions=frozenset({".mp4", ".mov", ".webm", ".avi"}),
    signatures=(b"\x00\x00\x00", b"RIFF", b"\x1aE\xdf\xa3"),
    mime_by_extension={
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
        ".avi": "video/x-msvideo",
    },
)
DOCUMENT_UPLOAD_POLICY = UploadPolicy(
    max_bytes=10 * 1024 * 1024,
    extensions=frozenset({".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}),
    signatures=(b"%PDF-", b"PK\x03\x04", b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff"),
    mime_by_extension={
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    },
)


def _extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return f".{filename.rsplit('.', 1)[1].lower()}"


def _has_allowed_signature(data: bytes, policy: UploadPolicy, extension: str) -> bool:
    if extension == ".txt":
        return b"\x00" not in data[:1024]
    return any(data.startswith(prefix) for prefix in policy.signatures)


def _read_validated_upload(field_name: str, policy: UploadPolicy) -> tuple[bytes | None, str | None, str | None, tuple[dict, int] | None]:
    upload: FileStorage | None = request.files.get(field_name)
    if upload is None:
        return None, None, None, ({"error": "No file provided"}, 400)

    filename = secure_filename(upload.filename or "")
    if not filename:
        return None, None, None, ({"error": "File must have a safe filename"}, 400)

    extension = _extension(filename)
    if extension not in policy.extensions:
        return None, None, None, ({"error": "Unsupported file type"}, 415)

    content_length = request.content_length
    if content_length and content_length > policy.max_bytes:
        return None, None, None, ({"error": "File too large", "max_size_bytes": policy.max_bytes}, 413)

    data = upload.stream.read(policy.max_bytes + 1)
    if len(data) > policy.max_bytes:
        return None, None, None, ({"error": "File too large", "max_size_bytes": policy.max_bytes}, 413)
    if not data:
        return None, None, None, ({"error": "File cannot be empty"}, 400)
    if not _has_allowed_signature(data, policy, extension):
        return None, None, None, ({"error": "File content does not match an allowed type"}, 415)

    return data, filename, policy.mime_by_extension[extension], None


def _public_error(exc: Exception, fallback: str) -> str:
    return normalize_public_error_message(str(exc), fallback)


@multimodal_bp.route('/audio/transcribe', methods=['POST'])
@api_login_required
def transcribe_audio():
    audio_bytes, filename, _mime_type, error = _read_validated_upload("file", AUDIO_UPLOAD_POLICY)
    if error:
        return jsonify(error[0]), error[1]
    
    try:
        text = asyncio.run(audio_service.transcribe(audio_bytes, filename=filename))
        return jsonify({"success": True, "text": text})
    except AudioCapabilityUnavailable:
        return jsonify({
            "error": "Audio transcription is not available in this production profile",
            "code": "AUDIO_CAPABILITY_UNAVAILABLE",
        }), 501
    except Exception as e:
        logger.error("Transcription failed", exc_info=True)
        return jsonify({"error": _public_error(e, "Internal transcription error")}), 500

@multimodal_bp.route('/audio/synthesize', methods=['POST'])
@api_login_required
def synthesize_speech():
    from backend.schemas.request_schemas import AudioSynthesizeRequest
    from pydantic import ValidationError
    
    try:
        req = AudioSynthesizeRequest(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    try:
        audio_bytes = asyncio.run(audio_service.synthesize(req.text, voice=req.voice))
        # In a real app, you might save to cloud storage and return a URL
        # For now, we return a success indicator
        return jsonify({"success": True, "message": "Speech synthesized successfully", "size": len(audio_bytes)})
    except AudioCapabilityUnavailable:
        return jsonify({
            "error": "Speech synthesis is not available in this production profile",
            "code": "AUDIO_CAPABILITY_UNAVAILABLE",
        }), 501
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return jsonify({"error": "Internal synthesis error"}), 500

@multimodal_bp.route('/video/analyze', methods=['POST'])
@api_login_required
def analyze_video():
    video_bytes, _filename, _mime_type, error = _read_validated_upload("file", VIDEO_UPLOAD_POLICY)
    if error:
        return jsonify(error[0]), error[1]
    
    try:
        analysis = asyncio.run(video_service.analyze_video(video_bytes))
        return jsonify({"success": True, "analysis": analysis})
    except Exception as e:
        logger.error("Video analysis failed", exc_info=True)
        return jsonify({"error": _public_error(e, "Internal video analysis error")}), 500

@multimodal_bp.route('/document/process', methods=['POST'])
@api_login_required
def process_document():
    doc_bytes, filename, mime_type, error = _read_validated_upload("file", DOCUMENT_UPLOAD_POLICY)
    if error:
        return jsonify(error[0]), error[1]
    
    try:
        result = document_processor.process_file(doc_bytes, filename, mime_type)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        logger.error("Document processing failed", exc_info=True)
        return jsonify({"error": _public_error(e, "Internal document processing error")}), 500
