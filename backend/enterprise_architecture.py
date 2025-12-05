
"""
UKG Enterprise Architecture

This module defines the enterprise architecture for the Universal Knowledge Graph system,
integrating Python and .NET components through an API Gateway pattern.
"""

import os
import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UKG-Enterprise")

@dataclass
class ServiceRegistry:
    """Registry of microservices in the UKG enterprise architecture"""
    name: str
    endpoint: str
    health_check_path: str
    service_type: str  # 'python', 'dotnet', 'external'
    status: str = "unknown"
    last_checked: Optional[datetime] = None
    
class EnterpriseArchitecture:
    """
    Enterprise Architecture Manager for UKG System
    
    Coordinates all microservices, handles service discovery,
    health monitoring, and cross-service communication.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the enterprise architecture manager"""
        self.services: Dict[str, ServiceRegistry] = {}
        self.config = self._load_config(config_path)
        self.gateway_port = int(os.environ.get("API_GATEWAY_PORT", 5000))
        self.webhook_port = int(os.environ.get("WEBHOOK_SERVER_PORT", 5001))
        self.model_context_port = int(os.environ.get("MODEL_CONTEXT_PORT", 5002))
        logger.info(f"Enterprise Architecture initialized with gateway on port {self.gateway_port}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        # Default configuration
        default_config = {
            "service_discovery": {
                "enabled": True,
                "refresh_interval_seconds": 30
            },
            "authentication": {
                "provider": "jwt",
                "token_expiry_minutes": 60
            },
            "cross_runtime": {
                "python_dotnet_bridge": "grpc"
            }
        }
        
        # If config file provided, merge with defaults
        if config_path and os.path.exists(config_path):
            import json
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
                # Merge configs
                for k, v in custom_config.items():
                    if isinstance(v, dict) and k in default_config:
                        default_config[k].update(v)
                    else:
                        default_config[k] = v
        
        return default_config
    
    def register_service(self, service: ServiceRegistry) -> None:
        """Register a microservice with the architecture"""
        self.services[service.name] = service
        logger.info(f"Registered service: {service.name} at {service.endpoint}")
    
    def get_service(self, service_name: str) -> Optional[ServiceRegistry]:
        """Get service by name"""
        return self.services.get(service_name)
    
    async def health_check_all(self) -> Dict[str, str]:
        """Check health of all registered services"""
        import aiohttp
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for name, service in self.services.items():
                health_url = f"{service.endpoint}{service.health_check_path}"
                try:
                    async with session.get(health_url, timeout=5) as response:
                        if response.status == 200:
                            service.status = "healthy"
                            results[name] = "healthy"
                        else:
                            service.status = f"unhealthy: {response.status}"
                            results[name] = f"unhealthy: {response.status}"
                except Exception as e:
                    service.status = f"error: {str(e)}"
                    results[name] = f"error: {str(e)}"
                
                service.last_checked = datetime.now()
        
        return results
    
    def start_service_discovery(self) -> None:
        """Start the service discovery background process"""
        if not self.config["service_discovery"]["enabled"]:
            logger.info("Service discovery disabled in configuration")
            return
        
        refresh_interval = self.config["service_discovery"]["refresh_interval_seconds"]
        logger.info(f"Starting service discovery with refresh interval of {refresh_interval}s")
        
        # In a complete implementation, this would start a background task
        # to periodically check for new services and their health
        
    def initialize_architecture(self) -> None:
        """Initialize the enterprise architecture components"""
        # Try to import config manager
        try:
            from backend.config_manager import get_config
            config = get_config()
            
            # Use ports from config
            api_port = config.get_port("api_gateway")
            webhook_port = config.get_port("webhook_server")
            model_context_port = config.get_port("model_context")
            core_ukg_port = config.get_port("core_ukg")
            dotnet_port = config.get_port("dotnet_service")
            frontend_port = config.get_port("frontend")
            
            logger.info("Using configuration from config manager")
        except ImportError:
            # Use default ports from instance variables
            api_port = self.gateway_port
            webhook_port = self.webhook_port
            model_context_port = self.model_context_port
            core_ukg_port = 5003
            dotnet_port = 5005
            frontend_port = 3000
            
            logger.info("Using default port configuration")
            
        # Register core services
        self.register_service(ServiceRegistry(
            name="api_gateway",
            endpoint=f"http://0.0.0.0:{api_port}",
            health_check_path="/health",
            service_type="python"
        ))
        
        self.register_service(ServiceRegistry(
            name="webhook_server",
            endpoint=f"http://0.0.0.0:{webhook_port}",
            health_check_path="/health",
            service_type="python"
        ))
        
        self.register_service(ServiceRegistry(
            name="model_context_server",
            endpoint=f"http://0.0.0.0:{model_context_port}",
            health_check_path="/health",
            service_type="python"
        ))
        
        self.register_service(ServiceRegistry(
            name="core_ukg",
            endpoint=f"http://0.0.0.0:{core_ukg_port}",
            health_check_path="/health",
            service_type="python"
        ))
        
        self.register_service(ServiceRegistry(
            name="dotnet_service",
            endpoint=f"http://0.0.0.0:{dotnet_port}",
            health_check_path="/health",
            service_type="dotnet"
        ))
        
        self.register_service(ServiceRegistry(
            name="frontend",
            endpoint=f"http://0.0.0.0:{frontend_port}",
            health_check_path="/api/health",  # Next.js exposes this via proxy
            service_type="nodejs"
        ))
        
        # Start service discovery
        self.start_service_discovery()
        
        logger.info("Enterprise Architecture components initialized")
    
    def get_architecture_status(self) -> Dict[str, Any]:
        """Get current status of the enterprise architecture"""
        return {
            "gateway_port": self.gateway_port,
            "registered_services": len(self.services),
            "services": {name: {"status": svc.status, "endpoint": svc.endpoint} 
                         for name, svc in self.services.items()},
            "timestamp": datetime.now().isoformat()
        }

# Singleton instance
enterprise_arch = None

def get_enterprise_architecture(config_path: Optional[str] = None) -> EnterpriseArchitecture:
    """Get or create the singleton enterprise architecture instance"""
    global enterprise_arch
    if enterprise_arch is None:
        enterprise_arch = EnterpriseArchitecture(config_path)
        enterprise_arch.initialize_architecture()
    return enterprise_arch
