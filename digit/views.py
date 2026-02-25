import random

from django.http import JsonResponse
from django.shortcuts import render

from .models import GameScore
from .utils import predict_digit, preprocess_image

# Mapping for number to text
NUMBER_TO_TEXT = {
	0: "zero",
	1: "one",
	2: "two",
	3: "three",
	4: "four",
	5: "five",
	6: "six",
	7: "seven",
	8: "eight",
	9: "nine",
}


def home(request):
	return render(request, "digit/home.html")

def scribble(request):
	if request.GET.get("restart") == "1":
		request.session.pop("game_id", None)
		request.session.pop("target", None)
		request.session.pop("last_predicted", None)
		request.session.pop("last_target", None)
		request.session.pop("last_correct", None)

	if "game_id" not in request.session:
		game = GameScore.objects.create()
		request.session["game_id"] = game.id

	target = random.randint(0, 9)
	request.session["target"] = target
	target_text = NUMBER_TO_TEXT[target]

	return render(request, "digit/scribble.html", {"target": target, "target_text": target_text})

def predict(request):
	if request.method != "POST":
		return JsonResponse({"error": "Only POST is allowed."}, status=405)

	image_data = request.POST.get("image")
	if not image_data:
		return JsonResponse({"error": "Missing image payload."}, status=400)

	try:
		processed = preprocess_image(image_data)
		predicted_digit = int(predict_digit(processed))
	except Exception as exc:
		return JsonResponse({"error": f"Invalid image payload: {exc}"}, status=400)

	target = request.session.get("target")
	game_id = request.session.get("game_id")

	game = None
	if game_id is not None:
		game = GameScore.objects.filter(id=game_id).first()

	if game is None:
		game = GameScore.objects.create()
		request.session["game_id"] = game.id

	is_correct = target is not None and predicted_digit == target
	game.total += 1
	if is_correct:
		game.correct += 1
	game.save(update_fields=["correct", "total"])

	# Store result in session for result page
	request.session["last_predicted"] = predicted_digit
	request.session["last_target"] = target
	request.session["last_correct"] = is_correct

	# Generate new target for next round
	new_target = random.randint(0, 9)
	request.session["target"] = new_target

	return JsonResponse({"success": True, "redirect": "/digit/result/"})

def result(request):
	predicted = request.session.get("last_predicted")
	target = request.session.get("last_target")
	is_correct = request.session.get("last_correct", False)
	
	game_id = request.session.get("game_id")
	game = None
	if game_id:
		game = GameScore.objects.filter(id=game_id).first()
	
	# Get text versions
	predicted_text = NUMBER_TO_TEXT.get(predicted, "unknown") if predicted is not None else "unknown"
	target_text = NUMBER_TO_TEXT.get(target, "unknown") if target is not None else "unknown"
	
	# Get next target text
	next_target = request.session.get("target")
	next_target_text = NUMBER_TO_TEXT.get(next_target, "unknown") if next_target is not None else "unknown"
	
	context = {
		"predicted": predicted,
		"predicted_text": predicted_text,
		"target": target,
		"target_text": target_text,
		"is_correct": is_correct,
		"score": game.correct if game else 0,
		"total": game.total if game else 0,
		"next_target_text": next_target_text,
	}
	
	return render(request, "digit/result.html", context)
