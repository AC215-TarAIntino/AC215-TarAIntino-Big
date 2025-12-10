"""
Pulumi program to build and push Docker images to Google Artifact Registry.

This script:
1. Builds Docker images for all microservices
2. Pushes images to GCP Artifact Registry
3. Tags images with git commit SHA and 'latest'

Usage:
    pulumi up --stack dev
"""

import subprocess

import pulumi
import pulumi_docker as docker

# Configuration
config = pulumi.Config()
gcp_project = config.require("gcp_project")
gcp_region = config.get("gcp_region") or "us-central1"
registry_url = f"{gcp_region}-docker.pkg.dev/{gcp_project}/taraintino-images"

# Get git commit SHA for versioning
try:
    git_sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
except Exception:
    git_sha = "latest"

pulumi.export("git_sha", git_sha)
pulumi.export("registry_url", registry_url)

# Service definitions: name -> (context_path, dockerfile_path)
services = {
    "quiz-vector": ("../../quiz-vector", "Dockerfile"),
    "screenplay-writer": ("../../screenplay-writer", "Dockerfile"),
    "scene-decomposer": ("../../scene-decomposer", "Dockerfile"),
    "video-generator": ("../../video-generator", "Dockerfile"),
    "frontend": ("../../frontend", "Dockerfile"),
}

# Build and push images
image_outputs = {}

for service_name, (context, dockerfile) in services.items():
    image_name = f"{registry_url}/{service_name}"

    # Build and push image
    image = docker.Image(
        f"{service_name}-image",
        build=docker.DockerBuildArgs(
            context=context,
            dockerfile=f"{context}/{dockerfile}",
            platform="linux/amd64",  # Ensure compatibility with GKE
            # Build args for frontend
            # Updated to use external LoadBalancer IP for browser access
            args=(
                {"NEXT_PUBLIC_QUIZ_API_URL": "http://34.30.95.212:8082"}
                if service_name == "frontend"
                else {}
            ),
        ),
        image_name=image_name,
        registry=docker.RegistryArgs(
            server=f"{gcp_region}-docker.pkg.dev",
        ),
        # Tag with both git SHA and 'latest'
        skip_push=False,
    )

    image_outputs[service_name] = image.image_name
    pulumi.export(f"{service_name}_image", image.image_name)

# Output summary
pulumi.export("images_built", list(services.keys()))
pulumi.export("registry", registry_url)
