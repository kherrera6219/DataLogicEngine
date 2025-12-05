
"""
UKG Enterprise Configuration Manager

Provides centralized configuration for all UKG enterprise services.
"""

import os
import logging
import json
# pathlib not needed
from typing import Dict, Any, Optional

logger = logging.getLogger("UKG-Config")

class ConfigManager:
    """
    Centralized configuration manager for the UKG Enterprise system.
    Handles loading, validating, and providing configuration values.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._config = {
            "ports": {
                "api_gateway": int(os.environ.get("API_GATEWAY_PORT", 5000)),
                "webhook_server": int(os.environ.get("WEBHOOK_SERVER_PORT", 5001)),
                "model_context": int(os.environ.get("MODEL_CONTEXT_PORT", 5002)),
                "core_ukg": int(os.environ.get("UKG_CORE_PORT", 5003)),
                "dotnet_service": int(os.environ.get("DOTNET_SERVICE_PORT", 5005)),
                "frontend": int(os.environ.get("FRONTEND_PORT", 3000))
            },
            "services": {
                "api_gateway": {
                    "host": "0.0.0.0",
                    "health_check_path": "/health",
                    "workers": 2,
                    "enable_cors": True
                },
                "webhook_server": {
                    "host": "0.0.0.0", 
                    "health_check_path": "/health"
                },
                "model_context": {
                    "host": "0.0.0.0",
                    "health_check_path": "/health"
                },
                "core_ukg": {
                    "host": "0.0.0.0",
                    "health_check_path": "/health"
                },
                "dotnet_service": {
                    "host": "0.0.0.0",
                    "health_check_path": "/health"
                },
                "frontend": {
                    "host": "0.0.0.0",
                    "api_url": "http://0.0.0.0:5000"
                }
            },
            "system": {
                "log_directory": "logs",
                "data_directory": "data",
                "debug": os.environ.get("DEBUG", "False").lower() == "true",
                "environment": os.environ.get("ENV", "development"),
                "startup_timeout": 30  # seconds
            },
            "auth": {
                "jwt_secret": os.environ.get("JWT_SECRET", "ukg-development-secret"),
                "token_expiry_minutes": 60
            }
        }
        
        self._initialized = True
        logger.info("Configuration manager initialized")
    
    def load_from_file(self, file_path: str) -> bool:
        """Load configuration from JSON file"""
        try:
            with open(file_path, 'r') as f:
                file_config = json.load(f)
                self._update_config(file_config)
            logger.info(f"Loaded configuration from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            return False
    
    def _update_config(self, new_config: Dict[str, Any], target: Optional[Dict[str, Any]] = None, path: str = ""):
        """Recursively update configuration dictionary"""
        if target is None:
            target = self._config
            
        for key, value in new_config.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively update nested dictionaries
                self._update_config(value, target[key], current_path)
            else:
                # Update or add value
                target[key] = value
                logger.debug(f"Updated config {current_path} = {value}")
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation path
        Example: config_manager.get("ports.api_gateway")
        """
        parts = path.split('.')
        value = self._config
        
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
            
        return value
    
    def get_port(self, service_name: str) -> int:
        """Get port for a specific service"""
        return self.get(f"ports.{service_name}")
    
    def get_service_url(self, service_name: str) -> str:
        """Get full URL for a service"""
        port = self.get_port(service_name)
        host = self.get(f"services.{service_name}.host", "0.0.0.0")
        return f"http://{host}:{port}"
    
    def get_health_check_url(self, service_name: str) -> str:
        """Get health check URL for a service"""
        service_url = self.get_service_url(service_name)
        health_path = self.get(f"services.{service_name}.health_check_path", "/health")
        return f"{service_url}{health_path}"
    
    def as_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary"""
        return self._config.copy()
    
    def get_env_dict(self) -> Dict[str, str]:
        """Get flattened environment variables dict for all services"""
        env_dict = {}
        
        # Add port variables
        for service, port in self._config["ports"].items():
            env_dict[f"{service.upper()}_PORT"] = str(port)
        
        # Add system variables
        env_dict["DEBUG"] = str(self._config["system"]["debug"]).lower()
        env_dict["ENV"] = self._config["system"]["environment"]
        
        # Add frontend environment variables
        env_dict["NEXT_PUBLIC_API_URL"] = self.get_service_url("api_gateway")
        
        return env_dict

# Singleton instance accessor
def get_config() -> ConfigManager:
    """Get the singleton ConfigManager instance"""
    return ConfigManager()
