#!/bin/bash
# Environment setup script for TarAIntino deployment
# Run this script once before deploying

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TarAIntino Environment Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Prompt for GCP Project ID
read -p "Enter your GCP Project ID: " GCP_PROJECT_ID

if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: Project ID cannot be empty${NC}"
    exit 1
fi

export GCP_PROJECT_ID

echo ""
echo -e "${GREEN}Setting up for project: ${GCP_PROJECT_ID}${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    echo "Install with: brew install google-cloud-sdk"
    exit 1
fi

echo -e "${YELLOW}1. Authenticating with GCP...${NC}"
gcloud auth login
gcloud auth application-default login
gcloud config set project $GCP_PROJECT_ID

echo ""
echo -e "${YELLOW}2. Enabling required GCP APIs...${NC}"
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com

echo ""
echo -e "${YELLOW}3. Creating service account...${NC}"

SERVICE_ACCOUNT_NAME="taraintino-deployer"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    echo "Service account already exists"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name "TarAIntino Deployment Service Account"
fi

echo ""
echo -e "${YELLOW}4. Granting IAM roles...${NC}"

ROLES=(
    "roles/container.admin"
    "roles/artifactregistry.admin"
    "roles/storage.admin"
    "roles/compute.admin"
    "roles/iam.serviceAccountUser"
)

for ROLE in "${ROLES[@]}"; do
    echo "  Granting $ROLE..."
    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="$ROLE" \
        --quiet
done

echo ""
echo -e "${YELLOW}5. Creating service account key...${NC}"

KEY_FILE="./secrets/gcp-service-account.json"
mkdir -p ./secrets

if [ -f "$KEY_FILE" ]; then
    read -p "Service account key already exists. Overwrite? (y/N): " OVERWRITE
    if [ "$OVERWRITE" != "y" ]; then
        echo "Keeping existing key"
    else
        rm $KEY_FILE
        gcloud iam service-accounts keys create $KEY_FILE \
            --iam-account=$SERVICE_ACCOUNT_EMAIL
        echo -e "${GREEN}✓ New key created${NC}"
    fi
else
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo -e "${GREEN}✓ Key created at: $KEY_FILE${NC}"
fi

export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/$KEY_FILE"

echo ""
echo -e "${YELLOW}6. Creating Artifact Registry repository...${NC}"

REPO_NAME="taraintino-images"
REGION="us-central1"

if gcloud artifacts repositories describe $REPO_NAME --location=$REGION &> /dev/null; then
    echo "Repository already exists"
else
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="TarAIntino Docker images"
    echo -e "${GREEN}✓ Repository created${NC}"
fi

echo ""
echo -e "${YELLOW}7. Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev

echo ""
echo -e "${YELLOW}8. Updating Pulumi configuration files...${NC}"

# Update deploy_images/Pulumi.dev.yaml
sed -i.bak "s/YOUR_GCP_PROJECT_ID/${GCP_PROJECT_ID}/g" deploy_images/Pulumi.dev.yaml && rm deploy_images/Pulumi.dev.yaml.bak

# Update deploy_k8s/Pulumi.dev.yaml
sed -i.bak "s/YOUR_GCP_PROJECT_ID/${GCP_PROJECT_ID}/g" deploy_k8s/Pulumi.dev.yaml && rm deploy_k8s/Pulumi.dev.yaml.bak

echo -e "${GREEN}✓ Configuration files updated${NC}"

echo ""
echo -e "${YELLOW}9. Setting up Pulumi...${NC}"

if ! command -v pulumi &> /dev/null; then
    echo -e "${RED}Error: Pulumi not found${NC}"
    echo "Install with: brew install pulumi"
    exit 1
fi

read -p "Use Pulumi Cloud or GCS backend? (cloud/gcs): " PULUMI_BACKEND

if [ "$PULUMI_BACKEND" == "gcs" ]; then
    BUCKET_NAME="${GCP_PROJECT_ID}-pulumi-state"

    if gsutil ls gs://$BUCKET_NAME &> /dev/null; then
        echo "Bucket already exists"
    else
        gsutil mb gs://$BUCKET_NAME
        echo -e "${GREEN}✓ GCS bucket created${NC}"
    fi

    pulumi login gs://$BUCKET_NAME
else
    pulumi login
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Environment Variables Set:${NC}"
echo "  GCP_PROJECT_ID=$GCP_PROJECT_ID"
echo "  GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
echo ""
echo -e "${YELLOW}To make these permanent, add to your shell profile (~/.zshrc or ~/.bashrc):${NC}"
echo "  export GCP_PROJECT_ID=\"$GCP_PROJECT_ID\""
echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"$GOOGLE_APPLICATION_CREDENTIALS\""
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Add your API keys to secrets/ (see secrets/SECRETS_TEMPLATE.md)"
echo "2. Run deployment:"
echo "   cd $(pwd)"
echo "   ./deploy.sh all"
echo ""
