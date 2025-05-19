
"""
Universal Knowledge Graph (UKG) Security Manager

This module provides security management capabilities for the UKG enterprise architecture,
supporting SOC 2 Type 2 compliance requirements.
"""

import os
import logging
import json
import time
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import threading
import uuid
import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UKG-Security")

class SecurityManager:
    """
    Security Manager for UKG Enterprise System
    
    Provides security capabilities to support SOC 2 compliance
    and protect the UKG system.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Security Manager.
        
        Args:
            config: Configuration settings
        """
        self.config = config or {}
        
        # Create security data directory
        os.makedirs("data/security", exist_ok=True)
        
        # Initialize encryption key
        self._initialize_encryption()
        
        # Initialize security scanning thread
        self.scanning_active = False
        self.scanning_thread = None
        
        # Security scan results
        self.last_scan_time = None
        self.last_scan_results = None
        
        # Rate limiting data
        self.rate_limit_data = {}
        
        # Start security scanning
        self.start_security_scanning()
        
        logger.info("Security Manager initialized")
    
    def _initialize_encryption(self):
        """Initialize encryption capabilities"""
        try:
            # Check for existing key
            key_file = "data/security/encryption.key"
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
            else:
                # Generate a new key
                self.encryption_key = Fernet.generate_key()
                
                # Save the key
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
                    
            # Initialize the cipher
            self.cipher = Fernet(self.encryption_key)
            
            logger.info("Encryption initialized")
            
        except Exception as e:
            logger.error(f"Error initializing encryption: {str(e)}")
            self.encryption_key = None
            self.cipher = None
    
    def start_security_scanning(self):
        """Start the security scanning thread"""
        if not self.scanning_active:
            self.scanning_active = True
            self.scanning_thread = threading.Thread(
                target=self._security_scanning_loop,
                daemon=True
            )
            self.scanning_thread.start()
            logger.info("Security scanning started")
    
    def stop_security_scanning(self):
        """Stop the security scanning thread"""
        self.scanning_active = False
        if self.scanning_thread:
            self.scanning_thread.join(timeout=5)
            logger.info("Security scanning stopped")
    
    def _security_scanning_loop(self):
        """Background thread for security scanning"""
        while self.scanning_active:
            try:
                # Perform security scans
                self._perform_security_scan()
                
                # Sleep interval (scan every 15 minutes)
                time.sleep(900)
                
            except Exception as e:
                logger.error(f"Error in security scanning: {str(e)}")
                time.sleep(300)  # Shorter interval on error
    
    def _perform_security_scan(self):
        """Perform a security scan of the system"""
        try:
            logger.info("Starting security scan")
            
            scan_results = {
                "scan_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "vulnerabilities": [],
                "warnings": [],
                "status": "completed"
            }
            
            # Check for common security issues
            self._check_file_permissions(scan_results)
            self._check_log_files(scan_results)
            self._check_configuration_files(scan_results)
            
            # Update scan results
            self.last_scan_time = datetime.now()
            self.last_scan_results = scan_results
            
            # Save scan results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = f"logs/security/scan_{timestamp}.json"
            
            os.makedirs("logs/security", exist_ok=True)
            
            with open(result_file, 'w') as f:
                json.dump(scan_results, f, indent=2)
            
            logger.info(f"Security scan completed: {len(scan_results['vulnerabilities'])} vulnerabilities, {len(scan_results['warnings'])} warnings")
            
        except Exception as e:
            logger.error(f"Error performing security scan: {str(e)}")
    
    def _check_file_permissions(self, scan_results):
        """Check file permissions for security issues"""
        # In a real implementation, this would check file permissions
        # For this demo, we'll just add a placeholder warning
        scan_results["warnings"].append({
            "type": "file_permissions",
            "description": "File permission checks are simulated in this environment",
            "severity": "low"
        })
    
    def _check_log_files(self, scan_results):
        """Check log files for security issues"""
        try:
            log_dir = "logs"
            if os.path.exists(log_dir):
                # Check for sensitive information in log files
                sensitive_patterns = [
                    r'password\s*=\s*[\'"][^\'"]+[\'"]',
                    r'apikey\s*=\s*[\'"][^\'"]+[\'"]',
                    r'token\s*=\s*[\'"][^\'"]+[\'"]',
                    r'secret\s*=\s*[\'"][^\'"]+[\'"]'
                ]
                
                for root, _, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith(".log") or file.endswith(".txt"):
                            file_path = os.path.join(root, file)
                            
                            try:
                                with open(file_path, 'r', errors='ignore') as f:
                                    content = f.read()
                                    
                                    for pattern in sensitive_patterns:
                                        matches = re.findall(pattern, content, re.IGNORECASE)
                                        
                                        if matches:
                                            scan_results["vulnerabilities"].append({
                                                "type": "sensitive_data_exposure",
                                                "description": f"Sensitive data pattern found in log file: {file_path}",
                                                "severity": "high",
                                                "details": {
                                                    "file": file_path,
                                                    "pattern": pattern,
                                                    "match_count": len(matches)
                                                }
                                            })
                            except Exception as e:
                                logger.error(f"Error checking log file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error checking log files: {str(e)}")
    
    def _check_configuration_files(self, scan_results):
        """Check configuration files for security issues"""
        try:
            # Check for hardcoded secrets in configuration files
            config_files = [".env", "config.env", "config.py", ".replit"]
            
            for file in config_files:
                if os.path.exists(file):
                    try:
                        with open(file, 'r', errors='ignore') as f:
                            content = f.read()
                            
                            # Check for hardcoded secrets
                            secret_patterns = [
                                r'password\s*=\s*[\'"][^\'"]+[\'"]',
                                r'apikey\s*=\s*[\'"][^\'"]+[\'"]',
                                r'token\s*=\s*[\'"][^\'"]+[\'"]',
                                r'secret\s*=\s*[\'"][^\'"]+[\'"]'
                            ]
                            
                            for pattern in secret_patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                
                                if matches:
                                    scan_results["vulnerabilities"].append({
                                        "type": "hardcoded_secrets",
                                        "description": f"Hardcoded secrets found in configuration file: {file}",
                                        "severity": "high",
                                        "details": {
                                            "file": file,
                                            "pattern": pattern,
                                            "match_count": len(matches)
                                        }
                                    })
                    except Exception as e:
                        logger.error(f"Error checking configuration file {file}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error checking configuration files: {str(e)}")
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: The data to encrypt
            
        Returns:
            The encrypted data as a base64 string
        """
        if not self.cipher:
            raise ValueError("Encryption not initialized")
            
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode()
                
            # Encrypt the data
            encrypted_data = self.cipher.encrypt(data)
            
            # Return as base64 string
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> bytes:
        """
        Decrypt encrypted data.
        
        Args:
            encrypted_data: The encrypted data as a base64 string
            
        Returns:
            The decrypted data as bytes
        """
        if not self.cipher:
            raise ValueError("Encryption not initialized")
            
        try:
            # Convert from base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Decrypt the data
            return self.cipher.decrypt(encrypted_bytes)
            
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """
        Hash a password for secure storage.
        
        Args:
            password: The password to hash
            salt: Optional salt bytes, generated if not provided
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        try:
            # Generate salt if not provided
            if not salt:
                salt = os.urandom(16)
                
            # Create the password hash
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            
            # Hash the password
            hashed_password = base64.b64encode(kdf.derive(password.encode())).decode()
            
            return hashed_password, salt
            
        except Exception as e:
            logger.error(f"Password hashing error: {str(e)}")
            raise
    
    def verify_password(self, password: str, hashed_password: str, salt: bytes) -> bool:
        """
        Verify a password against a stored hash.
        
        Args:
            password: The password to verify
            hashed_password: The stored hashed password
            salt: The salt used for hashing
            
        Returns:
            True if the password matches, False otherwise
        """
        try:
            # Hash the provided password with the same salt
            new_hash, _ = self.hash_password(password, salt)
            
            # Compare the hashes
            return new_hash == hashed_password
            
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def generate_token(self, length: int = 32) -> str:
        """
        Generate a secure random token.
        
        Args:
            length: The length of the token in bytes
            
        Returns:
            A secure random token as a hex string
        """
        return secrets.token_hex(length)
    
    def check_rate_limit(self, key: str, limit: int, period: int) -> bool:
        """
        Check if a rate limit has been exceeded.
        
        Args:
            key: The rate limit key (e.g., IP address, user ID)
            limit: Maximum number of requests
            period: Time period in seconds
            
        Returns:
            True if rate limit is not exceeded, False otherwise
        """
        current_time = time.time()
        
        # Initialize rate limit data for this key if needed
        if key not in self.rate_limit_data:
            self.rate_limit_data[key] = []
            
        # Remove expired timestamps
        self.rate_limit_data[key] = [ts for ts in self.rate_limit_data[key] if ts > current_time - period]
        
        # Check if limit is exceeded
        if len(self.rate_limit_data[key]) >= limit:
            return False
            
        # Add current timestamp
        self.rate_limit_data[key].append(current_time)
        
        return True
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get the current security status.
        
        Returns:
            Dict with security status information
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "encryption_enabled": self.cipher is not None,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "vulnerabilities_count": len(self.last_scan_results["vulnerabilities"]) if self.last_scan_results else 0,
            "warnings_count": len(self.last_scan_results["warnings"]) if self.last_scan_results else 0,
            "status": "healthy" if (not self.last_scan_results or len(self.last_scan_results["vulnerabilities"]) == 0) else "vulnerable"
        }
