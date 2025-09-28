# fraudsite/urls.py
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from predictor import views as pviews

urlpatterns = [
    path('admin/', admin.site.urls),

    # UI
    path('', pviews.form_view, name='home'),
    path('history/', pviews.history_view, name='history'),

    # Auth
    path('login/',  auth_views.LoginView.as_view(),  name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', pviews.signup_view, name='signup'),

    # API (v1 + legacy)
    path('api/v1/predict/', pviews.predict_view, name='api-predict'),
    path('api/v1/health/',  pviews.health_view, name='api-health'),

    # API docs
    path('docs/', pviews.docs_view, name='api-docs'),
]
