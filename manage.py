import os
from app import create_app

# Instantiate the app with default configuration (loads from FLASK_ENV or defaults to development)
app = create_app()

if __name__ == '__main__':
    app.run()
