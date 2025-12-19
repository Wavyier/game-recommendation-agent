"""
Demo script for the Game Recommendation Agent

This script demonstrates the agent's capabilities with predefined queries.
Perfect for presentations and talks about AI Agents.
"""

from agent import create_game_agent


def run_demo():
    """Run a demonstration of the game recommendation agent"""
    
    print("=" * 60)
    print("🎮 Game Recommendation Agent Demo")
    print("   Powered by Strands Agents SDK + Amazon Bedrock")
    print("=" * 60)
    
    agent = create_game_agent()
    
    demo_queries = [
        "What are the top 5 highest-rated games on PC of all time?",
        "Tell me about Baldur's Gate 3",
        "What good games came out recently on PS5?",
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{'─' * 60}")
        print(f"📝 Demo Query {i}: {query}")
        print("─" * 60)
        
        try:
            response = agent(query)
            print(f"\n🤖 Agent Response:\n{response}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print()
    
    print("=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
