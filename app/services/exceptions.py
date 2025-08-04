"""
Custom exceptions for JIA services.

This module defines custom exception classes for different types of
errors that can occur in the JIA application services.
"""


class JIAException(Exception):
    """Base exception class for JIA application."""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        """
        Initialize JIA exception.
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            status_code: HTTP status code for web responses
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code


class MCPException(JIAException):
    """Base exception for MCP-related errors."""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        super().__init__(message, error_code or "MCP_ERROR", status_code)


class MCPConnectionError(MCPException):
    """Exception raised when MCP connection fails."""
    
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message, "MCP_CONNECTION_ERROR", status_code)


class MCPValidationError(MCPException):
    """Exception raised when MCP configuration validation fails."""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, "MCP_VALIDATION_ERROR", status_code)


class MCPTimeoutError(MCPException):
    """Exception raised when MCP operation times out."""
    
    def __init__(self, message: str, status_code: int = 408):
        super().__init__(message, "MCP_TIMEOUT_ERROR", status_code)


class MCPAuthenticationError(MCPException):
    """Exception raised when MCP authentication fails."""
    
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message, "MCP_AUTHENTICATION_ERROR", status_code)


class MCPAuthorizationError(MCPException):
    """Exception raised when MCP authorization fails."""
    
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message, "MCP_AUTHORIZATION_ERROR", status_code)


class AIServiceException(JIAException):
    """Base exception for AI service-related errors."""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        super().__init__(message, error_code or "AI_SERVICE_ERROR", status_code)


class AIConnectionError(AIServiceException):
    """Exception raised when AI service connection fails."""
    
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message, "AI_CONNECTION_ERROR", status_code)


class AIValidationError(AIServiceException):
    """Exception raised when AI service validation fails."""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, "AI_VALIDATION_ERROR", status_code)


class AITimeoutError(AIServiceException):
    """Exception raised when AI service operation times out."""
    
    def __init__(self, message: str, status_code: int = 408):
        super().__init__(message, "AI_TIMEOUT_ERROR", status_code)


class ConfigurationError(JIAException):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, "CONFIGURATION_ERROR", status_code)


class ValidationError(JIAException):
    """Exception raised for general validation errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, "VALIDATION_ERROR", status_code)


class AuthenticationError(JIAException):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message, "AUTHENTICATION_ERROR", status_code)


class AuthorizationError(JIAException):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message, "AUTHORIZATION_ERROR", status_code)


class NotFoundError(JIAException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, message: str, status_code: int = 404):
        super().__init__(message, "NOT_FOUND_ERROR", status_code)


class ConflictError(JIAException):
    """Exception raised for resource conflicts."""
    
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message, "CONFLICT_ERROR", status_code)


class RateLimitError(JIAException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, message: str, status_code: int = 429):
        super().__init__(message, "RATE_LIMIT_ERROR", status_code)


class ServiceUnavailableError(JIAException):
    """Exception raised when a service is temporarily unavailable."""
    
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message, "SERVICE_UNAVAILABLE_ERROR", status_code)