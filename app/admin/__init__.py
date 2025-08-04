"""Admin blueprint for user management."""

from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes