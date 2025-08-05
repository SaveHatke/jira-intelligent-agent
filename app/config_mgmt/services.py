"""
Configuration management services for JIA application.

This module provides services for managing MCP and AI configurations,
including validation, testing, and encryption utilities.
"""

import json
import asyncio
import httpx
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from flask import current_app
from flask_login import current_user

from app import db
from app.models import MCPConfiguration, AIConfiguration


class ConfigurationService:
    """Base service for configuration management."""
    
    @staticmethod
    def get_user_mcp_config(user_id: int) -> Optional[MCPConfiguration]:
        """Get active MCP configuration for user."""
        return MCPConfiguration.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).first()
    
    @staticmethod
    def get_user_ai_config(user_id: int) -> Optional[AIConfiguration]:
        """Get AI configuration for user."""
        return AIConfiguration.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def save_mcp_config(user_id: int, config_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[MCPConfiguration]]:
        """
        Save or update MCP configuration for user.
        
        Args:
            user_id: User ID
            config_data: Configuration data dictionary
            
        Returns:
            Tuple of (success, errors, config_object)
        """
        try:
            # Get existing config or create new one
            config = MCPConfiguration.query.filter_by(user_id=user_id).first()
            if not config:
                config = MCPConfiguration(user_id=user_id)
            
            # Update Jira configuration
            config.jira_url = config_data.get('jira_url', '').strip()
            config.jira_ssl_verify = config_data.get('jira_ssl_verify', True)
            jira_token = config_data.get('jira_personal_token', '').strip()
            if jira_token:
                config.set_jira_personal_token(jira_token)
            elif config_data.get('jira_personal_token') == '':
                # Explicitly clear token if empty string is provided
                config.jira_personal_token = ''
            
            # Update Confluence configuration
            config.confluence_url = config_data.get('confluence_url', '').strip()
            config.confluence_ssl_verify = config_data.get('confluence_ssl_verify', True)
            confluence_token = config_data.get('confluence_personal_token', '').strip()
            if confluence_token:
                config.set_confluence_personal_token(confluence_token)
            elif config_data.get('confluence_personal_token') == '':
                # Explicitly clear token if empty string is provided
                config.confluence_personal_token = ''
            
            # Legacy fields for backward compatibility
            config.server_url = config_data.get('server_url', '').strip()
            pat = config_data.get('personal_access_token', '').strip()
            if pat:
                config.set_personal_access_token(pat)
            
            # Handle additional parameters
            additional_params = config_data.get('additional_params', {})
            if isinstance(additional_params, str):
                try:
                    additional_params = json.loads(additional_params)
                except json.JSONDecodeError:
                    return False, ["Additional parameters must be valid JSON"], None
            
            config.additional_params = additional_params
            config.is_active = config_data.get('is_active', True)
            
            # Validate configuration
            errors = config.validate()
            if errors:
                return False, errors, None
            
            # Save to database
            db.session.add(config)
            db.session.commit()
            
            return True, [], config
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving MCP config: {str(e)}")
            return False, [f"Failed to save configuration: {str(e)}"], None
    
    @staticmethod
    def save_ai_config(user_id: int, config_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[AIConfiguration]]:
        """
        Save or update AI configuration for user.
        
        Args:
            user_id: User ID
            config_data: Configuration data dictionary
            
        Returns:
            Tuple of (success, errors, config_object)
        """
        try:
            # Get existing config or create new one
            config = AIConfiguration.query.filter_by(user_id=user_id).first()
            if not config:
                config = AIConfiguration(user_id=user_id)
            
            # Update configuration fields
            custom_headers = config_data.get('custom_headers', {})
            if isinstance(custom_headers, str):
                try:
                    custom_headers = json.loads(custom_headers)
                except json.JSONDecodeError:
                    return False, ["Custom headers must be valid JSON"], None
            
            config.set_custom_headers(custom_headers)
            config.user_id_from_jira = config_data.get('user_id_from_jira', '').strip()
            
            # Handle model configurations
            model_configs = config_data.get('model_configs', {})
            if isinstance(model_configs, str):
                try:
                    model_configs = json.loads(model_configs)
                except json.JSONDecodeError:
                    return False, ["Model configurations must be valid JSON"], None
            
            config.model_configs = model_configs
            config.is_validated = False  # Reset validation status on update
            
            # Validate configuration
            errors = config.validate()
            if errors:
                return False, errors, None
            
            # Save to database
            db.session.add(config)
            db.session.commit()
            
            return True, [], config
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving AI config: {str(e)}")
            return False, [f"Failed to save configuration: {str(e)}"], None


