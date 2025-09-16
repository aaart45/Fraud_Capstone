from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from predictor.views import predict_view, form_view, history_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/",  auth_views.LoginView.as_view(),  name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/predict", predict_view, name="api-predict"),
    path("", form_view, name="home"),
    path("history/", history_view, name="history"),
]
