from django.shortcuts import render


def home(request):
	return render(request, "digit/home.html")

def scribble(request):
	return render(request, "digit/scribble.html")
