# In run.py
from app import create_app
from app.extensions import init_db

app = create_app()

# Perform one-time setup tasks like creating DB tables
with app.app_context():
    if not app.config.get("TESTING"):
        init_db(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)