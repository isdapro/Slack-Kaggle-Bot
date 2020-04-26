from django.db import models

# Create your models here.
class Users(models.Model):
    user_id = models.CharField(max_length=400, unique = True)

    def __str__(self):
        return self.user_id

class Datasets(models.Model):
    users = models.ManyToManyField(Users)
    dat_name = models.TextField()
    dat_url = models.CharField(max_length = 500, unique = True)
    last_updated = models.DateTimeField()
    disc_count = models.IntegerField()
    kernel_count = models.IntegerField()
    most_recent_disc = models.DateTimeField()

    def __str__(self):
        return self.dat_name

class BasicDatasets(models.Model):
    users = models.ManyToManyField(Users)
    dat_name = models.TextField()
    dat_url = models.CharField(max_length = 500, unique = True)
    last_updated = models.DateTimeField()

    def __str__(self):
        return self.dat_name

class Kernels(models.Model):
    users = models.ManyToManyField(Users)
    kernel_name = models.TextField()
    kernel_url = models.CharField(max_length = 500, unique = True)
    last_run = models.DateTimeField()
    comment_count = models.IntegerField()

    def __str__(self):
        return self.kernel_name
