#!/bin/bash

# Verification and Permission Fix Script for GKE Deployment
# This script verifies and applies the correct IAM permissions for the service account

set -e

echo "=================================================="
echo "GKE Deployment Permission Verification & Fix"
echo "=================================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Prompt for project ID
read -p "Enter your GCP Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: Project ID cannot be empty"
    exit 1
fi

# Prompt for service account email
echo ""
echo "To find your service account email:"
echo "  1. Check your GCP_SA_KEY secret in GitHub"
echo "  2. Or run: cat path/to/service-account-key.json | grep client_email"
echo ""
read -p "Enter your Service Account Email: " SERVICE_ACCOUNT_EMAIL

if [ -z "$SERVICE_ACCOUNT_EMAIL" ]; then
    echo "❌ Error: Service Account Email cannot be empty"
    exit 1
fi

echo ""
echo "=================================================="
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "=================================================="
echo ""

# Set the project
echo "📌 Setting active project..."
gcloud config set project $PROJECT_ID

# Step 1: Enable Required APIs
echo ""
echo "🔧 Step 1: Enabling required APIs..."
echo "------------------------------------------------"

APIs=(
    "container.googleapis.com"
    "compute.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for api in "${APIs[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID 2>&1 | grep -v "already enabled" || true
done

echo "✅ APIs enabled"

# Step 2: Check current IAM permissions
echo ""
echo "🔍 Step 2: Checking current IAM permissions..."
echo "------------------------------------------------"

CURRENT_ROLES=$(gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT_EMAIL}" 2>/dev/null || echo "")

if [ -z "$CURRENT_ROLES" ]; then
    echo "⚠️  No roles found for this service account"
else
    echo "Current roles:"
    echo "$CURRENT_ROLES"
fi

# Step 3: Apply required IAM roles
echo ""
echo "🔐 Step 3: Applying required IAM roles..."
echo "------------------------------------------------"

REQUIRED_ROLES=(
    "roles/container.admin"
    "roles/compute.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
)

for role in "${REQUIRED_ROLES[@]}"; do
    echo "  Granting $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="$role" \
        --condition=None \
        --quiet > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "  ✅ $role granted"
    else
        echo "  ⚠️  Warning: Failed to grant $role (might already exist or need org admin)"
    fi
done

# Step 4: Verify final permissions
echo ""
echo "🔍 Step 4: Verifying final permissions..."
echo "------------------------------------------------"

FINAL_ROLES=$(gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT_EMAIL}")

echo "$FINAL_ROLES"

# Step 5: Check for all required roles
echo ""
echo "✅ Step 5: Permission verification summary..."
echo "------------------------------------------------"

ALL_PRESENT=true
for role in "${REQUIRED_ROLES[@]}"; do
    if echo "$FINAL_ROLES" | grep -q "$role"; then
        echo "  ✅ $role - Present"
    else
        echo "  ❌ $role - MISSING"
        ALL_PRESENT=false
    fi
done

echo ""
echo "=================================================="

if [ "$ALL_PRESENT" = true ]; then
    echo "✅ SUCCESS: All required permissions are in place!"
    echo ""
    echo "Next steps:"
    echo "  1. Wait 2-3 minutes for permissions to propagate"
    echo "  2. Re-run your GitHub Actions workflow"
    echo "  3. The deployment should now succeed"
else
    echo "⚠️  WARNING: Some permissions are missing!"
    echo ""
    echo "Possible reasons:"
    echo "  1. You may need Organization Admin rights to grant these roles"
    echo "  2. Organization policies might be blocking certain roles"
    echo "  3. The service account might be from a different project"
    echo ""
    echo "Please contact your GCP organization administrator to grant the missing roles."
fi

echo "=================================================="
