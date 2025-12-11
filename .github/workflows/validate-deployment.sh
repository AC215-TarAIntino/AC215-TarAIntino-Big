#!/bin/bash
#
# Deployment Workflow Validation Script
# This script validates the CI/CD deployment configuration
#

set -e

echo "🔍 Validating CI/CD Deployment Configuration"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    exit 1
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

# 1. Check workflow file exists
echo "1. Checking workflow file..."
if [ -f ".github/workflows/ci.yml" ]; then
    check_pass "Workflow file exists"
else
    check_fail "Workflow file not found"
fi

# 2. Validate YAML syntax
echo ""
echo "2. Validating YAML syntax..."
if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" 2>/dev/null; then
    check_pass "YAML syntax is valid"
else
    check_fail "YAML syntax validation failed"
fi

# 3. Check deployment directories
echo ""
echo "3. Checking deployment directory structure..."
for dir in "src/deployment/deploy_images" "src/deployment/deploy_k8s"; do
    if [ -d "$dir" ]; then
        check_pass "Directory exists: $dir"
    else
        check_fail "Missing directory: $dir"
    fi
done

# 4. Check requirements.txt files
echo ""
echo "4. Checking requirements.txt files..."
for req in "src/deployment/deploy_images/requirements.txt" "src/deployment/deploy_k8s/requirements.txt"; do
    if [ -f "$req" ]; then
        check_pass "Found: $req"
    else
        check_fail "Missing: $req"
    fi
done

# 5. Check Pulumi files
echo ""
echo "5. Checking Pulumi configuration files..."
for pulumi_file in "src/deployment/deploy_images/__main__.py" "src/deployment/deploy_k8s/__main__.py"; do
    if [ -f "$pulumi_file" ]; then
        check_pass "Found: $pulumi_file"
    else
        check_fail "Missing: $pulumi_file"
    fi
done

# 6. Check Pulumi stack configs
echo ""
echo "6. Checking Pulumi stack configurations..."
for stack_file in "src/deployment/deploy_images/Pulumi.dev.yaml" "src/deployment/deploy_k8s/Pulumi.dev.yaml"; do
    if [ -f "$stack_file" ]; then
        check_pass "Found: $stack_file"
    else
        check_warn "Missing: $stack_file (will be created on first run)"
    fi
done

# 7. Verify workflow job dependencies
echo ""
echo "7. Validating workflow job dependencies..."
if grep -q "needs: \[status-check, detect-changes\]" .github/workflows/ci.yml; then
    check_pass "Deploy job has correct dependencies"
else
    check_fail "Deploy job dependencies are incorrect"
fi

# 8. Check for required secrets documentation
echo ""
echo "8. Checking secrets documentation..."
if grep -q "GCP_SA_KEY" README.md && grep -q "GCP_PROJECT_ID" README.md && grep -q "PULUMI_ACCESS_TOKEN" README.md; then
    check_pass "Required secrets are documented in README"
else
    check_warn "Some required secrets may not be documented"
fi

# 9. Verify Pulumi login is present
echo ""
echo "9. Checking Pulumi authentication..."
if grep -q "pulumi login" .github/workflows/ci.yml; then
    check_pass "Pulumi login step found"
else
    check_fail "Pulumi login step missing"
fi

# 10. Verify GCP authentication
echo ""
echo "10. Checking GCP authentication..."
if grep -q "google-github-actions/auth@v2" .github/workflows/ci.yml; then
    check_pass "GCP authentication step found"
else
    check_fail "GCP authentication step missing"
fi

# 11. Check for proper stack selection
echo ""
echo "11. Checking Pulumi stack selection..."
if grep -q "pulumi stack select dev" .github/workflows/ci.yml; then
    check_pass "Pulumi stack selection found"
else
    check_warn "Pulumi stack selection may need review"
fi

# 12. Verify config set commands
echo ""
echo "12. Checking Pulumi config commands..."
if grep -q "pulumi config set gcp_project" .github/workflows/ci.yml; then
    check_pass "GCP project config is set in workflow"
else
    check_fail "GCP project config is not set in workflow"
fi

# Summary
echo ""
echo "=============================================="
echo -e "${GREEN}✅ Validation Complete!${NC}"
echo ""
echo "📋 Next Steps:"
echo "1. Ensure GitHub secrets are configured:"
echo "   - GCP_SA_KEY"
echo "   - GCP_PROJECT_ID"
echo "   - PULUMI_ACCESS_TOKEN"
echo ""
echo "2. Test the workflow by pushing to main branch"
echo ""
echo "3. Monitor deployment in GitHub Actions tab"
echo ""
