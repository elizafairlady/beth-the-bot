import asyncio
import base64
import json
import os
import random
import websockets
from twitchio.ext import commands
from PIL import Image, ImageDraw, ImageFont
from cogs.logging import logger

# Constants
VTS_API_URL = os.getenv("VTS_API_URL")
APP_NAME = os.getenv("VTS_APP_NAME")
DEVELOPER = os.getenv("VTS_APP_DEVELOPER")
PLUGIN_ICON_PATH = os.getenv("VTS_APP_ICON_PATH", None)
IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600
FONT_SIZE = 50
FONT_PATH = os.path.expanduser(os.getenv("VTS_MEME_FONT"))
VTS_ITEMS_PATH = os.path.expanduser(os.getenv("VTS_ITEMS_PATH"))


class VTubeStudioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.websocket = None
        self.expression_map = {
            "love": "1.exp3.json",
            "cry": "2.exp3.json",
            "shadow": "3.exp3.json",
            "blush": "4.exp3.json",
            "stars": "5.exp3.json",
            "hand": "8.exp3.json",
        }

    @commands.Cog.event("event_ready")
    async def on_ready(self):
        await self.connect_vts()

    async def cog_unload(self):
        if self.websocket:
            await self.websocket.close()

    async def connect_vts(self):
        self.websocket = await websockets.connect(VTS_API_URL)
        auth_token = await self.request_auth_token()
        if not auth_token:
            logger.info("Could not obtain auth token. Exiting...")
            return

        authenticated = await self.authenticate(auth_token)
        if not authenticated:
            logger.info("Authentication failed. Exiting...")
            return

    def read_icon_base64(self, icon_path):
        if icon_path:
            with open(icon_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        return None

    def generate_meme_image(self, top_text, bottom_text, output_path):
        image = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (255, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        text_color = (255, 255, 255, 255)
        border_color = (0, 0, 0, 255)

        # Calculate text size and position for top text
        top_text_bbox = draw.textbbox((0, 0), top_text, font=font, stroke_width=2)
        top_text_width = top_text_bbox[2] - top_text_bbox[0]
        top_text_position = ((IMAGE_WIDTH - top_text_width) / 2, 10)
        draw.text(
            (top_text_position),
            top_text,
            font=font,
            fill=text_color,
            stroke_width=2,
            stroke_fill=border_color,
        )

        # Calculate text size and position for bottom text
        bottom_text_bbox = draw.textbbox((0, 0), bottom_text, font=font, stroke_width=2)
        bottom_text_width = bottom_text_bbox[2] - bottom_text_bbox[0]
        bottom_text_height = bottom_text_bbox[3] - bottom_text_bbox[1]
        bottom_text_position = (
            (IMAGE_WIDTH - bottom_text_width) / 2,
            IMAGE_HEIGHT - bottom_text_height - 10,
        )
        draw.text(
            (bottom_text_position),
            bottom_text,
            font=font,
            fill=text_color,
            stroke_width=2,
            stroke_fill=border_color,
        )

        image.save(output_path, "PNG")
        logger.debug(f"Meme image generated and saved as '{output_path}'")

    async def query(self, payload):
        await self.websocket.send(json.dumps(payload))
        response = await self.websocket.recv()
        response_data = json.loads(response)
        return response_data

    async def request_auth_token(self):
        plugin_icon_base64 = self.read_icon_base64(PLUGIN_ICON_PATH)
        request_auth_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "auth_request",
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": APP_NAME,
                "pluginDeveloper": DEVELOPER,
                "pluginIcon": plugin_icon_base64,
            },
        }

        response_data = await self.query(request_auth_payload)
        logger.debug(f"Auth token response: {response_data}")

        if (
            response_data.get("data")
            and response_data["messageType"] == "AuthenticationTokenResponse"
        ):
            auth_token = response_data["data"]["authenticationToken"]
            logger.debug(f"Auth token received: {auth_token}")
            return auth_token
        else:
            logger.info("Failed to receive auth token")
            return None

    async def authenticate(self, auth_token):
        authenticate_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "auth_request",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": APP_NAME,
                "pluginDeveloper": DEVELOPER,
                "authenticationToken": auth_token,
            },
        }

        response_data = await self.query(authenticate_payload)
        logger.debug(f"Auth response: {response_data}")

        if (
            response_data.get("data")
            and response_data["messageType"] == "AuthenticationResponse"
        ):
            if response_data["data"]["authenticated"]:
                logger.debug("Authenticated successfully")
                return True
            else:
                logger.info(f"Authentication failed: {response_data}")
                return False

    async def get_model_info(self):
        model_info_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "model_info_request",
            "messageType": "CurrentModelRequest",
        }

        response_data = await self.query(model_info_payload)
        logger.debug(f"Model info response: {response_data}")

        if (
            response_data.get("data")
            and response_data["messageType"] == "CurrentModelResponse"
        ):
            model_info = response_data["data"]
            logger.debug(f"Model Info: {model_info}")
            return model_info
        else:
            logger.info("Failed to get model info")
            return None

    async def add_item_to_scene(
        self, image_name, model_id, model_x, model_y, model_size
    ):
        size = abs(model_size)
        load_item_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "load_item_request",
            "messageType": "ItemLoadRequest",
            "data": {
                "fileName": image_name,
                "positionX": model_x,
                "positionY": model_y,
                "size": 0.34,
                "rotation": 0.0,
                "opacity": 1.0,
                "isPinned": False,
            },
        }

        response_data = await self.query(load_item_payload)
        logger.debug(f"Load item response: {response_data}")

        if (
            response_data.get("data")
            and response_data["messageType"] == "ItemLoadResponse"
        ):
            item_instance_id = response_data["data"]["instanceID"]
            logger.debug(f"Item loaded with instance ID: {item_instance_id}")
        else:
            logger.info("Failed to load item.")
            return None

        return item_instance_id

    async def pin_item_to_model(
        self, item_instance_id, model_id, model_size, art_mesh_id=""
    ):
        pin_item_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "pin_item_request",
            "messageType": "ItemPinRequest",
            "data": {
                "pin": True,
                "itemInstanceID": item_instance_id,
                "angleRelativeTo": "RelativeToModel",
                "sizeRelativeTo": "RelativeToWorld",
                "vertexPinType": "Provided",
                "pinInfo": {
                    "modelID": model_id,
                    "artMeshID": "ArtMesh115",
                    "angle": 0,
                    "size": 0.34,
                    "vertexID1": 405,
                    "vertexID2": 406,
                    "vertexID3": 396,
                    "vertexWeight1": 0.2025667130947113,
                    "vertexWeight2": 0.49878910183906555,
                    "vertexWeight3": 0.29864418506622314,
                },
            },
        }

        response_data = await self.query(pin_item_payload)
        logger.debug(f"Pin Item response: {response_data}")

        if (
            response_data.get("data")
            and response_data["messageType"] == "ItemPinResponse"
        ):
            if response_data["data"]["isPinned"]:
                logger.debug("Item pinned successfully")
            else:
                logger.info("Failed to pin item")
        else:
            logger.info("Failed to pin item")

    async def unload_item(self, item_instance_id):
        unload_item_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "unload_item_request",
            "messageType": "ItemUnloadRequest",
            "data": {"instanceIDs": [item_instance_id]},
        }

        response_data = await self.query(unload_item_payload)
        logger.debug(f"Unload item response: {response_data}")

        if (
            response_data.get("data")
            and response_data["messageType"] == "ItemUnloadResponse"
        ):
            if len(response_data["data"]["unloadedItems"]):
                logger.debug("Item unloaded successfully")
            else:
                logger.info("Failed to unload item")
        else:
            logger.info("Failed to unload item")

    async def toggle_expression(self, expression_file, expression_state):
        trigger_expression_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "trigger_expression_request",
            "messageType": "ExpressionActivationRequest",
            "data": {
                "expressionFile": expression_file,
                "active": expression_state,
            },
        }

        response_data = await self.query(trigger_expression_payload)
        logger.debug(f"Trigger expression response: {response_data}")

        if response_data.get("messageType") == "ExpressionActivationResponse":
            logger.debug(f"Expression {expression_file} triggered successfully")
        else:
            logger.info(f"Failed to trigger expression {expression_file}")

    def convert_modelsize_to_itemsize(self, model_size):
        return (model_size + 100) / 200

    @commands.command(name="meme")
    async def meme_command(self, ctx, *, text: str):
        parts = text.split("|")
        top_text = parts[0].strip()
        bottom_text = parts[1].strip() if len(parts) > 1 else ""

        expression = None
        if top_text.startswith("(") and ")" in top_text:
            expression = top_text[1 : top_text.index(")")].lower()
            top_text = top_text[top_text.index(")") + 1 :].strip()

        if expression and expression not in self.expression_map:
            await ctx.send(
                "Invalid expression. Available expressions are love, cry, shadow, blush, stars, and hand."
            )
            return

        model_info = await self.get_model_info()
        if not model_info:
            await ctx.send("Could not obtain model info.")
            return

        model_id = model_info["modelID"]
        model_size = model_info["modelPosition"]["size"]
        model_x = model_info["modelPosition"]["positionX"]
        model_y = model_info["modelPosition"]["positionY"]

        image_name = f"meme_image_{random.randint(1000, 9999)}.png"
        image_path = os.path.join(VTS_ITEMS_PATH, image_name)
        self.generate_meme_image(top_text, bottom_text, image_path)

        item_instance_id = await self.add_item_to_scene(
            image_name,
            model_id,
            model_x,
            model_y,
            self.convert_modelsize_to_itemsize(model_size),
        )
        if not item_instance_id:
            await ctx.send("Could not add item to scene.")
            return

        await self.pin_item_to_model(item_instance_id, model_id, model_size)

        if expression:
            expression_file = self.expression_map[expression]
            await self.toggle_expression(expression_file, True)

        await asyncio.sleep(10)

        await self.unload_item(item_instance_id)

        if expression:
            await self.toggle_expression(expression_file, False)


def prepare(bot):
    bot.add_cog(VTubeStudioCog(bot))
