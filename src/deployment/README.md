# TarAIntino - Production Deployment Guide

This directory contains Infrastructure as Code (IaC) using Pulumi to deploy the TarAIntino application to Google Kubernetes Engine (GKE).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          GKE Cluster                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      LoadBalancer                           │ │
│  │                           │                                  │ │
│  │                   NGINX Ingress                             │ │
│  │            (HTTP routing to services)                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌──────────────────────────┴──────────────────────────────┐   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Frontend   │  │ Quiz Service │  │ Screenplay   │  │   │
│  │  │  (3 pods)    │  │  (2-10 pods) │  │  Writer      │  │   │
│  │  │  Port: 3002  │  │  Port: 8082  │  │  (2 pods)    │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │    Scene     │  │    Video     │  │   ChromaDB   │  │   │
│  │  │  Decomposer  │  │  Generator   │  │   (1 pod)    │  │   │
│  │  │  (2 pods)    │  │  (1 pod)     │  │  Port: 8000  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                             │             │   │
│  │                                    ┌────────┴────────┐   │   │
│  │                                    │ Persistent Vol  │   │   │
│  │                                    │    (50 GB)      │   │   │
│  │                                    └─────────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Node Pool: 2-10 nodes (n1-standard-4, autoscaling)            │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Kubernetes Deployment**: Full microservices architecture on GKE
- **Auto-scaling**:
  - Node-level autoscaling (2-10 nodes)
  - Pod-level autoscaling (HPA) for frontend and quiz service
- **Load Balancing**: NGINX Ingress with external LoadBalancer
- **High Availability**: Multiple replicas for critical services
- **Infrastructure as Code**: Fully automated with Pulumi
- **Production-Ready**: Health checks, resource limits, persistent storage

## Prerequisites

### 1. Install Required Tools

```bash
# Install gcloud CLI (macOS)
brew install google-cloud-sdk

# Install Pulumi
brew install pulumi

# Install kubectl
brew install kubectl

# Install Docker (if not already installed)
brew install --cask docker
```

### 2. Set Up GCP Project

```bash
# Login to GCP
gcloud auth login
gcloud auth application-default login

# Set your project
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable storage.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create taraintino-deployer \
  --display-name "TarAIntino Deployment Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:taraintino-deployer@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/container.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:taraintino-deployer@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:taraintino-deployer@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:taraintino-deployer@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/compute.admin"

# Download key
gcloud iam service-accounts keys create ../secrets/gcp-service-account.json \
  --iam-account taraintino-deployer@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="../secrets/gcp-service-account.json"
```

### 4. Create Artifact Registry Repository

```bash
gcloud artifacts repositories create taraintino-images \
  --repository-format=docker \
  --location=us-central1 \
  --description="TarAIntino Docker images"

# Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 5. Set Up Pulumi

```bash
# Login to Pulumi (choose one):

# Option 1: Pulumi Cloud (easiest, free tier)
pulumi login

# Option 2: Self-hosted (GCS backend)
gsutil mb gs://${GCP_PROJECT_ID}-pulumi-state
pulumi login gs://${GCP_PROJECT_ID}-pulumi-state
```

## Deployment Process

The deployment is split into two stages:

1. **Stage 1**: Build and push Docker images to Artifact Registry
2. **Stage 2**: Deploy to GKE cluster

### Stage 1: Build and Push Images

```bash
cd deploy_images

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Update configuration
# Edit Pulumi.dev.yaml and replace YOUR_GCP_PROJECT_ID with your actual project ID

# Initialize Pulumi stack
pulumi stack init dev

# Preview changes
pulumi preview

# Deploy (build and push images)
pulumi up

# Save outputs
pulumi stack output registry_url
```

**Expected Output:**
```
Outputs:
    git_sha: "abc1234"
    registry_url: "us-central1-docker.pkg.dev/your-project/taraintino-images"
    frontend_image: "us-central1-docker.pkg.dev/your-project/taraintino-images/frontend:latest"
    quiz-vector_image: "..."
    ...
```

**Time**: ~15-20 minutes (building 5 Docker images)

### Stage 2: Deploy to Kubernetes

```bash
cd ../deploy_k8s

# Install Python dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Update configuration
# Edit Pulumi.dev.yaml and replace YOUR_GCP_PROJECT_ID

# Initialize Pulumi stack
pulumi stack init dev

# Preview infrastructure changes
pulumi preview

# Deploy to GKE
pulumi up

