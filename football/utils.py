from .models import Fixture, GroupStanding
from datetime import datetime

def update_standings(fixture):
    if fixture.stage != "Group" or fixture.status != "Complete":
        return

    group = fixture.group
    for team, goals_for, goals_against in [
        (fixture.team1, fixture.team1_score, fixture.team2_score),
        (fixture.team2, fixture.team2_score, fixture.team1_score)
    ]:
        standing, _ = GroupStanding.objects.get_or_create(group=group, team=team)
        standing.played += 1
        standing.goals_for += goals_for
        standing.goals_against += goals_against

        if fixture.team1_score == fixture.team2_score:
            standing.draws += 1
            standing.points += 1
        elif (team == fixture.team1 and fixture.team1_score > fixture.team2_score) or \
             (team == fixture.team2 and fixture.team2_score > fixture.team1_score):
            standing.wins += 1
            standing.points += 3
        else:
            standing.losses += 1

        standing.save()

def generate_knockout_fixtures(qualified_teams, competition):
    now = datetime.now()
    time = now.time()
    total = len(qualified_teams)
    matchups = []

    # Calculate starting round based on number of teams
    starting_round = total  # Example: 16 teams -> Round 16

    for i in range(total // 2):
        team1 = qualified_teams[i][0]
        team2 = qualified_teams[total - 1 - i][0]
        matchups.append((team1, team2))

    fixtures = []
    for t1, t2 in matchups:
        fixture = Fixture.objects.create(
            competition=competition,
            stage="Knockout",
            team1=t1,
            team2=t2,
            season=competition.season,
            round=starting_round,  # Use the calculated starting round
            date=now,
            time=time,
        )
        fixtures.append(fixture)

    return fixtures

def generate_classification_fixtures(group_standings, competition):
    bottom_teams = []

    for group in group_standings:
        sorted_teams = sorted(group, key=lambda g: g.position)
        bottom_teams.extend(sorted_teams[-2:])  # Last two teams

    return generate_knockout_fixtures(
        [(t.team, t.position) for t in bottom_teams],
        competition,
        stage_prefix="Classification"
    )


def generate_round_robin(group, competition):
    teams = list(group.teams.all())
    matches = []

    for t1, t2 in combinations(teams, 2):
        match = Fixture.objects.create(
            competition=competition,
            group=group,
            stage="Group",
            team1=t1,
            team2=t2
        )
        matches.append(match)
    return matches

