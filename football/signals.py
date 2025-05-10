# In signals.py file

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import *

# rt based on your actual model location
from .models import Football, FGroup


# create groups
@receiver(post_save, sender=Football)
def create_groups_for_season(sender, instance, created, **kwargs):
    if created:
        # Define the number of groups based on the 'groups' field in the Season model
        num_groups = instance.number_of_groups

        for i in range(1, num_groups + 1):
            group_name = f"GROUP {chr(ord('A') + i - 1)}"
            FGroup.objects.create(name=group_name, competition=instance)


# set score to zero and begin th game
@receiver(pre_save, sender=Fixture)
def reset_scores_if_inplay(sender, instance, **kwargs):
    if instance.id:
        previous = Fixture.objects.get(id=instance.id)
        if previous.status == "Pending" and instance.status == "InPlay":
            instance.team1_score = 0
            instance.team2_score = 0


# update score with event
@receiver(post_save, sender=MatchEvent)
def update_fixture_score(sender, instance, created, **kwargs):
    if created and instance.event_type == "Goal":
        match = instance.match
        if instance.team == match.team1:
            match.team1_score = (match.team1_score or 0) + 1
        elif instance.team == match.team2:
            match.team2_score = (match.team2_score or 0) + 1
        match.save()


# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Fixture, GroupStanding
from .models import FGroup
from django.db.models.signals import m2m_changed

@receiver(m2m_changed, sender=FGroup.teams.through)
def create_standings_for_group(sender, instance, action, **kwargs):
    if action == "post_add":
        for team in instance.teams.all():
            GroupStanding.objects.get_or_create(
                group=instance,
                team=team,
                defaults={
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "points": 0,
                    "position": None,
                },
            )
            
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Fixture, GroupStanding

@receiver(pre_save, sender=Fixture)
def update_standings_on_fixture_change(sender, instance, **kwargs):
    # Exit early if not a Group stage fixture
    if instance.stage != "Group":
        return

    try:
        previous = Fixture.objects.get(pk=instance.pk)
    except Fixture.DoesNotExist:
        previous = None

    group = instance.group
    team1 = instance.team1
    team2 = instance.team2

    # CASE 1: Status changed from Pending to InPlay — simulate 0-0 match
    if previous and previous.status == "Pending" and instance.status == "InPlay":
        if previous.team1_score is not None and previous.team2_score is not None:
            _reverse_standing(previous)

        instance.team1_score = 0
        instance.team2_score = 0
        _apply_standing(instance)

    # CASE 2: Score updated — adjust standings
    elif previous and instance.status == "InPlay":
        score_changed = (
            previous.team1_score != instance.team1_score or
            previous.team2_score != instance.team2_score
        )

        if score_changed and instance.team1_score is not None and instance.team2_score is not None:
            _reverse_standing(previous)
            _apply_standing(instance)

    # CASE 3: Fresh fixture entry with InPlay status
    elif not previous and instance.status == "InPlay":
        if instance.team1_score is None or instance.team2_score is None:
            instance.team1_score = 0
            instance.team2_score = 0
        _apply_standing(instance)

    # Update standings position
    _update_group_positions(group)

def _apply_standing(fixture):
    group = fixture.group
    team1 = fixture.team1
    team2 = fixture.team2
    t1_score = fixture.team1_score
    t2_score = fixture.team2_score

    t1, _ = GroupStanding.objects.get_or_create(group=group, team=team1)
    t2, _ = GroupStanding.objects.get_or_create(group=group, team=team2)

    t1.played += 1
    t2.played += 1

    t1.goals_for += t1_score
    t1.goals_against += t2_score

    t2.goals_for += t2_score
    t2.goals_against += t1_score

    if t1_score > t2_score:
        t1.wins += 1
        t1.points += 3
        t2.losses += 1
    elif t1_score < t2_score:
        t2.wins += 1
        t2.points += 3
        t1.losses += 1
    else:
        t1.draws += 1
        t2.draws += 1
        t1.points += 1
        t2.points += 1

    t1.save()
    t2.save()


def _reverse_standing(fixture):
    if fixture.team1_score is None or fixture.team2_score is None:
        return

    group = fixture.group
    team1 = fixture.team1
    team2 = fixture.team2
    t1_score = fixture.team1_score
    t2_score = fixture.team2_score

    t1 = GroupStanding.objects.get(group=group, team=team1)
    t2 = GroupStanding.objects.get(group=group, team=team2)

    t1.played = max(0, t1.played - 1)
    t2.played = max(0, t2.played - 1)

    t1.goals_for = max(0, t1.goals_for - t1_score)
    t1.goals_against = max(0, t1.goals_against - t2_score)

    t2.goals_for = max(0, t2.goals_for - t2_score)
    t2.goals_against = max(0, t2.goals_against - t1_score)

    if t1_score > t2_score:
        t1.wins = max(0, t1.wins - 1)
        t1.points = max(0, t1.points - 3)
        t2.losses = max(0, t2.losses - 1)
    elif t1_score < t2_score:
        t2.wins = max(0, t2.wins - 1)
        t2.points = max(0, t2.points - 3)
        t1.losses = max(0, t1.losses - 1)
    else:
        t1.draws = max(0, t1.draws - 1)
        t2.draws = max(0, t2.draws - 1)
        t1.points = max(0, t1.points - 1)
        t2.points = max(0, t2.points - 1)

    t1.save()
    t2.save()


def _update_group_positions(group):
    standings = GroupStanding.objects.filter(group=group)
    sorted_standings = sorted(
        standings,
        key=lambda s: (s.points, s.goal_difference(), s.goals_for),
        reverse=True,
    )
    for index, standing in enumerate(sorted_standings, start=1):
        standing.position = index
        standing.save()
