# payment_wipay/models/security_utils.py

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from odoo import fields
from odoo.exceptions import SecurityError

_logger = logging.getLogger(__name__)

class WiPaySecurityUtils:
    """Security utilities for WiPay payment processing."""
    
    @staticmethod
    def generate_nonce(length: int = 32) -> str:
        """Generate a secure random nonce.
        
        Args:
            length: Length of nonce to generate
            
        Returns:
            str: Secure random nonce
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_signature(secret_key: str, payload: Dict, timestamp: str) -> str:
        """Generate HMAC signature for request verification.
        
        Args:
            secret_key: API secret key
            payload: Request payload
            timestamp: Request timestamp
            
        Returns:
            str: HMAC signature
        """
        # Sort payload keys for consistent signing
        sorted_payload = {k: payload[k] for k in sorted(payload.keys())}
        
        # Create signing string
        signing_string = f"{timestamp}:{str(sorted_payload)}"
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            secret_key.encode(),
            signing_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    @staticmethod
    def verify_signature(secret_key: str, payload: Dict, timestamp: str, 
                        received_signature: str, max_age: int = 300) -> bool:
        """Verify the authenticity of a received signature.
        
        Args:
            secret_key: API secret key
            payload: Request payload
            timestamp: Request timestamp
            received_signature: Signature to verify
            max_age: Maximum age of request in seconds
            
        Returns:
            bool: True if signature is valid
            
        Raises:
            SecurityError: If verification fails
        """
        # Check timestamp freshness
        try:
            ts = datetime.fromtimestamp(float(timestamp))
            age = (datetime.now() - ts).total_seconds()
            if age > max_age:
                raise SecurityError("Request too old")
        except ValueError:
            raise SecurityError("Invalid timestamp format")

        # Generate expected signature
        expected_signature = WiPaySecurityUtils.generate_signature(
            secret_key, payload, timestamp
        )
        
        # Constant-time comparison
        return hmac.compare_digest(
            received_signature.encode(),
            expected_signature.encode()
        )

    @staticmethod
    def encrypt_card_data(card_data: Dict) -> Dict:
        """Encrypt sensitive card data for storage.
        
        Args:
            card_data: Card details to encrypt
            
        Returns:
            dict: Encrypted card data
        """
        from cryptography.fernet import Fernet
        
        # Generate key from environment or config
        key = Fernet.generate_key()
        f = Fernet(key)
        
        encrypted_data = {}
        for field, value in card_data.items():
            if value:
                encrypted_data[field] = f.encrypt(str(value).encode()).decode()
                
        return encrypted_data

    @staticmethod
    def sanitize_response(response_data: Dict) -> Dict:
        """Sanitize response data to remove sensitive information.
        
        Args:
            response_data: Response data to sanitize
            
        Returns:
            dict: Sanitized response data
        """
        sensitive_fields = {
            'card_number', 'cvv', 'expiry', 'api_key', 'token',
            'password', 'secret', 'authorization'
        }
        
        sanitized = {}
        for key, value in response_data.items():
            if key.lower() in sensitive_fields:
                sanitized[key] = '***'
            elif isinstance(value, dict):
                sanitized[key] = WiPaySecurityUtils.sanitize_response(value)
            else:
                sanitized[key] = value
                
        return sanitized

    @staticmethod
    def validate_ip_address(ip_address: str, allowed_ips: Optional[list] = None) -> bool:
        """Validate if IP address is allowed.
        
        Args:
            ip_address: IP address to validate
            allowed_ips: List of allowed IP addresses
            
        Returns:
            bool: True if IP is allowed
        """
        if not allowed_ips:
            # Get allowed IPs from configuration
            allowed_ips = []  # Configure this appropriately
            
        return ip_address in allowed_ips if allowed_ips else True

    @staticmethod
    def rate_limit_check(key: str, limit: int = 100, 
                        period: int = 3600) -> bool:
        """Check if request is within rate limits.
        
        Args:
            key: Rate limit key (e.g., IP address)
            limit: Maximum requests allowed
            period: Time period in seconds
            
        Returns:
            bool: True if within limits
        """
        # Implement rate limiting logic
        return True  # Placeholder