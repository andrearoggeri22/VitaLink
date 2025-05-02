"""
Main Application Entry Point.

This module serves as the entry point for running the VitaLink application directly.
It configures the web server using environment variables and starts the Flask
development server.

Environment variables:
    PORT: The port to run the server on (default: 5000)
    HOST: The host to bind to (default: 0.0.0.0, making it accessible externally)
    DEBUG: Whether to run in debug mode (default: True)

Usage:
    python -m app.main
"""

import os
from .app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "True").lower() == "true"
    app.run(host=host, port=port, debug=debug)
