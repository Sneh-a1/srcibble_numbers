from django.urls import path

from .views import home, predict, scribble, result

urlpatterns = [
    path("", home, name="home"),
    path("scribble/", scribble, name="scribble"),
    path("predict/", predict, name="predict"),
    path("result/", result, name="result"),
]
