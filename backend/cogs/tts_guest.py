from twitchio.ext import commands
from cogs.logging import logger
from collections import deque
import random
import asyncio
import os
import pyaudio
import wave
import numpy as np
import soundfile as sf
import io
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from obswebsocket import obsws, requests
from dotenv import load_dotenv


load_dotenv()


class SimpleChatter:
    def __init__(self, name):
        self.name = name


class TTSGuestCog(commands.Cog):
    def __init__(self, bot, socketio):
        self.bot = bot
        self.guest_list = []
        self.current_guest = None
        self.message_queue = deque()
        self.socketio = socketio
        self.tts_playing = False
        self.client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

        if os.getenv("OBS_WEBSOCKET_PASSWORD"):
            self.obs_enabled = True
            self.obs_client = obsws(
                os.getenv("OBS_WEBSOCKET_HOST"),
                int(os.getenv("OBS_WEBSOCKET_PORT")),
                os.getenv("OBS_WEBSOCKET_PASSWORD"),
            )
            self.obs_client.connect()
            logger.info("OBS Websocket connected.")
        else:
            self.obs_enabled = False

    @commands.Cog.event()
    async def event_message(self, message):
        if message.echo:
            return

        if self.current_guest and message.author.name == self.current_guest[0].name:
            logger.info(f"Message from current guest: {message.content}")
            self.message_queue.append(message)
            await self.process_queue()

    async def process_queue(self):
        if not self.tts_playing and self.message_queue:
            self.tts_playing = True
            while self.message_queue:
                message = self.message_queue.popleft()
                await self.handle_message(message.content)
            self.tts_playing = False

    def set_obs_source_visibility(self, scene_name, source_name, source_visible=True):
        if self.obs_enabled:
            response = self.obs_client.call(
                requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name)
            )
            source_id = response.datain["sceneItemId"]
            self.obs_client.call(
                requests.SetSceneItemEnabled(
                    sceneName=scene_name,
                    sceneItemId=source_id,
                    sceneItemEnabled=source_visible,
                )
            )

    def set_tts_avatar_visibility(self, visibility):
        self.set_obs_source_visibility("Just Chatting", "TTSAvatar", visibility)

    async def handle_message(self, text):
        try:
            # Update frontend and OBS
            # self.set_obs_source_visibility("Just Chatting", "TTSAvatar", True)

            # Play the TTS
            await self.play_tts(text)

            # Clear the message from the frontend and OBS after playback
            # if len(self.message_queue) == 0:
            #    self.set_obs_source_visibility("Just Chatting", "TTSAvatar", False)
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")

    async def play_tts(self, text):
        try:
            # Call the ElevenLabs API to generate the TTS audio
            audio = self.client.generate(
                text=text, voice="Leonard", model="eleven_multilingual_v2"
            )
            audio_data = [f for f in audio]

            amplitudes = self.calculate_amplitudes(audio_data)

            self.socketio.emit(
                "message_update",
                {"message": text, "amplitudes": amplitudes},
                namespace="/",
            )

            # Play the audio using ElevenLabs' play function
            await asyncio.sleep(0.4)
            play(b"".join(audio_data))

            # Wait for the duration of the audio to finish playback
            duration = len(audio_data) / 22050 + 2
            await asyncio.sleep(duration)

            self.socketio.emit(
                "message_update",
                {"message": ""},
                namespace="/",
            )
        except Exception as e:
            logger.error(f"Failed to play TTS: {e}")

    def calculate_amplitudes(self, audio_data):
        audio_array, _ = sf.read(io.BytesIO(b"".join(audio_data)))
        amplitudes = np.abs(audio_array)
        max_amplitude = np.max(amplitudes)
        normalized_amplitudes = amplitudes / max_amplitude

        return normalized_amplitudes.tolist()

    @commands.command()
    async def guest(self, ctx):
        if ctx.author.name in [guest[0].name for guest in self.guest_list]:
            logger.info(
                f"{ctx.author.name} is already in the guest list, updating their timestamp."
            )
            self.guest_list = [
                (
                    (guest[0], ctx.message.created_at)
                    if guest[0].name == ctx.author.name
                    else guest
                )
                for guest in self.guest_list
            ]
            return

        if self.current_guest and ctx.author.name == self.current_guest[0].name:
            logger.info(f"{ctx.author.name} is the current guest.")
            return

        self.guest_list.append((ctx.author, ctx.message.created_at))

    def pick_guest(self):
        if self.guest_list:
            self.current_guest = random.choice(self.guest_list)
            self.guest_list = [
                guest
                for guest in self.guest_list
                if guest[0].name != self.current_guest[0].name
            ]
            return self.current_guest
        return None

    def clear_guest(self):
        self.current_guest = None
        self.message_queue.clear()

    def set_guest(self, guest_name):
        guest = next(
            (guest for guest in self.guest_list if guest[0].name == guest_name), None
        )
        if guest:
            self.current_guest = guest
            self.guest_list = [g for g in self.guest_list if g[0].name != guest_name]
        else:
            # Handle the case where the guest is not in the guest_list
            chatter = SimpleChatter(guest_name)
            guest_tuple = (chatter, None)
            self.current_guest = guest_tuple
