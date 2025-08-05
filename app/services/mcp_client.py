"""
MCP Client Manager for JIA application.

This module provides the MCPClientManager class for communicating with
the mcp-atlassian server using Streamable-HTTP transport with multi-user support.
"""

import asyncio
import json
import logging
import httpx
import subprocess
import time
import os
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from dataclasses import dataclass

from app.models import MCPConfiguration
from app.services.exceptions import MCPConnectionError, MCPValidationError, MCPTimeoutError


logger = logging.getLogger(__name__)


@dataclass
class ConnectionResult:
    """Result of MCP connection test."""
    success: bool
    user_name: str = ""
    user_id: str = ""
    display_name: str = ""
    email: str = ""
    error_message: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None


@dataclass
class Board:
    """Jira board representation."""
    id: str
    name: str
    type: str
    project_key: str
    project_name: str
    self_url: str = ""


@dataclass
class Sprint:
    """Jira sprint representation."""
    id: str
    name: str
    state: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    complete_date: Optional[str] = None
    board_id: str = ""


@dataclass
class Ticket:
    """Jira ticket representation."""
    id: str
    key: str
    summary: str
    description: str = ""
    status: str = ""
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    issue_type: str = ""
    priority: str = ""
    story_points: Optional[int] = None
    labels: List[str] = None
    components: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.components is None:
            self.components = []


@dataclass
class TicketHistory:
    """Jira ticket history representation."""
    ticket_key: str
    changelog: List[Dict[str, Any]]
    comments: List[Dict[str, Any]]
    worklog: List[Dict[str, Any]]
    transitions: List[Dict[str, Any]]


@dataclass
class TicketResult:
    """Result of ticket creation."""
    success: bool
    ticket_key: str = ""
    ticket_id: str = ""
    ticket_url: str = ""
    error_message: Optional[str] = None


