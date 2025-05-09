from django.contrib import admin

# Register your models here.
from accounts.models import *
from dashboard.models import *
from football.models import *


# Register your models here.
admin.site.register(User)
admin.site.register(Sport)
admin.site.register(Championship)
admin.site.register(Season)
admin.site.register(School)
admin.site.register(Football)
admin.site.register(Fixture)

