"""
Configuration management routes for JIA application.

This module provides web interfaces for managing MCP and AI configurations.
"""

import json
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.config_mgmt import bp
from app.config_mgmt.services import (
    ConfigurationService, MCPTestService, AIConfigValidationService, 
    ConfigurationUtilities
)
from app.models import MCPConfiguration, AIConfiguration


@bp.route('/')
@login_required
def index():
    """Configuration management main page."""
    # Get current configurations
    mcp_config = ConfigurationService.get_user_mcp_config(current_user.id)
    ai_config = ConfigurationService.get_user_ai_config(current_user.id)
    
    return render_template('config/index.html',
                         title='Configuration Management',
                         mcp_config=mcp_config,
                         ai_config=ai_config)


@bp.route('/mcp')
@login_required
def mcp_config():
    """MCP configuration page."""
    config = ConfigurationService.get_user_mcp_config(current_user.id)
    default_params = ConfigurationUtilities.get_default_mcp_params()
    
    return render_template('config/mcp.html',
                         title='MCP Configuration',
                         config=config,
                         default_params=default_params)


@bp.route('/mcp', methods=['POST'])
@login_required
def save_mcp_config():
    """Save MCP configuration."""
    try:
        service_type = request.form.get('service_type', 'all')
        
        # Get existing configuration
        existing_config = ConfigurationService.get_user_mcp_config(current_user.id)
        
        # Prepare config data based on service type
        if service_type == 'jira':
            config_data = {
                'jira_url': ConfigurationUtilities.sanitize_url(request.form.get('jira_url', '')),
                'jira_personal_token': request.form.get('jira_personal_token', ''),
                'jira_ssl_verify': request.form.get('jira_ssl_verify') == 'on',
                # Preserve existing Confluence settings
                'confluence_url': existing_config.confluence_url if existing_config else '',
                'confluence_personal_token': existing_config.get_confluence_personal_token() if existing_config else '',
                'confluence_ssl_verify': existing_config.confluence_ssl_verify if existing_config else True,
                'is_active': existing_config.is_active if existing_config else True,
                'additional_params': existing_config.additional_params if existing_config else {}
            }
            flash_message = 'Jira configuration saved successfully!'
            
        elif service_type == 'confluence':
            config_data = {
                # Preserve existing Jira settings
                'jira_url': existing_config.jira_url if existing_config else '',
                'jira_personal_token': existing_config.get_jira_personal_token() if existing_config else '',
                'jira_ssl_verify': existing_config.jira_ssl_verify if existing_config else True,
                'confluence_url': ConfigurationUtilities.sanitize_url(request.form.get('confluence_url', '')),
                'confluence_personal_token': request.form.get('confluence_personal_token', ''),
                'confluence_ssl_verify': request.form.get('confluence_ssl_verify') == 'on',
                'is_active': existing_config.is_active if existing_config else True,
                'additional_params': existing_config.additional_params if existing_config else {}
            }
            flash_message = 'Confluence configuration saved successfully!'
            
        elif service_type == 'global':
            config_data = {
                # Preserve existing service settings
                'jira_url': existing_config.jira_url if existing_config else '',
                'jira_personal_token': existing_config.get_jira_personal_token() if existing_config else '',
                'jira_ssl_verify': existing_config.jira_ssl_verify if existing_config else True,
                'confluence_url': existing_config.confluence_url if existing_config else '',
                'confluence_personal_token': existing_config.get_confluence_personal_token() if existing_config else '',
                'confluence_ssl_verify': existing_config.confluence_ssl_verify if existing_config else True,
                'is_active': request.form.get('is_active') == 'on',
                'additional_params': existing_config.additional_params if existing_config else {}
            }
            flash_message = 'Global settings saved successfully!'
            
        else:
            # Legacy: save all fields
            config_data = {
                'jira_url': ConfigurationUtilities.sanitize_url(request.form.get('jira_url', '')),
                'jira_personal_token': request.form.get('jira_personal_token', ''),
                'jira_ssl_verify': request.form.get('jira_ssl_verify') == 'on',
                'confluence_url': ConfigurationUtilities.sanitize_url(request.form.get('confluence_url', '')),
                'confluence_personal_token': request.form.get('confluence_personal_token', ''),
                'confluence_ssl_verify': request.form.get('confluence_ssl_verify') == 'on',
                'is_active': request.form.get('is_active') == 'on',
                'additional_params': {}
            }
            flash_message = 'MCP configuration saved successfully!'
        
        # Save configuration
        success, errors, config = ConfigurationService.save_mcp_config(
            current_user.id, config_data
        )
        
        if success:
            flash(flash_message, 'success')
        else:
            for error in errors:
                flash(f'Configuration Error: {error}', 'error')
        
        return redirect(url_for('config.mcp_config'))
        
    except Exception as e:
        flash(f'Failed to save configuration: {str(e)}', 'error')
        return redirect(url_for('config.mcp_config'))


@bp.route('/mcp/test')
@login_required
def test_mcp_config():
    """Test MCP configuration."""
    service_type = request.args.get('service', 'jira')  # 'jira' or 'confluence'
    
    config = ConfigurationService.get_user_mcp_config(current_user.id)
    if not config:
        return jsonify({
            'success': False,
            'message': 'No MCP configuration found. Please configure your settings first.',
            'user_info': {}
        })
    
    # Test connection
    success, message, user_info = MCPTestService.test_connection_sync(config, service_type)
    
    return jsonify({
        'success': success,
        'message': message,
        'user_info': user_info,
        'service_type': service_type
    })


