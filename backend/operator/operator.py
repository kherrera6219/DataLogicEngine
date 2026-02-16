import kopf
import kubernetes.client as k8s_client
import kubernetes.config as k8s_config
import logging

# --- Constants ---
GROUP = 'ukg.datalogic.io'
VERSION = 'v1alpha1'

# --- Initialization ---
try:
    k8s_config.load_incluster_config()
except k8s_config.ConfigException:
    k8s_config.load_kube_config()

logger = logging.getLogger(__name__)

# --- UKGNode Handlers ---

@kopf.on.create(GROUP, VERSION, 'ukgnodes')
def create_ukg_node(spec, name, namespace, **kwargs):
    """
    Handle the creation of a UKGNode resource.
    Deploys a backend instance configured with specific personas.
    """
    role = spec.get('role', 'worker')
    personas = spec.get('personas', [])
    image = spec.get('image', 'ukg-backend:latest')
    replicas = spec.get('replicas', 1)
    
    logger.info(f"Reconciling UKGNode {name}: role={role}, personas={personas}")

    # Define the Deployment
    container = k8s_client.V1Container(
        name="backend",
        image=image,
        env=[
            k8s_client.V1EnvVar(name="UKG_ROLE", value=role),
            k8s_client.V1EnvVar(name="UKG_PERSONAS", value=",".join(personas)),
        ],
        ports=[k8s_client.V1ContainerPort(container_port=5000)]
    )
    
    template = k8s_client.V1PodTemplateSpec(
        metadata=k8s_client.V1ObjectMeta(labels={"app": name, "ukg-role": role}),
        spec=k8s_client.V1PodSpec(containers=[container])
    )
    
    deployment_spec = k8s_client.V1DeploymentSpec(
        replicas=replicas,
        template=template,
        selector=k8s_client.V1LabelSelector(match_labels={"app": name})
    )
    
    deployment = k8s_client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=k8s_client.V1ObjectMeta(name=name, labels={"app": name}),
        spec=deployment_spec
    )

    # Make the deployment a child of the UKGNode for automatic cleanup
    kopf.adopt(deployment)

    # Create the Deployment
    apps_api = k8s_client.AppsV1Api()
    try:
        apps_api.create_namespaced_deployment(namespace=namespace, body=deployment)
        logger.info(f"Deployment {name} created successfully.")
    except k8s_client.ApiException as e:
        logger.error(f"Failed to create deployment {name}: {e}")
        raise kopf.PermanentError(f"Deployment creation failed: {e}")

    return {'status': 'Created', 'message': f"Managed deployment {name} active."}

@kopf.on.update(GROUP, VERSION, 'ukgnodes')
def update_ukg_node(spec, status, name, namespace, **kwargs):
    """
    Handle updates to UKGNode (e.g. scaling or persona changes).
    """
    replicas = spec.get('replicas', 1)
    
    logger.info(f"Updating UKGNode {name}: scaling to {replicas}")

    apps_api = k8s_client.AppsV1Api()
    try:
        # Update deployment replicas
        patch = {"spec": {"replicas": replicas}}
        apps_api.patch_namespaced_deployment(name=name, namespace=namespace, body=patch)
    except k8s_client.ApiException as e:
        logger.error(f"Failed to update deployment {name}: {e}")

# --- MCPServer Handlers ---

@kopf.on.create(GROUP, VERSION, 'mcpservers')
def create_mcp_server(spec, name, namespace, **kwargs):
    """
    Handle MCPServer creation. Sets up the external tool integration.
    """
    image = spec.get('image')
    protocol = spec.get('protocol', 'sse')
    
    logger.info(f"Deploying MCPServer {name}: image={image}, protocol={protocol}")
    
    # Logic for deploying MCP Server Pods/Services would go here...
    return {'status': 'Active'}
