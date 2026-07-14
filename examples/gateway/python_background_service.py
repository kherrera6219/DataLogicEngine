"""Durable background-service polling pattern with bounded cancellation."""

import os
import time
import uuid

from ukg_sdk import UKGClient


client = UKGClient(
    base_url=os.getenv("DATALOGICENGINE_API_URL", "http://127.0.0.1:5000/api/v1"),
    api_key=os.environ["DATALOGICENGINE_API_KEY"],
)
job = client.gateway.create_run(
    [{"role": "user", "content": "Produce the governed background review."}],
    idempotency_key=str(uuid.uuid4()),
)

deadline = time.monotonic() + 120
while job.status in {"queued", "running"} and time.monotonic() < deadline:
    time.sleep(1)
    job = client.gateway.run(job.job_id)

if job.status == "completed":
    print(client.gateway.run_result(job.job_id))
elif job.status in {"queued", "running"}:
    client.gateway.cancel_run(job.job_id)
    raise TimeoutError("Cancelled the DataLogicEngine job after the local deadline.")
else:
    raise RuntimeError(f"Gateway job ended as {job.status}: {job.error_code}")
