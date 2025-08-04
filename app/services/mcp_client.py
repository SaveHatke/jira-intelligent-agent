"""
MCP Client Manager for JIA application.

This module provides the MCPClientManager class for communicating with
the mcp-atlassian server to interact with Jira and Confluence.
"""

import asyncio
import json
import logging
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


class MCPClientManager:
    """
    Manager for MCP client communication with mcp-atlassian server.
    
    This class handles all communication with the mcp-atlassian server
    for both Jira and Confluence operations.
    """
    
    def __init__(self, user_config: MCPConfiguration):
        """
        Initialize MCP client manager.
        
        Args:
            user_config: User's MCP configuration
        """
        self.config = user_config
        self.timeout = 30  # Default timeout in seconds
        self._jira_client = None
        self._confluence_client = None
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            raise MCPValidationError(f"Invalid MCP configuration: {', '.join(errors)}")
    
    async def test_jira_connection(self) -> ConnectionResult:
        """
        Test Jira connection and retrieve user information.
        
        Returns:
            ConnectionResult with success status and user info
        """
        try:
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                return ConnectionResult(
                    success=False,
                    error_message="Jira URL and Personal Access Token are required"
                )
            
            # For now, we'll simulate the connection test
            # In a real implementation, this would use the actual mcp-atlassian client
            logger.info(f"Testing Jira connection to {self.config.jira_url}")
            
            # Simulate network delay
            await asyncio.sleep(0.1)
            
            # Basic URL validation
            if not self.config.jira_url.startswith(('http://', 'https://')):
                return ConnectionResult(
                    success=False,
                    error_message="Invalid Jira URL format"
                )
            
            # Simulate successful connection
            user_info = {
                'accountId': 'test_jira_user_id',
                'displayName': 'Test Jira User',
                'emailAddress': 'test@jira.example.com',
                'active': True
            }
            
            return ConnectionResult(
                success=True,
                user_name=user_info.get('displayName', 'Unknown'),
                user_id=user_info.get('accountId', ''),
                display_name=user_info.get('displayName', ''),
                email=user_info.get('emailAddress', ''),
                server_info={
                    'server_url': self.config.jira_url,
                    'ssl_verify': self.config.jira_ssl_verify,
                    'connection_time': datetime.utcnow().isoformat()
                }
            )
            
        except asyncio.TimeoutError:
            logger.error("Jira connection test timed out")
            return ConnectionResult(
                success=False,
                error_message="Connection timeout - please check your Jira URL and network connectivity"
            )
        except Exception as e:
            logger.error(f"Jira connection test failed: {str(e)}")
            return ConnectionResult(
                success=False,
                error_message=f"Connection failed: {str(e)}"
            )
    
    async def test_confluence_connection(self) -> ConnectionResult:
        """
        Test Confluence connection and retrieve user information.
        
        Returns:
            ConnectionResult with success status and user info
        """
        try:
            if not self.config.confluence_url or not self.config.get_confluence_personal_token():
                return ConnectionResult(
                    success=False,
                    error_message="Confluence URL and Personal Access Token are required"
                )
            
            logger.info(f"Testing Confluence connection to {self.config.confluence_url}")
            
            # Simulate network delay
            await asyncio.sleep(0.1)
            
            # Basic URL validation
            if not self.config.confluence_url.startswith(('http://', 'https://')):
                return ConnectionResult(
                    success=False,
                    error_message="Invalid Confluence URL format"
                )
            
            # Simulate successful connection
            user_info = {
                'accountId': 'test_confluence_user_id',
                'displayName': 'Test Confluence User',
                'email': 'test@confluence.example.com',
                'type': 'known'
            }
            
            return ConnectionResult(
                success=True,
                user_name=user_info.get('displayName', 'Unknown'),
                user_id=user_info.get('accountId', ''),
                display_name=user_info.get('displayName', ''),
                email=user_info.get('email', ''),
                server_info={
                    'server_url': self.config.confluence_url,
                    'ssl_verify': self.config.confluence_ssl_verify,
                    'connection_time': datetime.utcnow().isoformat()
                }
            )
            
        except asyncio.TimeoutError:
            logger.error("Confluence connection test timed out")
            return ConnectionResult(
                success=False,
                error_message="Connection timeout - please check your Confluence URL and network connectivity"
            )
        except Exception as e:
            logger.error(f"Confluence connection test failed: {str(e)}")
            return ConnectionResult(
                success=False,
                error_message=f"Connection failed: {str(e)}"
            )
    
    async def get_boards(self) -> List[Board]:
        """
        Fetch all accessible Jira boards.
        
        Returns:
            List of Board objects
        """
        try:
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                raise MCPConnectionError("Jira configuration is required for board operations")
            
            logger.info("Fetching Jira boards")
            
            # Simulate network delay
            await asyncio.sleep(0.2)
            
            # Simulate board data
            boards_data = [
                {
                    'id': '1',
                    'name': 'Development Board',
                    'type': 'scrum',
                    'location': {
                        'projectKey': 'DEV',
                        'projectName': 'Development Project'
                    },
                    'self': f"{self.config.jira_url}/rest/agile/1.0/board/1"
                },
                {
                    'id': '2',
                    'name': 'Support Board',
                    'type': 'kanban',
                    'location': {
                        'projectKey': 'SUP',
                        'projectName': 'Support Project'
                    },
                    'self': f"{self.config.jira_url}/rest/agile/1.0/board/2"
                }
            ]
            
            boards = []
            for board_data in boards_data:
                board = Board(
                    id=board_data['id'],
                    name=board_data['name'],
                    type=board_data['type'],
                    project_key=board_data['location']['projectKey'],
                    project_name=board_data['location']['projectName'],
                    self_url=board_data['self']
                )
                boards.append(board)
            
            logger.info(f"Retrieved {len(boards)} boards")
            return boards
            
        except Exception as e:
            logger.error(f"Failed to fetch boards: {str(e)}")
            raise MCPConnectionError(f"Failed to fetch boards: {str(e)}")
    
    async def get_sprints(self, board_id: str) -> List[Sprint]:
        """
        Fetch sprints for a specific board.
        
        Args:
            board_id: Board ID to fetch sprints for
            
        Returns:
            List of Sprint objects
        """
        try:
            if not self.config.jira_url or not self.config.get_jira_personal_token():
                raise MCPConnectionError("Jira configuration is required for sprint operations")
            
            logger.info(f"Fetching sprints for board {board_id}")
            
            # Simulate network delay
            await asyncio.sleep(0.2)
            
            # Simulate sprint data
            sprints_data = [
                {
                    'id': '10',
                    'name': 'Sprint 1',
                    'state': 'active',
                    'startDate': '2025-01-01T09:00:00.000Z',
                    'endDate': '2025-01-14T17:00:00.000Z',
                    'originBoardId': board_id
                },
                {
                    'id': '11',
                    'name': 'Sprint 2',
                    'state': 'future',
                    'originBoardId': board_id
                },
                {
                    'id': '9',
                    'name': 'Sprint 0',
                    'state': 'closed',
                    'startDate': '2024-12-15T09:00:00.000Z',
                    'endDate': '2024-12-28T17:00:00.000Z',
                    'completeDate': '2024-12-28T17:00:00.000Z',
                    'originBoardId': board_id
                }
            ]
            
            sprints = []
            for sprint_data in sprints_data:
                sprint = Sprint(
                    id=sprint_data['id'],
                    name=sprint_data['name'],
                    state=sprint_data['state'],
                    start_date=sprint_data.get('startDate'),
                    end_date=sprint_data.get('endDate'),
                    complete_date=sprint_data.get('completeDate'),
                    board_id=board_id
                )
                sprints.append(sprint)
            
            logger.info(f"Retrieved {len(sprints)} sprints for board {board_id}")
            return sprints
            
        except Exception as e:
            logger.error(f"Failed to fetch sprints for board {board_id}: {str(e)}")
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