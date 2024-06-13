import os
import subprocess
import threading
import sys
from dotenv import load_dotenv

load_dotenv()


def run_flask():
    sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
    from app import create_app, socketio

    app = create_app()
    socketio.run(app, debug=True, use_reloader=False, port=5001)


def run_react():
    subprocess.run(
        ["npx", "concurrently", "npm:start"],
        cwd=os.path.join(os.path.dirname(__file__), "../frontend"),
    )


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    react_thread = threading.Thread(target=run_react)
    react_thread.start()

    flask_thread.join()
    react_thread.join()
