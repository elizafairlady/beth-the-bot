from setuptools import setup, find_packages

setup(
    name="beth-the-bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "colorlog",
        "elevenlabs",
        "Flask",
        "Flask_Cors",
        "Flask_SocketIO",
        "numpy",
        "obs_websocket_py",
        "Pillow",
        "PyAudio",
        "setuptools",
        "soundfile",
        "twitchio",
    ],
)
