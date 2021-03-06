from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Company(models.Model):
    name = models.CharField(max_length=20)
    email = models.EmailField()
    city = models.CharField(max_length=20)

    def __str__(self) -> str:
        return str(self.name)


class Tag(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self) -> str:
        return str(self.name)


class SkiResort(models.Model):
    name = models.TextField()
    address = models.TextField()
    tracks_number = models.IntegerField()
    opened = models.BooleanField()
    description = models.TextField(max_length=20)
    rating = models.IntegerField(null=True)
    phone_number = models.CharField(max_length=12)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)

    def __str__(self) -> str:
        return str(self.name)


class SkiLiftLimit(models.Model):
    DEFAULT = "DEF"
    PROFESSIONAL = "PRO"
    TYPES_OF_USERS = [(DEFAULT, "Normal Skier"), (PROFESSIONAL, "Professional Skier")]
    user_status = models.CharField(
        max_length=3, choices=TYPES_OF_USERS, default=DEFAULT, unique=True
    )
    daily_limit = models.IntegerField()
    monthly_limit = models.IntegerField()
    days_in_row_limit = models.IntegerField()
    weekend_limit = models.IntegerField(default=0)

    def __str__(self) -> str:
        return str(self.user_status)


class User(AbstractUser):
    partnered_ski_resorts = models.ManyToManyField(SkiResort, blank=True)
    status = models.ForeignKey(SkiLiftLimit, on_delete=models.SET_NULL, null=True)


class SkiLift(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    ski_resort = models.ForeignKey(SkiResort, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"<SkiLift User={self.user}, Date={self.date}>"
