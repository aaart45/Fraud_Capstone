from django.contrib import admin
from django.urls import path
from predictor.views import predict_view, form_view, history_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/predict", predict_view, name="api-predict"),
    path("", form_view, name="home"),
    path("history/", history_view, name="history"),   # note trailing slash
]
