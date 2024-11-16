import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, flash, redirect, session, render_template, url_for, g
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import json
from models import db, connect_db, User, Team, League, StatisticsForLeague, TeamsFollowedByUser, LeaguesFollowedByUser
from dataClasses import LeagueInfo, TeamInfoForLeague
from soccerScraper import retrieveLeagueInfo, TeamInfo
from datetime import datetime, timedelta, timezone
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


load_dotenv()
CURR_USER_KEY = "curr_user"
app = Flask(__name__)
# CORS(app)
# CORS(app, supports_credentials=True)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "https://soccer-proleagues-frontend-final.onrender.com"}})

bcrypt = Bcrypt(app)

app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URI']
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config["JWT_SECRET_KEY"] = os.environ['SECRET_KEY']
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)


jwt = JWTManager(app)

@jwt.expired_token_loader
def my_expired_token_callback(expired_token, date):
    # print("Hello from jwt_expired_decorator")
    return redirect(url_for('logout_user'))

connect_db(app)


# Next steps:
# 1) Web scraper -> Deploy to the cloud and get it to run once per day.
#       - Get it to scrape once per day and store in a database.
# 2) Website that feeds from this database -> deploy this to the cloud.
# "Chron Job" - A program that has a certain schedule to run.

# Start by trying to deploy website to the cloud. Use Amazon web services for this.


##############################################################################
# User signup/login/logout

@app.route("/register", methods=["POST"])
def register_user():
    username = request.json["username"]
    password = request.json["password"]

    user_exists = User.query.filter_by(username=username).first() is not None

    if user_exists:
        return jsonify({"error": "User already exists"}), 409
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    user_info = {"username": username, "user_id": new_user.id}
    access_token = create_access_token(identity=json.dumps(user_info))
    # print("access_token@@@register", access_token)
    return jsonify(access_token=access_token)


@app.route("/login", methods=["POST"])
def login_user():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    user = User.query.filter_by(username=username).one_or_none()

    # Checks if user exists.
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    # Checks if the password is the same as hashed password
    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401

    # access_token = create_refresh_token(identity=username)
    user_info = {"username": username, "user_id": user.id}
    access_token = create_access_token(identity=json.dumps(user_info))
    # print("access_token@@@login", access_token)
    return jsonify(access_token=access_token)


@app.route("/token/<username>", methods=["GET"])
@jwt_required()
def get_token(username):
    user_info = User.query.filter_by(username=username).one_or_none()
    access_token = create_access_token(identity=json.dumps(user_info))
    # print("current_user@token", current_user)
    return jsonify(access_token=access_token)


# TODO: Figure out this route with jwt library.
@app.route("/logout", methods=["POST"])
def logout_user():
    # print("session@@logout", session)
    session.pop("user_id")
    return "200"


@app.route("/users", methods=["GET"])
def get_all_users():
    user_id = session["user_id"]

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    all_users = User.query.all()
    users = [{"user_id": user.id, "username": user.username}
             for user in all_users]

    return jsonify(users)


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.filter_by(id=user_id).one_or_none()
    # print("user!", user)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({
        "username": user.username,
        "user_id": user.id
    })


#######################################################################
# API endpoints


# Homepage. If user is logged in, will show list of followed leagues with other links. If not logged in, will show login/create account option and all leagues.
# @app.get('/')
# def root():
#     """Show recent list of posts, most-recent first."""


@app.get("/leagues")
@cross_origin()
def get_all_leagues():
    """Returns name + link for each league."""

    all_leagues = db.session.query(
        League.id, League.league_name, League.league_country, League.league_description, League.league_url, League.last_updated_date)

    leagues = [LeagueInfo(league.id, league.league_name, league.league_country, league.league_description, league.league_url,
                          league.last_updated_date) for league in all_leagues]
    return leagues


@app.route("/users/<int:user_id>/leagues/<int:league_id>/follow", methods=["POST"])
@jwt_required()
@cross_origin()
def follow_league(user_id, league_id):
    """Follows a league, to be displayed on the user's league page (or homepage)."""
    # print("Follow_league@backend", user_id, league_id)

    # Checks if user exists.
    user = db.session.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    # print("user!", user)

    # Checks if league exists.
    league = db.session.query(League).filter(
        League.id == league_id).one_or_none()
    if not league:
        return jsonify({"error": "Unauthorized"}), 401

    LeaguesFollowedByUser.follow_league(league_id, user_id)

    return jsonify({
        "league_followed": league.league_name,
        "followed_by": user.username,
    })


