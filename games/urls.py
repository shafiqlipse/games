from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include
from client.views import Home
from accounts.views import user_login
# from competition.views import get_teams


urlpatterns = [
    path("admin/", admin.site.urls),
    # includes
    path("", Home, name="home"),
    path("login/", user_login, name="login"),
    path("dashboard/", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("football/", include("football.urls")),
    # path("client/", include("client.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
