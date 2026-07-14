"""Bounded OpenAI client shape routed through DataLogicEngine governance."""

import os

from openai import OpenAI


client = OpenAI(
    base_url=os.getenv("DATALOGICENGINE_COMPAT_URL", "http://127.0.0.1:5000/v1"),
    api_key=os.environ["DATALOGICENGINE_API_KEY"],
)
completion = client.chat.completions.create(
    model="dle-standard",
    messages=[{"role": "user", "content": "Summarize the governed evidence."}],
)
print(completion.choices[0].message.content)
