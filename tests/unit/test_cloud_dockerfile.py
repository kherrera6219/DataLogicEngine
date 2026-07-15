from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_cloud_frontend_builder_receives_product_version_authority():
    dockerfile = (ROOT / "Dockerfile.cloud").read_text(encoding="utf-8")

    authority_copy = "COPY config/product-versions.json /app/config/product-versions.json"
    assert authority_copy in dockerfile
    assert dockerfile.index(authority_copy) < dockerfile.index("RUN npm run build")


def test_standalone_frontend_builder_receives_product_version_authority():
    dockerfile = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY frontend/package.json frontend/package-lock.json* ./" in dockerfile
    authority_copy = "COPY config/product-versions.json /config/product-versions.json"
    assert authority_copy in dockerfile
    assert dockerfile.index(authority_copy) < dockerfile.index("RUN npm run build")


def test_ci_and_compose_give_frontend_dockerfile_repository_context():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "context: .\n        file: frontend/Dockerfile" in workflow
    assert "context: .\n      dockerfile: frontend/Dockerfile" in compose