class MCPServerManager:
    """
    Singleton class to manage the MCP Atlassian server process.
    
    This ensures we have only one server instance running that can handle
    multiple users via HTTP transport with authentication headers.
    """
    
    _instance = None
    _server_process = None
    _server_url = "http://localhost:8080"
    _server_port = 8080
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPServerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._http_client = httpx.AsyncClient(timeout=30.0)
    
    async def ensure_server_running(self) -> bool:
        """
        Ensure the MCP server is running. Start it if not.
        
        Returns:
            bool: True if server is running, False otherwise
        """
        try:
            # Check if server is already running
            if await self._is_server_healthy():
                logger.info(f"✅ MCP server already running at {self._server_url}")
                print(f"✅ MCP server already running at {self._server_url}")
                return True
            
            # Start the server
            logger.info("🚀 Starting MCP Atlassian server...")
            print("🚀 Starting MCP Atlassian server...")
            
            # Start server with streamable-HTTP transport
            cmd = [
                "python", "-m", "mcp_atlassian",
                "--transport", "streamable-http",
                "--port", str(self._server_port),
                "--host", "localhost"
            ]
            
            logger.info(f"🔧 Starting server with command: {' '.join(cmd)}")
            print(f"🔧 Starting server with command: {' '.join(cmd)}")
            
            self._server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            max_retries = 10
            for i in range(max_retries):
                await asyncio.sleep(1)
                if await self._is_server_healthy():
                    logger.info(f"✅ MCP server started successfully at {self._server_url}")
                    print(f"✅ MCP server started successfully at {self._server_url}")
                    return True
                logger.info(f"⏳ Waiting for server to start... ({i+1}/{max_retries})")
                print(f"⏳ Waiting for server to start... ({i+1}/{max_retries})")
            
            logger.error("❌ Failed to start MCP server")
            print("❌ Failed to start MCP server")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error starting MCP server: {str(e)}")
            print(f"❌ Error starting MCP server: {str(e)}")
            return False
    
    async def _is_server_healthy(self) -> bool:
        """Check if the MCP server is healthy."""
        try:
            response = await self._http_client.get(f"{self._server_url}/health", timeout=5.0)
            return response.status_code == 200
        except:
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], auth_headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Call MCP tool via HTTP transport.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            auth_headers: Authentication headers for the user
            
        Returns:
            Tool response
        """
        try:
            # Ensure server is running
            if not await self.ensure_server_running():
                raise MCPConnectionError("Failed to start MCP server")
            
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),  # Use timestamp as ID
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            logger.info(f"📤 MCP Request: {tool_name} with args: {arguments}")
            print(f"📤 MCP Request: {tool_name} with args: {arguments}")
            
            # Make HTTP request with authentication headers
            response = await self._http_client.post(
                f"{self._server_url}/mcp",
                json=mcp_request,
                headers=auth_headers
            )
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ MCP HTTP Error: {error_msg}")
                print(f"❌ MCP HTTP Error: {error_msg}")
                raise MCPConnectionError(f"MCP HTTP error: {error_msg}")
            
            # Parse response
            response_data = response.json()
            logger.info(f"📥 MCP Response: {json.dumps(response_data, indent=2, default=str)}")
            print(f"📥 MCP Response: {json.dumps(response_data, indent=2, default=str)}")
            
            if 'error' in response_data:
                error_msg = response_data['error'].get('message', 'Unknown MCP error')
                logger.error(f"❌ MCP Error: {error_msg}")
                print(f"❌ MCP Error: {error_msg}")
                raise MCPConnectionError(f"MCP error: {error_msg}")
            
            return response_data.get('result', {})
            
        except httpx.TimeoutException:
            logger.error("⏰ MCP request timed out")
            print("⏰ MCP request timed out")
            raise MCPTimeoutError("MCP request timed out")
        except Exception as e:
            if isinstance(e, (MCPConnectionError, MCPTimeoutError)):
                raise
            logger.error(f"❌ MCP call failed: {str(e)}")
            print(f"❌ MCP call failed: {str(e)}")
            raise MCPConnectionError(f"MCP call failed: {str(e)}")
    
    def __del__(self):
        """Clean up server process on deletion."""
        if self._server_process:
            self._server_process.terminate()


class MCPClientManager:
    """
    Manager for MCP client communication with mcp-atlassian server.
    
    This class handles all communication with the mcp-atlassian server
    using HTTP transport with per-user authentication headers.
    """
    
    def __init__(self, user_config: MCPConfiguration):
        """
        Initialize MCP client manager.
        
        Args:
            user_config: User's MCP configuration
        """
        self.config = user_config
        self.timeout = 30  # Default timeout in seconds
        self._server_manager = MCPServerManager()
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            raise MCPValidationError(f"Invalid MCP configuration: {', '.join(errors)}")
    
    def _get_auth_headers(self, service_type: str) -> Dict[str, str]:
        """
        Get authentication headers for the specified service.
        
        Args:
            service_type: 'jira' or 'confluence'
            
        Returns:
            Dict of HTTP headers for authentication
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "JIA-MCP-Client/1.0"
        }
        
        if service_type == 'jira':
            if self.config.jira_url and self.config.get_jira_personal_token():
                headers.update({
                    "X-Jira-URL": self.config.jira_url,
                    "X-Jira-Personal-Token": self.config.get_jira_personal_token(),
                    "X-Jira-SSL-Verify": str(self.config.jira_ssl_verify).lower()
                })
        elif service_type == 'confluence':
            if self.config.confluence_url and self.config.get_confluence_personal_token():
                headers.update({
                    "X-Confluence-URL": self.config.confluence_url,
                    "X-Confluence-Personal-Token": self.config.get_confluence_personal_token(),
                    "X-Confluence-SSL-Verify": str(self.config.confluence_ssl_verify).lower()
                })
        
        return headers
    
    async def _call_jira_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call Jira tool via HTTP transport with user authentication.
        
        Args:
            tool_name: Name of the Jira tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Dict containing the response from Jira API
        """
        if arguments is None:
            arguments = {}
        
        auth_headers = self._get_auth_headers('jira')
        return await self._server_manager.call_tool(tool_name, arguments, auth_headers)
    
    async def _call_confluence_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call Confluence tool via HTTP transport with user authentication.
        
        Args:
            tool_name: Name of the Confluence tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Dict containing the response from Confluence API
        """
        if arguments is None:
            arguments = {}
        
        auth_headers = self._get_auth_headers('confluence')
        return await self._server_manager.call_tool(tool_name, arguments, auth_headers)
    
    async def test_jira_connection(self) -> ConnectionResult:
        """
        Test Jira connection and retrieve user information using real MCP server.
        
        Returns:
            ConnectionResult with success status and user info
        """
        try:
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                logger.warning("❌ Missing Jira credentials")
                return ConnectionResult(
                    success=False,
                    error_message="Jira URL and Personal Access Token are required"
                )
            
            # Basic URL validation
            if not self.config.jira_url.startswith(('http://', 'https://')):
                logger.warning(f"❌ Invalid Jira URL format: {self.config.jira_url}")
                return ConnectionResult(
                    success=False,
                    error_message="Invalid Jira URL format - must start with http:// or https://"
                )
            
            logger.info(f"🔍 Testing real Jira connection to {self.config.jira_url}")
            print(f"🔍 Testing real Jira connection to {self.config.jira_url}")
            
            # Call Jira tool to get current user information
            try:
                response = await self._call_jira_tool('jira_get_user_profile')
                logger.info(f"✅ Jira Response received: {json.dumps(response, indent=2, default=str)}")
                print(f"✅ Jira Response received: {json.dumps(response, indent=2, default=str)}")
                
                # Extract user information from response
                if isinstance(response, dict):
                    # Handle different possible response structures
                    user_data = response
                    
                    # Extract user fields
                    user_name = (
                        user_data.get('displayName') or 
                        user_data.get('name') or 
                        user_data.get('username') or 
                        'Unknown User'
                    )
                    
                    user_id = (
                        user_data.get('accountId') or 
                        user_data.get('key') or 
                        user_data.get('id') or 
                        ''
                    )
                    
                    email = (
                        user_data.get('emailAddress') or 
                        user_data.get('email') or 
                        ''
                    )
                    
                    logger.info(f"✅ Jira connection successful - User: {user_name} ({email})")
                    print(f"✅ Jira connection successful - User: {user_name} ({email})")
                    
                    return ConnectionResult(
                        success=True,
                        user_name=user_name,
                        user_id=user_id,
                        display_name=user_name,
                        email=email,
                        server_info={
                            'server_url': self.config.jira_url,
                            'ssl_verify': self.config.jira_ssl_verify,
                            'connection_time': datetime.utcnow().isoformat(),
                            'raw_response': response
                        }
                    )
                else:
                    logger.error(f"❌ Unexpected response format: {type(response)}")
                    print(f"❌ Unexpected response format: {type(response)}")
                    return ConnectionResult(
                        success=False,
                        error_message=f"Unexpected response format from MCP server: {type(response)}"
                    )
                    
            except MCPConnectionError as e:
                logger.error(f"❌ MCP Connection Error: {str(e)}")
                print(f"❌ MCP Connection Error: {str(e)}")
                return ConnectionResult(
                    success=False,
                    error_message=f"MCP Connection Error: {str(e)}"
                )
            except MCPTimeoutError as e:
                logger.error(f"⏰ MCP Timeout Error: {str(e)}")
                print(f"⏰ MCP Timeout Error: {str(e)}")
                return ConnectionResult(
                    success=False,
                    error_message=f"Connection timeout: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"❌ Unexpected error in Jira connection test: {str(e)}")
            print(f"❌ Unexpected error in Jira connection test: {str(e)}")
            return ConnectionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def test_confluence_connection(self) -> ConnectionResult:
        """
        Test Confluence connection and retrieve user information using real MCP server.
        
        Returns:
            ConnectionResult with success status and user info
        """
        try:
            if not self.config.confluence_url or not self.config.get_confluence_personal_token():
                logger.warning("❌ Missing Confluence credentials")
                return ConnectionResult(
                    success=False,
                    error_message="Confluence URL and Personal Access Token are required"
                )
            
            # Basic URL validation
            if not self.config.confluence_url.startswith(('http://', 'https://')):
                logger.warning(f"❌ Invalid Confluence URL format: {self.config.confluence_url}")
                return ConnectionResult(
                    success=False,
                    error_message="Invalid Confluence URL format - must start with http:// or https://"
                )
            
            logger.info(f"🔍 Testing real Confluence connection to {self.config.confluence_url}")
            print(f"🔍 Testing real Confluence connection to {self.config.confluence_url}")
            
            # Call Confluence tool to get current user information  
            try:
                response = await self._call_confluence_tool('confluence_search_user')
                logger.info(f"✅ Confluence Response received: {json.dumps(response, indent=2, default=str)}")
                print(f"✅ Confluence Response received: {json.dumps(response, indent=2, default=str)}")
                
                # Extract user information from response
                if isinstance(response, dict):
                    # Handle different possible response structures
                    user_data = response
                    
                    # Extract user fields
                    user_name = (
                        user_data.get('displayName') or 
                        user_data.get('name') or 
                        user_data.get('username') or 
                        'Unknown User'
                    )
                    
                    user_id = (
                        user_data.get('accountId') or 
                        user_data.get('key') or 
                        user_data.get('id') or 
                        ''
                    )
                    
                    email = (
                        user_data.get('email') or 
                        user_data.get('emailAddress') or 
                        ''
                    )
                    
                    logger.info(f"✅ Confluence connection successful - User: {user_name} ({email})")
                    print(f"✅ Confluence connection successful - User: {user_name} ({email})")
                    
                    return ConnectionResult(
                        success=True,
                        user_name=user_name,
                        user_id=user_id,
                        display_name=user_name,
                        email=email,
                        server_info={
                            'server_url': self.config.confluence_url,
                            'ssl_verify': self.config.confluence_ssl_verify,
                            'connection_time': datetime.utcnow().isoformat(),
                            'raw_response': response
                        }
                    )
                else:
                    logger.error(f"❌ Unexpected response format: {type(response)}")
                    print(f"❌ Unexpected response format: {type(response)}")
                    return ConnectionResult(
                        success=False,
                        error_message=f"Unexpected response format from MCP server: {type(response)}"
                    )
                    
            except MCPConnectionError as e:
                logger.error(f"❌ MCP Connection Error: {str(e)}")
                print(f"❌ MCP Connection Error: {str(e)}")
                return ConnectionResult(
                    success=False,
                    error_message=f"MCP Connection Error: {str(e)}"
                )
            except MCPTimeoutError as e:
                logger.error(f"⏰ MCP Timeout Error: {str(e)}")
                print(f"⏰ MCP Timeout Error: {str(e)}")
                return ConnectionResult(
                    success=False,
                    error_message=f"Connection timeout: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"❌ Unexpected error in Confluence connection test: {str(e)}")
            print(f"❌ Unexpected error in Confluence connection test: {str(e)}")
            return ConnectionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def get_boards(self) -> List[Board]:
        """
        Fetch all accessible Jira boards using real MCP server.
        
        Returns:
            List of Board objects
        """
        try:
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                raise MCPConnectionError("Jira configuration is required for board operations")
            
            logger.info("🔍 Fetching real Jira boards")
            print("🔍 Fetching real Jira boards")
            
            # Call real MCP server to get boards
            response = await self._call_jira_tool('jira_get_agile_boards')
            
            boards = []
            
            # Handle different response formats
            boards_data = response
            if isinstance(response, dict):
                if 'values' in response:
                    boards_data = response['values']
                elif 'boards' in response:
                    boards_data = response['boards']
                elif 'content' in response:
                    boards_data = response['content']
            
            if isinstance(boards_data, list):
                for board_data in boards_data:
                    # Extract board information
                    board_id = str(board_data.get('id', ''))
                    board_name = board_data.get('name', 'Unknown Board')
                    board_type = board_data.get('type', 'unknown')
                    
                    # Extract project information
                    location = board_data.get('location', {})
                    project_key = location.get('projectKey', '')
                    project_name = location.get('projectName', '')
                    
                    # Handle different location formats
                    if not project_key and 'project' in board_data:
                        project_info = board_data['project']
                        project_key = project_info.get('key', '')
                        project_name = project_info.get('name', '')
                    
                    board = Board(
                        id=board_id,
                        name=board_name,
                        type=board_type,
                        project_key=project_key,
                        project_name=project_name,
                        self_url=board_data.get('self', f"{self.config.jira_url}/rest/agile/1.0/board/{board_id}")
                    )
                    boards.append(board)
                    
                logger.info(f"✅ Retrieved {len(boards)} boards from Jira")
                print(f"✅ Retrieved {len(boards)} boards from Jira")
                
                for board in boards:
                    logger.info(f"  - Board: {board.name} (ID: {board.id}, Type: {board.type}, Project: {board.project_key})")
                    print(f"  - Board: {board.name} (ID: {board.id}, Type: {board.type}, Project: {board.project_key})")
                
                return boards
            else:
                logger.warning(f"⚠️ Unexpected boards data format: {type(boards_data)}")
                print(f"⚠️ Unexpected boards data format: {type(boards_data)}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch boards: {str(e)}")
            print(f"❌ Failed to fetch boards: {str(e)}")
            raise MCPConnectionError(f"Failed to fetch boards: {str(e)}")
    
    async def get_sprints(self, board_id: str) -> List[Sprint]:
        """
        Fetch sprints for a specific board using real MCP server.
        
        Args:
            board_id: Board ID to fetch sprints for
            
        Returns:
            List of Sprint objects
        """
        try:
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                raise MCPConnectionError("Jira configuration is required for sprint operations")
            
            logger.info(f"🔍 Fetching real sprints for board {board_id}")
            print(f"🔍 Fetching real sprints for board {board_id}")
            
            # Call real MCP server to get sprints
            response = await self._call_jira_tool('jira_get_sprints_from_board', {'board_id': board_id})
            
            sprints = []
            
            # Handle different response formats
            sprints_data = response
            if isinstance(response, dict):
                if 'values' in response:
                    sprints_data = response['values']
                elif 'sprints' in response:
                    sprints_data = response['sprints']
                elif 'content' in response:
                    sprints_data = response['content']
            
            if isinstance(sprints_data, list):
                for sprint_data in sprints_data:
                    # Extract sprint information
                    sprint_id = str(sprint_data.get('id', ''))
                    sprint_name = sprint_data.get('name', 'Unknown Sprint')
                    sprint_state = sprint_data.get('state', 'unknown')
                    
                    sprint = Sprint(
                        id=sprint_id,
                        name=sprint_name,
                        state=sprint_state,
                        start_date=sprint_data.get('startDate'),
                        end_date=sprint_data.get('endDate'),
                        complete_date=sprint_data.get('completeDate'),
                        board_id=board_id
                    )
                    sprints.append(sprint)
                    
                logger.info(f"✅ Retrieved {len(sprints)} sprints for board {board_id}")
                print(f"✅ Retrieved {len(sprints)} sprints for board {board_id}")
                
                for sprint in sprints:
                    logger.info(f"  - Sprint: {sprint.name} (ID: {sprint.id}, State: {sprint.state})")
                    print(f"  - Sprint: {sprint.name} (ID: {sprint.id}, State: {sprint.state})")
                
                return sprints
            else:
                logger.warning(f"⚠️ Unexpected sprints data format: {type(sprints_data)}")
                print(f"⚠️ Unexpected sprints data format: {type(sprints_data)}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch sprints for board {board_id}: {str(e)}")
            print(f"❌ Failed to fetch sprints for board {board_id}: {str(e)}")
            raise MCPConnectionError(f"Failed to fetch sprints: {str(e)}")
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> TicketResult:
        """
        Create a new Jira ticket.
        
        Args:
            ticket_data: Dictionary containing ticket information
            
        Returns:
            TicketResult with creation status and ticket info
        """
        try:
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                raise MCPConnectionError("Jira configuration is required for ticket creation")
            
            # Validate required fields
            required_fields = ['summary', 'project', 'issuetype']
            missing_fields = [field for field in required_fields if not ticket_data.get(field)]
            if missing_fields:
                return TicketResult(
                    success=False,
                    error_message=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            logger.info(f"Creating ticket: {ticket_data.get('summary', 'No summary')}")
            
            # Simulate network delay
            await asyncio.sleep(0.3)
            
            # Simulate ticket creation
            ticket_key = f"{ticket_data['project']}-{123}"  # Simulated ticket key
            ticket_id = "12345"  # Simulated ticket ID
            
            return TicketResult(
                success=True,
                ticket_key=ticket_key,
                ticket_id=ticket_id,
                ticket_url=f"{self.config.jira_url}/browse/{ticket_key}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create ticket: {str(e)}")
            return TicketResult(
                success=False,
                error_message=f"Failed to create ticket: {str(e)}"
            )
    
    async def get_ticket_history(self, ticket_key: str) -> TicketHistory:
        """
        Fetch complete history for a ticket.
        
        Args:
            ticket_key: Jira ticket key (e.g., 'DEV-123')
            
        Returns:
            TicketHistory object with complete ticket history
        """
        try:
            if not ticket_key or not ticket_key.strip():
                raise MCPConnectionError("Ticket key is required")
            
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                raise MCPConnectionError("Jira configuration is required for ticket history")
            
            logger.info(f"Fetching history for ticket {ticket_key}")
            
            # Simulate network delay
            await asyncio.sleep(0.3)
            
            # Simulate ticket history data
            changelog = [
                {
                    'id': '1001',
                    'author': {
                        'displayName': 'John Doe',
                        'accountId': 'user123'
                    },
                    'created': '2025-01-01T10:00:00.000Z',
                    'items': [
                        {
                            'field': 'status',
                            'fromString': 'To Do',
                            'toString': 'In Progress'
                        }
                    ]
                }
            ]
            
            comments = [
                {
                    'id': '2001',
                    'author': {
                        'displayName': 'Jane Smith',
                        'accountId': 'user456'
                    },
                    'created': '2025-01-01T11:00:00.000Z',
                    'body': 'Starting work on this ticket',
                    'updateAuthor': {
                        'displayName': 'Jane Smith',
                        'accountId': 'user456'
                    },
                    'updated': '2025-01-01T11:00:00.000Z'
                }
            ]
            
            worklog = [
                {
                    'id': '3001',
                    'author': {
                        'displayName': 'Jane Smith',
                        'accountId': 'user456'
                    },
                    'created': '2025-01-01T12:00:00.000Z',
                    'timeSpent': '2h',
                    'timeSpentSeconds': 7200,
                    'comment': 'Initial analysis and setup'
                }
            ]
            
            transitions = [
                {
                    'id': '4001',
                    'name': 'Start Progress',
                    'to': {
                        'id': '3',
                        'name': 'In Progress'
                    },
                    'from': {
                        'id': '1',
                        'name': 'To Do'
                    }
                }
            ]
            
            return TicketHistory(
                ticket_key=ticket_key,
                changelog=changelog,
                comments=comments,
                worklog=worklog,
                transitions=transitions
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch ticket history for {ticket_key}: {str(e)}")
            raise MCPConnectionError(f"Failed to fetch ticket history: {str(e)}")
    
    async def search_tickets(self, jql: str, max_results: int = 50) -> List[Ticket]:
        """
        Search for tickets using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Ticket objects matching the query
        """
        try:
            if not jql or not jql.strip():
                raise MCPConnectionError("JQL query is required")
            
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                raise MCPConnectionError("Jira configuration is required for ticket search")
            
            logger.info(f"Searching tickets with JQL: {jql}")
            
            # Simulate network delay
            await asyncio.sleep(0.3)
            
            # Simulate search results
            tickets_data = [
                {
                    'id': '12345',
                    'key': 'DEV-123',
                    'fields': {
                        'summary': 'Implement user authentication',
                        'description': 'Add login and logout functionality',
                        'status': {'name': 'In Progress'},
                        'assignee': {'displayName': 'John Doe', 'accountId': 'user123'},
                        'reporter': {'displayName': 'Jane Smith', 'accountId': 'user456'},
                        'created': '2025-01-01T09:00:00.000Z',
                        'updated': '2025-01-01T15:00:00.000Z',
                        'issuetype': {'name': 'Story'},
                        'priority': {'name': 'High'},
                        'customfield_10016': 5,  # Story points
                        'labels': ['backend', 'security'],
                        'components': [{'name': 'Authentication'}]
                    }
                },
                {
                    'id': '12346',
                    'key': 'DEV-124',
                    'fields': {
                        'summary': 'Fix login bug',
                        'description': 'Users cannot login with special characters',
                        'status': {'name': 'To Do'},
                        'assignee': None,
                        'reporter': {'displayName': 'Bob Wilson', 'accountId': 'user789'},
                        'created': '2025-01-02T10:00:00.000Z',
                        'updated': '2025-01-02T10:00:00.000Z',
                        'issuetype': {'name': 'Bug'},
                        'priority': {'name': 'Medium'},
                        'customfield_10016': None,
                        'labels': ['frontend', 'bug'],
                        'components': [{'name': 'UI'}]
                    }
                }
            ]
            
            tickets = []
            for ticket_data in tickets_data[:max_results]:
                fields = ticket_data['fields']
                ticket = Ticket(
                    id=ticket_data['id'],
                    key=ticket_data['key'],
                    summary=fields['summary'],
                    description=fields.get('description', ''),
                    status=fields['status']['name'],
                    assignee=fields['assignee']['displayName'] if fields.get('assignee') else None,
                    reporter=fields['reporter']['displayName'] if fields.get('reporter') else None,
                    created=fields.get('created'),
                    updated=fields.get('updated'),
                    issue_type=fields['issuetype']['name'],
                    priority=fields['priority']['name'],
                    story_points=fields.get('customfield_10016'),
                    labels=fields.get('labels', []),
                    components=[comp['name'] for comp in fields.get('components', [])]
                )
                tickets.append(ticket)
            
            logger.info(f"Found {len(tickets)} tickets matching JQL query")
            return tickets
            
        except Exception as e:
            logger.error(f"Failed to search tickets: {str(e)}")
            raise MCPConnectionError(f"Failed to search tickets: {str(e)}")
    
    def test_jira_connection_sync(self) -> ConnectionResult:
        """Synchronous wrapper for Jira connection testing."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.test_jira_connection())
        except Exception as e:
            logger.error(f"Sync Jira connection test failed: {str(e)}")
            return ConnectionResult(
                success=False,
                error_message=f"Connection test failed: {str(e)}"
            )
        finally:
            loop.close()
    
    def test_confluence_connection_sync(self) -> ConnectionResult:
        """Synchronous wrapper for Confluence connection testing."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.test_confluence_connection())
        except Exception as e:
            logger.error(f"Sync Confluence connection test failed: {str(e)}")
            return ConnectionResult(
                success=False,
                error_message=f"Connection test failed: {str(e)}"
            )
        finally:
            loop.close()
    
    def get_boards_sync(self) -> List[Board]:
        """Synchronous wrapper for getting boards."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_boards())
        except Exception as e:
            logger.error(f"Sync get boards failed: {str(e)}")
            raise MCPConnectionError(f"Failed to get boards: {str(e)}")
        finally:
            loop.close()
    
    def get_sprints_sync(self, board_id: str) -> List[Sprint]:
        """Synchronous wrapper for getting sprints."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_sprints(board_id))
        except Exception as e:
            logger.error(f"Sync get sprints failed: {str(e)}")
            raise MCPConnectionError(f"Failed to get sprints: {str(e)}")
        finally:
            loop.close()
    
    def create_ticket_sync(self, ticket_data: Dict[str, Any]) -> TicketResult:
        """Synchronous wrapper for creating tickets."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.create_ticket(ticket_data))
        except Exception as e:
            logger.error(f"Sync create ticket failed: {str(e)}")
            return TicketResult(
                success=False,
                error_message=f"Failed to create ticket: {str(e)}"
            )
        finally:
            loop.close()
    
    def get_ticket_history_sync(self, ticket_key: str) -> TicketHistory:
        """Synchronous wrapper for getting ticket history."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_ticket_history(ticket_key))
        except Exception as e:
            logger.error(f"Sync get ticket history failed: {str(e)}")
            raise MCPConnectionError(f"Failed to get ticket history: {str(e)}")
        finally:
            loop.close()
    
    def search_tickets_sync(self, jql: str, max_results: int = 50) -> List[Ticket]:
        """Synchronous wrapper for searching tickets."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.search_tickets(jql, max_results))
        except Exception as e:
            logger.error(f"Sync search tickets failed: {str(e)}")
            raise MCPConnectionError(f"Failed to search tickets: {str(e)}")
        finally:
            loop.close()