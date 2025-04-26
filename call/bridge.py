import os
import asyncio
from typing import Callable, Awaitable

from google import genai
from google.genai.types import (
    Blob,
    Content,
    Part,
    LiveConnectConfig,
    Modality,
)
from google.genai.live import AsyncSession

MODEL = "models/gemini-2.0-flash-live-001"
CONFIG = LiveConnectConfig(
    response_modalities=[Modality.TEXT, Modality.AUDIO],
    # input_audio_transcription=AudioTranscriptionConfig(),
    # output_audio_transcription=AudioTranscriptionConfig(),
)


class GeminiAudioBridge:
    def __init__(self):
        self._q = asyncio.Queue()
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self._transcript = []

    async def add_request(self, chunk: bytes):
        """Called by Twilio‐media handler to enqueue raw PCM."""
        await self._q.put(chunk)

    async def terminate(self):
        """Signal end of stream."""
        await self._q.put(None)

    async def start(self, send_audio: Callable[[bytes], Awaitable[None]]):
        async with self.client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            send_task = asyncio.create_task(self._send_loop(session))
            recv_task = asyncio.create_task(self._recv_loop(session, send_audio))
            await asyncio.gather(send_task, recv_task)

    async def _send_loop(self, session: AsyncSession):
        """Pull from queue and send PCM to Gemini"""
        while True:
            chunk = await self._q.get()
            if chunk is None:
                await session.send_client_content(
                    turns=Content(parts=[Part(audio=b"")], role="user"),
                    turn_complete=True,
                )
                break
            await session.send_realtime_input(
                audio=Blob(data=chunk, mime_type="audio/pcm")
            )

    async def _recv_loop(
        self,
        session: AsyncSession,
        send_audio: Callable[[bytes], Awaitable[None]],
    ):
        async for message in session.receive():
            if data := message.data:
                await send_audio(data)
            # if text := message.text:
            #     self._transcript.append(text)
