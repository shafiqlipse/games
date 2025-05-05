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


# Create your views here.
def Futball(request):
    football = Sport.objects.get(name="Football")
    fcomps = Football.objects.filter(sport=football)

    if request.method == "POST":
        cform = CompForm(request.POST, request.FILES)

        if cform.is_valid():
            competn = cform.save(commit=False)
            competn.sport = football
            competn.save()
            teams = cform.cleaned_data.get(
                "teams"
            )  # Replace 'athletes' with the actual form field name
            competn.teams.set(teams)
            competn.save()
            return HttpResponseRedirect(reverse("football"))
    else:
        cform = CompForm()

    # If form is invalid, re-render form with errors
    context = {"cform": cform, "fcomps": fcomps}
    return render(request, "server/football.html", context)


# delete
def delete_football(request, id):
    football = get_object_or_404(Football, id=id)

    if request.method == "POST":
        football.delete()
        return redirect("comps")  # Redirect to the official list page or another URL

    return render(request, "comps/delete_comp.html", {"football": football})


# view official details
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.forms import inlineformset_factory
from django.http import JsonResponse
from .models import Football, FGroup, Fixture
from .forms import FGroupForm, FixtureForm


def ftourn_details(request, id):
    tournament = get_object_or_404(Football, id=id)
    fgroups = FGroup.objects.filter(competition=tournament)

    GroupFormset = inlineformset_factory(
        Football,
        FGroup,
        form=FGroupForm,
        extra=0,
    )

    if request.method == "POST":
        formset = GroupFormset(request.POST, instance=tournament)
        if formset.is_valid():
            formset.save()
            return redirect("football_tournament", tournament.id)

        fixture_form = FixtureForm(request.POST)
        if fixture_form.is_valid():
            fixture = fixture_form.save(commit=False)
            fixture.football = tournament
            fixture.save()
            return redirect("football_tournament", tournament.id)
        else:
            error_message = "There was an error in the form submission. Please correct the errors below."
    else:
        formset = GroupFormset(instance=tournament)
        fixture_form = FixtureForm()

    fixtures = Fixture.objects.filter(competition=tournament)

    context = {
        "tournament": tournament,
        "formset": formset,
        "fixture_form": fixture_form,
        "fixtures": fixtures,
        "fgroups": fgroups,
    }
    return render(request, "server/tournament.html", context)


from datetime import datetime


def generate_futfixtures_view(request, id):
    football = get_object_or_404(Football, id=id)
    season = football.season
    now = datetime.now()

    time = now.time()
    # Fetch all teams for the football (assuming you have a Team model)
    teams = SchoolTeam.objects.all()

    # Fetch all groups for the football
    groups = FGroup.objects.filter(competition=football)

    # Implement your fixture generation logic here
    fixtures = []
    for group in groups:
        group_teams = teams.filter(fgroup=group)
        team_count = group_teams.count()

        # Simple round-robin algorithm for group stage fixtures
        for i in range(team_count - 1):
            for j in range(i + 1, team_count):
                fixture = Fixture(
                    competition=football,
                    season=season,
                    round=1,
                    group=group,
                    stage="Group",
                    date=now,  # Capturing the current date and time
                    time=time,  # Capturing the current date and time
                    team1=group_teams[i],
                    team2=group_teams[j],
                    # You may set other fixture properties such as venue, date, etc.
                )
                fixtures.append(fixture)

    # Bulk create fixtures
    Fixture.objects.bulk_create(fixtures)

    return JsonResponse({"success": True, "message": "Fixtures generated successfully"})


def edit_fixtures_view(request, id):
    fixture = get_object_or_404(Fixture, id=id)

    if request.method == "POST":
        form = FixtureForm(request.POST, instance=fixture)
        if form.is_valid():
            form.save()
            return redirect(
                "update_fixture", id=id
            )  # Replace 'success_url' with the actual URL
    else:
        form = FixtureForm(instance=fixture)

    return render(
        request, "server/edit_fixture.html", {"form": form, "fixture": fixture}
    )


from django.db.models import Q


