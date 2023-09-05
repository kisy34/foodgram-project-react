from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint
from rest_framework.exceptions import ValidationError


class User(AbstractUser):
    """Переопределенная модель User"""
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    USER = 'user'

    ALLOWED_ROLES = (
            (MODERATOR, 'Moderator'),
            (ADMIN, 'Admin'),
            (USER, 'User')
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        UniqueConstraint(fields=['email', 'username'],
                         name='unique_draft_user')

    @property
    def is_moderator(self):
        return self.role == User.MODERATOR

    @property
    def is_admin_or_superuser(self):
        if self.role == User.ADMIN or self.is_superuser:
            self.is_staff = True
        return self.is_staff

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        if self.username == 'me':
            raise ValidationError('Имя me запрещено.')


class Followers(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='follower')
    followed = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='followed')
