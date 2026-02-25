from django.db import models

#create a Gamescore object where the user first visits,store its ID in session nad update that record

class GameScore(models.Model):
    correct = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add = True)
