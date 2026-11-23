"""Object-storage clients must stay on the supervised local endpoint."""

import threading
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

from backend.routes.storage_routes import _test_object
from backend.runtime.podman_data_plane import PodmanDataPlaneManager
from backend.storage.connection_manager import ConnectionManager, StorageConfig
from backend.storage.object_store import S3Backend
from core.security.egress_guard import EgressDenied, loopback_s3_client


def _settings(endpoint):
    return {
        "object_endpoint": endpoint,
        "object_access_key": "local-key",
        "object_secret_key": "local-secret",
        "object_region": "us-east-1",
        "object_buckets": ("test-bucket",),
    }


@pytest.mark.parametrize(
    "endpoint", [None, "https://outside.example", "http://192.0.2.1"]
)
def test_object_clients_reject_remote_or_missing_endpoints(endpoint):
    backend = S3Backend(endpoint, "local-key", "local-secret")
    for operation in (backend.exists, backend.delete, backend.get_info):
        with pytest.raises(EgressDenied):
            operation("test-bucket", "item")
    with pytest.raises(EgressDenied):
        backend.create_bucket("test-bucket")

    manager = object.__new__(ConnectionManager)
    manager.config = StorageConfig()
    manager.config.object_storage.endpoint_url = endpoint or "http://outside.example"
    manager.config.object_storage.access_key = "local-key"
    manager.config.object_storage.secret_key = "local-secret"
    with pytest.raises(EgressDenied):
        manager.check_health("object")

    podman = object.__new__(PodmanDataPlaneManager)
    podman.connection_settings = lambda: _settings(endpoint)
    with pytest.raises(EgressDenied):
        podman._probe_protocol("minio")


def test_legacy_storage_diagnostic_reports_denial():
    result = _test_object(
        {
            "provider": "s3",
            "endpoint_url": "http://outside.example",
            "access_key": "local-key",
            "secret_key": "local-secret",
        }
    )
    assert result["connected"] is False


class _S3Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/redirect-bucket"):
            self.send_response(307)
            self.send_header("Location", "http://outside.example/redirect-bucket")
            self.end_headers()
            return
        body = b"<ListBucketResult><Name>test-bucket</Name><IsTruncated>false</IsTruncated></ListBucketResult>"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


@pytest.fixture
def object_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _S3Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://localhost:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def test_object_health_uses_local_service_without_proxy(object_server, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://outside.example:8080")
    monkeypatch.setenv("NO_PROXY", "")
    manager = object.__new__(PodmanDataPlaneManager)
    manager.connection_settings = lambda: _settings(object_server)
    assert manager._probe_protocol("minio") is None


def test_s3_transport_checks_each_request_before_send(object_server):
    client = loopback_s3_client(
        object_server,
        access_key="local-key",
        secret_key="local-secret",
        region="us-east-1",
    )
    with pytest.raises(EgressDenied):
        client.meta.events.emit(
            "before-send.s3.ListBuckets",
            request=SimpleNamespace(url="http://outside.example/", headers={}),
        )
    with pytest.raises(EgressDenied):
        client.meta.events.emit(
            "before-send.s3.ListBuckets",
            request=SimpleNamespace(
                url=client.meta.endpoint_url, headers={"Host": "outside.example"}
            ),
        )


def test_s3_request_redirected_by_sdk_is_denied_before_network(
    object_server, monkeypatch
):
    def fail_if_resolved(*_args, **_kwargs):
        pytest.fail("a denied object-storage request reached DNS")

    monkeypatch.setattr(socket, "getaddrinfo", fail_if_resolved)
    client = loopback_s3_client(
        object_server,
        access_key="local-key",
        secret_key="local-secret",
        region="us-east-1",
    )

    def change_destination(request, **_kwargs):
        request.url = "http://outside.example/"

    client.meta.events.register("before-sign.s3.ListBuckets", change_destination)
    with pytest.raises(EgressDenied):
        client.list_buckets()


def test_s3_redirect_cannot_contact_remote_host(object_server, monkeypatch):
    original_getaddrinfo = socket.getaddrinfo

    def local_only(host, *args, **kwargs):
        assert host == "127.0.0.1", "unexpected DNS or remote connection"
        return original_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", local_only)
    client = loopback_s3_client(
        object_server,
        access_key="local-key",
        secret_key="local-secret",
        region="us-east-1",
    )
    with pytest.raises((ClientError, EgressDenied)):
        client.list_objects_v2(Bucket="redirect-bucket")
