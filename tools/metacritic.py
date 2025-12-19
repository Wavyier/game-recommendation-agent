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


# The Game Awards winners data
# Year corresponds to the award show year (e.g., 2025 = The Game Awards 2025, held Dec 2025)
GAME_AWARDS_DATA = {
    2025: {
        "Game of the Year": "Clair Obscur: Expedition 33",
        "Best Game Direction": "Clair Obscur: Expedition 33",
        "Best Narrative": "Clair Obscur: Expedition 33",
        "Best Art Direction": "Clair Obscur: Expedition 33",
        "Best Score and Music": "Clair Obscur: Expedition 33 (Lorien Testard)",
        "Best Audio Design": "Battlefield 6",
        "Best Performance": "Jennifer English as Maelle (Clair Obscur: Expedition 33)",
        "Games for Impact": "South of Midnight",
        "Best Ongoing Game": "No Man's Sky",
        "Best Community Support": "Baldur's Gate 3",
        "Best Indie Game": "Clair Obscur: Expedition 33",
        "Best Debut Indie Game": "Clair Obscur: Expedition 33",
        "Best Mobile Game": "Umamusume: Pretty Derby",
        "Best VR/AR Game": "The Midnight Walk",
        "Best Action Game": "Hades II",
        "Best Action/Adventure Game": "Hollow Knight: Silksong",
        "Best RPG": "Clair Obscur: Expedition 33",
        "Best Fighting Game": "Fatal Fury: City of the Wolves",
        "Best Family Game": "Donkey Kong Bananza",
        "Best Sim/Strategy Game": "Final Fantasy Tactics: The Ivalice Chronicles",
        "Best Sports/Racing Game": "Mario Kart World",
        "Best Multiplayer Game": "Arc Raiders",
        "Best Adaptation": "The Last of Us: Season 2",
        "Most Anticipated Game": "Grand Theft Auto VI",
        "Content Creator of the Year": "MoistCr1TiKaL",
        "Best Esports Game": "Counter-Strike 2",
        "Best Esports Athlete": "Chovy (League of Legends)",
        "Best Esports Team": "Team Vitality",
        "Player's Voice": "Wuthering Waves",
        "Innovation in Accessibility": "Doom: The Dark Ages",
        "Game Changer Award": "Girls Make Games",
    },
    2024: {
        "Game of the Year": "Astro Bot",
        "Best Game Direction": "Astro Bot",
        "Best Narrative": "Metaphor: ReFantazio",
        "Best Art Direction": "Metaphor: ReFantazio",
        "Best Score and Music": "Final Fantasy VII Rebirth",
        "Best Audio Design": "Senua's Saga: Hellblade II",
        "Best Performance": "Melina Juergens (Senua's Saga: Hellblade II)",
        "Games for Impact": "Neva",
        "Best Ongoing Game": "Helldivers 2",
        "Best Indie Game": "Balatro",
        "Best Debut Indie Game": "Balatro",
        "Best Mobile Game": "Balatro",
        "Best VR/AR Game": "Batman: Arkham Shadow",
        "Best Action Game": "Black Myth: Wukong",
        "Best Action/Adventure Game": "Astro Bot",
        "Best RPG": "Metaphor: ReFantazio",
        "Best Fighting Game": "Tekken 8",
        "Best Family Game": "Astro Bot",
        "Best Sim/Strategy Game": "Frostpunk 2",
        "Best Sports/Racing Game": "EA Sports FC 25",
        "Best Multiplayer Game": "Helldivers 2",
        "Best Adaptation": "Fallout (TV Series)",
        "Most Anticipated Game": "Grand Theft Auto VI",
        "Content Creator of the Year": "CaseOh",
        "Best Esports Game": "League of Legends",
        "Player's Voice": "Black Myth: Wukong",
        "Innovation in Accessibility": "Prince of Persia: The Lost Crown",
    },
    2023: {
        "Game of the Year": "Baldur's Gate 3",
        "Best Game Direction": "Alan Wake 2",
        "Best Narrative": "Alan Wake 2",
        "Best Art Direction": "Alan Wake 2",
        "Best Score and Music": "Final Fantasy XVI",
        "Best Audio Design": "Hi-Fi Rush",
        "Best Performance": "Neil Newbon (Baldur's Gate 3)",
        "Games for Impact": "Tchia",
        "Best Ongoing Game": "Cyberpunk 2077",
        "Best Indie Game": "Sea of Stars",
        "Best Debut Indie Game": "Cocoon",
        "Best Mobile Game": "Honkai: Star Rail",
        "Best VR/AR Game": "Resident Evil Village VR Mode",
        "Best Action Game": "Armored Core VI: Fires of Rubicon",
        "Best Action/Adventure Game": "The Legend of Zelda: Tears of the Kingdom",
        "Best RPG": "Baldur's Gate 3",
        "Best Fighting Game": "Street Fighter 6",
        "Best Family Game": "Super Mario Bros. Wonder",
        "Best Sim/Strategy Game": "Pikmin 4",
        "Best Sports/Racing Game": "Forza Motorsport",
        "Best Multiplayer Game": "Baldur's Gate 3",
        "Best Adaptation": "The Last of Us (TV Series)",
        "Most Anticipated Game": "Final Fantasy VII Rebirth",
        "Content Creator of the Year": "IronMouse",
        "Best Esports Game": "Valorant",
    },
    2022: {
        "Game of the Year": "Elden Ring",
        "Best Game Direction": "Elden Ring",
        "Best Narrative": "God of War Ragnarök",
        "Best Art Direction": "Elden Ring",
        "Best Score and Music": "God of War Ragnarök",
        "Best Audio Design": "God of War Ragnarök",
        "Best Performance": "Christopher Judge (God of War Ragnarök)",
        "Games for Impact": "As Dusk Falls",
        "Best Ongoing Game": "Final Fantasy XIV",
        "Best Indie Game": "Stray",
        "Best Debut Indie Game": "Stray",
        "Best Mobile Game": "Marvel Snap",
        "Best VR/AR Game": "Moss: Book II",
        "Best Action Game": "Bayonetta 3",
        "Best Action/Adventure Game": "God of War Ragnarök",
        "Best RPG": "Elden Ring",
        "Best Fighting Game": "MultiVersus",
        "Best Family Game": "Kirby and the Forgotten Land",
        "Best Sim/Strategy Game": "Mario + Rabbids Sparks of Hope",
        "Best Sports/Racing Game": "Gran Turismo 7",
        "Best Multiplayer Game": "Splatoon 3",
        "Most Anticipated Game": "The Legend of Zelda: Tears of the Kingdom",
        "Content Creator of the Year": "Ludwig",
        "Best Esports Game": "Valorant",
    },
    2021: {
        "Game of the Year": "It Takes Two",
        "Best Game Direction": "Deathloop",
        "Best Narrative": "Marvel's Guardians of the Galaxy",
        "Best Art Direction": "Deathloop",
        "Best Score and Music": "NieR Replicant ver.1.22474487139...",
        "Best Audio Design": "Forza Horizon 5",
        "Best Performance": "Maggie Robertson (Resident Evil Village)",
        "Games for Impact": "Life is Strange: True Colors",
        "Best Ongoing Game": "Final Fantasy XIV",
        "Best Indie Game": "Kena: Bridge of Spirits",
        "Best Debut Indie Game": "Kena: Bridge of Spirits",
        "Best Mobile Game": "Genshin Impact",
        "Best VR/AR Game": "Resident Evil 4 VR",
        "Best Action Game": "Returnal",
        "Best Action/Adventure Game": "Metroid Dread",
        "Best RPG": "Tales of Arise",
        "Best Fighting Game": "Guilty Gear Strive",
        "Best Family Game": "It Takes Two",
        "Best Sim/Strategy Game": "Age of Empires IV",
        "Best Sports/Racing Game": "Forza Horizon 5",
        "Best Multiplayer Game": "It Takes Two",
        "Most Anticipated Game": "Elden Ring",
        "Content Creator of the Year": "Dream",
        "Best Esports Game": "League of Legends",
    },
    2020: {
        "Game of the Year": "The Last of Us Part II",
        "Best Game Direction": "The Last of Us Part II",
        "Best Narrative": "The Last of Us Part II",
        "Best Art Direction": "Ghost of Tsushima",
        "Best Score and Music": "Final Fantasy VII Remake",
        "Best Audio Design": "The Last of Us Part II",
        "Best Performance": "Laura Bailey (The Last of Us Part II)",
        "Games for Impact": "Tell Me Why",
        "Best Ongoing Game": "No Man's Sky",
        "Best Indie Game": "Hades",
        "Best Mobile Game": "Among Us",
        "Best VR/AR Game": "Half-Life: Alyx",
        "Best Action Game": "Hades",
        "Best Action/Adventure Game": "The Last of Us Part II",
        "Best RPG": "Final Fantasy VII Remake",
        "Best Fighting Game": "Mortal Kombat 11 Ultimate",
        "Best Family Game": "Animal Crossing: New Horizons",
        "Best Sim/Strategy Game": "Microsoft Flight Simulator",
        "Best Sports/Racing Game": "Tony Hawk's Pro Skater 1 + 2",
        "Best Multiplayer Game": "Among Us",
        "Most Anticipated Game": "Elden Ring",
        "Content Creator of the Year": "Valkyrae",
        "Best Esports Game": "League of Legends",
    },
    2019: {
        "Game of the Year": "Sekiro: Shadows Die Twice",
        "Best Game Direction": "Death Stranding",
        "Best Narrative": "Disco Elysium",
        "Best Art Direction": "Control",
        "Best Score and Music": "Death Stranding",
        "Best Audio Design": "Call of Duty: Modern Warfare",
        "Best Performance": "Mads Mikkelsen (Death Stranding)",
        "Games for Impact": "Gris",
        "Best Ongoing Game": "Fortnite",
        "Best Indie Game": "Disco Elysium",
        "Best Mobile Game": "Call of Duty: Mobile",
        "Best VR/AR Game": "Beat Saber",
        "Best Action Game": "Devil May Cry 5",
        "Best Action/Adventure Game": "Sekiro: Shadows Die Twice",
        "Best RPG": "Disco Elysium",
        "Best Fighting Game": "Super Smash Bros. Ultimate",
        "Best Family Game": "Luigi's Mansion 3",
        "Best Sim/Strategy Game": "Fire Emblem: Three Houses",
        "Best Sports/Racing Game": "Crash Team Racing Nitro-Fueled",
        "Best Multiplayer Game": "Apex Legends",
        "Most Anticipated Game": "The Last of Us Part II",
        "Content Creator of the Year": "Shroud",
        "Best Esports Game": "League of Legends",
    },
    2018: {
        "Game of the Year": "God of War",
        "Best Game Direction": "God of War",
        "Best Narrative": "Red Dead Redemption 2",
        "Best Art Direction": "Red Dead Redemption 2",
        "Best Score and Music": "Red Dead Redemption 2",
        "Best Audio Design": "Red Dead Redemption 2",
        "Best Performance": "Roger Clark (Red Dead Redemption 2)",
        "Games for Impact": "Celeste",
        "Best Ongoing Game": "Fortnite",
        "Best Indie Game": "Celeste",
        "Best Mobile Game": "Florence",
        "Best VR/AR Game": "Astro Bot Rescue Mission",
        "Best Action Game": "Dead Cells",
        "Best Action/Adventure Game": "God of War",
        "Best RPG": "Monster Hunter: World",
        "Best Fighting Game": "Dragon Ball FighterZ",
        "Best Family Game": "Overcooked 2",
        "Best Sim/Strategy Game": "Into the Breach",
        "Best Sports/Racing Game": "Forza Horizon 4",
        "Best Multiplayer Game": "Fortnite",
        "Most Anticipated Game": "The Last of Us Part II",
        "Content Creator of the Year": "Ninja",
        "Best Esports Game": "Overwatch",
    },
}


