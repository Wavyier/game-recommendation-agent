"""
Game Recommendation Agent powered by Metacritic

This agent uses the Strands Agents SDK to provide personalized game recommendations
based on Metacritic scores, user preferences, and gaming platform.

Features:
- Streaming responses for real-time output
- Session management for conversation persistence
- Agent state for user preferences

Built for the talk: "What are Agents, How Do They Work and How Can We Create an Agent?"
"""

import os
from strands import Agent
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager
from tools import (
    search_games,
    get_game_details,
    get_top_games_by_platform,
    get_recent_releases,
    get_game_awards,
    get_game_of_the_year_history,
)

SYSTEM_PROMPT = """You are GameGuide, an expert video game recommendation assistant powered by Metacritic data.

Your role is to help users discover great games based on their preferences, platform, and interests.

## Your Capabilities:
1. **Search Games**: Find games by title or keywords
2. **Get Game Details**: Provide in-depth information about specific games
3. **Top Games by Platform**: Show the highest-rated games for any platform
4. **Recent Releases**: Find newly released games with good reviews
5. **Game Awards**: Look up The Game Awards winners by year and category (2018-2025)
6. **GOTY History**: See all Game of the Year winners throughout history

## Guidelines:
- Always consider the user's preferred gaming platform (PC, PS5, Xbox, Switch, etc.)
- Use Metascores to gauge critical reception (90+ = Universal Acclaim, 75-89 = Generally Favorable)
- Consider user scores alongside critic scores for a balanced view
- When recommending games, explain WHY a game might appeal to the user
- If a user mentions genres they like, factor that into recommendations
- Be enthusiastic about games but honest about potential drawbacks
- If you can't find a specific game, suggest alternatives or ask for clarification
- Remember user preferences mentioned in the conversation (favorite genres, platforms, etc.)

## Response Style:
- Be conversational and friendly
- Use emojis sparingly to make responses engaging
- Provide concise but informative recommendations
- Always cite Metacritic scores when discussing game quality

Remember: Your goal is to help users find their next favorite game!
"""


def create_game_agent(session_id: str | None = None) -> Agent:
    """Create and configure the game recommendation agent
    
    Args:
        session_id: Optional session ID for conversation persistence.
                   If provided, conversation history and state will be saved.
    """
    # Using cross-region inference profile for Claude 3.5 Haiku
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name="us-east-1",
    )
    
    # Set up session manager for persistence (optional)
    session_manager = None
    if session_id:
        sessions_dir = os.path.join(os.path.dirname(__file__), ".sessions")
        session_manager = FileSessionManager(
            session_id=session_id,
            storage_dir=sessions_dir,
        )
    
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            search_games,
            get_game_details,
            get_top_games_by_platform,
            get_recent_releases,
            get_game_awards,
            get_game_of_the_year_history,
        ],
        session_manager=session_manager,
    )
    
    return agent


def streaming_callback(**kwargs):
    """Callback handler for streaming responses"""
    # Print text chunks as they arrive
    if "data" in kwargs:
        print(kwargs["data"], end="", flush=True)


def create_streaming_agent(session_id: str | None = None) -> Agent:
    """Create agent with streaming callback for real-time output"""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name="us-east-1",
    )
    
    session_manager = None
    if session_id:
        sessions_dir = os.path.join(os.path.dirname(__file__), ".sessions")
        session_manager = FileSessionManager(
            session_id=session_id,
            storage_dir=sessions_dir,
        )
    
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            search_games,
            get_game_details,
            get_top_games_by_platform,
            get_recent_releases,
            get_game_awards,
            get_game_of_the_year_history,
        ],
        session_manager=session_manager,
        callback_handler=streaming_callback,
    )
    
    return agent


async def run_with_async_streaming(agent: Agent, prompt: str):
    """Run agent with async streaming for real-time output"""
    async for event in agent.stream_async(prompt):
        # Print text as it streams
        if "data" in event:
            print(event["data"], end="", flush=True)
        
        # Show tool usage
        if "current_tool_use" in event:
            tool_info = event["current_tool_use"]
            if tool_info.get("name"):
                print(f"\n🔧 Using tool: {tool_info['name']}", flush=True)
    
    print()  # Newline after streaming completes


def main():
    """Run the game recommendation agent in interactive mode with streaming"""
    print("🎮 GameGuide - Your AI Game Recommendation Assistant")
    print("=" * 55)
    print("Powered by Metacritic & Strands Agents SDK")
    print("\nFeatures: Streaming responses, Session persistence")
    print("\nAsk me anything about games! Examples:")
    print("  • 'What are the best RPGs on PC?'")
    print("  • 'Tell me about Elden Ring'")
    print("  • 'What new games came out recently with good reviews?'")
    print("  • 'Recommend games like The Witcher 3'")
    print("  • 'What won Game of the Year in 2025?'")
    print("\nType 'quit' to exit, 'new' for new session.\n")
    
    # Create agent with session persistence and streaming
    session_id = "default-session"
    agent = create_streaming_agent(session_id=session_id)
    
    print(f"📁 Session: {session_id} (conversation will be saved)\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Thanks for using GameGuide! Happy gaming!")
                break
            
            if user_input.lower() == "new":
                # Start a new session
                import uuid
                session_id = f"session-{uuid.uuid4().hex[:8]}"
                agent = create_streaming_agent(session_id=session_id)
                print(f"\n🆕 Started new session: {session_id}\n")
                continue
            
            if user_input.lower() == "history":
                # Show conversation history
                print("\n📜 Conversation History:")
                for msg in agent.messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", [])
                    if content and isinstance(content, list):
                        text = content[0].get("text", "")[:100]
                        print(f"  [{role}]: {text}...")
                print()
                continue
            
            print("\nGameGuide: ", end="", flush=True)
            
            # Agent call with streaming callback - output streams automatically
            agent(user_input)
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
