#!/bin/bash
# Quick deployment script for TarAIntino to GKE
# Usage: ./deploy.sh [stage]
#   stage: images | k8s | all (default: all)

set -e  # Exit on error

STAGE=${1:-all}
GCP_PROJECT=${GCP_PROJECT_ID:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TarAIntino GKE Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install it first.${NC}"
    echo "  brew install google-cloud-sdk"
    exit 1
fi

if ! command -v pulumi &> /dev/null; then
    echo -e "${RED}Error: Pulumi not found. Please install it first.${NC}"
    echo "  brew install pulumi"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found. Please install it first.${NC}"
    echo "  brew install kubectl"
    exit 1
fi

if [ -z "$GCP_PROJECT" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable not set.${NC}"
    echo "  export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites found${NC}"
echo ""

# Function to deploy images
deploy_images() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Stage 1: Building and Pushing Images${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    cd deploy_images

    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt

    echo ""
    echo -e "${YELLOW}Starting image build and push (this will take 15-20 minutes)...${NC}"
    pulumi up --yes --stack dev

    echo ""
    echo -e "${GREEN}✓ Images built and pushed successfully${NC}"

    deactivate
    cd ..
}

# Function to deploy Kubernetes
deploy_k8s() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Stage 2: Deploying to GKE${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    cd deploy_k8s

    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt

    echo ""
    echo -e "${YELLOW}Starting GKE cluster deployment (this will take 15-20 minutes)...${NC}"
    pulumi up --yes --stack dev

    echo ""
    echo -e "${GREEN}✓ GKE cluster deployed successfully${NC}"

    # Export kubeconfig
    echo ""
    echo "Exporting kubeconfig..."
    pulumi stack output kubeconfig > kubeconfig.yaml
    export KUBECONFIG=$(pwd)/kubeconfig.yaml

    echo -e "${GREEN}✓ Kubeconfig saved to: $(pwd)/kubeconfig.yaml${NC}"
    echo ""
    echo "To use kubectl with your cluster, run:"
    echo -e "${YELLOW}  export KUBECONFIG=$(pwd)/kubeconfig.yaml${NC}"

    deactivate
    cd ..
}

# Function to show status
show_status() {
    cd deploy_k8s

    if [ ! -f "kubeconfig.yaml" ]; then
        echo -e "${YELLOW}Warning: kubeconfig.yaml not found. Run deployment first.${NC}"
        cd ..
        return
    fi

    export KUBECONFIG=$(pwd)/kubeconfig.yaml

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Status${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    echo -e "${YELLOW}Cluster Info:${NC}"
    pulumi stack output app_url

    echo ""
    echo -e "${YELLOW}Pods Status:${NC}"
    kubectl get pods -n taraintino

    echo ""
    echo -e "${YELLOW}Services:${NC}"
    kubectl get svc -n taraintino

    echo ""
    echo -e "${YELLOW}Ingress:${NC}"
    kubectl get ingress -n taraintino

    echo ""
    echo -e "${GREEN}Application URL:${NC}"
    pulumi stack output app_url

    cd ..
}

# Main execution
case $STAGE in
    images)
        deploy_images
        ;;
    k8s)
        deploy_k8s
        show_status
        ;;
    all)
        deploy_images
        deploy_k8s
        show_status
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "${RED}Error: Invalid stage '$STAGE'${NC}"
        echo "Usage: ./deploy.sh [images|k8s|all|status]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete! 🚀${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Create API secrets:"
echo "   kubectl create secret generic api-secrets \\"
echo "     --from-file=gcp-credentials.json=./secrets/gcp-service-account.json \\"
echo "     --from-literal=openrouter-api-key=YOUR_KEY \\"
echo "     -n taraintino"
echo ""
echo "2. Access your application:"
echo "   Open the URL shown above in your browser"
echo ""
echo "3. Monitor logs:"
echo "   kubectl logs -f deployment/frontend -n taraintino"
echo ""
