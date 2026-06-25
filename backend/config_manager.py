
"""
DataLogicEngine Configuration Manager

Provides centralized configuration (ports, data directories, database URL) for the
single-mode local-first app — the desktop Flask backend and the Next.js frontend.
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
            
        # Determine base data directory
        default_data_dir = "data"
        if os.name == 'nt':
            # Windows default: shared machine-wide location.
            program_data = os.environ.get("PROGRAMDATA", "C:\\ProgramData")
            default_data_dir = os.path.join(program_data, "DataLogicEngine")
        
        base_data_dir = os.environ.get("UKG_DATA_DIR", default_data_dir)
        default_bind_host = os.environ.get("SERVICE_BIND_HOST", "127.0.0.1")
        api_host = os.environ.get("API_HOST", default_bind_host)
        
        self._config = {
            # Single-mode local-first: the only services are the desktop Flask
            # backend ("api_gateway" == port 5000) and the Next.js frontend.
            # The standalone enterprise FastAPI services (webhook_server /
            # model_context / core_ukg / dotnet_service) and the JWT auth block
            # were retired with the multi-service layer (A28) and multi-user auth
            # deprecation — their config entries are removed here (A30).
            "ports": {
                "api_gateway": int(os.environ.get("API_GATEWAY_PORT", 5000)),
                "frontend": int(os.environ.get("FRONTEND_PORT", 3000))
            },
            "services": {
                "api_gateway": {
                    "host": api_host,
                    "health_check_path": "/health",
                    "workers": 2,
                    "enable_cors": True
                },
                "frontend": {
                    "host": default_bind_host,
                    "api_url": f"http://{api_host}:5000"
                }
            },
            "system": {
                "log_directory": os.path.join(base_data_dir, "logs"),
                "data_directory": base_data_dir,
                "debug": os.environ.get("DEBUG", "False").lower() == "true",
                "environment": os.environ.get("ENV", "development"),
                "startup_timeout": 30  # seconds
            },
            "database": {
                "url": self._get_db_url(),
                "pool_size": 10,
                "pool_recycle": 3600,
                "engine_options": {
                    "pool_pre_ping": True,  # Essential for service-restart resilience
                    "connect_args": {
                        "connect_timeout": 10
                    }
                }
            }
        }

        
        self._initialized = True
        logger.info("Configuration manager initialized")

    def _get_db_url(self) -> str:
        """Resolves the database URL based on the environment."""
        env_url = os.environ.get("DATABASE_URL")
        if env_url:
            return env_url
            
        if os.name == 'nt':
            # Desktop Build Default: Local PostgreSQL with ukg_app
            db_user = "ukg_app"
            db_name = "ukg_local"
            db_host = "localhost"
            db_port = 5432
            
            # Fetch password from environmental override or default
            db_pwd = os.environ.get("UKG_DB_PASSWORD", "ukg_local_pwd") 
            
            return f"postgresql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}"
            
        return "postgresql://localhost/ukg"
    
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
        host = self.get(f"services.{service_name}.host", "127.0.0.1")
        return f"http://{host}:{port}"
    
    def get_health_check_url(self, service_name: str) -> str:
        """Get health check URL for a service"""
        service_url = self.get_service_url(service_name)
        health_path = self.get(f"services.{service_name}.health_check_path", "/health")
        return f"{service_url}{health_path}"
    
    @property
    def UKG_DATA_DIR(self) -> str:
        """Get the base data directory for the system."""
        return self.get("system.data_directory")

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
