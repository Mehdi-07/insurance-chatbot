# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # You can customize host/port here, or rely on Flask's defaults
    app.run(debug=True)