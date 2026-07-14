# DataLogicEngine Client Gateway Examples

These examples call an installed same-host `dle-gateway.v1` service. Create a
least-privilege client in **Settings → Client Gateway**, copy the `ukg_` key once,
and place it in the `DATALOGICENGINE_API_KEY` environment variable. Never paste
an OpenAI or Google provider credential into a client application.

| Example | Use case |
|---|---|
| `powershell_business_app.ps1` | Normal Windows business application using native sync chat. |
| `python_chatbot.py` | Minimal chatbot with the supported Python SDK. |
| `typescript_agent.mjs` | Agent/service call with the supported TypeScript SDK. |
| `python_background_service.py` | Durable background run, polling, result read, and cancellation pattern. |
| `python_openai_compat.py` | Bounded OpenAI client shape using a DataLogicEngine virtual model. |

The default endpoint is loopback. Private-network use is not qualified; follow
`docs/PRIVATE_GATEWAY_RUNBOOK.md` only after a signed release candidate exists.