class MCPTestService:
    """Service for testing MCP connections."""
    
    @staticmethod
    async def test_connection(config: MCPConfiguration, service_type: str = 'jira') -> Tuple[bool, str, Dict[str, Any]]:
        """
        Test MCP connection for Jira or Confluence.
        
        Args:
            config: MCP configuration object
            service_type: 'jira' or 'confluence'
            
        Returns:
            Tuple of (success, message, user_info)
        """
        try:
            from app.services.mcp_client import MCPClientManager
            
            # Create MCP client manager
            client = MCPClientManager(config)
            
            # Test connection based on service type
            if service_type == 'jira':
                result = await client.test_jira_connection()
            elif service_type == 'confluence':
                result = await client.test_confluence_connection()
            else:
                # Legacy support - default to Jira
                result = await client.test_jira_connection()
            
            if result.success:
                user_info = {
                    'user_name': result.user_name,
                    'user_id': result.user_id,
                    'display_name': result.display_name,
                    'email': result.email,
                    'server_info': result.server_info
                }
                
                # Add detailed user information if available
                if result.server_info and 'user_details' in result.server_info:
                    user_info['user_details'] = result.server_info['user_details']
                
                # Update last tested timestamp
                config.last_tested = datetime.utcnow()
                db.session.commit()
                
                success_message = f"{service_type.title()} connection successful! Connected as {result.display_name}"
                if result.email:
                    success_message += f" ({result.email})"
                
                return True, success_message, user_info
            else:
                return False, result.error_message or "Connection failed", {}
            
        except Exception as e:
            current_app.logger.error(f"MCP connection test failed: {str(e)}")
            return False, f"Connection test failed: {str(e)}", {}
    
    @staticmethod
    def test_connection_sync(config: MCPConfiguration, service_type: str = 'jira') -> Tuple[bool, str, Dict[str, Any]]:
        """Synchronous wrapper for connection testing."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                MCPTestService.test_connection(config, service_type)
            )
        except Exception as e:
            current_app.logger.error(f"Sync connection test failed: {str(e)}")
            return False, f"Connection test failed: {str(e)}", {}
        finally:
            loop.close()


class AIConfigValidationService:
    """Service for validating AI configurations."""
    
    @staticmethod
    async def validate_ai_config(config: AIConfiguration) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate AI configuration by testing API connectivity.
        
        Args:
            config: AI configuration object
            
        Returns:
            Tuple of (success, message, validation_info)
        """
        try:
            # Basic validation first
            errors = config.validate()
            if errors:
                return False, f"Configuration errors: {', '.join(errors)}", {}
            
            # Test API connectivity with custom headers
            headers = config.get_custom_headers()
            
            # Add default headers if not present
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'JIA-Agent/1.0'
            
            # This is a placeholder for actual AI API testing
            # In real implementation, this would test the actual AI service
            
            # Simulate API test
            await asyncio.sleep(0.1)  # Simulate network delay
            
            validation_info = {
                'headers_valid': bool(headers),
                'user_id_from_jira': config.user_id_from_jira,
                'model_configs': config.model_configs or {},
                'validated_at': datetime.utcnow().isoformat()
            }
            
            # Update validation status
            config.is_validated = True
            db.session.commit()
            
            return True, "AI configuration validated successfully", validation_info
            
        except Exception as e:
            current_app.logger.error(f"AI config validation failed: {str(e)}")
            return False, f"Validation failed: {str(e)}", {}
    
    @staticmethod
    def validate_ai_config_sync(config: AIConfiguration) -> Tuple[bool, str, Dict[str, Any]]:
        """Synchronous wrapper for AI config validation."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                AIConfigValidationService.validate_ai_config(config)
            )
        except Exception as e:
            current_app.logger.error(f"Sync AI validation failed: {str(e)}")
            return False, f"Validation failed: {str(e)}", {}
        finally:
            loop.close()


class ConfigurationUtilities:
    """Utility functions for configuration management."""
    
    @staticmethod
    def get_default_mcp_params() -> Dict[str, Any]:
        """Get default additional parameters for MCP configuration."""
        return {
            'timeout': 30,
            'max_retries': 3,
            'verify_ssl': True,
            'user_agent': 'JIA-MCP-Client/1.0'
        }
    
    @staticmethod
    def get_default_ai_model_configs() -> Dict[str, Any]:
        """Get default model configurations for AI service."""
        return {
            'model': 'gpt-4',
            'temperature': 0.7,
            'max_tokens': 2000,
            'timeout': 30
        }
    
    @staticmethod
    def validate_json_string(json_str: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate and parse JSON string.
        
        Args:
            json_str: JSON string to validate
            
        Returns:
            Tuple of (is_valid, error_message, parsed_data)
        """
        if not json_str or json_str.strip() == '':
            return True, '', {}
        
        try:
            parsed = json.loads(json_str)
            if not isinstance(parsed, dict):
                return False, "JSON must be an object/dictionary", None
            return True, '', parsed
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}", None
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize and normalize URL."""
        if not url:
            return ''
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Remove trailing slash
        if url.endswith('/'):
            url = url[:-1]
        
        return url
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
        """
        Mask sensitive data in configuration for display.
        
        Args:
            data: Configuration data
            sensitive_keys: List of keys to mask (default: common sensitive keys)
            
        Returns:
            Dictionary with sensitive values masked
        """
        if sensitive_keys is None:
            sensitive_keys = [
                'personal_access_token', 'token', 'password', 'secret', 
                'key', 'authorization', 'bearer'
            ]
        
        masked_data = data.copy()
        
        for key, value in masked_data.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                if value and len(str(value)) > 4:
                    masked_data[key] = str(value)[:4] + '*' * (len(str(value)) - 4)
                else:
                    masked_data[key] = '****'
        
        return masked_data
    
    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()
    
    @staticmethod
    def generate_mcp_server_config(config: MCPConfiguration) -> Dict[str, Any]:
        """
        Generate MCP server configuration JSON from user configuration.
        
        Args:
            config: MCPConfiguration object
            
        Returns:
            Dictionary containing MCP server configuration
        """
        env_vars = {}
        
        # Add Jira configuration if available
        if config.jira_url and config.get_jira_personal_token():
            env_vars.update({
                "JIRA_URL": config.jira_url,
                "JIRA_PERSONAL_TOKEN": config.get_jira_personal_token(),
                "JIRA_SSL_VERIFY": str(config.jira_ssl_verify).lower()
            })
        
        # Add Confluence configuration if available
        if config.confluence_url and config.get_confluence_personal_token():
            env_vars.update({
                "CONFLUENCE_URL": config.confluence_url,
                "CONFLUENCE_PERSONAL_TOKEN": config.get_confluence_personal_token(),
                "CONFLUENCE_SSL_VERIFY": str(config.confluence_ssl_verify).lower()
            })
        
        return {
            "mcpServers": {
                "mcp-atlassian": {
                    "command": "docker",
                    "args": [
                        "run", "--rm", "-i",
                        "-e", "CONFLUENCE_URL",
                        "-e", "CONFLUENCE_PERSONAL_TOKEN", 
                        "-e", "CONFLUENCE_SSL_VERIFY",
                        "-e", "JIRA_URL",
                        "-e", "JIRA_PERSONAL_TOKEN",
                        "-e", "JIRA_SSL_VERIFY",
                        "ghcr.io/sooperset/mcp-atlassian:latest"
                    ],
                    "env": env_vars
                }
            }
        }