def FixtureDetail(request, id):
    fixture = get_object_or_404(Fixture, id=id)
    officials = match_official.objects.filter(fixture_id=id)
    events = MatchEvent.objects.filter(match_id=id)

    if request.method == "POST":
        if "official_form" in request.POST:
            cform = MatchOfficialForm(request.POST, request.FILES)
            eform = MatchEventForm()  # Initialize empty event form
            if cform.is_valid():
                new_official = cform.save(commit=False)
                new_official.fixture = fixture
                new_official.save()
                return redirect("fixture", id=id)
        elif "event_form" in request.POST:
            eform = MatchEventForm(request.POST, fixture_instance=fixture)
            cform = MatchOfficialForm()  # Initialize empty official form
            if eform.is_valid():
                new_event = eform.save(commit=False)
                new_event.match = fixture
                new_event.save()
                return redirect("fixture", id=id)
        else:
            cform = MatchOfficialForm()
            eform = MatchEventForm(
                fixture_instance=fixture
            )  # Initialize event form with fixture_instance
    else:
        cform = MatchOfficialForm()
        eform = MatchEventForm(
            fixture_instance=fixture
        )  # Initialize event form with fixture_instance

    context = {
        "fixture": fixture,
        "cform": cform,
        "eform": eform,
        "officials": officials,
        "events": events,
    }

    return render(request, "server/fixture.html", context)
    # team1_yellowcards = events.filter(
    #     event_type="YellowCard", team=fixture.team1
    # ).count()
    # team2_yellowcards = events.filter(
    #     event_type="YellowCard", team=fixture.team2
    # ).count()
    # team1_redcards = events.filter(event_type="RedCard", team=fixture.team1).count()
    # team2_redcards = events.filter(event_type="RedCard", team=fixture.team2).count()
    # team1_goals = events.filter(event_type="Goal", team=fixture.team1).count()
    # team2_goals = events.filter(event_type="Goal", team=fixture.team2).count()

    # # fixtures by team
    # team1_fixtures = Fixture.objects.filter(
    #     Q(team1=fixture.team1) | Q(team2=fixture.team1)
    # ).distinct()
    # team2_fixtures = Fixture.objects.filter(
    #     Q(team1=fixture.team2) | Q(team2=fixture.team2)
    # ).distinct()


def Fixturepage(request, id):
    fixture = get_object_or_404(Fixture, id=id)
    events = MatchEvent.objects.filter(match_id=id)
    goals1 = events.filter(event_type="Goal", team=fixture.team1)
    goals2 = events.filter(event_type="Goal", team=fixture.team2)
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
    team1_fouls = events.filter(event_type="Foul", team=fixture.team1).count()
    team2_fouls = events.filter(event_type="Foul", team=fixture.team2).count()
    team1_Save = events.filter(event_type="Save", team=fixture.team1).count()
    team2_Save = events.filter(event_type="Save", team=fixture.team2).count()
    context = {
        "fixture": fixture,
        "events": events,
        "team1_yellowcards": team1_yellowcards,
        "team2_yellowcards": team2_yellowcards,
        "team1_redcards": team1_redcards,
        "team2_redcards": team2_redcards,
        "team1_goals": team1_goals,
        "team2_goals": team2_goals,
        "team1_fouls": team1_fouls,
        "team2_fouls": team2_fouls,
        "team1_Save": team1_Save,
        "team2_Save": team2_Save,
        "goals1": goals1,
        "goals2": goals2,
    }
    return render(request, "frontend/fixturepage.html", context)


def fixtures(request):
    fixtures = Fixture.objects.filter(competition_id=4).order_by("-date")
    context = {"fixtures": fixtures}
    return render(request, "server/fixtures.html", context)

def standings_view(request, id):
    competition = get_object_or_404(Football, id=id)
    groups = FGroup.objects.filter(competition=competition).prefetch_related("groupstanding_set")

    group_standings = []
    for group in groups:
        standings = GroupStanding.objects.filter(group=group).order_by("position")
        group_standings.append((group, standings))

    context = {
        "competition": competition,
        "group_standings": group_standings,
    }

    return render(request, "server/standings.html", context)

def footfixtures(request):
    futfixures = Fixture.objects.all()
    context = {"futfixures": futfixures}
    return render(request, "frontend/footfixtures.html", context)

from django.shortcuts import render, redirect
from .models import Football, GroupStanding, FGroup
from .utils import generate_knockout_fixtures, generate_classification_fixtures, generate_round_robin

