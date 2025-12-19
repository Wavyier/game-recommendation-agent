#!/bin/bash
# Run the Game Recommendation Agent demo
# Usage: ./scripts/demo.sh [demo_type]
# Demo types: all, basic, streaming, session, tools

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.installed
fi

DEMO_TYPE="${1:-all}"

echo ""
echo "🎬 Game Recommendation Agent Demo"
echo "=================================="
echo ""

case "$DEMO_TYPE" in
    "basic")
        echo "Running basic demo (no streaming)..."
        python -c "from demo import run_basic_demo; run_basic_demo()"
        ;;
    "streaming")
        echo "Running streaming demo..."
        python -c "from demo import run_streaming_demo; run_streaming_demo()"
        ;;
    "session")
        echo "Running session/memory demo..."
        python -c "from demo import run_session_demo; run_session_demo()"
        ;;
    "tools")
        echo "Running tool selection demo..."
        python -c "from demo import run_tool_selection_demo; run_tool_selection_demo()"
        ;;
    "all"|*)
        echo "Running full demo suite..."
        python demo.py
        ;;
esac

echo ""
echo "✅ Demo complete!"
