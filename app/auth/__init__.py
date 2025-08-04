"""Authentication blueprint for JIA application."""

from flask import Blueprint

bp = Blueprint('auth', __name__)

from app.auth import routes, decorators