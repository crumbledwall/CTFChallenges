from django.db import models


class HashTable(models.Model):
    reveal = models.IntegerField()
    commitlastblock = models.IntegerField()
    commit = models.CharField(max_length=64)
    is_settle = models.BooleanField(default=False)


class Contract(models.Model):
    address = models.CharField(max_length=64)
    team_id = models.CharField(max_length=64)
    is_visited = models.BooleanField(default=False)