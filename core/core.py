import asyncio
import random
import re
import string
import requests

from store.db import Database
from exceptions.exceptions import ElevenLabsException
from asyncio import Semaphore
from typing import Generator, Tuple, Dict


class Semaphores:
    """A class managing semaphores for user concurrency.

    Attributes:
        semaphores (Dict[str, Semaphore]): A dictionary mapping usernames to Semaphore instances.
        lock (asyncio.Lock): A lock for synchronizing access to the semaphores dictionary.
    """

    semaphores: Dict[str, Semaphore]
    lock: asyncio.Lock

    def __init__(self) -> None:
        """Initializes the Semaphores with an empty dictionary for user semaphores and an asyncio lock."""
        self.semaphores: Dict[str, Semaphore] = {}
        self.lock = asyncio.Lock()

    async def get(self, name: str) -> Semaphore:
        """Retrieves a semaphore for the specified user, creating one if it does not exist.

        Args:
            name (str): The username for which to retrieve or create a semaphore.

        Returns:
            asyncio.Semaphore: The semaphore associated with the specified user.
        """
        async with self.lock:
            semaphore = self.semaphores.get(name)
            if semaphore is None:
                semaphore = asyncio.Semaphore(3)
                self.semaphores[name] = semaphore
            return semaphore


class App:
    """A class representing the main application logic.

    Attributes:
        db (Database): An instance of the Database class for user management.
        re_pattern (str): A regex pattern for identifying words in text.
        api_key (str): The API key for the ElevenLabs service.
        elevenlabs_url (str): The URL for the ElevenLabs text-to-speech service.
        semaphores (Semaphores): An instance of the Semaphores class for concurrency control.
    """

    db: Database

    re_pattern: str
    api_key: str
    voice_id: str
    elevenlabs_url: str

    semaphores: Semaphores

    def __init__(self, db: Database, api_key: str):
        """Initializes the App with the database and API key.

        Args:
            db (Database): An instance of the Database class.
            api_key (str): The API key for the ElevenLabs service.
        """
        self.re_pattern = r"\b\S+\b"

        self.api_key = api_key
        self.elevenlabs_url = (
            "https://api.elevenlabs.io/v1/text-to-speech/pMsXgVXv3BLzUgSXRplE/stream"
        )

        self.db = db
        self.semaphores = Semaphores()

    async def authenticate(self, username, password: str) -> bool:
        """Authenticates a user by comparing the stored password with the provided password.

        Args:
            username (str): The username of the user attempting to authenticate.
            password (str): The password provided by the user.

        Returns:
            bool: True if the authentication is successful, False otherwise.
        """
        stored_password = await self.db.get_password(username)
        return stored_password == password

    async def _call_elevenlabs(self, text: str) -> requests.Response:
        """Calls the ElevenLabs text-to-speech API to convert text to audio.

        Args:
            text (str): The text to convert to speech.

        Returns:
            requests.Response: The response from the ElevenLabs API.
        """
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        json_data = {
            "text": text,
            "voice_settings": {"stability": 0.75, "similarity_boost": 0.75},
        }
        return requests.post(self.elevenlabs_url, headers=headers, json=json_data)

    async def text_to_speech(self, username, text: str) -> Tuple[str, Generator]:
        """Converts text to speech for a specified user, managing concurrency with semaphores.

        Args:
            username (str): The username of the user requesting the text-to-speech conversion.
            text (str): The text to convert to speech.

        Returns:
            Tuple[str, Generator]: A tuple containing the generated filename and a generator for the audio data.

        Raises:
            ElevenLabsException: If the API response indicates an error.
        """
        semaphore = await self.semaphores.get(username)
        async with semaphore:
            await asyncio.sleep(2)  # delay for tests

            credits = len(re.findall(self.re_pattern, text))
            await self.db.reserve(username, credits)

            response = await self._call_elevenlabs(text)
            if response.status_code != 200:
                await self.db.unreserve(username, credits)
                raise ElevenLabsException(
                    f"Error while processing text: {text}, error: {response.text}"
                )

            filename = f"{''.join(random.choice(string.ascii_lowercase) for _ in range(10))}.mp3"
            await self.db.pay(username, credits)
            return filename, (chunk for chunk in response.iter_content(chunk_size=1024))
