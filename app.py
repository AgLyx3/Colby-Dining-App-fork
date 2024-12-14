"""
Filename:
    app.py
Usage:
    python3 app.py
Note:
    Debug mode should be disabled in production environments (debug = False).
"""
from website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, port=8000)
