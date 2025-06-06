from django.shortcuts import render, redirect, get_object_or_404


from .forms import *
from .models import *

from accounts.models import Sport
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy


from django.db import connection

# template

from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce


def get_rankings(competition):
    # Athlete Rankings (unchanged)
    athlete_rankings = (
        Athlete.objects.filter(athlete__match__competition=competition)
        .annotate(
            goals=Count("athlete", filter=Q(athlete__event_type="Goal")),
            assists=Count("athlete", filter=Q(athlete__event_type="Assist")),
            yellow_cards=Count("athlete", filter=Q(athlete__event_type="YellowCard")),
            red_cards=Count("athlete", filter=Q(athlete__event_type="RedCard")),
            fouls=Count("athlete", filter=Q(athlete__event_type="Foul")),
        )
        .order_by("-goals", "-assists")
    )

    # Team Rankings
    team_rankings = (
        SchoolTeam.objects.filter(team__match__competition=competition)
        .annotate(
            goals=Count("team", filter=Q(team__event_type="Goal")),
            yellow_cards=Count("team", filter=Q(team__event_type="YellowCard")),
            red_cards=Count("team", filter=Q(team__event_type="RedCard")),
            fouls=Count("team", filter=Q(team__event_type="Foul")),
        )
        .order_by("-goals")
    )

    # The rest of the function remains unchanged
    top_scorers = athlete_rankings.order_by("-goals")[:10]
    top_assisters = athlete_rankings.order_by("-assists")[:10]
    most_yellow_cards = athlete_rankings.order_by("-yellow_cards")[:10]
    most_red_cards = athlete_rankings.order_by("-red_cards")[:10]
    most_fouls = athlete_rankings.order_by("-fouls")[:10]

    team_goals = team_rankings.order_by("-goals")[:10]
    team_yellow_cards = team_rankings.order_by("-yellow_cards")[:10]
    team_red_cards = team_rankings.order_by("-red_cards")[:10]
    team_fouls = team_rankings.order_by("-fouls")[:10]

    return {
        "athlete_rankings": athlete_rankings,
        "team_rankings": team_rankings,  # This now contains all team stats
    }

import json

def Furtbol(request, id):
    competition = Football.objects.get(id=id)
    fgroups = FGroup.objects.filter(competition=competition)
    pending_fixtures = Fixture.objects.filter(
        status="Pending", competition=competition
    ).order_by("date")
    fixtures = Fixture.objects.filter(
    competition=competition,
    stage="Knockout"
    ).order_by('round', 'date', 'time')

    results = Fixture.objects.filter(competition=competition).order_by(
        "-date"
    ).exclude(status="Pending")
    rankings = get_rankings(competition)

    standings_data = {}
    groups = FGroup.objects.filter(competition=competition)
    rounds = {}
    for fixture in fixtures:
        rounds.setdefault(fixture.round, []).append({
            "team1": fixture.team1.school.name if fixture.team1 else "TBD",
            "team2": fixture.team2.school.name if fixture.team2 else "TBD",
            "score1": fixture.team1_score if hasattr(fixture, 'team1_score') else None,
            "score2": fixture.team2_score if hasattr(fixture, 'team2_score') else None,
        })
    
    for group in groups:
        standings = {
            team: {
                "points": 0,
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "gd": 0,
                "gs": 0,
                "gc": 0,
            }
            for team in group.teams.all()
        }

        group_fixtures = Fixture.objects.filter(group=group)
        for fixture in group_fixtures:
            if fixture.team1_score is not None and fixture.team2_score is not None:
                # Update played matches
                standings[fixture.team1]["played"] += 1
                standings[fixture.team2]["played"] += 1

                # Update goals scored and conceded
                standings[fixture.team1]["gs"] += fixture.team1_score
                standings[fixture.team2]["gs"] += fixture.team2_score
                standings[fixture.team1]["gc"] += fixture.team2_score
                standings[fixture.team2]["gc"] += fixture.team1_score

                # Update match results
                if fixture.team1_score > fixture.team2_score:
                    standings[fixture.team1]["points"] += 3
                    standings[fixture.team1]["won"] += 1
                    standings[fixture.team2]["lost"] += 1
                elif fixture.team1_score < fixture.team2_score:
                    standings[fixture.team2]["points"] += 3
                    standings[fixture.team2]["won"] += 1
                    standings[fixture.team1]["lost"] += 1
                else:
                    standings[fixture.team1]["points"] += 1
                    standings[fixture.team2]["points"] += 1
                    standings[fixture.team1]["drawn"] += 1
                    standings[fixture.team2]["drawn"] += 1

                # Update goal difference
                standings[fixture.team1]["gd"] = (
                    standings[fixture.team1]["gs"] - standings[fixture.team1]["gc"]
                )
                standings[fixture.team2]["gd"] = (
                    standings[fixture.team2]["gs"] - standings[fixture.team2]["gc"]
                )

        # Sort standings by points, goal difference, and goals scored
        sorted_standings = sorted(
            standings.items(),
            key=lambda x: (x[1]["points"], x[1]["gd"], x[1]["gs"]),
            reverse=True,
        )
        standings_data[group] = sorted_standings

    context = {
        "competition": competition,
        "fgroups": fgroups,
        "results": results,
        "fixtures": pending_fixtures,
        "rankings": rankings,
        "standings_data": standings_data,  "rounds": json.dumps(rounds),
    }
    return render(request, "frontend/football.html", context)


