#!/bin/bash

# A2A Registry Environment Setup Script

set -e

echo "🚀 Setting up A2A Registry environment..."

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Create .env from example
if [ -f "env.example" ]; then
    cp env.example .env
    echo "✅ Created .env from env.example"
else
    echo "❌ env.example not found. Creating basic .env file..."
    cat > .env << EOF
# GCP Configuration
GCP_PROJECT_ID=a2a-registry-dev
GCP_REGION=us-central1
GCP_CLUSTER_NAME=a2a-registry-cluster

# Domain Configuration
DOMAIN=a2a-registry.dev
API_SUBDOMAIN=api
REGISTRY_SUBDOMAIN=registry

# Deployment Configuration
USE_CLOUDFLARE=true
ENABLE_DIRECT_SSL=false

# Docker Configuration
DOCKER_REGISTRY=gcr.io
DOCKER_IMAGE_NAME=a2a-registry
EOF
fi

# Make the script executable
chmod +x scripts/setup-env.sh

echo "📝 Please edit .env file with your specific values:"
echo "   nano .env"
echo ""
echo "🔧 To load environment variables in your current shell:"
echo "   source .env"
echo ""
echo "🔧 To load environment variables automatically, add to your shell profile:"
echo "   echo 'source $(pwd)/.env' >> ~/.bashrc  # or ~/.zshrc"
echo ""
echo "✅ Environment setup complete!" 