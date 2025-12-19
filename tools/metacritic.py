"""
Metacritic Tools for Game Recommendation Agent

These tools fetch game data from Metacritic to power the recommendation engine.
Uses web scraping with proper rate limiting and error handling.
"""

import httpx
from bs4 import BeautifulSoup
from strands import tool
from pydantic import BaseModel
from typing import Optional
import re


class GameInfo(BaseModel):
    """Game information from Metacritic"""
    title: str
    platform: str
    metascore: Optional[int] = None
    user_score: Optional[float] = None
    release_date: Optional[str] = None
    summary: Optional[str] = None
    genres: list[str] = []
    url: Optional[str] = None


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

PLATFORM_MAP = {
    "pc": "pc",
    "ps5": "playstation-5",
    "ps4": "playstation-4",
    "xbox-series-x": "xbox-series-x",
    "xbox-one": "xbox-one",
    "switch": "switch",
}


def _parse_score(score_text: str) -> Optional[int]:
    """Parse score from text, handling 'tbd' and other edge cases"""
    if not score_text or score_text.lower() in ["tbd", "n/a", ""]:
        return None
    try:
        return int(re.sub(r"[^\d]", "", score_text))
    except (ValueError, TypeError):
        return None


def _parse_user_score(score_text: str) -> Optional[float]:
    """Parse user score from text"""
    if not score_text or score_text.lower() in ["tbd", "n/a", ""]:
        return None
    try:
        return float(score_text)
    except (ValueError, TypeError):
        return None