from django.db.models import Q


def FFixtureDetail(request, id):
    fixture = get_object_or_404(Fixture, id=id)
    officials = match_official.objects.filter(fixture_id=id)
    events = MatchEvent.objects.filter(match_id=id)

    team1_yellowcards = events.filter(
        event_type="YellowCard", team=fixture.team1
    ).count()
    team2_yellowcards = events.filter(
        event_type="YellowCard", team=fixture.team2
    ).count()
    team1_redcards = events.filter(event_type="RedCard", team=fixture.team1).count()
    team2_redcards = events.filter(event_type="RedCard", team=fixture.team2).count()
    team1_goals = events.filter(event_type="Goal", team=fixture.team1).count()
    team2_goals = events.filter(event_type="Goal", team=fixture.team2).count()
    # ------fixtures by team
    team1_fixtures = Fixture.objects.filter(
        Q(team1=fixture.team1) | Q(team2=fixture.team1)
    ).distinct()
    team2_fixtures = Fixture.objects.filter(
        Q(team1=fixture.team2) | Q(team2=fixture.team2)
    ).distinct()
    context = {
        "fixture": fixture,
        "officials": officials,
        "events": events,
        # sevents
        "team1_yellowcards": team1_yellowcards,
        "team2_yellowcards": team2_yellowcards,
        "team1_goals": team1_goals,
        "team2_redcards": team2_redcards,
        "team1_redcards": team1_redcards,
        "team2_goals": team2_goals,
        # fixtures
        "team1_fixtures": team1_fixtures,
        "team2_fixtures": team2_fixtures,
    }

    return render(request, "frontend/fixture.html", context)


def Fhome(request):

    context = {}
    return render(request, "frontend/fhome.html", context)


def footbollStandings(request):
    sports = Sport.objects.all()

    standings_data = []
    for sport in sports:
        football_competitions = Football.objects.filter(sport=sport)

        for football in football_competitions:
            groups = FGroup.objects.filter(competition=football)
            competition_standings = {}

            for group in groups:
                # Initialize standings with default values for all teams in the group
                standings = {}
                for team in group.teams.all():
                    standings[team] = {
                        "points": 0,
                        "played": 0,
                        "won": 0,
                        "drawn": 0,
                        "lost": 0,
                        "gd": 0,
                        "gs": 0,
                        "gc": 0,
                    }

                # Update standings based on fixtures
                fixtures = Fixture.objects.filter(group=group)
                for fixture in fixtures:
                    if (
                        fixture.team1_score is not None
                        and fixture.team2_score is not None
                    ):
                        # Update played matches
                        standings[fixture.team1]["played"] += 1
                        standings[fixture.team2]["played"] += 1

                        # Update goals scored and conceded
                        standings[fixture.team1]["gs"] += fixture.team1_score
                        standings[fixture.team2]["gs"] += fixture.team2_score
                        standings[fixture.team1]["gc"] += fixture.team2_score
                        standings[fixture.team2]["gc"] += fixture.team1_score

                        # Update match results
                        if fixture.team1_score > fixture.team2_score:
                            standings[fixture.team1]["points"] += 3
                            standings[fixture.team1]["won"] += 1
                            standings[fixture.team2]["lost"] += 1
                        elif fixture.team1_score < fixture.team2_score:
                            standings[fixture.team2]["points"] += 3
                            standings[fixture.team2]["won"] += 1
                            standings[fixture.team1]["lost"] += 1
                        else:
                            standings[fixture.team1]["points"] += 1
                            standings[fixture.team2]["points"] += 1
                            standings[fixture.team1]["drawn"] += 1
                            standings[fixture.team2]["drawn"] += 1

                        # Update goal difference
                        standings[fixture.team1]["gd"] = (
                            standings[fixture.team1]["gs"]
                            - standings[fixture.team1]["gc"]
                        )
                        standings[fixture.team2]["gd"] = (
                            standings[fixture.team2]["gs"]
                            - standings[fixture.team2]["gc"]
                        )

                # Sort standings by points, goal difference, and goals scored
                sorted_standings = sorted(
                    standings.items(),
                    key=lambda x: (x[1]["points"], x[1]["gd"], x[1]["gs"]),
                    reverse=True,
                )
                competition_standings[group] = sorted_standings

            standings_data.append(
                {
                    "sport": sport,
                    "competition": football,
                    "standings": competition_standings,
                }
            )

    context = {
        "standings_data": standings_data,
    }

    return render(request, "frontend/standings.html", context)


def competition_rankings(request, competition_id):
    competition = get_object_or_404(Football, id=competition_id)
    rankings = get_rankings(competition)

    context = {
        "competition": competition,
        "rankings": rankings,
    }

    return render(request, "frotend/futrankings.html", context)





