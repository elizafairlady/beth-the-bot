# Beth the Bot

Beth the Bot is a Twitch chat bot that provides Text-to-Speech (TTS) functionality for chat messages, integrated with OBS to display the avatar and messages. It uses ElevenLabs for TTS and PyAudio for audio playback.

## Features

- Connects to Twitch chat using `twitchio`
- Text-to-Speech using ElevenLabs
- Displays TTS Avatar and messages on OBS using OBS Websockets
- Animated message display in React frontend

## Setup and Installation

### Prerequisites

- Python 3.6+
- Node.js and npm
- OBS > 28.0.0, or with OBS Websockets plugin installed

### Clone the Repository

```sh
git clone https://github.com/yourusername/beth-the-bot.git
cd beth-the-bot
```

### Setup

A script is provided to perform the setup of the virtualenv for python, and gather all the dependencies for both the frontend and backend. In the root directory of the project, run:

```sh
scripts/setup.sh
```

Create a `.env` file in the root directory of the project, like the following:

```
FLASK_APP=scripts/run.py
FLASK_ENV=development
TWITCH_BOT_ACCESS_TOKEN=<your twitchbot access token>
TWITCH_CHANNELS=<your channels>
ELEVEN_API_KEY=<your elevenlabs api key>
OBS_WEBSOCKET_HOST=localhost
OBS_WEBSOCKET_PORT=4455
OBS_WEBSOCKET_PASSWORD=<your obs websockets password>
```

### Run the Application
In the root directory of the project, run:

```sh
source venv/bin/activate
python scripts/run.py
```

This will start the Flask server, the Twitch bot, and the React app.

The Flask server runs at http://localhost:5000
The React app runs at http://localhost:3000

## Usage

* The bot will join the specified Twitch channel and listen for chat messages.
* The React frontend will display the avatar and animated messages.
* OBS will show/hide the avatar and messages using OBS Websockets.
* If you need to find the vertices for a specific place on a model, use `scripts/click_event_test.py`

## Contributing

Contributions are welcome! Please create a pull request or open an issue to discuss any changes.