@app.route("/users/<int:user_id>/leagues/<int:league_id>/unfollow", methods=["POST"])
@jwt_required()
@cross_origin()
def unfollow_league(user_id, league_id):
    """Unfollows a league, to be removed from the user's custom league page."""
    # print("Unfollow_league@backend", user_id, league_id)

    # Checks if user exists.
    user = db.session.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Checks if team exists.
    league = db.session.query(League).filter(
        League.id == league_id).one_or_none()
    if not league:
        return jsonify({"error": "Unauthorized"}), 401

    LeaguesFollowedByUser.unfollow_league(league_id=league_id, user_id=user_id)

    return jsonify({
        "league_unfollowed": league.league_name,
        "unfollowed_by": user.username,
    })


@app.route("/users/<int:user_id>/teams/<int:team_id>/follow", methods=["POST"])
@jwt_required()
@cross_origin()
def follow_team(user_id, team_id):
    """Follows a team, to be displayed on the user's custom team page."""
    # print("Follow_team@backend", user_id, team_id)

    # Checks if user exists.
    user = db.session.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Checks if team exists.
    team = db.session.query(Team).filter(Team.id == team_id).one_or_none()
    if not team:
        return jsonify({"error": "Unauthorized"}), 401

    TeamsFollowedByUser.follow_team(team_id=team_id, user_id=user_id)

    return jsonify({
        "team_followed": team.team_name,
        "followed_by": user.username,
    })


@app.route("/users/<int:user_id>/teams/<int:team_id>/unfollow", methods=["POST"])
@jwt_required()
@cross_origin()
def unfollow_team(user_id, team_id):
    """Unfollows a team, to be removed from the user's custom team page."""
    # print("Unfollow_team@backend", user_id, team_id)

    # Checks if user exists.
    user = db.session.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Checks if team exists.
    team = db.session.query(Team).filter(Team.id == team_id).one_or_none()
    if not team:
        return jsonify({"error": "Unauthorized"}), 401

    TeamsFollowedByUser.unfollow_team(team_id=team_id, user_id=user_id)

    return jsonify({
        "team_unfollowed": team.team_name,
        "unfollowed_by": user.username,
    })


@app.get("/users/<int:user_id>/leagues")
@jwt_required()
@cross_origin()
def get_followed_leagues(user_id):
    """Returns name + link for each league that a user has followed."""

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.filter_by(id=user_id).one_or_none()

    followed_leagues = user.leagues_followed_by_user

    leagues = [{"league_name": league.league_name,
                "league_country": league.league_country,
                "league_description": league.league_description,
                "league_url": league.league_url,
                "league_id": league.id,
                "last_updated_date": league.last_updated_date,
                "is_followed_by_user": True} for league in followed_leagues]

    return jsonify(leagues)


@app.get("/users/<int:user_id>/teams")
@jwt_required()
@cross_origin()
def get_followed_teams(user_id):
    """Returns name + link for each team that a user has followed."""

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.filter_by(id=user_id).one_or_none()

    followed_teams = user.teams_followed_by_user
    # print("followed_teams", followed_teams)

    teams = [{"team_name": team.team_name,
              "team_name_abbrev": team.team_name_abbrev,
              "team_crest": team.team_crest,
              "team_hyperlink": team.team_hyperlink,
              "team_id": team.id,
              "is_followed_by_user": True} for team in followed_teams]

    return jsonify(teams)


