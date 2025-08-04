"""
Connection service for JIA application.

This module provides unified connection testing and validation
for both Jira and Confluence services.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.models import MCPConfiguration
from app.services.mcp_client import MCPClientManager, ConnectionResult
from app.services.jira_service import JiraService
from app.services.confluence_service import ConfluenceService
from app.services.exceptions import MCPConnectionError, ValidationError


logger = logging.getLogger(__name__)


class ConnectionService:
    """
    Unified service for testing and validating MCP connections.
    
    This service provides a single interface for testing both
    Jira and Confluence connections.
    """
    
    def __init__(self, user_config: MCPConfiguration):
        """
        Initialize connection service.
        
        Args:
            user_config: User's MCP configuration
        """
        self.config = user_config
        self.client = MCPClientManager(user_config)
    
    def test_all_connections(self) -> Dict[str, Any]:
        """
        Test all configured connections (Jira and Confluence).
        
        Returns:
            Dictionary with test results for all services
        """
        results = {
            'overall_success': True,
            'tested_at': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Test Jira connection if configured
        if self.config.jira_url and self.config.get_jira_personal_token():
            try:
                jira_service = JiraService(self.config)
                jira_result = jira_service.test_connection()
                results['services']['jira'] = jira_result
                
                if not jira_result['success']:
                    results['overall_success'] = False
                    
            except Exception as e:
                logger.error(f"Jira connection test failed: {str(e)}")
                results['services']['jira'] = {
                    'success': False,
                    'message': f"Test failed: {str(e)}",
                    'user_info': None,
                    'server_info': None,
                    'tested_at': datetime.utcnow().isoformat()
                }
                results['overall_success'] = False
        else:
            results['services']['jira'] = {
                'success': False,
                'message': 'Jira not configured',
                'user_info': None,
                'server_info': None,
                'tested_at': datetime.utcnow().isoformat()
            }
        
        # Test Confluence connection if configured
        if self.config.confluence_url and self.config.get_confluence_personal_token():
            try:
                confluence_service = ConfluenceService(self.config)
                confluence_result = confluence_service.test_connection()
                results['services']['confluence'] = confluence_result
                
                if not confluence_result['success']:
                    results['overall_success'] = False
                    
            except Exception as e:
                logger.error(f"Confluence connection test failed: {str(e)}")
                results['services']['confluence'] = {
                    'success': False,
                    'message': f"Test failed: {str(e)}",
                    'user_info': None,
                    'server_info': None,
                    'tested_at': datetime.utcnow().isoformat()
                }
                results['overall_success'] = False
        else:
            results['services']['confluence'] = {
                'success': False,
                'message': 'Confluence not configured',
                'user_info': None,
                'server_info': None,
                'tested_at': datetime.utcnow().isoformat()
            }
        
        return results
    
    def test_jira_connection(self) -> Dict[str, Any]:
        """
        Test Jira connection specifically.
        
        Returns:
            Dictionary with Jira connection test results
        """
        try:
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                return {
                    'success': False,
                    'message': 'Jira URL and Personal Access Token are required',
                    'user_info': None,
                    'server_info': None,
                    'tested_at': datetime.utcnow().isoformat()
                }
            
            jira_service = JiraService(self.config)
            return jira_service.test_connection()
            
        except Exception as e:
            logger.error(f"Jira connection test failed: {str(e)}")
            return {
                'success': False,
                'message': f"Connection test failed: {str(e)}",
                'user_info': None,
                'server_info': None,
                'tested_at': datetime.utcnow().isoformat()
            }
    
    def test_confluence_connection(self) -> Dict[str, Any]:
        """
        Test Confluence connection specifically.
        
        Returns:
            Dictionary with Confluence connection test results
        """
        try:
            if not self.config.confluence_url or not self.config.get_confluence_personal_token():
                return {
                    'success': False,
                    'message': 'Confluence URL and Personal Access Token are required',
                    'user_info': None,
                    'server_info': None,
                    'tested_at': datetime.utcnow().isoformat()
                }
            
            confluence_service = ConfluenceService(self.config)
            return confluence_service.test_connection()
            
        except Exception as e:
            logger.error(f"Confluence connection test failed: {str(e)}")
            return {
                'success': False,
                'message': f"Connection test failed: {str(e)}",
                'user_info': None,
                'server_info': None,
                'tested_at': datetime.utcnow().isoformat()
            }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the MCP configuration without testing connections.
        
        Returns:
            Dictionary with validation results
        """
        try:
            errors = self.config.validate()
            
            validation_result = {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': [],
                'validated_at': datetime.utcnow().isoformat()
            }
            
            # Add warnings for incomplete configurations
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                validation_result['warnings'].append('Jira configuration is incomplete')
            
            if not self.config.confluence_url or not self.config.get_confluence_personal_token():
                validation_result['warnings'].append('Confluence configuration is incomplete')
            
            # Check for legacy configuration
            if self.config.server_url or self.config.get_personal_access_token():
                validation_result['warnings'].append('Legacy configuration detected - consider migrating to separate Jira/Confluence settings')
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'validated_at': datetime.utcnow().isoformat()
            }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status without performing new tests.
        
        Returns:
            Dictionary with connection status information
        """
        try:
            status = {
                'jira': {
                    'configured': bool(self.config.jira_url and self.config.get_jira_personal_token()),
                    'url': self.config.jira_url,
                    'ssl_verify': self.config.jira_ssl_verify,
                    'has_token': bool(self.config.get_jira_personal_token())
                },
                'confluence': {
                    'configured': bool(self.config.confluence_url and self.config.get_confluence_personal_token()),
                    'url': self.config.confluence_url,
                    'ssl_verify': self.config.confluence_ssl_verify,
                    'has_token': bool(self.config.get_confluence_personal_token())
                },
                'legacy': {
                    'configured': bool(self.config.server_url and self.config.get_personal_access_token()),
                    'url': self.config.server_url,
                    'has_token': bool(self.config.get_personal_access_token())
                },
                'last_tested': self.config.last_tested.isoformat() if self.config.last_tested else None,
                'is_active': self.config.is_active,
                'checked_at': datetime.utcnow().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get connection status: {str(e)}")
            return {
                'error': f"Failed to get status: {str(e)}",
                'checked_at': datetime.utcnow().isoformat()
            }
    
    def get_service_capabilities(self) -> Dict[str, Any]:
        """
        Get capabilities of configured services.
        
        Returns:
            Dictionary with service capabilities
        """
        capabilities = {
            'jira': {
                'available': bool(self.config.jira_url and self.config.get_jira_personal_token()),
                'features': [
                    'boards',
                    'sprints',
                    'tickets',
                    'search',
                    'history',
                    'creation',
                    'reports'
                ] if self.config.jira_url and self.config.get_jira_personal_token() else []
            },
            'confluence': {
                'available': bool(self.config.confluence_url and self.config.get_confluence_personal_token()),
                'features': [
                    'spaces',
                    'pages',
                    'search',
                    'content',
                    'attachments',
                    'creation',
                    'updates'
                ] if self.config.confluence_url and self.config.get_confluence_personal_token() else []
            },
            'checked_at': datetime.utcnow().isoformat()
        }
        
        return capabilities
    
    def diagnose_connection_issues(self) -> Dict[str, Any]:
        """
        Diagnose potential connection issues.
        
        Returns:
            Dictionary with diagnostic information
        """
        diagnosis = {
            'issues': [],
            'recommendations': [],
            'checked_at': datetime.utcnow().isoformat()
        }
        
        # Check Jira configuration
        if self.config.jira_url:
            if not self.config.jira_url.startswith(('http://', 'https://')):
                diagnosis['issues'].append('Jira URL should start with http:// or https://')
                diagnosis['recommendations'].append('Update Jira URL to include protocol')
            
            if not self.config.get_jira_personal_token():
                diagnosis['issues'].append('Jira Personal Access Token is missing')
                diagnosis['recommendations'].append('Configure Jira Personal Access Token')
        
        # Check Confluence configuration
        if self.config.confluence_url:
            if not self.config.confluence_url.startswith(('http://', 'https://')):
                diagnosis['issues'].append('Confluence URL should start with http:// or https://')
                diagnosis['recommendations'].append('Update Confluence URL to include protocol')
            
            if not self.config.get_confluence_personal_token():
                diagnosis['issues'].append('Confluence Personal Access Token is missing')
                diagnosis['recommendations'].append('Configure Confluence Personal Access Token')
        
        # Check if no services are configured
        jira_configured = bool(self.config.jira_url and self.config.get_jira_personal_token())
        confluence_configured = bool(self.config.confluence_url and self.config.get_confluence_personal_token())
        
        if not jira_configured and not confluence_configured:
            diagnosis['issues'].append('No services are properly configured')
            diagnosis['recommendations'].append('Configure at least one service (Jira or Confluence)')
        
        # Check SSL verification settings
        if not self.config.jira_ssl_verify and self.config.jira_url:
            diagnosis['issues'].append('Jira SSL verification is disabled')
            diagnosis['recommendations'].append('Enable SSL verification for security')
        
        if not self.config.confluence_ssl_verify and self.config.confluence_url:
            diagnosis['issues'].append('Confluence SSL verification is disabled')
            diagnosis['recommendations'].append('Enable SSL verification for security')
        
        return diagnosis