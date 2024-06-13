import threading
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from .twitch_bot import run_bot

socketio = SocketIO(cors_allowed_origins="*")


def create_app():
    app = Flask(__name__, static_folder="static")
    CORS(app)

    with app.app_context():
        from .routes import main

        app.register_blueprint(main)

    print("Starting bot")
    bot_thread = threading.Thread(target=run_bot, args=(socketio,))
    bot_thread.start()

    socketio.init_app(app)

    return app