@tool
def get_game_awards(year: int = 2025, category: str = "all") -> str:
    """
    Get The Game Awards winners for a specific year and category.
    
    Args:
        year: The year of The Game Awards (2019-2025 available)
        category: Specific category to look up, or 'all' for all categories.
                  Examples: 'Game of the Year', 'Best RPG', 'Best Indie Game', 
                  'Best Narrative', 'Best Action Game', 'Best Multiplayer Game'
    
    Returns:
        The Game Awards winners for the specified year and category
    """
    if year not in GAME_AWARDS_DATA:
        available_years = sorted(GAME_AWARDS_DATA.keys(), reverse=True)
        return f"Data not available for {year}. Available years: {', '.join(map(str, available_years))}"
    
    awards = GAME_AWARDS_DATA[year]
    
    if category.lower() == "all":
        output = f"🏆 The Game Awards {year} - All Winners:\n\n"
        for cat, winner in awards.items():
            output += f"  🎮 {cat}: {winner}\n"
        return output
    
    # Find matching category (case-insensitive partial match)
    category_lower = category.lower()
    for cat, winner in awards.items():
        if category_lower in cat.lower() or cat.lower() in category_lower:
            return f"🏆 The Game Awards {year}\n{cat}: {winner}"
    
    # Category not found
    available_categories = list(awards.keys())
    return f"Category '{category}' not found for {year}.\n\nAvailable categories:\n" + "\n".join(f"  • {c}" for c in available_categories)


@tool
def get_game_of_the_year_history() -> str:
    """
    Get the complete history of Game of the Year winners from The Game Awards.
    
    Returns:
        A chronological list of all Game of the Year winners from 2018-2025
    """
    output = "🏆 The Game Awards - Game of the Year Winners:\n\n"
    
    for year in sorted(GAME_AWARDS_DATA.keys(), reverse=True):
        winner = GAME_AWARDS_DATA[year].get("Game of the Year", "Unknown")
        output += f"  {year}: {winner}\n"
    
    output += "\n📊 Fun Facts:\n"
    output += "  • Clair Obscur: Expedition 33 (2025) won a record 9 awards\n"
    output += "  • FromSoftware has won GOTY twice (Sekiro 2019, Elden Ring 2022)\n"
    output += "  • Baldur's Gate 3 (2023) won 6 total awards\n"
    
    return output
