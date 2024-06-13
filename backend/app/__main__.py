import os
import sys
import threading
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app


def run_flask():
    app = create_app()
    app.run(debug=True, use_reloader=False, port=5001)


if __name__ == "__main__":
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
