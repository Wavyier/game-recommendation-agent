"""
Demo script for the Game Recommendation Agent

This script demonstrates the agent's capabilities with predefined queries.
Perfect for presentations and talks about AI Agents.

Features demonstrated:
- Streaming responses (real-time output)
- Session state (conversation persistence)
- Tool selection (model-driven approach)
"""

import asyncio
from agent import create_game_agent, run_with_async_streaming


def run_basic_demo():
    """Run a basic demonstration without streaming"""
    print("=" * 60)
    print("🎮 Game Recommendation Agent Demo (Basic)")
    print("   Powered by Strands Agents SDK + Amazon Bedrock")
    print("=" * 60)
    
    agent = create_game_agent()
    
    query = "What won Game of the Year in 2025?"
    print(f"\n📝 Query: {query}")
    print("─" * 60)
    
    response = agent(query)
    print(f"\n🤖 Response:\n{response}")


def run_streaming_demo():
    """Run demonstration with streaming responses"""
    print("\n" + "=" * 60)
    print("🎮 Game Recommendation Agent Demo (Streaming)")
    print("   Watch the response appear in real-time!")
    print("=" * 60)
    
    # Create agent with streaming callback
    agent = create_game_agent()
    
    query = "What are the top 3 RPGs on PC?"
    print(f"\n📝 Query: {query}")
    print("─" * 60)
    print("\n🤖 Response: ", end="", flush=True)
    
    # Response streams automatically via callback
    agent(query)
    print("\n")


async def run_async_streaming_demo():
    """Run demonstration with async streaming"""
    print("\n" + "=" * 60)
    print("🎮 Game Recommendation Agent Demo (Async Streaming)")
    print("   Using async iterator pattern")
    print("=" * 60)
    
    agent = create_game_agent()
    
    query = "Tell me about Clair Obscur: Expedition 33"
    print(f"\n📝 Query: {query}")
    print("─" * 60)
    print("\n🤖 Response: ", end="", flush=True)
    
    await run_with_async_streaming(agent, query)


def run_session_demo():
    """Demonstrate session persistence and memory"""
    print("\n" + "=" * 60)
    print("🎮 Game Recommendation Agent Demo (Session State)")
    print("   Showing conversation memory across turns")
    print("=" * 60)
    
    # Create agent with session persistence
    agent = create_game_agent(session_id="demo-session")
    
    conversations = [
        "I really love RPGs and action games",
        "What games would you recommend based on my preferences?",
    ]
    
    for i, query in enumerate(conversations, 1):
        print(f"\n📝 Turn {i}: {query}")
        print("─" * 60)
        print("\n🤖 Response: ", end="", flush=True)
        agent(query)
        print("\n")
    
    # Show that state is maintained
    print("📊 Agent State:")
    print(f"   Messages in history: {len(agent.messages)}")


def run_tool_selection_demo():
    """Demonstrate how the agent selects different tools"""
    print("\n" + "=" * 60)
    print("🎮 Game Recommendation Agent Demo (Tool Selection)")
    print("   Watch the agent choose different tools automatically")
    print("=" * 60)
    
    agent = create_game_agent()
    
    queries = [
        ("Game Awards query", "Who won Best RPG at The Game Awards 2025?"),
        ("Search query", "Find games with 'zelda' in the name"),
        ("Platform query", "What are the best games on Nintendo Switch?"),
    ]
    
    for label, query in queries:
        print(f"\n📝 {label}: {query}")
        print("─" * 60)
        print("\n🤖 Response: ", end="", flush=True)
        agent(query)
        print("\n")
        
        # Reset for next query (fresh context)
        agent = create_game_agent()


def main():
    """Run all demonstrations"""
    print("\n" + "🎬" * 30)
    print("\n  GAME RECOMMENDATION AGENT - FULL DEMO")
    print("  For: 'What are Agents, How Do They Work'")
    print("\n" + "🎬" * 30)
    
    # Demo 1: Basic (no streaming)
    run_basic_demo()
    
    # Demo 2: Streaming responses
    run_streaming_demo()
    
    # Demo 3: Session state
    run_session_demo()
    
    # Demo 4: Tool selection
    run_tool_selection_demo()
    
    # Demo 5: Async streaming (optional)
    # asyncio.run(run_async_streaming_demo())
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
