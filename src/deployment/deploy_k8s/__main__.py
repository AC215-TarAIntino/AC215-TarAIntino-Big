"""
Pulumi program to deploy TarAIntino application to Google Kubernetes Engine (GKE).

This script:
1. Creates a GKE cluster with autoscaling node pools
2. Deploys all microservices (ChromaDB, quiz, screenplay, scene, video, frontend)
3. Sets up NGINX Ingress Controller with LoadBalancer
4. Configures secrets and environment variables
5. Sets up persistent volumes for ChromaDB data

Usage:
    pulumi up --stack dev
"""

import subprocess

import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apps.v1 import DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs as Container,
)
from pulumi_kubernetes.core.v1 import (
    ContainerPortArgs,
    EnvVarArgs,
    EnvVarSourceArgs,
    HTTPGetActionArgs,
    PersistentVolumeClaimSpecArgs,
    PodSpecArgs,
    PodTemplateSpecArgs,
    ResourceRequirementsArgs,
    SecretKeySelectorArgs,
    ServicePortArgs,
    ServiceSpecArgs,
    VolumeArgs,
    VolumeMountArgs,
)
from pulumi_kubernetes.core.v1 import (
    ProbeArgs as Probe,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

# ============================================================================
# Configuration
# ============================================================================

config = pulumi.Config()
gcp_project = config.require("gcp_project")
gcp_region = config.get("gcp_region") or "us-central1"
gcp_zone = config.get("gcp_zone") or f"{gcp_region}-a"
cluster_name = config.get("cluster_name") or "taraintino-cluster"
node_count = config.get_int("node_count") or 3
node_machine_type = config.get("node_machine_type") or "n1-standard-4"
registry_url = f"{gcp_region}-docker.pkg.dev/{gcp_project}/taraintino-images"

# ============================================================================
# GKE Cluster
# ============================================================================

# Create GKE cluster
cluster = gcp.container.Cluster(
    cluster_name,
    name=cluster_name,
    location=gcp_zone,
    initial_node_count=1,  # Will be managed by node pool
    remove_default_node_pool=True,
    deletion_protection=False,  # Set to True in production
    min_master_version="latest",
    network="default",
    subnetwork="default",
)

# Create node pool with autoscaling
node_pool = gcp.container.NodePool(
    f"{cluster_name}-node-pool",
    cluster=cluster.name,
    location=gcp_zone,
    initial_node_count=node_count,
    autoscaling=gcp.container.NodePoolAutoscalingArgs(
        min_node_count=2,
        max_node_count=10,
    ),
    node_config=gcp.container.NodePoolNodeConfigArgs(
        machine_type=node_machine_type,
        oauth_scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
        ],
        disk_size_gb=50,
        disk_type="pd-standard",
    ),
    management=gcp.container.NodePoolManagementArgs(
        auto_repair=True,
        auto_upgrade=True,
    ),
    opts=pulumi.ResourceOptions(ignore_changes=["node_config"]),
)


# Create kubeconfig
def generate_kubeconfig(cluster_name, cluster_endpoint, cluster_ca):
    return f"""apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {cluster_ca}
    server: https://{cluster_endpoint}
  name: {cluster_name}
contexts:
- context:
    cluster: {cluster_name}
    user: {cluster_name}
  name: {cluster_name}
current-context: {cluster_name}
kind: Config
preferences: {{}}
users:
- name: {cluster_name}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      installHint: Install gke-gcloud-auth-plugin for use with kubectl
      provideClusterInfo: true
"""


kubeconfig = pulumi.Output.all(
    cluster.name, cluster.endpoint, cluster.master_auth.cluster_ca_certificate
).apply(lambda args: generate_kubeconfig(args[0], args[1], args[2]))

# Create Kubernetes provider using token-based kubeconfig
# This avoids the gke-gcloud-auth-plugin requirement


