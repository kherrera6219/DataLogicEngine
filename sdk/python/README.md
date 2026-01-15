# UKG Python SDK

A typed Python client library for the UKG Trace API.

## Installation

```bash
pip install ukg-sdk
# or for development
pip install -e sdk/python
```

## Quick Start

```python
from ukg_sdk import UKGClient

# Initialize client
client = UKGClient(
    base_url="http://localhost:5000/api/v1",
    api_key="your-api-key"
)

# List runs
runs = client.runs.list(status="pass", page=1, per_page=20)
for run in runs.items:
    print(f"Run {run.run_id}: {run.status}")

# Get run details
run = client.runs.get("run-uuid-here")
print(f"Confidence: {run.scores.confidence}")

# Get stages
stages = client.runs.stages("run-uuid-here")
for stage in stages:
    print(f"Stage {stage.name}: {stage.status}")

# Get evidence
evidence = client.runs.evidence("run-uuid-here")
for e in evidence:
    print(f"Evidence from {e.source.type}: {e.snippet[:50]}...")

# Create a chat session
session = client.sessions.create(
    title="New Chat",
    mode="trace",
    constraints={"strict_citations": True}
)

# Export a run
export = client.exports.create("run-uuid-here")
client.exports.download(export.export_id, "output.json")
```

## Features

- **Fully typed** with Pydantic models
- **Async support** with `UKGAsyncClient`
- **Auto-retry** with exponential backoff
- **Rate limiting** aware
- **Bearer token** authentication

## API Coverage

| Module              | Methods                                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| `client.sessions`   | list, create, get, update                                                                                      |
| `client.runs`       | list, get, stages, evidence, claims, axes, personas, kas, policy, memory, metrics, spans, logs, replay, export |
| `client.exports`    | list, get, download                                                                                            |
| `client.compliance` | get, add                                                                                                       |

## License

PolyForm Noncommercial License 1.0.0. See the root [LICENSE](../../LICENSE).
