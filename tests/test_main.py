import time
import pytest
import asyncio
import httpx

from main import api

@pytest.mark.asyncio
async def test_semaphore_limit_per_user():
    url = "/ttx"
    username = "robert"
    password = "robertHeslo"
    tts_data = {"text": "test speech"}

    async def send_request():
        async with httpx.AsyncClient(app=api, base_url="http://test") as async_client:
            response = await async_client.post(
                url,
                json=tts_data,
                auth=(username, password)
            )
            end_time = time.time()
            return end_time, response

    tasks = [send_request() for _ in range(6)]
    results = await asyncio.gather(*tasks)

    end_times = [res[0] for res in results]
    responses = [res[1] for res in results]

    first_batch_start_times = sorted(end_times[:3])
    second_batch_start_times = sorted(end_times[3:])

    assert second_batch_start_times[0] - first_batch_start_times[-1] >= 2, "More than 3 requests ran simultaneously"
    assert all([res.status_code == 200 for res in responses])