def get_token_kubeconfig(cluster_name_val, endpoint_val, ca_cert_val):
    """Generate kubeconfig that uses gcloud access token instead of auth plugin"""
    # Get a fresh access token
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True
    )
    token = result.stdout.strip()

    return f"""apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {ca_cert_val}
    server: https://{endpoint_val}
  name: {cluster_name_val}
contexts:
- context:
    cluster: {cluster_name_val}
    user: {cluster_name_val}
  name: {cluster_name_val}
current-context: {cluster_name_val}
kind: Config
preferences: {{}}
users:
- name: {cluster_name_val}
  user:
    token: {token}
"""


token_kubeconfig = pulumi.Output.all(
    cluster.name, cluster.endpoint, cluster.master_auth.cluster_ca_certificate
).apply(lambda args: get_token_kubeconfig(args[0], args[1], args[2]))

# Create K8s provider with token-based kubeconfig
k8s_provider = k8s.Provider(
    "gke-k8s", kubeconfig=token_kubeconfig, opts=pulumi.ResourceOptions(depends_on=[node_pool])
)

# ============================================================================
# Namespace
# ============================================================================

namespace = k8s.core.v1.Namespace(
    "taraintino-namespace",
    metadata=ObjectMetaArgs(name="taraintino"),
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

ns_name = namespace.metadata.name

# ============================================================================
# ConfigMaps and Secrets
# ============================================================================

# ConfigMap for shared environment variables
config_map = k8s.core.v1.ConfigMap(
    "app-config",
    metadata=ObjectMetaArgs(
        name="app-config",
        namespace=ns_name,
    ),
    data={
        "CHROMA_SERVER_HOST": "chroma-service",
        "CHROMA_SERVER_PORT": "8000",
        "CHROMA_COLLECTION": "movie_tag_relevance_cos",
        "GCS_BUCKET_NAME": "taraintino-showcase-videos",
        "GCS_PREFIX": "video_generator_outputs",
        "TAG_REL_OBJECT": "datasets/tag_genome/tag_relevance.dat",
        "MOVIES_OBJECT": "datasets/tag_genome/movies.dat",
        "TAGS_OBJECT": "datasets/tag_genome/tags.dat",
        "TAGMETA_COLLECTION": "tag_metadata",
        "BATCH_SIZE": "2000",
        "ANONYMIZED_TELEMETRY": "False",
        "CHROMA_TELEMETRY_IMPL": "none",
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# Secret placeholder (user must create this separately with actual credentials)
# kubectl create secret generic api-secrets --from-file=gcp-credentials.json=./path/to/file \
#   --from-literal=openrouter-api-key=YOUR_KEY -n taraintino

# ============================================================================
# Persistent Volume for ChromaDB
# ============================================================================

chroma_pvc = k8s.core.v1.PersistentVolumeClaim(
    "chroma-pvc",
    metadata=ObjectMetaArgs(
        name="chroma-pvc",
        namespace=ns_name,
    ),
    spec=PersistentVolumeClaimSpecArgs(
        access_modes=["ReadWriteOnce"],
        resources=ResourceRequirementsArgs(requests={"storage": "50Gi"}),
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# ============================================================================
# ChromaDB Deployment and Service
# ============================================================================

chroma_deployment = k8s.apps.v1.Deployment(
    "chroma-deployment",
    metadata=ObjectMetaArgs(
        name="chroma",
        namespace=ns_name,
    ),
    spec=DeploymentSpecArgs(
        replicas=1,
        selector=LabelSelectorArgs(match_labels={"app": "chroma"}),
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "chroma"}),
            spec=PodSpecArgs(
                containers=[
                    Container(
                        name="chroma",
                        image="ghcr.io/chroma-core/chroma:0.5.23",
                        ports=[ContainerPortArgs(container_port=8000)],
                        env=[
                            EnvVarArgs(name="CHROMA_SERVER_HOST", value="0.0.0.0"),
                            EnvVarArgs(name="CHROMA_SERVER_HTTP_PORT", value="8000"),
                            EnvVarArgs(name="ALLOW_RESET", value="true"),
                        ],
                        volume_mounts=[VolumeMountArgs(name="chroma-data", mount_path="/data")],
                        liveness_probe=Probe(
                            http_get=HTTPGetActionArgs(path="/api/v1/heartbeat", port=8000),
                            initial_delay_seconds=10,
                            period_seconds=10,
                        ),
                    )
                ],
                volumes=[
                    VolumeArgs(
                        name="chroma-data", persistent_volume_claim={"claim_name": "chroma-pvc"}
                    )
                ],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[chroma_pvc]),
)

chroma_service = k8s.core.v1.Service(
    "chroma-service",
    metadata=ObjectMetaArgs(
        name="chroma-service",
        namespace=ns_name,
    ),
    spec=ServiceSpecArgs(
        selector={"app": "chroma"},
        ports=[ServicePortArgs(port=8000, target_port=8000)],
        type="ClusterIP",
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# ============================================================================
# ChromaDB Initialization Job
# ============================================================================

# ChromaDB init job commented out - data already exists in persistent volume
# chroma_init_job = k8s.batch.v1.Job(
#     "chroma-init-job",
#     metadata=ObjectMetaArgs(
#         name="chroma-init",
#         namespace=ns_name,
#     ),
#     spec=JobSpecArgs(
#         template=PodTemplateSpecArgs(
#             metadata=ObjectMetaArgs(labels={"app": "chroma-init"}),
#             spec=PodSpecArgs(
#                 restart_policy="OnFailure",
#                 containers=[
#                     Container(
#                         name="chroma-init",
#                         image=f"{registry_url}/quiz-vector:latest",
#                         command=[
#                             "sh",
#                             "-c",
#                             "echo 'Starting ChromaDB data ingestion...' && "
#                             "python -m src.datapipeline.downloader --to_chroma --to_tagmeta && "
#                             "echo 'Uploading prior files to GCS...' && "
#                             "gsutil cp /app/src/datapipeline/logs/prior_mean.npy gs://taraintino-showcase-data/quiz-priors/ && "
#                             "gsutil cp /app/src/datapipeline/logs/prior_cov.npy gs://taraintino-showcase-data/quiz-priors/ && "
#                             "gsutil cp /app/src/datapipeline/logs/movie_tag_relevance_cos__tag_index.json gs://taraintino-showcase-data/quiz-priors/ && "
#                             "echo 'ChromaDB initialization complete!'",
#                         ],
#                         env=[
#                             EnvVarArgs(name="CHROMA_SERVER_HOST", value="chroma-service"),
#                             EnvVarArgs(name="CHROMA_SERVER_PORT", value="8000"),
#                             EnvVarArgs(name="CHROMA_COLLECTION", value="movie_tag_relevance_cos"),
#                             EnvVarArgs(name="GCS_BUCKET", value="taraintino-showcase-data"),
#                             EnvVarArgs(
#                                 name="TAG_REL_OBJECT", value="datasets/tag_genome/tag_relevance.dat"
#                             ),
#                             EnvVarArgs(
#                                 name="MOVIES_OBJECT", value="datasets/tag_genome/movies.dat"
#                             ),
#                             EnvVarArgs(name="TAGS_OBJECT", value="datasets/tag_genome/tags.dat"),
#                             EnvVarArgs(name="TAGMETA_COLLECTION", value="tag_metadata"),
#                             EnvVarArgs(name="LOG_DIR", value="/app/src/datapipeline/logs"),
#                             EnvVarArgs(name="BATCH_SIZE", value="2000"),
#                             EnvVarArgs(name="ANONYMIZED_TELEMETRY", value="False"),
#                             EnvVarArgs(name="CHROMA_TELEMETRY_IMPL", value="none"),
#                         ],
#                     )
#                 ],
#             ),
#         ),
#         backoff_limit=3,
#     ),
#     opts=pulumi.ResourceOptions(
#         provider=k8s_provider, depends_on=[chroma_deployment, chroma_service]
#     ),
# )

# ============================================================================
# Quiz Service Deployment and Service
# ============================================================================

quiz_deployment = k8s.apps.v1.Deployment(
    "quiz-deployment",
    metadata=ObjectMetaArgs(
        name="quiz-service",
        namespace=ns_name,
    ),
    spec=DeploymentSpecArgs(
        replicas=2,  # Multiple replicas for load balancing
        selector=LabelSelectorArgs(match_labels={"app": "quiz-service"}),
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "quiz-service"}),
            spec=PodSpecArgs(
                init_containers=[
                    Container(
                        name="download-priors",
                        image="google/cloud-sdk:slim",
                        command=[
                            "sh",
                            "-c",
                            "mkdir -p /data && "
                            "gsutil cp gs://taraintino-showcase-data/quiz-priors/prior_mean.npy /data/ && "
                            "gsutil cp gs://taraintino-showcase-data/quiz-priors/prior_cov.npy /data/ && "
                            "gsutil cp gs://taraintino-showcase-data/quiz-priors/movie_tag_relevance_cos__tag_index.json /data/ && "
                            "echo 'Prior files downloaded successfully'",
                        ],
                        volume_mounts=[VolumeMountArgs(name="prior-data", mount_path="/data")],
                    )
                ],
                containers=[
                    Container(
                        name="quiz-service",
                        image=f"{registry_url}/quiz-vector:latest",
                        command=[
                            "uvicorn",
                            "src.quiz_service.api:app",
                            "--host",
                            "0.0.0.0",
                            "--port",
                            "8082",
                        ],
                        ports=[ContainerPortArgs(container_port=8082)],
                        env=[
                            EnvVarArgs(name="CHROMA_SERVER_HOST", value="chroma-service"),
                            EnvVarArgs(name="CHROMA_SERVER_PORT", value="8000"),
                            EnvVarArgs(name="CHROMA_COLLECTION", value="movie_tag_relevance_cos"),
                            EnvVarArgs(name="PRIOR_MEAN_PATH", value="/data/prior_mean.npy"),
                            EnvVarArgs(name="PRIOR_COV_PATH", value="/data/prior_cov.npy"),
                            EnvVarArgs(
                                name="TAG_INDEX_JSON",
                                value="/data/movie_tag_relevance_cos__tag_index.json",
                            ),
                            EnvVarArgs(name="ANONYMIZED_TELEMETRY", value="False"),
                            EnvVarArgs(name="CHROMA_TELEMETRY_IMPL", value="none"),
                        ],
                        volume_mounts=[VolumeMountArgs(name="prior-data", mount_path="/data")],
                        liveness_probe=Probe(
                            http_get=HTTPGetActionArgs(path="/health", port=8082),
                            initial_delay_seconds=30,
                            period_seconds=10,
                        ),
                        readiness_probe=Probe(
                            http_get=HTTPGetActionArgs(path="/health", port=8082),
                            initial_delay_seconds=10,
                            period_seconds=5,
                        ),
                        resources=ResourceRequirementsArgs(
                            requests={"cpu": "500m", "memory": "1Gi"},
                            limits={"cpu": "2", "memory": "4Gi"},
                        ),
                    )
                ],
                volumes=[VolumeArgs(name="prior-data", empty_dir={})],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider, depends_on=[chroma_deployment, chroma_service]
    ),
)

quiz_service = k8s.core.v1.Service(
    "quiz-k8s-service",
    metadata=ObjectMetaArgs(
        name="quiz-service",
        namespace=ns_name,
    ),
    spec=ServiceSpecArgs(
        selector={"app": "quiz-service"},
        ports=[ServicePortArgs(port=8082, target_port=8082)],
        type="LoadBalancer",  # Changed from ClusterIP to allow external browser access
        session_affinity="ClientIP",  # Ensure same client goes to same pod (required for in-memory sessions)
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# ============================================================================
# Screenplay Writer Deployment and Service
# ============================================================================

screenplay_deployment = k8s.apps.v1.Deployment(
    "screenplay-deployment",
    metadata=ObjectMetaArgs(
        name="screenplay-writer",
        namespace=ns_name,
    ),
    spec=DeploymentSpecArgs(
        replicas=2,
        selector=LabelSelectorArgs(match_labels={"app": "screenplay-writer"}),
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "screenplay-writer"}),
            spec=PodSpecArgs(
                containers=[
                    Container(
                        name="screenplay-writer",
                        image=f"{registry_url}/screenplay-writer:latest",
                        ports=[ContainerPortArgs(container_port=8000)],
                        env=[
                            EnvVarArgs(name="API_HOST", value="0.0.0.0"),
                            EnvVarArgs(name="API_PORT", value="8000"),
                            EnvVarArgs(
                                name="OPENROUTER_API_KEY",
                                value_from=EnvVarSourceArgs(
                                    secret_key_ref=SecretKeySelectorArgs(
                                        name="api-secrets", key="openrouter-api-key"
                                    )
                                ),
                            ),
                            EnvVarArgs(
                                name="OMDB_API_KEY",
                                value_from=EnvVarSourceArgs(
                                    secret_key_ref=SecretKeySelectorArgs(
                                        name="api-secrets", key="omdb-api-key"
                                    )
                                ),
                            ),
                        ],
                        liveness_probe=Probe(
                            http_get=HTTPGetActionArgs(path="/health", port=8000),
                            initial_delay_seconds=10,
                            period_seconds=10,
                            timeout_seconds=5,  # Allow 5 seconds for health check response
                            failure_threshold=12,  # Allow 12 failures (120s total) before restart
                        ),
                        resources=ResourceRequirementsArgs(
                            requests={"cpu": "500m", "memory": "1Gi"},
                            limits={"cpu": "2", "memory": "4Gi"},
                        ),
                    )
                ],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

screenplay_service = k8s.core.v1.Service(
    "screenplay-service",
    metadata=ObjectMetaArgs(
        name="screenplay-service",
        namespace=ns_name,
    ),
    spec=ServiceSpecArgs(
        selector={"app": "screenplay-writer"},
        ports=[ServicePortArgs(port=8080, target_port=8000)],
        type="ClusterIP",
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# ============================================================================
# Scene Decomposer Deployment and Service
# ============================================================================

scene_deployment = k8s.apps.v1.Deployment(
    "scene-deployment",
    metadata=ObjectMetaArgs(
        name="scene-decomposer",
        namespace=ns_name,
    ),
    spec=DeploymentSpecArgs(
        replicas=2,
        selector=LabelSelectorArgs(match_labels={"app": "scene-decomposer"}),
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "scene-decomposer"}),
            spec=PodSpecArgs(
                containers=[
                    Container(
                        name="scene-decomposer",
                        image=f"{registry_url}/scene-decomposer:latest",
                        ports=[ContainerPortArgs(container_port=8001)],
                        env=[
                            EnvVarArgs(name="API_HOST", value="0.0.0.0"),
                            EnvVarArgs(name="API_PORT", value="8001"),
                            EnvVarArgs(
                                name="OPENROUTER_API_KEY",
                                value_from=EnvVarSourceArgs(
                                    secret_key_ref=SecretKeySelectorArgs(
                                        name="api-secrets", key="openrouter-api-key"
                                    )
                                ),
                            ),
                        ],
                        liveness_probe=Probe(
                            http_get=HTTPGetActionArgs(path="/health", port=8001),
                            initial_delay_seconds=10,
                            period_seconds=10,
                            timeout_seconds=5,  # Allow 5 seconds for health check response
                            failure_threshold=12,  # Allow 12 failures (120s total) before restart
                        ),
                        resources=ResourceRequirementsArgs(
                            requests={"cpu": "500m", "memory": "1Gi"},
                            limits={"cpu": "2", "memory": "4Gi"},
                        ),
                    )
                ],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

scene_service = k8s.core.v1.Service(
    "scene-service",
    metadata=ObjectMetaArgs(
        name="scene-service",
        namespace=ns_name,
    ),
    spec=ServiceSpecArgs(
        selector={"app": "scene-decomposer"},
        ports=[ServicePortArgs(port=8001, target_port=8001)],
        type="ClusterIP",
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# ============================================================================
# Video Generator Deployment and Service
# ============================================================================

video_deployment = k8s.apps.v1.Deployment(
    "video-deployment",
    metadata=ObjectMetaArgs(
        name="video-generator",
        namespace=ns_name,
    ),
    spec=DeploymentSpecArgs(
        replicas=1,  # Expensive operation, limit replicas
        selector=LabelSelectorArgs(match_labels={"app": "video-generator"}),
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "video-generator"}),
            spec=PodSpecArgs(
                containers=[
                    Container(
                        name="video-generator",
                        image=f"{registry_url}/video-generator:latest",
                        ports=[ContainerPortArgs(container_port=8003)],
                        env=[
                            EnvVarArgs(name="GCS_BUCKET_NAME", value="taraintino-showcase-videos"),
                            EnvVarArgs(name="GCS_PREFIX", value="video_generator_outputs"),
                        ],
                        liveness_probe=Probe(
                            http_get=HTTPGetActionArgs(path="/health", port=8003),
                            initial_delay_seconds=10,
                            period_seconds=10,
                            timeout_seconds=5,  # Allow 5 seconds for health check response
                            failure_threshold=12,  # Allow 12 failures (120s total) before restart
                        ),
                        resources=ResourceRequirementsArgs(
                            requests={"cpu": "1", "memory": "2Gi"},
                            limits={"cpu": "4", "memory": "8Gi"},
                        ),
                    )
                ],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

video_service = k8s.core.v1.Service(
    "video-service",
    metadata=ObjectMetaArgs(
        name="video-service",
        namespace=ns_name,
    ),
    spec=ServiceSpecArgs(
        selector={"app": "video-generator"},
        ports=[ServicePortArgs(port=8003, target_port=8003)],
        type="ClusterIP",
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# ============================================================================
# Frontend Deployment and Service
# ============================================================================

frontend_deployment = k8s.apps.v1.Deployment(
    "frontend-deployment",
    metadata=ObjectMetaArgs(
        name="frontend",
        namespace=ns_name,
    ),
    spec=DeploymentSpecArgs(
        replicas=3,  # Multiple replicas for high availability
        selector=LabelSelectorArgs(match_labels={"app": "frontend"}),
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "frontend"}),
            spec=PodSpecArgs(
                containers=[
                    Container(
                        name="frontend",
                        image=f"{registry_url}/frontend:latest",
                        ports=[ContainerPortArgs(container_port=3002)],
                        env=[
                            EnvVarArgs(name="NODE_ENV", value="production"),
                            EnvVarArgs(name="NEXT_TELEMETRY_DISABLED", value="1"),
                            EnvVarArgs(name="PORT", value="3002"),
                            EnvVarArgs(name="HOSTNAME", value="0.0.0.0"),
                            # NOTE: Quiz service is exposed via LoadBalancer for browser access
                            # The IP (34.30.95.212) is dynamically assigned by GCP
                            # For production, consider using a static IP reservation
                            EnvVarArgs(
                                name="NEXT_PUBLIC_QUIZ_API_URL", value="http://34.30.95.212:8082"
                            ),
                        ],
                        # Liveness probe removed - Next.js doesn't have /api/health endpoint
                        # Frontend is stable and will restart automatically if it crashes
                        resources=ResourceRequirementsArgs(
                            requests={"cpu": "250m", "memory": "512Mi"},
                            limits={"cpu": "1", "memory": "2Gi"},
                        ),
                    )
                ],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[quiz_service, screenplay_service, scene_service, video_service],
    ),
)

frontend_service = k8s.core.v1.Service(
    "frontend-service",
    metadata=ObjectMetaArgs(
        name="frontend-service",
        namespace=ns_name,
    ),
    spec=ServiceSpecArgs(
        selector={"app": "frontend"},
        ports=[ServicePortArgs(port=80, target_port=3002)],
        type="LoadBalancer",  # Direct LoadBalancer instead of Ingress
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# ============================================================================
# NGINX Ingress Controller
# ============================================================================

# Using LoadBalancer directly instead of Ingress for simplicity
# (NGINX Ingress Helm chart had compatibility issues)

# ============================================================================
# Horizontal Pod Autoscaler (HPA)
# ============================================================================

quiz_hpa = k8s.autoscaling.v2.HorizontalPodAutoscaler(
    "quiz-hpa",
    metadata=ObjectMetaArgs(
        name="quiz-hpa",
        namespace=ns_name,
    ),
    spec=k8s.autoscaling.v2.HorizontalPodAutoscalerSpecArgs(
        scale_target_ref=k8s.autoscaling.v2.CrossVersionObjectReferenceArgs(
            api_version="apps/v1",
            kind="Deployment",
            name="quiz-service",
        ),
        min_replicas=2,
        max_replicas=10,
        metrics=[
            k8s.autoscaling.v2.MetricSpecArgs(
                type="Resource",
                resource=k8s.autoscaling.v2.ResourceMetricSourceArgs(
                    name="cpu",
                    target=k8s.autoscaling.v2.MetricTargetArgs(
                        type="Utilization",
                        average_utilization=70,
                    ),
                ),
            ),
        ],
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[quiz_deployment]),
)

frontend_hpa = k8s.autoscaling.v2.HorizontalPodAutoscaler(
    "frontend-hpa",
    metadata=ObjectMetaArgs(
        name="frontend-hpa",
        namespace=ns_name,
    ),
    spec=k8s.autoscaling.v2.HorizontalPodAutoscalerSpecArgs(
        scale_target_ref=k8s.autoscaling.v2.CrossVersionObjectReferenceArgs(
            api_version="apps/v1",
            kind="Deployment",
            name="frontend",
        ),
        min_replicas=3,
        max_replicas=15,
        metrics=[
            k8s.autoscaling.v2.MetricSpecArgs(
                type="Resource",
                resource=k8s.autoscaling.v2.ResourceMetricSourceArgs(
                    name="cpu",
                    target=k8s.autoscaling.v2.MetricTargetArgs(
                        type="Utilization",
                        average_utilization=70,
                    ),
                ),
            ),
        ],
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[frontend_deployment]),
)

# ============================================================================
# Outputs
# ============================================================================

pulumi.export("cluster_name", cluster.name)
pulumi.export("cluster_endpoint", cluster.endpoint)
pulumi.export("kubeconfig", kubeconfig)
pulumi.export("namespace", ns_name)

# Get LoadBalancer IP from frontend service
load_balancer_ip = frontend_service.status.apply(
    lambda status: (
        status.load_balancer.ingress[0].ip
        if status and status.load_balancer and status.load_balancer.ingress
        else "pending..."
    )
)

pulumi.export("load_balancer_ip", load_balancer_ip)
pulumi.export(
    "app_url",
    load_balancer_ip.apply(lambda ip: f"http://{ip}" if ip != "pending..." else "pending..."),
)

# Get LoadBalancer IP from quiz service
quiz_load_balancer_ip = quiz_service.status.apply(
    lambda status: (
        status.load_balancer.ingress[0].ip
        if status and status.load_balancer and status.load_balancer.ingress
        else "pending..."
    )
)

pulumi.export("quiz_service_ip", quiz_load_balancer_ip)
pulumi.export(
    "quiz_api_url",
    quiz_load_balancer_ip.apply(
        lambda ip: f"http://{ip}:8082" if ip != "pending..." else "pending..."
    ),
)

pulumi.export(
    "services_deployed",
    [
        "chroma",
        "quiz-service",
        "screenplay-writer",
        "scene-decomposer",
        "video-generator",
        "frontend",
    ],
)
