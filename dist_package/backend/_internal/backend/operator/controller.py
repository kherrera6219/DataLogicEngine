"""
UKG K8s Operator - Core Controller
Manages KnowledgeAlgorithm (KA) resources and scales workers based on Redis queue depth.
"""
import time
import logging
import os
import redis
from kubernetes import client, config, watch

logger = logging.getLogger(__name__)

class DRController:
    """Automated Disaster Recovery Controller. Monitors region health and triggers KA-107."""
    def __init__(self, operator):
        self.operator = operator
        self.health_status = True # Mocking health status

    def check_and_recover(self):
        """Check infrastructure health and trigger recovery if needed."""
        # 1. Simulate check (e.g., checking a health endpoint or AWS CloudWatch)
        is_healthy = self._check_region_health()
        
        if not is_healthy and self.health_status:
            logger.critical("Health Check FAILED. Initiating Automated Disaster Recovery...")
            self.health_status = False
            self._trigger_ka_107()
        elif is_healthy and not self.health_status:
            logger.info("Region health RESTORED.")
            self.health_status = True

    def _check_region_health(self):
        # Mock logic: return False to simulate failure if an environment variable is set
        return os.getenv("SIMULATE_REGION_FAILURE", "false").lower() != "true"

    def _trigger_ka_107(self):
        """Invoke KA-107 Disaster Recovery logic."""
        logger.info("Triggering KA-107 (Disaster Recovery Orchestrator)...")
        # In a real system, this could create a TraceRun CRD or call a KA dispatcher
        # Here we simulate the dispatch
        try:
            from backend.knowledge_algorithms.ka_107_disaster_recovery import run
            context = {"failure_id": "auto_ops_failure", "trigger": "K8s_Operator"}
            result = run(context)
            logger.info(f"KA-107 Execution Result: {result.get('recovery_status')} -> {result.get('target_region')}")
        except ImportError:
            logger.warning("KA-107 module not available in operator context. Simulation only.")

class KAOperator:
    def __init__(self):
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
            
        self.custom_api = client.CustomObjectsApi()
        self.apps_api = client.AppsV1Api()
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379))
        )
        self.dr_controller = DRController(self)

    def reconcile_ka(self, ka_resource):
        """Ensure a Deployment exists for the given KA resource."""
        name = ka_resource['metadata']['name']
        namespace = ka_resource['metadata']['namespace']
        spec = ka_resource['spec']
        ka_id = spec['kaId']
        
        deployment_name = f"ka-worker-{name}"
        
        # 1. Check if deployment exists
        try:
            deploy = self.apps_api.read_namespaced_deployment(deployment_name, namespace)
            logger.info(f"Deployment {deployment_name} already exists. Checking for updates...")
            # Update logic could go here (image changes, resource limits, etc.)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                logger.info(f"Creating new deployment for {ka_id}...")
                self._create_deployment(namespace, deployment_name, spec)
            else:
                raise

    def scale_workers(self):
        """Periodically check queue depths and scale deployments."""
        kas = self.custom_api.list_cluster_custom_object(
            group="ukg.io", version="v1alpha1", plural="knowledgealgorithms"
        )
        
        for ka in kas.get('items', []):
            name = ka['metadata']['name']
            namespace = ka['metadata']['namespace']
            spec = ka['spec']
            scaling = spec.get('scaling', {})
            
            if not scaling:
                continue
                
            queue_name = scaling.get('queueName', 'celery')
            target_depth = scaling.get('targetQueueDepth', 10)
            min_replicas = scaling.get('minReplicas', 1)
            max_replicas = scaling.get('maxReplicas', 10)
            
            # Get actual depth from Redis
            current_depth = self.redis_client.llen(queue_name)
            
            # Simple scaling logic: 1 replica per N items in queue
            desired_replicas = max(min_replicas, min(max_replicas, (current_depth // target_depth) + 1))
            
            deployment_name = f"ka-worker-{name}"
            try:
                deploy = self.apps_api.read_namespaced_deployment(deployment_name, namespace)
                if deploy.spec.replicas != desired_replicas:
                    logger.info(f"Scaling {deployment_name} from {deploy.spec.replicas} to {desired_replicas} (Queue Depth: {current_depth})")
                    deploy.spec.replicas = desired_replicas
                    self.apps_api.patch_namespaced_deployment(deployment_name, namespace, deploy)
            except Exception as e:
                logger.error(f"Failed to scale {deployment_name}: {e}")

    def _create_deployment(self, namespace, name, spec):
        """Helper to create a standard KA worker deployment."""
        container = client.V1Container(
            name="worker",
            image=spec['image'],
            env=[client.V1EnvVar(name="KA_ID", value=spec['kaId'])] + [
                client.V1EnvVar(name=k, value=v) for k, v in spec.get('config', {}).items()
            ],
            resources=client.V1ResourceRequirements(
                limits={"cpu": "500m", "memory": "512Mi"},
                requests={"cpu": "100m", "memory": "128Mi"}
            )
        )
        
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": name, "ka-id": spec['kaId']}),
            spec=client.V1PodSpec(containers=[container])
        )
        
        deployment_spec = client.V1DeploymentSpec(
            replicas=spec.get('replicas', 1),
            selector=client.V1LabelSelector(match_labels={"app": name}),
            template=template
        )
        
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=deployment_spec
        )
        
        self.apps_api.create_namespaced_deployment(namespace, deployment)

    def run(self):
        """Main operator loop."""
        logger.info("UKG Operator starting loop...")
        while True:
            try:
                self.scale_workers()
                # Also watch for CRD events here if using a real framework
            except Exception as e:
                logger.error(f"Error in operator loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    op = KAOperator()
    op.run()
