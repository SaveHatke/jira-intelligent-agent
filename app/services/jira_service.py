"""
Jira service for JIA application.

This module provides high-level Jira operations using the MCPClientManager.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.models import MCPConfiguration
from app.services.mcp_client import MCPClientManager, Board, Sprint, Ticket, TicketHistory, TicketResult
from app.services.exceptions import MCPConnectionError, ValidationError


logger = logging.getLogger(__name__)


class JiraService:
    """
    High-level service for Jira operations.
    
    This service provides business logic for Jira operations,
    using the MCPClientManager for low-level communication.
    """
    
    def __init__(self, user_config: MCPConfiguration):
        """
        Initialize Jira service.
        
        Args:
            user_config: User's MCP configuration
        """
        self.config = user_config
        self.client = MCPClientManager(user_config)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Jira connection and return formatted result.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            result = self.client.test_jira_connection_sync()
            
            return {
                'success': result.success,
                'message': 'Connection successful' if result.success else result.error_message,
                'user_info': {
                    'user_name': result.user_name,
                    'user_id': result.user_id,
                    'display_name': result.display_name,
                    'email': result.email
                } if result.success else None,
                'server_info': result.server_info if result.success else None,
                'tested_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Jira connection test failed: {str(e)}")
            return {
                'success': False,
                'message': f"Connection test failed: {str(e)}",
                'user_info': None,
                'server_info': None,
                'tested_at': datetime.utcnow().isoformat()
            }
    
    def get_boards(self) -> List[Dict[str, Any]]:
        """
        Get all accessible Jira boards.
        
        Returns:
            List of board dictionaries
        """
        try:
            boards = self.client.get_boards_sync()
            
            return [
                {
                    'id': board.id,
                    'name': board.name,
                    'type': board.type,
                    'project_key': board.project_key,
                    'project_name': board.project_name,
                    'url': board.self_url
                }
                for board in boards
            ]
            
        except Exception as e:
            logger.error(f"Failed to get boards: {str(e)}")
            raise MCPConnectionError(f"Failed to retrieve boards: {str(e)}")
    
    def get_sprints(self, board_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get sprints for a board, categorized by state.
        
        Args:
            board_id: Board ID to get sprints for
            
        Returns:
            Dictionary with sprints categorized by state
        """
        try:
            if not board_id:
                raise ValidationError("Board ID is required")
            
            sprints = self.client.get_sprints_sync(board_id)
            
            # Categorize sprints by state
            categorized = {
                'active': [],
                'future': [],
                'closed': []
            }
            
            for sprint in sprints:
                sprint_dict = {
                    'id': sprint.id,
                    'name': sprint.name,
                    'state': sprint.state,
                    'start_date': sprint.start_date,
                    'end_date': sprint.end_date,
                    'complete_date': sprint.complete_date,
                    'board_id': sprint.board_id
                }
                
                if sprint.state in categorized:
                    categorized[sprint.state].append(sprint_dict)
                else:
                    # Handle any unexpected states
                    if 'other' not in categorized:
                        categorized['other'] = []
                    categorized['other'].append(sprint_dict)
            
            return categorized
            
        except Exception as e:
            logger.error(f"Failed to get sprints for board {board_id}: {str(e)}")
            raise MCPConnectionError(f"Failed to retrieve sprints: {str(e)}")
    
    def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Jira ticket.
        
        Args:
            ticket_data: Ticket creation data
            
        Returns:
            Dictionary with creation result
        """
        try:
            # Validate required fields
            required_fields = ['summary', 'project', 'issuetype']
            missing_fields = [field for field in required_fields if not ticket_data.get(field)]
            if missing_fields:
                raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
            
            result = self.client.create_ticket_sync(ticket_data)
            
            return {
                'success': result.success,
                'message': 'Ticket created successfully' if result.success else result.error_message,
                'ticket': {
                    'key': result.ticket_key,
                    'id': result.ticket_id,
                    'url': result.ticket_url
                } if result.success else None,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create ticket: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to create ticket: {str(e)}",
                'ticket': None,
                'created_at': datetime.utcnow().isoformat()
            }
    
    def get_ticket_history(self, ticket_key: str) -> Dict[str, Any]:
        """
        Get complete history for a ticket.
        
        Args:
            ticket_key: Jira ticket key
            
        Returns:
            Dictionary with ticket history
        """
        try:
            if not ticket_key:
                raise ValidationError("Ticket key is required")
            
            history = self.client.get_ticket_history_sync(ticket_key)
            
            return {
                'ticket_key': history.ticket_key,
                'changelog': history.changelog,
                'comments': history.comments,
                'worklog': history.worklog,
                'transitions': history.transitions,
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get ticket history for {ticket_key}: {str(e)}")
            raise MCPConnectionError(f"Failed to retrieve ticket history: {str(e)}")
    
    def search_tickets(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        """
        Search for tickets using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        try:
            if not jql:
                raise ValidationError("JQL query is required")
            
            tickets = self.client.search_tickets_sync(jql, max_results)
            
            ticket_list = []
            for ticket in tickets:
                ticket_dict = {
                    'id': ticket.id,
                    'key': ticket.key,
                    'summary': ticket.summary,
                    'description': ticket.description,
                    'status': ticket.status,
                    'assignee': ticket.assignee,
                    'reporter': ticket.reporter,
                    'created': ticket.created,
                    'updated': ticket.updated,
                    'issue_type': ticket.issue_type,
                    'priority': ticket.priority,
                    'story_points': ticket.story_points,
                    'labels': ticket.labels,
                    'components': ticket.components
                }
                ticket_list.append(ticket_dict)
            
            return {
                'jql': jql,
                'total': len(ticket_list),
                'max_results': max_results,
                'tickets': ticket_list,
                'searched_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to search tickets with JQL '{jql}': {str(e)}")
            raise MCPConnectionError(f"Failed to search tickets: {str(e)}")
    
    def get_board_configuration(self, board_id: str) -> Dict[str, Any]:
        """
        Get board configuration details.
        
        Args:
            board_id: Board ID
            
        Returns:
            Dictionary with board configuration
        """
        try:
            # This would typically fetch board configuration from Jira
            # For now, we'll return a simulated configuration
            
            return {
                'board_id': board_id,
                'estimation': {
                    'type': 'story_points',
                    'field': 'customfield_10016'
                },
                'columns': [
                    {'name': 'To Do', 'statuses': ['To Do', 'Open']},
                    {'name': 'In Progress', 'statuses': ['In Progress']},
                    {'name': 'Done', 'statuses': ['Done', 'Closed', 'Resolved']}
                ],
                'quick_filters': [
                    {'name': 'Only My Issues', 'query': 'assignee = currentUser()'},
                    {'name': 'Recently Updated', 'query': 'updated >= -1d'}
                ],
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get board configuration for {board_id}: {str(e)}")
            raise MCPConnectionError(f"Failed to retrieve board configuration: {str(e)}")
    
    def get_sprint_report(self, sprint_id: str) -> Dict[str, Any]:
        """
        Get sprint report with metrics.
        
        Args:
            sprint_id: Sprint ID
            
        Returns:
            Dictionary with sprint report data
        """
        try:
            # This would typically fetch sprint report from Jira
            # For now, we'll return a simulated report
            
            return {
                'sprint_id': sprint_id,
                'name': f'Sprint {sprint_id}',
                'state': 'active',
                'commitment': {
                    'story_points': 25,
                    'issues': 8
                },
                'completed': {
                    'story_points': 15,
                    'issues': 5
                },
                'remaining': {
                    'story_points': 10,
                    'issues': 3
                },
                'velocity': {
                    'current': 15,
                    'average': 18
                },
                'burndown': [
                    {'day': 1, 'remaining': 25},
                    {'day': 2, 'remaining': 22},
                    {'day': 3, 'remaining': 18},
                    {'day': 4, 'remaining': 15}
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get sprint report for {sprint_id}: {str(e)}")
            raise MCPConnectionError(f"Failed to retrieve sprint report: {str(e)}")
    
    def validate_jql(self, jql: str) -> Dict[str, Any]:
        """
        Validate JQL query syntax.
        
        Args:
            jql: JQL query to validate
            
        Returns:
            Dictionary with validation result
        """
        try:
            if not jql:
                return {
                    'valid': False,
                    'error': 'JQL query cannot be empty'
                }
            
            # Basic JQL validation (in real implementation, this would use Jira API)
            # For now, we'll do simple validation
            
            # Check for basic JQL structure
            if not any(keyword in jql.lower() for keyword in ['project', 'assignee', 'status', 'created', 'updated']):
                return {
                    'valid': False,
                    'error': 'JQL query should contain at least one field (project, assignee, status, etc.)'
                }
            
            return {
                'valid': True,
                'message': 'JQL query is valid',
                'estimated_results': 'Unknown (validation only)'
            }
            
        except Exception as e:
            logger.error(f"Failed to validate JQL '{jql}': {str(e)}")
            return {
                'valid': False,
                'error': f'Validation failed: {str(e)}'
            }