"""
WSGI entry point for production deployment on Vercel.
This file is used by the Vercel Python runtime to start the application.
"""

import os
from app import create_app

# Create Flask app instance for Vercel
app = create_app()

# For local testing with gunicorn
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