# Save kubeconfig
pulumi stack output kubeconfig > kubeconfig.yaml
export KUBECONFIG=$(pwd)/kubeconfig.yaml
```

**Expected Output:**
```
Outputs:
    cluster_name: "taraintino-cluster"
    cluster_endpoint: "34.123.45.67"
    load_balancer_ip: "35.223.45.89"
    app_url: "http://35.223.45.89"
    namespace: "taraintino"
    services_deployed: ["chroma", "quiz-service", "screenplay-writer", ...]
```

**Time**: ~15-20 minutes (cluster creation + deployments)

## Post-Deployment Steps

### 1. Verify Cluster is Running

```bash
# Set kubeconfig
export KUBECONFIG=$(pwd)/kubeconfig.yaml

# Check cluster nodes
kubectl get nodes

# Check all pods
kubectl get pods -n taraintino

# Watch pods until all are Running
kubectl get pods -n taraintino -w
```

Expected output:
```
NAME                                READY   STATUS      RESTARTS   AGE
chroma-...                          1/1     Running     0          5m
chroma-init-...                     0/1     Completed   0          5m
frontend-...                        1/1     Running     0          4m
frontend-...                        1/1     Running     0          4m
frontend-...                        1/1     Running     0          4m
quiz-service-...                    1/1     Running     0          4m
quiz-service-...                    1/1     Running     0          4m
scene-decomposer-...                1/1     Running     0          4m
screenplay-writer-...               1/1     Running     0          4m
video-generator-...                 1/1     Running     0          4m
```

### 2. Create Secrets for API Keys

The deployment doesn't include sensitive API keys. Create them manually:

```bash
# Navigate to secrets directory
cd ../secrets

# Create API secrets
kubectl create secret generic api-secrets \
  --from-file=gcp-credentials.json=./gcp-service-account.json \
  --from-literal=openrouter-api-key=YOUR_OPENROUTER_KEY \
  --from-literal=omdb-api-key=YOUR_OMDB_KEY \
  -n taraintino

# Verify secret
kubectl get secrets -n taraintino
```

**Note**: After creating secrets, you may need to restart deployments:

```bash
kubectl rollout restart deployment screenplay-writer -n taraintino
kubectl rollout restart deployment scene-decomposer -n taraintino
kubectl rollout restart deployment video-generator -n taraintino
```

### 3. Access the Application

```bash
# Get LoadBalancer IP
pulumi stack output app_url

# Or use kubectl
kubectl get svc -n taraintino

# Open in browser
# http://<LOAD_BALANCER_IP>
```

### 4. Monitor Logs

```bash
# View logs for specific service
kubectl logs -f deployment/frontend -n taraintino
kubectl logs -f deployment/quiz-service -n taraintino

# View all pod logs
kubectl logs -l app=frontend -n taraintino --tail=100
```

## Testing Autoscaling

### Test Pod Autoscaling (HPA)

Generate load to trigger Horizontal Pod Autoscaling:

```bash
# Install Apache Bench (macOS)
brew install httpd

# Get LoadBalancer IP
LOAD_BALANCER_IP=$(pulumi stack output load_balancer_ip)

# Generate load (1000 requests, 10 concurrent)
ab -n 1000 -c 10 http://${LOAD_BALANCER_IP}/

# Watch pods scale up
kubectl get hpa -n taraintino -w

# Watch pod count increase
kubectl get pods -n taraintino -l app=frontend -w
```

Expected behavior:
- CPU utilization increases above 70%
- HPA triggers scaling
- New pods are created (up to max replicas)
- After load stops, pods scale down after cooldown period

### Test Node Autoscaling

If pod autoscaling hits node capacity:

```bash
# Increase quiz service replicas beyond current capacity
kubectl scale deployment quiz-service --replicas=20 -n taraintino

# Watch for pending pods
kubectl get pods -n taraintino -w

# Watch new nodes being added
kubectl get nodes -w
```

Expected behavior:
- Pods go to "Pending" state (insufficient resources)
- GKE node pool autoscaler adds new nodes (up to max: 10)
- Pending pods schedule on new nodes

## Monitoring and Debugging

### View Resource Usage

```bash
# Check resource usage across nodes
kubectl top nodes

# Check pod resource usage
kubectl top pods -n taraintino

# Describe pod for detailed info
kubectl describe pod <pod-name> -n taraintino
```

### Check Ingress Status

```bash
# Get ingress details
kubectl get ingress -n taraintino

# Describe ingress (shows routing rules)
kubectl describe ingress app-ingress -n taraintino

# Check NGINX Ingress logs
kubectl logs -n taraintino -l app.kubernetes.io/name=ingress-nginx
```

### Debug Service Connectivity

```bash
# Test internal service connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n taraintino -- sh

