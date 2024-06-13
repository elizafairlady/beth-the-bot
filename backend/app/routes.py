import os
import random
from flask import Blueprint, jsonify, request
from flask_socketio import emit
from . import socketio
from .twitch_bot import get_bot
from cogs.logging import logger

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return jsonify({"message": "Welcome to beth-the-bot API"})


@main.route("/api/pick_guest", methods=["POST"])
def pick_guest():
    bot = get_bot()
    if bot and bot.tts_guest:
        guest = bot.tts_guest.pick_guest()
        if guest:
            logger.info(f"Current guest: {guest[0].name}")
            emit(
                "guest_update", {"guest": guest[0].name}, namespace="/", broadcast=True
            )
            return jsonify({"guest": guest[0].name, "timestamp": guest[1].isoformat()})
    return jsonify({"message": "No guests available"}), 404


@main.route("/api/clear_guest", methods=["POST"])
def clear_guest():
    bot = get_bot()
    if bot and bot.tts_guest:
        bot.tts_guest.clear_guest()
        logger.info("Current guest cleared")
        emit("guest_clear", {"guest": ""}, namespace="/", broadcast=True)
        return jsonify({"message": "Current guest cleared"})
    return jsonify({"message": "No guest to clear"}), 404


@main.route("/api/set_guest", methods=["POST"])
def set_guest():
    bot = get_bot()
    try:
        data = request.get_json()
        guest_name = data.get("guest")
        logger.info(f"Set guest request: {guest_name}")
        if bot and bot.tts_guest and guest_name:
            bot.tts_guest.set_guest(guest_name)
            emit("guest_update", {"guest": guest_name}, namespace="/", broadcast=True)
            logger.info(f"Set guest: {guest_name}")
            return jsonify({"guest": guest_name})
    except Exception as e:
        logger.error(f"Failed to set guest: {e}")

    return jsonify({"message": f"Failed to set guest: {bot}, {guest_name}"}), 400


@main.route("/api/random_avatar", methods=["GET"])
def random_avatar():
    avatars_dir = os.path.join(os.path.dirname(__file__), "static/avatars")
    avatars = [
        f
        for f in os.listdir(avatars_dir)
        if os.path.isfile(os.path.join(avatars_dir, f))
    ]
    if avatars:
        avatar = random.choice(avatars)
        logger.info(f"Random avatar: {avatar}")
        return jsonify({"avatar": f"/static/avatars/{avatar}"})
    return jsonify({"message": "No avatars available"}), 404


@main.route("/api/get_guest_message", methods=["GET"])
def get_guest_message():
    bot = get_bot()
    guest_name = request.args.get("guest")
    if bot and bot.tts_guest:
        # For demonstration, we return a dummy message
        # Replace this with actual logic to fetch the guest's message
        if len(bot.tts_guest.message_queue) > 0:
            message = bot.tts_guest.message_queue.popleft()
            emit(
                "message_update",
                {"message": message.content},
                namespace="/",
                broadcast=True,
            )
            return jsonify({"message": message})
    return jsonify({"message": "No message available"}), 404
