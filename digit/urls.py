from django.urls import path
from .views import home,scribble

urlpatterns = [
    path("", home, name="home"),
    path("scribble/", scribble, name="scribble"),
]
