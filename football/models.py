from django.db import models
from accounts.models import *
from dashboard.models import *
# from .utils import update_standings
# Create your models here.


# Create your models here.
class Football(models.Model):
    name = models.CharField(max_length=255)
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    gender = models.CharField(
        choices=[("Male", "Male"), ("Female", "Female")],
        max_length=10,
        null=True,
        blank=True,
    )
    age = models.CharField(
        choices=(("U16", "U16"), ("U18", "U18"), ("U20", "U20")),
        max_length=50,
        null=True,
        blank=True,
    )
    teams = models.ManyToManyField(SchoolTeam)
    participants = models.IntegerField()
    number_of_groups = models.IntegerField()

    def __str__(self):
        return self.name


class FGroup(models.Model):
    competition = models.ForeignKey(Football, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    teams = models.ManyToManyField(SchoolTeam)

    def __str__(self):
        return self.name


class Fixture(models.Model):
    statuses = (
        ("Pending", "Pending"),
        ("InPlay", "InPlay"),
        ("Complete", "Complete"),
        ("Postponed", "Postponed"),
    )

    stages = (("Group", "Group"), ("Knockout", "Knockout"), ("Classification", "Classification"))
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    competition = models.ForeignKey(
        Football, on_delete=models.CASCADE, null=True, blank=True
    )
    stage = models.CharField(choices=stages, max_length=100, null=True, blank=True)
    status = models.CharField(
        choices=statuses, max_length=100, null=True, blank=True, default="Pending"
    )
    round = models.CharField(max_length=100, null=True, blank=True)
    group = models.ForeignKey(FGroup, on_delete=models.CASCADE, null=True, blank=True)

    # Use UUIDField for match_number

    venue = models.CharField(max_length=100, null=True, blank=True)
    # Separate date and time fields
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)

    team1 = models.ForeignKey(
        SchoolTeam, related_name="team1", on_delete=models.CASCADE
    )
    team2 = models.ForeignKey(
        SchoolTeam, related_name="team2", on_delete=models.CASCADE
    )
    team1_score = models.IntegerField(null=True, blank=True)
    team2_score = models.IntegerField(null=True, blank=True)
    
        # Optional penalty scores (used only when match is drawn and resolved via penalties)
    team1_penalty_score = models.IntegerField(null=True, blank=True)
    team2_penalty_score = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Match {self.id}: {self.team1} vs {self.team2}"



class MatchEvent(models.Model):
    match = models.ForeignKey(Fixture, on_delete=models.CASCADE)
    EVENT_CHOICES = [
        ("RedCard", "RedCard"),
        ("YellowCard", "YellowCard"),
        ("Corner", "Corner"),
        ("Foul", "Foul"),
        ("Assist", "Assist"),
        ("Goal", "Goal"),
        ("Save", "Save"),
        ("Substitution", "Substitution"),
        ("Short on goal", "Short on goal"),
        ("Short off target", "Short off target"),
        ("penalty", "penalty"),
        # Add more choices as needed
    ]

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_CHOICES,
    )  # Example: "Card", "Corner", "Foul", "Assist"
    team = models.ForeignKey(SchoolTeam, related_name="team", on_delete=models.CASCADE)
    athlete = models.ForeignKey(
        Athlete, related_name="athlete", on_delete=models.CASCADE, null=True, blank=True
    )
    minute = models.IntegerField()
    commentary = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.team} - {self.event_type} at {self.minute}'"


class match_official(models.Model):
    role = (
        ("Referee", "Referee"),
        ("Umpire", "Umpire"),
        ("First assistant", "First assistant "),
        ("Second assistant", "Second assistant "),
        ("4th Official", "4th Official"),
    )

    fixture = models.ForeignKey(
        Fixture, on_delete=models.CASCADE, null=True, blank=True
    )

    match_role = models.CharField(choices=role, max_length=100, null=True, blank=True)

    def __str__(self):
        return self.fixture


class GroupStanding(models.Model):
    group = models.ForeignKey(FGroup, on_delete=models.CASCADE)
    team = models.ForeignKey(SchoolTeam, on_delete=models.CASCADE)
    played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('group', 'team')
        ordering = ['-points', '-goals_for', 'goals_against']

    def goal_difference(self):
        return self.goals_for - self.goals_against

    def __str__(self):
        return f"{self.group.name} - {self.team} ({self.points} pts)"


class PlayerStatistic(models.Model):
    athlete = models.ForeignKey(Athlete, on_delete=models.CASCADE)
    competition = models.ForeignKey(Football, on_delete=models.CASCADE)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    minutes_played = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('athlete', 'competition')

    def __str__(self):
        return f"{self.athlete.full_name} - {self.competition.name}"


