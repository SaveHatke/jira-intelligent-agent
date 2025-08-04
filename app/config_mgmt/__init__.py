"""Configuration management blueprint for JIA application."""

from flask import Blueprint

bp = Blueprint('config', __name__, url_prefix='/config')

from app.config_mgmt import routes