def ftourn_details(request, id):
    tournament = get_object_or_404(Football, id=id)
    fgroups = FGroup.objects.filter(competition=tournament)

    GroupFormset = inlineformset_factory(
        Football,
        FGroup,
        form=FGroupForm,
        extra=0,
    )

    fixtures = Fixture.objects.filter(competition=tournament)

    if request.method == "POST":
        if "fixture_mode" in request.POST:
            # Handle fixture generation
            mode = request.POST.get("fixture_mode")

            if mode == "Knockout":
                standings = GroupStanding.objects.filter(
                    group__competition=tournament, position__lte=2
                ).order_by('position')
                qualified = [(s.team, s.position) for s in standings]
                generate_knockout_fixtures(qualified, tournament)

            elif mode == "Classification":
                all_groups = FGroup.objects.filter(competition=tournament)
                grouped_standings = [
                    list(GroupStanding.objects.filter(group=group)) for group in all_groups
                ]
                generate_classification_fixtures(grouped_standings, tournament)

            elif mode == "round_robin":
                groups = FGroup.objects.filter(competition=tournament)
                for group in groups:
                    generate_round_robin(group, tournament)

            return redirect("football_tournament", id=tournament.id)

        else:
            # Handle normal formset or fixture form
            formset = GroupFormset(request.POST, instance=tournament)
            fixture_form = FixtureForm(request.POST)

            if formset.is_valid():
                formset.save()
                return redirect("football_tournament", id=tournament.id)

            if fixture_form.is_valid():
                fixture = fixture_form.save(commit=False)
                fixture.football = tournament
                fixture.save()
                return redirect("football_tournament", id=tournament.id)

            # If neither is valid, show errors
            error_message = "There was an error in the form submission. Please correct the errors below."

    else:
        formset = GroupFormset(instance=tournament)
        fixture_form = FixtureForm()
        error_message = None

    context = {
        "tournament": tournament,
        "formset": formset,
        "fixture_form": fixture_form,
        "fixtures": fixtures,
        "fgroups": fgroups,
        "error_message": error_message,
    }
    return render(request, "server/tournament.html", context)


from .models import GroupStanding, Fixture, FGroup, Football

def generate_post_group_fixtures(group):
    standings = GroupStanding.objects.filter(group=group).order_by("position")

    if standings.count() < 4:
        print(f"Group {group.name} has fewer than 4 teams — skipping.")
        return

    # Top 2 → Knockout
    top_two = standings[:2]
    # Bottom 2 → Classification
    bottom_two = standings[2:4]

    competition = group.competition

    # Generate Knockout Fixture
    Fixture.objects.create(
        competition=competition,
        stage="Knockout",
        team1=top_two[0].team,
        team2=top_two[1].team,
        status="Pending"
    )

    # Generate Classification Fixture
    Fixture.objects.create(
        competition=competition,
        stage="Classification",
        team1=bottom_two[0].team,
        team2=bottom_two[1].team,
        status="Pending"
    )


from football.models import Fixture, GroupStanding, FGroup

# def recalculate_group_standings():
#     standings = {}

#     fixtures = Fixture.objects.filter(stage="Group", status="inplay")

#     for fixture in fixtures:
#         try:
#             group = FGroup.objects.get(competition=fixture.competition, teams=fixture.team1)
#         except FGroup.DoesNotExist:
#             continue  # Skip fixtures where group can't be determined

#         for team in [fixture.team1, fixture.team2]:
#             key = (team.id, group.id)
#             if key not in standings:
#                 standings[key] = {
#                     'team': team,
#                     'group': group,
#                     'played': 0,
#                     'won': 0,
#                     'drawn': 0,
#                     'lost': 0,
#                     'goals_for': 0,
#                     'goals_against': 0,
#                     'points': 0,
#                 }

#         team1_data = standings[(fixture.team1.id, group.id)]
#         team2_data = standings[(fixture.team2.id, group.id)]

#         team1_data['played'] += 1
#         team2_data['played'] += 1

#         team1_data['goals_for'] += fixture.team1_score
#         team1_data['goals_against'] += fixture.team2_score

#         team2_data['goals_for'] += fixture.team2_score
#         team2_data['goals_against'] += fixture.team1_score

#         if fixture.team1_score > fixture.team2_score:
#             team1_data['won'] += 1
#             team2_data['lost'] += 1
#             team1_data['points'] += 3
#         elif fixture.team1_score < fixture.team2_score:
#             team2_data['won'] += 1
#             team1_data['lost'] += 1
#             team2_data['points'] += 3
#         else:
#             team1_data['drawn'] += 1
#             team2_data['drawn'] += 1
#             team1_data['points'] += 1
#             team2_data['points'] += 1

#     # Clear existing standings
#     GroupStanding.objects.all().delete()

#     # Save new standings
#     for data in standings.values():
#         GroupStanding.objects.create(
#             team=data['team'],
#             group=data['group'],
#             played=data['played'],
#             won=data['won'],
#             drawn=data['drawn'],
#             lost=data['lost'],
#             goals_for=data['goals_for'],
#             goals_against=data['goals_against'],
#             points=data['points'],
#         )

#     print("✅ Standings updated based on fixture scores.")
