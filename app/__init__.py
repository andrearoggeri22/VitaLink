"""
VitaLink Application Package.

This package serves as the main entry point for the VitaLink healthcare application.
It exports Flask application instance and all related extensions that are
initialized in the app module.
"""

from .app import (          
    app,                    
    db,
    migrate,
    jwt,
    login_manager,
    babel,
)

__all__ = ["app", "db", "migrate", "jwt", "login_manager", "babel"]