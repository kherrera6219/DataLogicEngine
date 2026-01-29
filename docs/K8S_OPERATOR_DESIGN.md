# Design Sketch: UKG Kubernetes Operator

**Status**: Planning
**Phase**: 30 (v3.0 Strategy)
**Target**: Orchestration of DataLogicEngine clusters ("UKG Operator")

## 1. Objective
To automate the deployment, scaling, and management of the Universal Knowledge Graph (UKG) components on Kubernetes. The Operator will treat "Simulations" and "MCP Servers" as first-class citizens.

## 2. Technical Stack
- **Language**: Python (to leverage existing backend logic/schemas).
- **Framework**: **Kopf** (Kubernetes Operator Pythonic Framework) or **Operator SDK** (Ansible/Helm). Recommended: **Kopf** for flexibility.
- **Base Image**: `python:3.11-slim` with `kubectl`.

## 3. Custom Resource Definitions (CRDs)

### 3.1 `UKGNode`
Represents a core reasoning engine instance.
```yaml
apiVersion: ukg.datalogic.io/v1alpha1
kind: UKGNode
metadata:
  name: primary-reasoning-node
spec:
  role: "coordinator" | "worker"
  personas: ["analyst", "auditor"] # Quad Personas to load
  resources:
    cpu: "2"
    memory: "4Gi"
  knowledge_shards: ["shard-01", "shard-02"]
  vector_store: "chromadb-service"
```

### 3.2 `MCPServer`
Represents an external tool integration point.
```yaml
apiVersion: ukg.datalogic.io/v1alpha1
kind: MCPServer
metadata:
  name: salesforce-connector
spec:
  image: "mcp-salesforce:latest"
  env:
    - name: SF_URL
      value: "https://login.salesforce.com"
  protocol: "sse" | "websocket"
  replicas: 2
```

### 3.3 `SimulationJob`
Represents a finite reasoning task (e.g. "Run 1000 year projection").
```yaml
kind: SimulationJob
spec:
  scenarios: 1000
  complexity_axis: 17
  output_sink: "s3://results-bucket"
```

## 4. Controller Logic (Reconciliation Loop)

### 4.1 Node Reconciliation
1.  **Watch** `UKGNode` events.
2.  **Check** if `Deployment` exists for this node.
3.  **Update** Env Vars with Persona configs.
4.  **Register** Node in `Redis` Service Discovery on startup.
5.  **Heal**: If internal health check (`/health`) fails 3 times, kill Pod (standard K8s, but Operator can trigger alert).

### 4.2 MCP Auto-Wiring
1.  **Watch** `MCPServer` CRD.
2.  **Create** K8s Service (`ClusterIP`).
3.  **Inject** Service DNS (e.g., `salesforce-connector.default.svc.cluster.local`) into the `UKGNode`'s environment so it can discover the tool automatically.

## 5. Scaling Strategy
- **Horizontal Pod Autoscaling (HPA)**:
  - Standard CPU/Mem metrics.
  - **Custom Metrics**: "Queue Depth" from Redis.
- **Node Sharding**:
  - The Operator manages a `StatefulSet` for Vector Store sharding if running embedded ChromaDB.

## 6. Security Model
- **RBAC**: Operator needs Role to manage Deployments, Services, ConfigMaps.
- **Secrets**: API Keys (OpenAI, Salesforce) referenced via `SecretProviderClass` or K8s Secrets, injected into `UKGNode` envs.

## 7. Implementation Roadmap
1.  Define CRDs (OpenAPI Schema).
2.  Write `operator.py` with Kopf handlers.
3.  Build Docker image for Controller.
4.  Deploy to Minikube for testing using `frontend/k8s` manifests (to be created).
