# fraudsite/urls.py
from django.contrib import admin
from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from predictor import views as pviews

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # UI
    path('', pviews.form_view, name='home'),
    path('history/', pviews.history_view, name='history'),

    # Auth
    path('login/',  auth_views.LoginView.as_view(),  name='login')
    ,
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', pviews.signup_view, name='signup'),

    # API (v1)
    path('api/v1/predict/', pviews.predict_view, name='api-predict'),
    path('api/v1/health/',  pviews.health_view, name='api-health'),

    # Legacy API paths (kept so older front-end code still works)
    path('api/predict/', pviews.predict_view, name='api-predict-legacy'),
    path('api/health/',  pviews.health_view, name='api-health-legacy'),

    # Docs
    path('docs/', pviews.docs_view, name='api-docs'),

    # Quiet the favicon.ico 404
    re_path(r'^favicon\.ico$', lambda r: HttpResponse(status=204)),
]
