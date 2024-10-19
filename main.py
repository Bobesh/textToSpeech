import os
import uvicorn

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from slowapi.util import get_remote_address
from starlette import status
from starlette.requests import Request
from starlette.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from exceptions.exceptions import (
    UserDoesNotExistException,
    ElevenLabsException,
    CreditsException,
)
from core import core
from store import db

limiter = Limiter(key_func=get_remote_address)

app = core.App(db.Database(), os.environ["API_KEY"])
api = FastAPI()
api.state.limiter = limiter
api.add_exception_handler(429, _rate_limit_exceeded_handler)

security = HTTPBasic()


@limiter.limit("20/minute")
async def authenticate(
    request: Request, credentials: HTTPBasicCredentials = Depends(security)
):
    """Authenticates a user with basic authentication.

    Args:
        request (Request): The FastAPI request object.
        credentials (HTTPBasicCredentials): The HTTP Basic credentials provided by the user.

    Returns:
        str: The username of the authenticated user.

    Raises:
        HTTPException: If authentication fails due to incorrect username/password or user does not exist.
    """
    try:
        authenticated = await app.authenticate(
            credentials.username, credentials.password
        )
        if not authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username
    except UserDoesNotExistException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Basic"},
        )


class TextToSpeech(BaseModel):
    """A Pydantic model representing the request body for the text-to-speech conversion.

    Attributes:
        text (str): The text to be converted to speech.
    """

    text: str


@api.post("/ttx")
async def text_to_speech(ttx: TextToSpeech, username: str = Depends(authenticate)):
    """Converts text to speech and returns the audio as a streaming response.

    Args:
        ttx (TextToSpeech): The request body containing the text to convert.
        username (str): The authenticated username.

    Returns:
        StreamingResponse: The audio data as a streaming response.

    Raises:
        HTTPException: If there is an error during the text-to-speech conversion.
    """
    try:
        filename, audio_data = await app.text_to_speech(username, ttx.text)
        return StreamingResponse(
            audio_data,
            media_type="audio/mpeg",
            headers={"Content-Disposition": f'"attachment; filename={filename}"'},
        )
    except (ElevenLabsException, CreditsException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"WWW-Authenticate": "Basic"},
        )


if __name__ == "__main__":
    uvicorn.run("main:api")
