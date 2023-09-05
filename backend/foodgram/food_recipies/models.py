from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredients(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


class IngredientAndItsQuantity(models.Model):
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Tags(models.Model):
    name = models.CharField(max_length=200)
    color = models.ColorField()
    slug = models.SlugField(unique=True)


class Recipies(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    picture = models.ImageField(upload_to='food_pictures/')
    description = models.TextField()
    ingredients = models.ManyToManyField(IngredientAndItsQuantity)
    tag = models.ManyToManyField(Tags)
    timing = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    pub_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-pub_date']


class Favorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipie = models.ForeignKey(Recipies, on_delete=models.CASCADE)


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipie = models.ForeignKey(Recipies, on_delete=models.CASCADE)
