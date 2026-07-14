"""Minimal same-host chatbot using the supported Python gateway client."""

import os

from ukg_sdk import UKGClient


client = UKGClient(
    base_url=os.getenv("DATALOGICENGINE_API_URL", "http://127.0.0.1:5000/api/v1"),
    api_key=os.environ["DATALOGICENGINE_API_KEY"],
)

result = client.gateway.chat([
    {"role": "user", "content": "Explain the governed result and cite its approved evidence."}
])
print(result.response)
print(result.run_id)
