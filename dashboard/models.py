from django.db import models
from accounts.models import *


# Create your models here.
class Season(models.Model):
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE)
    host = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(auto_now=False, null=True, blank=True)
    end_date = models.DateField(auto_now=False, null=True, blank=True)

    def __str__(self):
        return self.name


class SchoolTeam(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, null=True)
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, null=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True)
    age = models.CharField(
        choices=(("U16", "U16"), ("U18", "U18"), ("U20", "U20")), max_length=50
    )
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female")],
    )
    status = models.CharField(
        max_length=10,
        default="Inactive",
        choices=[("Active", "Active"), ("Inactive", "Inactive")],
        null=True,
    )
    athletes = models.ManyToManyField(Athlete)

    def __str__(self):
        return str(self.school)



