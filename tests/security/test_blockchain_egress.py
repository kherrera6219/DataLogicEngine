"""The legacy blockchain transport is confined to its local RPC endpoint."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from backend.truth_engine.truth_link.blockchain_adapter import BlockchainAdapter
from core.security.egress_guard import EgressDenied, loopback_requests_session


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://outside.example",
        "http://outside.example:8545",
        "http://192.0.2.1:8545",
        "http://127.0.0.1@outside.example:8545",
    ],
)
def test_blockchain_rejects_nonlocal_endpoints(endpoint):
    with pytest.raises(EgressDenied):
        BlockchainAdapter(rpc_url=endpoint)


class _RPCHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        body = json.dumps(
            {"jsonrpc": "2.0", "id": request["id"], "result": "local"}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.send_response(302)
        self.send_header("Location", "http://outside.example/")
        self.end_headers()

    def log_message(self, *_args):
        pass


@pytest.fixture
def rpc_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RPCHandler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://localhost:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def test_blockchain_reaches_local_rpc_without_environment_proxy(
    rpc_server, monkeypatch
):
    monkeypatch.setenv("HTTP_PROXY", "http://outside.example:8080")
    monkeypatch.setenv("NO_PROXY", "")
    adapter = BlockchainAdapter(rpc_url=rpc_server)
    assert adapter.rpc_url.startswith("http://127.0.0.1:")
    assert adapter.w3.is_connected()


def test_local_session_refuses_redirects_and_other_origins(rpc_server):
    endpoint, session = loopback_requests_session(rpc_server)
    try:
        assert session.get(endpoint, allow_redirects=True, timeout=3).status_code == 302
        with pytest.raises(EgressDenied):
            session.get("http://outside.example/", timeout=3)
        with pytest.raises(EgressDenied):
            session.get(endpoint, headers={"Host": "outside.example"}, timeout=3)
        assert (
            session.get(
                endpoint, proxies={"http": "http://outside.example:8080"}, timeout=3
            ).status_code
            == 302
        )
    finally:
        session.close()