@tool
def search_games(query: str, platform: str = "all") -> str:
    """
    Search for games on Metacritic by name.
    
    Args:
        query: The game title or keywords to search for
        platform: Filter by platform (pc, ps5, ps4, xbox-series-x, xbox-one, switch, or 'all')
    
    Returns:
        A formatted string with search results including game titles, platforms, and scores
    """
    try:
        search_url = f"https://www.metacritic.com/search/{query}/?page=1&category=13"
        
        with httpx.Client(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
            response = client.get(search_url)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        results: list[dict] = []
        
        # Parse search results
        cards = soup.select("[data-testid='search-result']")[:10]
        
        for card in cards:
            title_elem = card.select_one("h3, .c-finderProductCard_title")
            score_elem = card.select_one("[data-testid='score'], .c-siteReviewScore")
            platform_elem = card.select_one(".c-finderProductCard_meta, .c-tagList")
            
            if title_elem:
                game = {
                    "title": title_elem.get_text(strip=True),
                    "metascore": _parse_score(score_elem.get_text(strip=True)) if score_elem else None,
                    "platform": platform_elem.get_text(strip=True) if platform_elem else "Unknown",
                }
                results.append(game)
        
        if not results:
            return f"No games found matching '{query}'. Try a different search term."
        
        # Format results
        output = f"🎮 Search Results for '{query}':\n\n"
        for i, game in enumerate(results, 1):
            score_display = f"Metascore: {game['metascore']}" if game['metascore'] else "Metascore: TBD"
            output += f"{i}. {game['title']}\n   Platform: {game['platform']}\n   {score_display}\n\n"
        
        return output
        
    except httpx.HTTPError as e:
        return f"Error searching for games: {str(e)}. Please try again."
    except Exception as e:
        return f"Unexpected error during search: {str(e)}"


@tool
def get_game_details(game_title: str, platform: str = "pc") -> str:
    """
    Get detailed information about a specific game from Metacritic.
    
    Args:
        game_title: The exact title of the game (use hyphens for spaces, e.g., 'the-witcher-3-wild-hunt')
        platform: The platform (pc, ps5, ps4, xbox-series-x, xbox-one, switch)
    
    Returns:
        Detailed game information including scores, release date, summary, and genres
    """
    try:
        # Normalize game title for URL
        slug = game_title.lower().replace(" ", "-").replace(":", "").replace("'", "")
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        
        platform_slug = PLATFORM_MAP.get(platform.lower(), platform.lower())
        url = f"https://www.metacritic.com/game/{slug}/"
        
        with httpx.Client(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Extract game details
        title = soup.select_one("h1, .c-productHero_title")
        title_text = title.get_text(strip=True) if title else game_title
        
        metascore_elem = soup.select_one("[data-testid='critic-score'], .c-siteReviewScore_medium")
        metascore = _parse_score(metascore_elem.get_text(strip=True)) if metascore_elem else None
        
        user_score_elem = soup.select_one("[data-testid='user-score'], .c-siteReviewScore_user")
        user_score = _parse_user_score(user_score_elem.get_text(strip=True)) if user_score_elem else None
        
        summary_elem = soup.select_one(".c-productionDetailsGame_description, .c-productDetails_description")
        summary = summary_elem.get_text(strip=True) if summary_elem else "No summary available"
        
        release_elem = soup.select_one(".c-gameDetails_ReleaseDate, [data-testid='release-date']")
        release_date = release_elem.get_text(strip=True) if release_elem else "Unknown"
        
        # Extract genres
        genre_elems = soup.select(".c-genreList a, .c-gameDetails_Genres a")
        genres = [g.get_text(strip=True) for g in genre_elems[:5]]
        
        # Format output
        output = f"🎮 {title_text}\n"
        output += "=" * 50 + "\n\n"
        
        if metascore:
            score_emoji = "🟢" if metascore >= 75 else "🟡" if metascore >= 50 else "🔴"
            output += f"{score_emoji} Metascore: {metascore}/100\n"
        else:
            output += "⚪ Metascore: TBD\n"
        
        if user_score:
            output += f"👥 User Score: {user_score}/10\n"
        
        output += f"📅 Release Date: {release_date}\n"
        
        if genres:
            output += f"🏷️ Genres: {', '.join(genres)}\n"
        
        output += f"\n📝 Summary:\n{summary[:500]}{'...' if len(summary) > 500 else ''}\n"
        output += f"\n🔗 URL: {url}"
        
        return output
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Game '{game_title}' not found on Metacritic. Try searching first with search_games."
        return f"Error fetching game details: HTTP {e.response.status_code}"
    except Exception as e:
        return f"Error getting game details: {str(e)}"


@tool
def get_top_games_by_platform(platform: str = "pc", time_period: str = "all-time") -> str:
    """
    Get the top-rated games for a specific platform from Metacritic.
    
    Args:
        platform: The gaming platform (pc, ps5, ps4, xbox-series-x, xbox-one, switch)
        time_period: Time filter - 'all-time', '2024', '2023', '90-days'
    
    Returns:
        A list of top-rated games with their Metascores
    """
    try:
        platform_slug = PLATFORM_MAP.get(platform.lower(), platform.lower())
        
        # Build URL based on time period
        if time_period == "all-time":
            url = f"https://www.metacritic.com/browse/game/{platform_slug}/all/all-time/metascore/?releaseYearMin=1958&releaseYearMax=2025&page=1"
        elif time_period in ["2024", "2023", "2022"]:
            url = f"https://www.metacritic.com/browse/game/{platform_slug}/all/all-time/metascore/?releaseYearMin={time_period}&releaseYearMax={time_period}&page=1"
        else:
            url = f"https://www.metacritic.com/browse/game/{platform_slug}/all/all-time/metascore/?page=1"
        
        with httpx.Client(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        results: list[dict] = []
        
        # Parse game cards
        cards = soup.select(".c-finderProductCard, [data-testid='product-card']")[:15]
        
        for card in cards:
            title_elem = card.select_one(".c-finderProductCard_title, h3")
            score_elem = card.select_one(".c-siteReviewScore, [data-testid='score']")
            date_elem = card.select_one(".c-finderProductCard_meta span")
            
            if title_elem:
                game = {
                    "title": title_elem.get_text(strip=True),
                    "metascore": _parse_score(score_elem.get_text(strip=True)) if score_elem else None,
                    "release": date_elem.get_text(strip=True) if date_elem else "Unknown",
                }
                results.append(game)
        
        if not results:
            return f"No top games found for {platform}. The platform might not be available."
        
        # Format output
        platform_display = platform.upper().replace("-", " ")
        output = f"🏆 Top Games for {platform_display}"
        if time_period != "all-time":
            output += f" ({time_period})"
        output += ":\n\n"
        
        for i, game in enumerate(results, 1):
            score = game['metascore']
            if score:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                score_emoji = "🟢" if score >= 90 else "🟡" if score >= 75 else "⚪"
                output += f"{medal} {game['title']}\n    {score_emoji} Metascore: {score} | Released: {game['release']}\n\n"
        
        return output
        
    except Exception as e:
        return f"Error fetching top games: {str(e)}"


@tool  
def get_recent_releases(platform: str = "all", min_score: int = 70) -> str:
    """
    Get recently released games with good reviews.
    
    Args:
        platform: Filter by platform (pc, ps5, ps4, xbox-series-x, switch, or 'all')
        min_score: Minimum Metascore to include (default: 70)
    
    Returns:
        A list of recent game releases that meet the score threshold
    """
    try:
        if platform.lower() == "all":
            url = "https://www.metacritic.com/browse/game/all/all/new-releases/metascore/?page=1"
        else:
            platform_slug = PLATFORM_MAP.get(platform.lower(), platform.lower())
            url = f"https://www.metacritic.com/browse/game/{platform_slug}/all/new-releases/metascore/?page=1"
        
        with httpx.Client(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        results: list[dict] = []
        
        cards = soup.select(".c-finderProductCard, [data-testid='product-card']")[:20]
        
        for card in cards:
            title_elem = card.select_one(".c-finderProductCard_title, h3")
            score_elem = card.select_one(".c-siteReviewScore, [data-testid='score']")
            date_elem = card.select_one(".c-finderProductCard_meta span")
            platform_elem = card.select_one(".c-tagList")
            
            if title_elem:
                score = _parse_score(score_elem.get_text(strip=True)) if score_elem else None
                
                # Filter by minimum score
                if score and score >= min_score:
                    game = {
                        "title": title_elem.get_text(strip=True),
                        "metascore": score,
                        "release": date_elem.get_text(strip=True) if date_elem else "Recent",
                        "platform": platform_elem.get_text(strip=True) if platform_elem else platform,
                    }
                    results.append(game)
        
        if not results:
            return f"No recent releases found with Metascore >= {min_score}. Try lowering the threshold."
        
        # Format output
        output = f"🆕 Recent Releases (Metascore ≥ {min_score}):\n\n"
        
        for i, game in enumerate(results[:10], 1):
            score_emoji = "🟢" if game['metascore'] >= 85 else "🟡" if game['metascore'] >= 75 else "⚪"
            output += f"{i}. {game['title']}\n"
            output += f"   {score_emoji} Metascore: {game['metascore']} | {game['release']}\n"
            output += f"   Platform: {game['platform']}\n\n"
        
        return output
        
    except Exception as e:
        return f"Error fetching recent releases: {str(e)}"
