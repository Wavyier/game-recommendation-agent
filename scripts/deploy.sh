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
        check_aws_credentials
        
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
        echo "🧹 Cleaning up AgentCore resources"
        echo "==================================="
        echo ""
        
        setup_venv
        check_aws_credentials
        
        print_warning "This will delete your deployed agent and associated resources"
        read -p "Continue? (y/N) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            agentcore destroy
            print_status "Cleanup complete"
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
        check_aws_credentials
        
        agentcore status 2>/dev/null || echo "No agent deployed yet"
        ;;
        
    "help"|*)
        echo ""
        echo "🎮 Game Recommendation Agent - Deployment Script"
        echo "================================================"
        echo ""
        echo "Usage: ./scripts/deploy.sh [command] [args]"
        echo ""
        echo "Commands:"
        echo "  setup      Install dependencies and configure environment"
        echo "  dev        Start local development server"
        echo "  invoke-dev Invoke the local dev agent (optional: prompt)"
        echo "  launch     Deploy to Amazon Bedrock AgentCore Runtime"
        echo "  invoke     Invoke the deployed agent (optional: prompt)"
        echo "  status     Check deployment status"
        echo "  cleanup    Delete deployed resources"
        echo "  help       Show this help message"
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