# Get info and statistics for all teams in one league.
@app.get("/leagues/<int:league_id>")
@cross_origin()
def get_league_table(league_id):
    """Returns info for specified league."""

    current_league_table = db.session.query(StatisticsForLeague.team_id, StatisticsForLeague.league_id,
                                            Team.team_name, Team.team_name_abbrev,
                                            Team.team_crest, Team.team_hyperlink,
                                            StatisticsForLeague.current_standing,
                                            StatisticsForLeague.games_played,
                                            StatisticsForLeague.wins,
                                            StatisticsForLeague.draws,
                                            StatisticsForLeague.losses,
                                            StatisticsForLeague.goals_for,
                                            StatisticsForLeague.goals_against,
                                            StatisticsForLeague.goals_differential,
                                            StatisticsForLeague.points).filter(
        StatisticsForLeague.league_id == league_id).filter(
        Team.id == StatisticsForLeague.team_id)

    league_table = [TeamInfoForLeague(team_id=team.team_id, league_id=team.league_id,
                                      team_name=team.team_name, team_name_abbrev=team.team_name_abbrev,
                                      team_crest=team.team_crest, team_url=team.team_hyperlink,
                                      current_standing=team.current_standing, games_played=team.games_played,
                                      wins=team.wins, draws=team.draws, losses=team.losses,
                                      goals_for=team.goals_for, goals_against=team.goals_against,
                                      goal_differential=team.goals_differential, points=team.points) for team in current_league_table]

    return league_table


@app.get("/teams")
def get_all_teams():
    """Returns all teams in database."""
    all_teams = db.session.query(StatisticsForLeague.team_id,
                                 StatisticsForLeague.league_id,
                                 Team.team_name,
                                 Team.team_name_abbrev,
                                 Team.team_crest,
                                 Team.team_hyperlink,
                                 StatisticsForLeague.current_standing,
                                 StatisticsForLeague.games_played,
                                 StatisticsForLeague.wins,
                                 StatisticsForLeague.draws,
                                 StatisticsForLeague.losses,
                                 StatisticsForLeague.goals_for,
                                 StatisticsForLeague.goals_against,
                                 StatisticsForLeague.goals_differential,
                                 StatisticsForLeague.points).filter(
        StatisticsForLeague.team_id == Team.id).order_by(Team.team_name)

    teams = [TeamInfoForLeague(team.team_id, team.league_id, team.team_name,
                               team.team_name_abbrev, team.team_crest, team.team_hyperlink,
                               team.current_standing, team.games_played, team.wins, team.draws,
                               team.losses, team.goals_for, team.goals_against,
                               team.goals_differential, team.points) for team in all_teams]

    return teams


# Get info for a single team, along with statistics for any (and all) leagues the team is a member of.
@app.get("/teams/<int:team_id>")
@cross_origin()
def get_team(team_id):
    """Returns a team from the database given a team_id."""

    team = db.session.query(Team).filter(Team.id == team_id).one_or_none()
    if not team:
        return jsonify({"error": "Unauthorized"}), 401

    # Consider Refinining this route to return data for league performance AND team details.
    return jsonify({"team_name": team.team_name,
                    "team_name_abbrev": team.team_name_abbrev,
                    "team_crest": team.team_crest,
                    "team_hyperlink": team.team_hyperlink,
                    "leagues_team_is_member_of": [{"league_name": league.league_name, "league_id": league.id, "league_url": league.league_url, "league_description": league.league_description, "last_updated_date": league.last_updated_date, } for league in team.leagues_team_is_member_of]})


@app.route("/leagues/<int:league_id>/update", methods=["POST"])
def update_league_stats(league_id):
    """Update the stats for a league by re-scraping data from the page. Display all team info."""

    league_url = League.get_league_url(league_id)

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
        current_team_league_statistics = StatisticsForLeague(team_id=current_team.id, league_id=league_id,
                                                             current_standing=team_info.currentStanding, games_played=team_info.gamesPlayed,
                                                             wins=team_info.wins, draws=team_info.draws, losses=team_info.losses,
                                                             goals_for=team_info.goalsFor, goals_against=team_info.goalsAgainst,
                                                             goals_differential=team_info.goalDifferential, points=team_info.points)

        db.session.merge(current_team_league_statistics)
        db.session.commit()

    return redirect(url_for('get_league_table', league_id=league_id))


# Error route.
@app.errorhandler(404)
def page_not_found(e):
    """Show 404 NOT FOUND page."""

    return render_template('404.html'), 404


# if __name__ == '__main__':
#     app.run(port=5001, debug=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='4000')

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port='4000')