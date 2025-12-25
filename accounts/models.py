from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    RANK_IRON = 'iron'
    RANK_BRONZE = 'bronze'
    RANK_SILVER = 'silver'
    RANK_GOLD = 'gold'
    RANK_PLATINUM = 'platinum'

    RANK_CHOICE = [
        (RANK_IRON, 'Iron'),
        (RANK_BRONZE, 'Bronze'),
        (RANK_SILVER, 'Silver'),
        (RANK_GOLD, 'Gold'),
        (RANK_PLATINUM, 'Platinum'),
    ]

    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    rank = models.CharField(
        max_length=20,
        choices=RANK_CHOICE,
        default=RANK_IRON
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
