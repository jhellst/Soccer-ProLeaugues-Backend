# import os
from flask_sqlalchemy import SQLAlchemy
import datetime
import uuid
from flask_bcrypt import Bcrypt
from config import ApplicationConfig

bcrypt = Bcrypt()

db = SQLAlchemy()


def connect_db(app):
    """Connect database to Flask app."""
    app.config.from_object(ApplicationConfig)

    app.app_context().push()
    db.app = app
    db.init_app(app)


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.String(30),
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.String,
        nullable=False,
    )

    teams_followed_by_user = db.relationship(
        'Team', secondary='teams_followed_by_users', backref='users', order_by='Team.team_name')

    leagues_followed_by_user = db.relationship(
        'League', secondary='leagues_followed_by_users', backref='users', order_by='League.league_name')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.password}>"

    @classmethod
    def signup(cls, username, password):
        """Sign up user. Hashes password and adds user to session."""

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            password=hashed_pwd
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If this can't find matching user (or if password is wrong), returns
        False.
        """

        user = cls.query.filter_by(username=username).one_or_none()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Team(db.Model):
    """Store information for an individual pro soccer team."""

    __tablename__ = "teams"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    team_name = db.Column(
        db.String,
        nullable=False
    )
    team_name_abbrev = db.Column(
        db.String,
        nullable=True
    )
    team_crest = db.Column(
        db.String,
        nullable=True
    )
    team_hyperlink = db.Column(
        db.String,
        nullable=True
    )

    leagues_team_is_member_of = db.relationship(
        'League', secondary='statistics_for_leagues', backref='teams')

    users_following_team = db.relationship(
        'User', secondary='teams_followed_by_users', backref='teams')

    @classmethod
    def get_team(cls, team_id):
        """Gets a team and statistics for all leagues it is a member of."""
        team = db.session.query(Team).filter(Team.id == team_id)
        return team


class League(db.Model):
    """References each league that a team is a member of."""

    __tablename__ = "leagues"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    # League Name
    league_name = db.Column(
        db.String,
        nullable=False
    )
    # League Region/Country
    league_country = db.Column(
        db.String,
        nullable=True,
        default="N/A",
    )
    # League Description -> Description of League's division and/or region.
    league_description = db.Column(
        db.String,
        nullable=True,
        default="",
    )
    # League URL
    league_url = db.Column(
        db.String,
        nullable=False
    )
    # Date that League was Last Updated.
    last_updated_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.datetime.now
    )

    league_table = db.relationship(
        'Team', secondary='statistics_for_leagues', backref='leagues')

    users_following_league = db.relationship(
        'User', secondary='leagues_followed_by_users', backref='leagues')

    @classmethod
    def get_league_url(cls, league_id):
        league = db.session.query(League).filter(
            League.id == league_id)
        return league[0].league_url


class StatisticsForLeague(db.Model):
    """Standings and other statistics from a pro soccer league."""

    __tablename__ = "statistics_for_leagues"

    # Team ID.
    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # League ID.
    league_id = db.Column(
        db.Integer,
        db.ForeignKey("leagues.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Current standing in league.
    current_standing = db.Column(
        db.Integer,
        nullable=False
    )

    # Number of games played in league.
    games_played = db.Column(
        db.Integer,
        nullable=False
    )

    # Number of wins in league.
    wins = db.Column(
        db.Integer,
        nullable=False
    )

    # Number of draws in league.
    draws = db.Column(
        db.Integer,
        nullable=False
    )

    # Number of losses in league.
    losses = db.Column(
        db.Integer,
        nullable=False
    )

    # Number of goals for (scored by team) in league.
    goals_for = db.Column(
        db.Integer,
        nullable=False
    )

    # Number of goals against (scored against team) in league.
    goals_against = db.Column(
        db.Integer,
        nullable=False
    )

    # Goal differential (total goals scored - total goals against) in league.
    goals_differential = db.Column(
        db.Integer,
        nullable=False
    )

    # Number of points earned in league.
    points = db.Column(
        db.Integer,
        nullable=False
    )

    # TODO: Add team_form as a final database column. Investigate how to best visualize this in league table (graph or text-based).
    # List of results (text description) over team's last 5 games.
    # team_form = db.Column(
    #     db.Integer,
    #     nullable=False
    # )


class TeamsFollowedByUser(db.Model):
    """Stores the id of each team that is being followed by a user."""

    __tablename__ = "teams_followed_by_users"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    )

    @classmethod
    def follow_team(cls, team_id, user_id):
        """Follows a team to be included in the user's custom team page."""
        # print("team_and_user_id@backend", team_id, user_id)
        team_follow = TeamsFollowedByUser(user_id=user_id, team_id=team_id)

        db.session.merge(team_follow)
        db.session.commit()
        return team_follow.team_id

    @classmethod
    def unfollow_team(cls, team_id, user_id):
        """Unfollows a team that was included in the user's custom team page."""
        # print("unfollow_team", team_id, user_id)
        team_unfollow = TeamsFollowedByUser.query.filter(TeamsFollowedByUser.team_id == team_id).filter(
            TeamsFollowedByUser.user_id == user_id)

        team_unfollow.delete()
        db.session.commit()

        return {
            "Deleted": True,
            user_id: user_id,
            team_id: team_id
        }


class LeaguesFollowedByUser(db.Model):
    """Stores the id of each team that is being followed by a user."""

    __tablename__ = "leagues_followed_by_users"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    league_id = db.Column(
        db.Integer,
        db.ForeignKey("leagues.id", ondelete="CASCADE"),
        primary_key=True,
    )

    @classmethod
    def follow_league(cls, league_id, user_id):
        """Follows a league to be included in the user's custom leagues page."""
        league_follow = LeaguesFollowedByUser(
            user_id=user_id, league_id=league_id)

        db.session.merge(league_follow)
        db.session.commit()
        return league_follow.league_id

    @classmethod
    def unfollow_league(cls, league_id, user_id):
        """Unfollows a league that was included in the user's custom leagues page."""

        league_unfollow = LeaguesFollowedByUser.query.filter(LeaguesFollowedByUser.league_id == league_id).filter(
            LeaguesFollowedByUser.user_id == user_id)

        league_unfollow.delete()
        db.session.commit()

        return {
            "Deleted": True,
            user_id: user_id,
            league_id: league_id
        }

    @classmethod  # TODO: Refine this and test.
    def get_followed_leagues(cls, user_id):
        """Gets a list of leagues that a user is following."""
        followed_leagues = db.session.query(League, LeaguesFollowedByUser).filter(
            LeaguesFollowedByUser.user_id == user_id)

        return followed_leagues
