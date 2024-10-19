import asyncio
from typing import Dict, TypedDict

from exceptions.exceptions import UserDoesNotExistException, CreditsException


class UsersDict(TypedDict):
    """Dictionary structure for user data.

    Attributes:
        credits (int): The number of credits available to the user.
        reserved (int): The number of credits currently reserved by the user.
        password (str): The user's password.
    """

    credits: int
    reserved: int
    password: str


class Database:
    """A class representing a database of users with asynchronous access.

    Attributes:
        users (Dict[str, UsersDict]): A dictionary containing user data,
            where keys are usernames and values are user data dictionaries.
        lock (asyncio.Lock): A lock for synchronizing access to the users dictionary.
    """

    users: Dict[str, UsersDict]
    lock: asyncio.Lock

    def __init__(self):
        """Initializes the Database with predefined users and an asyncio lock."""
        self.users = {
            "robert": {
                "credits": 69,
                "reserved": 0,
                "password": "robertHeslo",
            },
            "karel": {
                "credits": 1,
                "reserved": 0,
                "password": "karlovHeslo",
            },
            "oliver": {
                "credits": 20000,
                "reserved": 0,
                "password": "oliverHeslo",
            },
            "blanka": {
                "credits": 0,
                "reserved": 0,
                "password": "blankaHeslo",
            },
        }
        self.lock = asyncio.Lock()

    async def get_password(self, username: str) -> str:
        """Retrieves the password for a given username.

        Args:
            username (str): The username for which to retrieve the password.

        Returns:
            str: The password for the specified username.

        Raises:
            UserDoesNotExistException: If the username does not exist in the database.
        """
        async with self.lock:
            if username in self.users.keys():
                return str(self.users[username]["password"])
            raise UserDoesNotExistException(f"username {username} not found")

    async def reserve(self, username: str, amount: int) -> None:
        """Reserves a specified amount of credits for a user.

        Args:
            username (str): The username of the user requesting the reservation.
            amount (int): The amount of credits to reserve.

        Raises:
            CreditsException: If the user does not have enough available credits to reserve.
        """
        async with self.lock:
            user = self.users.get(username)
            if user is None:
                raise UserDoesNotExistException(f"Username {username} not found")

            if user["credits"] - user["reserved"] < amount:
                raise CreditsException(
                    f"User {username} has less credits than required {amount}"
                )
            user["reserved"] += amount

    async def unreserve(self, username: str, amount: int) -> None:
        """Unreserves a specified amount of credits for a user.

        Args:
            username (str): The username of the user requesting the unreservation.
            amount (int): The amount of credits to unreserve.
        """
        async with self.lock:
            user = self.users.get(username)
            user["reserved"] -= amount

    async def pay(self, username: str, amount: int) -> None:
        """Processes a payment by deducting reserved credits and actual credits from the user.

        Args:
            username (str): The username of the user making the payment.
            amount (int): The amount of credits to deduct from the user.

        """
        async with self.lock:
            user = self.users.get(username)
            user["reserved"] -= amount
            user["credits"] -= amount
