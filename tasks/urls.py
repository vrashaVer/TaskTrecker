from django.urls import path
from tasks import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
]