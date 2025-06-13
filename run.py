# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # You can customize host/port here, or rely on Flask's defaults
    # This part is for running the app locally for development, e.g., `python run.py`
    # It won't be used by Gunicorn, but it's good practice to have.
    app.run(host='0.0.0.0', debug=True)