@bp.route('/ai')
@login_required
def ai_config():
    """AI configuration page."""
    config = ConfigurationService.get_user_ai_config(current_user.id)
    default_model_configs = ConfigurationUtilities.get_default_ai_model_configs()
    
    return render_template('config/ai.html',
                         title='AI Configuration',
                         config=config,
                         default_model_configs=default_model_configs)


@bp.route('/ai', methods=['POST'])
@login_required
def save_ai_config():
    """Save AI configuration."""
    try:
        # Get form data
        config_data = {
            'custom_headers': request.form.get('custom_headers', '{}'),
            'user_id_from_jira': request.form.get('user_id_from_jira', ''),
            'model_configs': request.form.get('model_configs', '{}')
        }
        
        # Validate custom headers JSON
        is_valid, error_msg, parsed_headers = ConfigurationUtilities.validate_json_string(
            config_data['custom_headers']
        )
        if not is_valid:
            flash(f'Custom Headers Error: {error_msg}', 'error')
            return redirect(url_for('config.ai_config'))
        
        config_data['custom_headers'] = parsed_headers
        
        # Validate model configs JSON
        is_valid, error_msg, parsed_configs = ConfigurationUtilities.validate_json_string(
            config_data['model_configs']
        )
        if not is_valid:
            flash(f'Model Configurations Error: {error_msg}', 'error')
            return redirect(url_for('config.ai_config'))
        
        config_data['model_configs'] = parsed_configs
        
        # Save configuration
        success, errors, config = ConfigurationService.save_ai_config(
            current_user.id, config_data
        )
        
        if success:
            flash('AI configuration saved successfully!', 'success')
        else:
            for error in errors:
                flash(f'Configuration Error: {error}', 'error')
        
        return redirect(url_for('config.ai_config'))
        
    except Exception as e:
        flash(f'Failed to save configuration: {str(e)}', 'error')
        return redirect(url_for('config.ai_config'))


@bp.route('/ai/validate')
@login_required
def validate_ai_config():
    """Validate AI configuration."""
    config = ConfigurationService.get_user_ai_config(current_user.id)
    if not config:
        return jsonify({
            'success': False,
            'message': 'No AI configuration found. Please configure your settings first.',
            'validation_info': {}
        })
    
    # Validate configuration
    success, message, validation_info = AIConfigValidationService.validate_ai_config_sync(config)
    
    return jsonify({
        'success': success,
        'message': message,
        'validation_info': validation_info
    })


@bp.route('/export')
@login_required
def export_config():
    """Export user configurations (excluding sensitive data)."""
    mcp_config = ConfigurationService.get_user_mcp_config(current_user.id)
    ai_config = ConfigurationService.get_user_ai_config(current_user.id)
    
    export_data = {
        'user_id': current_user.id,
        'username': current_user.username,
        'export_timestamp': ConfigurationUtilities.get_current_timestamp(),
        'mcp_configuration': None,
        'ai_configuration': None
    }
    
    if mcp_config:
        mcp_data = mcp_config.to_dict(include_token=False)
        # Mask additional sensitive data
        if mcp_data.get('additional_params'):
            mcp_data['additional_params'] = ConfigurationUtilities.mask_sensitive_data(
                mcp_data['additional_params']
            )
        export_data['mcp_configuration'] = mcp_data
    
    if ai_config:
        ai_data = ai_config.to_dict()
        # Mask sensitive headers
        if ai_data.get('custom_headers'):
            ai_data['custom_headers'] = ConfigurationUtilities.mask_sensitive_data(
                ai_data['custom_headers']
            )
        export_data['ai_configuration'] = ai_data
    
    return jsonify(export_data)


@bp.route('/status')
@login_required
def config_status():
    """Get configuration status summary."""
    mcp_config = ConfigurationService.get_user_mcp_config(current_user.id)
    ai_config = ConfigurationService.get_user_ai_config(current_user.id)
    
    # Check MCP configuration status
    jira_configured = bool(mcp_config and mcp_config.jira_url and mcp_config.get_jira_personal_token())
    confluence_configured = bool(mcp_config and mcp_config.confluence_url and mcp_config.get_confluence_personal_token())
    legacy_configured = bool(mcp_config and mcp_config.server_url and mcp_config.get_personal_access_token())
    mcp_configured = jira_configured or confluence_configured or legacy_configured
    
    status = {
        'mcp_configured': mcp_configured,
        'jira_configured': jira_configured,
        'confluence_configured': confluence_configured,
        'mcp_tested': bool(mcp_config and mcp_config.last_tested),
        'mcp_active': bool(mcp_config and mcp_config.is_active),
        'ai_configured': bool(ai_config and (ai_config.get_custom_headers() or ai_config.user_id_from_jira)),
        'ai_validated': bool(ai_config and ai_config.is_validated),
        'last_mcp_test': mcp_config.last_tested.isoformat() if mcp_config and mcp_config.last_tested else None,
        'configuration_complete': False
    }
    
    # Check if configuration is complete
    status['configuration_complete'] = (
        status['mcp_configured'] and 
        status['mcp_active'] and 
        status['ai_configured']
    )
    
    return jsonify(status)


@bp.route('/mcp/export')
@login_required
def export_mcp_server_config():
    """Export MCP server configuration JSON."""
    config = ConfigurationService.get_user_mcp_config(current_user.id)
    if not config:
        return jsonify({
            'success': False,
            'message': 'No MCP configuration found. Please configure your settings first.',
            'config': {}
        })
    
    # Generate MCP server configuration
    mcp_server_config = ConfigurationUtilities.generate_mcp_server_config(config)
    
    return jsonify({
        'success': True,
        'message': 'MCP server configuration generated successfully',
        'config': mcp_server_config,
        'user': current_user.username,
        'generated_at': ConfigurationUtilities.get_current_timestamp()
    })