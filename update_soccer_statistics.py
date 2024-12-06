from app import db
from models import User, Team, League, StatisticsForLeague, LeaguesFollowedByUser, TeamsFollowedByUser
from soccerScraper import retrieveLeagueInfo
# from flask_bcrypt import Bcrypt



def update_league_stats(league):
    """Update the stats for a league by re-scraping data from the page. Display all team info."""
    current_league = db.session.query(League).filter(
        League.league_name == league.league_name).one()

    league_url = League.get_league_url(current_league.id)

    team_infos = retrieveLeagueInfo(league_url)
    for team_info in team_infos:  # Update teams from newly scraped table data.

        team_exists = db.session.query(Team).filter(
            Team.team_name == team_info.teamName).one_or_none()  # Checks if team exists already.

        if not team_exists:
            team = Team(team_name=team_info.teamName,
                        team_name_abbrev=team_info.teamNameAbbrev,
                        team_crest=team_info.teamCrest,
                        team_hyperlink=team_info.teamHyperlink)

            db.session.merge(team)
            db.session.commit()

        current_team = db.session.query(Team).filter(
            Team.team_name == team_info.teamName).one()

        # Using team_id and league_id as reference, update the team's statistics for specific league in the database.
        current_team_league_statistics = StatisticsForLeague(team_id=current_team.id, league_id=current_league.id,
                                                             current_standing=team_info.currentStanding, games_played=team_info.gamesPlayed,
                                                             wins=team_info.wins, draws=team_info.draws, losses=team_info.losses,
                                                             goals_for=team_info.goalsFor, goals_against=team_info.goalsAgainst,
                                                             goals_differential=team_info.goalDifferential, points=team_info.points)

        db.session.merge(current_team_league_statistics)
        db.session.commit()

# Update each league in the database.
leagues = db.session.query(League).all()

# Add Teams from League(s)
for league in leagues:
    update_league_stats(league)


db.session.commit()
