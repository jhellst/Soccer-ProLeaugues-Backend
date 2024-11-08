from dataclasses import dataclass
import datetime

@dataclass
class LeagueInfo:
    """Class to hold info for a pro soccer league."""
    league_id: int
    league_name: str
    league_country: str
    league_description: str
    league_url: str
    last_updated_date: datetime.datetime

@dataclass
class TeamInfoForLeague:
    """Class to hold info for a pro soccer team in a specific league."""
    team_id: int
    league_id: int
    team_name: str
    team_name_abbrev: str
    team_crest: str
    team_url: str
    current_standing: int
    games_played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_differential: int
    points: int
    # is_followed_by_user: bool