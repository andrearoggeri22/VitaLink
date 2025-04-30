import os
from .app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "True").lower() == "true"
    app.run(host=host, port=port, debug=debug)
