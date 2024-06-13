import asyncio
import json
import os
import websockets
import base64

# Constants
VTS_API_URL = "ws://localhost:8001"
APP_NAME = "click_event_tester"
DEVELOPER = "eliza"
PLUGIN_ICON_PATH = None  # Provide the path to your plugin icon if you have one


def read_icon_base64(icon_path):
    if icon_path:
        with open(icon_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    return None


async def query(websocket, payload):
    await websocket.send(json.dumps(payload))
    response = await websocket.recv()
    response_data = json.loads(response)
    return response_data


async def request_auth_token(websocket):
    plugin_icon_base64 = read_icon_base64(PLUGIN_ICON_PATH)
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

    response_data = await query(websocket, request_auth_payload)
    print("Auth token response:", response_data)

    if (
        response_data.get("data")
        and response_data["messageType"] == "AuthenticationTokenResponse"
    ):
        auth_token = response_data["data"]["authenticationToken"]
        print("Auth token received:", auth_token)
        return auth_token
    else:
        print("Failed to receive auth token")
        return None


async def authenticate(websocket, auth_token):
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

    response_data = await query(websocket, authenticate_payload)
    print("Auth response:", response_data)

    if (
        response_data.get("data")
        and response_data["messageType"] == "AuthenticationResponse"
    ):
        if response_data["data"]["authenticated"]:
            print("Authenticated successfully")
            return True
        else:
            print("Authentication failed:", response_data)
            return False


async def subscribe_to_model_click_event(websocket):
    subscribe_payload = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "subscribe_model_click_event",
        "messageType": "EventSubscriptionRequest",
        "data": {
            "eventName": "ModelClickedEvent",
            "subscribe": True,
            "config": {"onlyClicksOnModel": True},
        },
    }

    response_data = await query(websocket, subscribe_payload)
    print("Subscribe to ModelClickedEvent response:", response_data)

    if (
        response_data.get("data")
        and response_data["messageType"] == "EventSubscriptionResponse"
    ):
        if response_data["data"]["subscribedEventCount"] > 0:
            print("Subscribed to ModelClickedEvent successfully")
        else:
            print("Failed to subscribe to ModelClickedEvent")
    else:
        print("Failed to subscribe to ModelClickedEvent")


async def handle_events(websocket):
    async for message in websocket:
        event_data = json.loads(message)
        if event_data["messageType"] == "ModelClickedEvent":
            print("Model clicked event:", json.dumps(event_data, indent=4))


async def main():
    async with websockets.connect(VTS_API_URL) as websocket:
        auth_token = await request_auth_token(websocket)

        if not auth_token:
            print("Could not obtain auth token. Exiting...")
            return

        authenticated = await authenticate(websocket, auth_token)

        if not authenticated:
            print("Authentication failed. Exiting...")
            return

        await subscribe_to_model_click_event(websocket)
        await handle_events(websocket)


if __name__ == "__main__":
    asyncio.run(main())
