#!/bin/bash

# A2A Registry Deployment Validation Script
# This script validates the deployment status and health of the A2A Registry

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"a2a-registry-dev"}
REGION=${GCP_REGION:-"us-central1"}
CLUSTER_NAME=${GCP_CLUSTER_NAME:-"a2a-registry-cluster"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Set environment-specific variables
if [ "$ENVIRONMENT" = "staging" ]; then
    DEPLOYMENT_NAME="a2a-registry-staging"
    SERVICE_NAME="a2a-registry-staging-service"
    INGRESS_NAME="a2a-registry-staging-ingress"
else
    DEPLOYMENT_NAME="a2a-registry"
    SERVICE_NAME="a2a-registry-service"
    INGRESS_NAME="a2a-registry-ingress"
fi

echo -e "${BLUE}=== A2A Registry Deployment Validation ===${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Cluster: ${CLUSTER_NAME}${NC}"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓ ${message}${NC}"
    elif [ "$status" = "WARNING" ]; then
        echo -e "${YELLOW}⚠ ${message}${NC}"
    else
        echo -e "${RED}✗ ${message}${NC}"
    fi
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if gcloud is available
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud is not installed or not in PATH${NC}"
    exit 1
fi

echo -e "${BLUE}1. Checking GKE cluster access...${NC}"
if gcloud container clusters get-credentials "$CLUSTER_NAME" --region "$REGION" --project "$PROJECT_ID" > /dev/null 2>&1; then
    print_status "OK" "Successfully connected to GKE cluster"
else
    print_status "ERROR" "Failed to connect to GKE cluster"
    exit 1
fi

echo ""
echo -e "${BLUE}2. Checking deployment status...${NC}"
if kubectl get deployment "$DEPLOYMENT_NAME" > /dev/null 2>&1; then
    DEPLOYMENT_STATUS=$(kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.status.conditions[?(@.type=="Available")].status}')
    if [ "$DEPLOYMENT_STATUS" = "True" ]; then
        print_status "OK" "Deployment $DEPLOYMENT_NAME is available"
    else
        print_status "ERROR" "Deployment $DEPLOYMENT_NAME is not available"
    fi
    
    # Check replicas
    DESIRED_REPLICAS=$(kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.spec.replicas}')
    AVAILABLE_REPLICAS=$(kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.status.availableReplicas}')
    if [ "$DESIRED_REPLICAS" = "$AVAILABLE_REPLICAS" ]; then
        print_status "OK" "All replicas are available ($AVAILABLE_REPLICAS/$DESIRED_REPLICAS)"
    else
        print_status "ERROR" "Not all replicas are available ($AVAILABLE_REPLICAS/$DESIRED_REPLICAS)"
    fi
else
    print_status "ERROR" "Deployment $DEPLOYMENT_NAME not found"
fi

echo ""
echo -e "${BLUE}3. Checking pod status...${NC}"
PODS=$(kubectl get pods -l app="$DEPLOYMENT_NAME" --no-headers)
if [ -n "$PODS" ]; then
    echo "$PODS" | while read -r pod; do
        POD_NAME=$(echo "$pod" | awk '{print $1}')
        POD_STATUS=$(echo "$pod" | awk '{print $3}')
        POD_READY=$(echo "$pod" | awk '{print $2}')
        
        if [ "$POD_STATUS" = "Running" ] && [[ "$POD_READY" == *"/1" ]]; then
            print_status "OK" "Pod $POD_NAME is running and ready"
        else
            print_status "ERROR" "Pod $POD_NAME status: $POD_STATUS, ready: $POD_READY"
        fi
    done
else
    print_status "ERROR" "No pods found for deployment $DEPLOYMENT_NAME"
fi

echo ""
echo -e "${BLUE}4. Checking service status...${NC}"
if kubectl get service "$SERVICE_NAME" > /dev/null 2>&1; then
    SERVICE_TYPE=$(kubectl get service "$SERVICE_NAME" -o jsonpath='{.spec.type}')
    print_status "OK" "Service $SERVICE_NAME exists (type: $SERVICE_TYPE)"
    
    # Check endpoints
    ENDPOINTS=$(kubectl get endpoints "$SERVICE_NAME" -o jsonpath='{.subsets[0].addresses[*].ip}')
    if [ -n "$ENDPOINTS" ]; then
        print_status "OK" "Service has endpoints: $ENDPOINTS"
    else
        print_status "WARNING" "Service has no endpoints"
    fi
else
    print_status "ERROR" "Service $SERVICE_NAME not found"
fi

echo ""
echo -e "${BLUE}5. Checking ingress status...${NC}"
if kubectl get ingress "$INGRESS_NAME" > /dev/null 2>&1; then
    INGRESS_STATUS=$(kubectl get ingress "$INGRESS_NAME" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -n "$INGRESS_STATUS" ]; then
        print_status "OK" "Ingress $INGRESS_NAME has IP: $INGRESS_STATUS"
    else
        print_status "WARNING" "Ingress $INGRESS_NAME has no external IP"
    fi
else
    print_status "ERROR" "Ingress $INGRESS_NAME not found"
fi

echo ""
echo -e "${BLUE}6. Checking application health...${NC}"
# Try to get service IP for health check
SERVICE_IP=$(kubectl get service "$SERVICE_NAME" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -n "$SERVICE_IP" ]; then
    if curl -f -s "http://$SERVICE_IP/health" > /dev/null; then
        print_status "OK" "Health endpoint is responding"
    else
        print_status "ERROR" "Health endpoint is not responding"
    fi
else
    # Try port-forward as fallback
    print_status "WARNING" "No external IP, trying port-forward for health check"
    kubectl port-forward service/"$SERVICE_NAME" 8080:80 &
    PF_PID=$!
    sleep 5
    
    if curl -f -s "http://localhost:8080/health" > /dev/null; then
        print_status "OK" "Health endpoint is responding (via port-forward)"
    else
        print_status "ERROR" "Health endpoint is not responding (via port-forward)"
    fi
    
    kill $PF_PID 2>/dev/null || true
fi

echo ""
echo -e "${BLUE}7. Checking resource usage...${NC}"
if command -v kubectl top &> /dev/null; then
    TOP_OUTPUT=$(kubectl top pods -l app="$DEPLOYMENT_NAME" 2>/dev/null || echo "")
    if [ -n "$TOP_OUTPUT" ]; then
        echo "$TOP_OUTPUT"
    else
        print_status "WARNING" "Metrics server not available or no resource data"
    fi
else
    print_status "WARNING" "kubectl top command not available"
fi

echo ""
echo -e "${BLUE}8. Checking recent events...${NC}"
RECENT_EVENTS=$(kubectl get events --field-selector involvedObject.name="$DEPLOYMENT_NAME" --sort-by='.lastTimestamp' --no-headers | tail -5)
if [ -n "$RECENT_EVENTS" ]; then
    echo "$RECENT_EVENTS"
else
    print_status "OK" "No recent events for deployment"
fi

echo ""
echo -e "${BLUE}=== Validation Summary ===${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Deployment: ${DEPLOYMENT_NAME}${NC}"
echo -e "${BLUE}Timestamp: $(date)${NC}"

# Final status check
if kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null | grep -q "True"; then
    echo -e "${GREEN}✓ Deployment validation completed successfully${NC}"
    exit 0
else
    echo -e "${RED}✗ Deployment validation failed${NC}"
    exit 1
fi 