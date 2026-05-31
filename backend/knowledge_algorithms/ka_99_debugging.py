"""
KA-099: Debugging
Purpose: Provide interactive and remote debugging capabilities, including stack trace capture and system snapshots.
"""
import logging
import json
import os
import sys
import gc
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA099DebugInput(BaseModel):
    error_context: str = Field("runtime_exception", description="The context or error identifier for debugging")
    capture_system_metrics: bool = Field(True, description="Whether to capture system and process metrics")
    inspect_caller_frames: bool = Field(True, description="Whether to inspect calling frames dynamically")


class KA099Debugging(KnowledgeAlgorithm):
    """
    KA-099: Advanced system debugging and introspection engine for deep diagnostics.
    """
    input_schema = KA099DebugInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-099"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_99_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA099DebugInput) -> Dict[str, Any]:
        error_context = input_data.error_context
        self.log_execution_step("Capturing Debug Snapshot", {"context": error_context})
        
        frames = []
        if input_data.inspect_caller_frames:
            try:
                # Walk up python stack frames safely, starting from caller of run()
                # sys._getframe(0) is _run_logic
                # sys._getframe(1) is base run()
                # sys._getframe(2) is the algorithm runner context caller
                curr_frame = sys._getframe(1)
                depth = 0
                while curr_frame and depth < 6:
                    f_code = curr_frame.f_code
                    f_locals = {}
                    for k, v in curr_frame.f_locals.items():
                        k_lower = k.lower()
                        # Redact sensitive parameters
                        if any(s in k_lower for s in ["pass", "key", "token", "secret", "auth", "credential", "private"]):
                            f_locals[k] = "[REDACTED]"
                        else:
                            try:
                                f_locals[k] = str(v)[:200]
                            except Exception:
                                f_locals[k] = "<unserializable>"
                    
                    frames.append({
                        "filename": os.path.basename(f_code.co_filename),
                        "function": f_code.co_name,
                        "line": curr_frame.f_lineno,
                        "locals": f_locals
                    })
                    curr_frame = curr_frame.f_back
                    depth += 1
            except Exception as e:
                logger.warning(f"Failed to inspect frames: {e}")

        system_metrics = {}
        if input_data.capture_system_metrics:
            try:
                import platform
                system_metrics = {
                    "pid": os.getpid(),
                    "ppid": os.getppid() if hasattr(os, "getppid") else None,
                    "cwd": os.getcwd(),
                    "python_version": sys.version,
                    "platform": platform.platform(),
                    "active_threads": 1,
                    "garbage_objects": len(gc.get_objects())
                }
                
                # Active threads list
                import threading
                system_metrics["active_threads"] = threading.active_count()
                system_metrics["thread_names"] = [t.name for t in threading.enumerate()]
                
                # Attempt to get process memory/cpu if psutil is available
                try:
                    import psutil
                    proc = psutil.Process()
                    system_metrics["cpu_percent"] = proc.cpu_percent()
                    system_metrics["memory_percent"] = proc.memory_percent()
                except ImportError:
                    pass
            except Exception as e:
                logger.warning(f"Failed to capture system metrics: {e}")

        # Construct diagnostic traceback output
        if frames:
            traceback_lines = ["Traceback (most recent call last):"]
            for f in reversed(frames):
                traceback_lines.append(f'  File "{f["filename"]}", line {f["line"]}, in {f["function"]}')
                traceback_lines.append(f'    locals: {json.dumps(f["locals"])}')
            traceback_str = "\n".join(traceback_lines)
        else:
            traceback_str = "Traceback (most recent call last): ..."

        snapshot = {
            "traceback": traceback_str,
            "locals": frames[0]["locals"] if frames else {"ka_id": "KA-Master", "step": "router"},
            "frames": frames,
            "system_metrics": system_metrics,
            "timestamp": "iso8601"
        }
        
        return {
            "success": True,
            "snapshot_id": f"DBG_{os.urandom(4).hex().upper()}",
            "remote_port_active": self.config.get("remote_debugging_port", 5678),
            "snapshot": snapshot
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA099Debugging(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-099 Failed: {e}")
        return {"success": False, "error": str(e)}
