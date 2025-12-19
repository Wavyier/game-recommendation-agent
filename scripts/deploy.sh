#!/bin/bash
# Deploy the Game Recommendation Agent to Amazon Bedrock AgentCore
# Usage: ./scripts/deploy.sh [command]
# Commands: setup, dev, launch, invoke, cleanup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if virtual environment exists
setup_venv() {
    if [ ! -d "venv" ]; then
        echo "🔧 Creating virtual environment..."
        python3 -m venv venv
    fi
    source venv/bin/activate
}

install_deps() {
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install bedrock-agentcore-starter-toolkit
    print_status "Dependencies installed"
}

check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        echo "Run: aws configure"
        exit 1
    fi
    print_status "AWS credentials configured"
}

check_agentcore_installed() {
    if ! python -c "import bedrock_agentcore_starter_toolkit" &> /dev/null; then
        print_error "AgentCore CLI not installed"
        echo "Run: ./scripts/deploy.sh setup"
        exit 1
    fi
    print_status "AgentCore CLI installed"
}

configure_agent() {
    echo "🔧 Configuring agent with AgentCore..."
    agentcore configure -e main.py
    print_status "Agent configured"
}

COMMAND="${1:-help}"

case "$COMMAND" in
    "setup")
        echo ""
        echo "🚀 Setting up AgentCore deployment environment"
        echo "=============================================="
        echo ""
        
        setup_venv
        install_deps
        check_aws_credentials
        configure_agent
        
        echo ""
        print_status "Setup complete! Next steps:"
        echo "  1. Run: ./scripts/deploy.sh dev    # Test locally"
        echo "  2. Run: ./scripts/deploy.sh launch # Deploy to AWS"
        ;;
        
    "dev")
        echo ""
        echo "🔧 Starting local development server"
        echo "===================================="
        echo ""
        
        setup_venv
        check_agentcore_installed
        check_aws_credentials
        
        echo "Starting AgentCore dev server on http://localhost:8080"
        echo "In another terminal, run: ./scripts/deploy.sh invoke-dev"
        echo ""
        
        agentcore dev
        ;;
        
    "invoke-dev")
        echo ""
        echo "📤 Invoking local dev agent"
        echo "==========================="
        echo ""
        
        setup_venv
        
        PROMPT="${2:-What won Game of the Year in 2025?}"
        echo "Prompt: $PROMPT"
        echo ""
        
        agentcore invoke --dev "{\"prompt\": \"$PROMPT\"}"
        ;;
        
    "launch")
        echo ""
        echo "🚀 Deploying to Amazon Bedrock AgentCore Runtime"
        echo "================================================"
        echo ""
        
        setup_venv
        check_agentcore_installed
        check_aws_credentials
        
        # Run configure if .bedrock_agentcore.yaml doesn't have bedrock_agentcore section
        if ! grep -q "bedrock_agentcore:" .bedrock_agentcore.yaml 2>/dev/null; then
            echo "📝 Running initial configuration..."
            configure_agent
        fi
        
        print_warning "This will create AWS resources and may incur charges"
        read -p "Continue? (y/N) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "Building and deploying agent..."
            agentcore launch
            
            echo ""
            print_status "Deployment complete!"
            echo ""
            echo "Next: Run ./scripts/deploy.sh invoke to test"
        else
            echo "Deployment cancelled"
        fi
        ;;
        
    "invoke")
        echo ""
        echo "📤 Invoking deployed agent"
        echo "=========================="
        echo ""
        
        setup_venv
        
        PROMPT="${2:-What won Game of the Year in 2025?}"
        echo "Prompt: $PROMPT"
        echo ""
        
        agentcore invoke "{\"prompt\": \"$PROMPT\"}"
        ;;
        
    "cleanup")
        echo ""
        echo "🧹 Full Cleanup - AgentCore + AWS Resources"
        echo "============================================"
        echo ""
        
        setup_venv
        check_agentcore_installed
        check_aws_credentials
        
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        REGION="us-east-1"
        
        print_warning "This will delete ALL AgentCore resources including:"
        echo "  • AgentCore agent"
        echo "  • S3 bucket: bedrock-agentcore-${ACCOUNT_ID}-${REGION}"
        echo "  • ECR repository: bedrock-agentcore-*"
        echo "  • IAM roles: *BedrockAgentCore*"
        echo ""
        read -p "Are you sure? This cannot be undone! (y/N) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # 1. Destroy AgentCore agent
            echo ""
            echo "1/4 Destroying AgentCore agent..."
            agentcore destroy 2>/dev/null || echo "No agent to destroy"
            
            # 2. Delete S3 bucket
            echo ""
            echo "2/4 Cleaning up S3 bucket..."
            S3_BUCKET="bedrock-agentcore-${ACCOUNT_ID}-${REGION}"
            if aws s3 ls "s3://${S3_BUCKET}" &>/dev/null; then
                aws s3 rm "s3://${S3_BUCKET}" --recursive
                aws s3 rb "s3://${S3_BUCKET}"
                print_status "Deleted S3 bucket: ${S3_BUCKET}"
            else
                echo "S3 bucket not found or already deleted"
            fi
            
            # 3. Delete ECR repositories
            echo ""
            echo "3/4 Cleaning up ECR repositories..."
            ECR_REPOS=$(aws ecr describe-repositories --query "repositories[?starts_with(repositoryName, 'bedrock-agentcore')].repositoryName" --output text 2>/dev/null)
            if [ -n "$ECR_REPOS" ]; then
                for repo in $ECR_REPOS; do
                    aws ecr delete-repository --repository-name "$repo" --force
                    print_status "Deleted ECR repo: $repo"
                done
            else
                echo "No ECR repositories found"
            fi
            
            # 4. Delete IAM roles
            echo ""
            echo "4/4 Cleaning up IAM roles..."
            IAM_ROLES=$(aws iam list-roles --query "Roles[?contains(RoleName, 'BedrockAgentCore')].RoleName" --output text 2>/dev/null)
            if [ -n "$IAM_ROLES" ]; then
                for role in $IAM_ROLES; do
                    # Detach managed policies
                    POLICIES=$(aws iam list-attached-role-policies --role-name "$role" --query "AttachedPolicies[].PolicyArn" --output text 2>/dev/null)
                    for policy in $POLICIES; do
                        aws iam detach-role-policy --role-name "$role" --policy-arn "$policy" 2>/dev/null
                    done
                    # Delete inline policies
                    INLINE=$(aws iam list-role-policies --role-name "$role" --query "PolicyNames[]" --output text 2>/dev/null)
                    for policy in $INLINE; do
                        aws iam delete-role-policy --role-name "$role" --policy-name "$policy" 2>/dev/null
                    done
                    # Delete the role
                    aws iam delete-role --role-name "$role" 2>/dev/null
                    print_status "Deleted IAM role: $role"
                done
            else
                echo "No IAM roles found"
            fi
            
            echo ""
            print_status "Full cleanup complete!"
        else
            echo "Cleanup cancelled"
        fi
        ;;
        
    "status")
        echo ""
        echo "📊 AgentCore Status"
        echo "==================="
        echo ""
        
        setup_venv
        check_agentcore_installed
        check_aws_credentials
        
        agentcore status 2>/dev/null || echo "No agent deployed yet"
        ;;
        
    "configure")
        echo ""
        echo "🔧 Configuring Agent for AgentCore"
        echo "==================================="
        echo ""
        
        setup_venv
        check_agentcore_installed
        configure_agent
        
        echo ""
        print_status "Configuration complete!"
        echo "The .bedrock_agentcore.yaml file has been updated."
        ;;
        
    "help"|*)
        echo ""
        echo "🎮 Game Recommendation Agent - Deployment Script"
        echo "================================================"
        echo ""
        echo "Usage: ./scripts/deploy.sh [command] [args]"
        echo ""
        echo "Commands:"
        echo "  setup       Install dependencies and configure environment"
        echo "  configure   Run agentcore configure for the agent"
        echo "  dev         Start local development server"
        echo "  invoke-dev  Invoke the local dev agent (optional: prompt)"
        echo "  launch      Deploy to Amazon Bedrock AgentCore Runtime"
        echo "  invoke      Invoke the deployed agent (optional: prompt)"
        echo "  status      Check deployment status"
        echo "  cleanup     Delete agent + S3 bucket + ECR repos + IAM roles"
        echo "  help        Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./scripts/deploy.sh setup"
        echo "  ./scripts/deploy.sh dev"
        echo "  ./scripts/deploy.sh invoke-dev \"What are the best RPGs?\""
        echo "  ./scripts/deploy.sh launch"
        echo "  ./scripts/deploy.sh invoke \"Recommend me a game\""
        echo ""
        ;;
esac