# Inside debug pod:
curl http://chroma-service:8000/api/v1/heartbeat
curl http://quiz-service:8082/health
curl http://screenplay-service:8080/health
curl http://scene-service:8001/health
curl http://video-service:8003/health
curl http://frontend-service:3000/api/health
```

### Check ChromaDB Initialization

```bash
# Check if chroma-init job completed successfully
kubectl get jobs -n taraintino

# View chroma-init logs
kubectl logs job/chroma-init -n taraintino
```

## Cost Management

### Estimate Monthly Costs

**GKE Cluster**:
- 3 x n1-standard-4 nodes (4 vCPU, 15 GB RAM each)
- 24/7 operation: ~$200-250/month

**Storage**:
- 50 GB persistent disk: ~$2/month

**LoadBalancer**:
- External IP + forwarding rules: ~$20/month

**Total Estimated**: ~$220-270/month

### Cost Optimization Tips

1. **Scale down when not in use**:
   ```bash
   # Scale all deployments to 0
   kubectl scale deployment --all --replicas=0 -n taraintino

   # Scale back up
   kubectl scale deployment frontend --replicas=3 -n taraintino
   kubectl scale deployment quiz-service --replicas=2 -n taraintino
   ```

2. **Use preemptible nodes** (add to node pool config):
   ```python
   preemptible=True  # ~70% cheaper, but can be terminated
   ```

3. **Delete cluster when not needed**:
   ```bash
   pulumi destroy  # Tears down entire infrastructure
   ```

## Cleanup

### Destroy Infrastructure

```bash
# Stage 2: Delete GKE cluster and resources
cd deploy_k8s
pulumi destroy

# Stage 1: Delete Docker images (optional)
cd ../deploy_images
pulumi destroy

# Delete Artifact Registry repository
gcloud artifacts repositories delete taraintino-images \
  --location=us-central1

# Delete GCS bucket (if using Pulumi self-hosted)
gsutil rm -r gs://${GCP_PROJECT_ID}-pulumi-state
```

## Troubleshooting

### Issue: Pods stuck in "ImagePullBackOff"

**Cause**: Docker image not found in Artifact Registry or authentication failure

**Solution**:
```bash
# Check image exists
gcloud artifacts docker images list us-central1-docker.pkg.dev/${GCP_PROJECT_ID}/taraintino-images

# Verify service account has Artifact Registry permissions
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:taraintino-deployer*"

# Re-authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Rebuild and push images
cd deploy_images && pulumi up
```

### Issue: LoadBalancer IP stays "pending"

**Cause**: Ingress controller not fully initialized

**Solution**:
```bash
# Check NGINX Ingress controller status
kubectl get pods -n taraintino -l app.kubernetes.io/name=ingress-nginx

# Wait for controller to be ready (can take 5-10 minutes)
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=ingress-nginx \
  -n taraintino --timeout=600s

# Check service
kubectl get svc -n taraintino | grep LoadBalancer
```

### Issue: ChromaDB initialization fails

**Cause**: GCS bucket access denied or data files missing

**Solution**:
```bash
# Check job logs
kubectl logs job/chroma-init -n taraintino

# Verify GCS bucket exists and is accessible
gsutil ls gs://tag-genome-data/datasets/tag_genome/

# Restart job
kubectl delete job chroma-init -n taraintino
# Job will be recreated by Pulumi or manually:
kubectl create job --from=job/chroma-init chroma-init-retry -n taraintino
```

### Issue: Services can't connect to ChromaDB

**Cause**: ChromaDB pod not ready or service misconfigured

**Solution**:
```bash
# Check ChromaDB pod
kubectl get pods -n taraintino -l app=chroma

# Check ChromaDB service
kubectl get svc chroma-service -n taraintino

# Test connectivity from quiz pod
kubectl exec -it deployment/quiz-service -n taraintino -- \
  curl http://chroma-service:8000/api/v1/heartbeat
```

## CI/CD Integration (Optional)

To integrate with GitHub Actions or other CI/CD:

```yaml
# .github/workflows/deploy.yml
name: Deploy to GKE

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup gcloud
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Install Pulumi
        uses: pulumi/actions@v4

      - name: Build and Push Images
        run: |
          cd src/deployment/deploy_images
          pulumi up --yes --stack prod

      - name: Deploy to K8s
        run: |
          cd src/deployment/deploy_k8s
          pulumi up --yes --stack prod
```

## Additional Resources

- [Pulumi GCP Documentation](https://www.pulumi.com/docs/clouds/gcp/)
- [Pulumi Kubernetes Documentation](https://www.pulumi.com/docs/clouds/kubernetes/)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. View application logs: `kubectl logs -n taraintino <pod-name>`
3. Check Pulumi logs: `pulumi logs`
4. Open an issue in the repository

---

**Remember to rock and roll! 🚀**
