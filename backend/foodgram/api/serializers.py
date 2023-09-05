from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from ..food_recipies.models import (IngredientAndItsQuantity, Ingredients,
                                    Recipies, Tags)
from ..users.models import Followers

User = get_user_model()


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ['id', 'name', 'color', 'slug']


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
            max_length=254,
            required=True,
            validators=[UniqueValidator(User.objects.all())])

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'bio',
                  'role']

    def validate_username(self, username):
        if username == 'me':
            raise ValidationError(
                    'Name "me" is prohibited.'
            )
        return username


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ['id', 'name', 'measurement_unit']


class AddIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientAndItsQuantity
        fields = ['id', 'amount']


class IngredientsAndItsQuantitySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    measurement_unit = serializers.ReadOnlyField()

    class Meta:
        model = IngredientAndItsQuantity
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipiesSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    tags = TagsSerializer(read_only=True, many=True)
    ingredients = IngredientsAndItsQuantitySerializer(read_only=True,
                                                      many=True)

    class Meta:
        model = Recipies
        fields = ['id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time']

    def get_is_favorited(self, obj):
        if (self.context['request'].user.is_authenticated
                and obj.favorite_recipes.filter(
                        user=self.context['request'].user).exists()):
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        if (self.context['request'].user.is_authenticated
                and obj.shopping_list_recipes.filter(
                        user=self.context['request'].user).exists()):
            return True
        return False


class AddRecipiesSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    author = UserSerializer(read_only=True)
    ingredients = AddIngredientsSerializer()
    tags = serializers.PrimaryKeyRelatedField(
            queryset=Tags.objects.all(),
            many=True
    )

    class Meta:
        model = Recipies
        fields = ['id', 'tags', 'author', 'ingredients', 'name', 'image',
                  'text', 'cooking_time']

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients = validated_data.pop('ingredient')
        tags = validated_data.pop('tag')
        recipie = Recipies.objects.create(image=image, **validated_data)
        recipie.tag.set(tags)
        for ingredient in ingredients:
            add_ingredient = IngredientAndItsQuantity.objects.create(
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'])
            recipie.ingredient.add(add_ingredient)
        return recipie

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredient')
        tags = validated_data.pop('tag')
        super().update(instance, validated_data)
        IngredientAndItsQuantity.objects.filter(recipes=instance).delete()
        recipie = instance
        for ingredient in ingredients:
            object = IngredientAndItsQuantity.objects.create(
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'])
            recipie.ingredient.add(object)
        instance.tag.set(tags)
        return recipie


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipies
        fields = ['id', 'name', 'image', 'cooking_time']


# class IngredientsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Ingredients
#         fields = ['id', 'name', 'measurement_unit']


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()

#
# class RecipiesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Recipies
#         fields = ['id', 'name', 'image', 'cooking_time']


class SubscriptionsSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count']

        def get_recipes(self, obj):
            limits = (
                    self.context['request'].query_params.get('recipes_limit'))
            recipie = obj.recipes.all()
            if limits is not None:
                limit = int(limits)
                serializer = RecipiesSerializer(
                        recipie[:limit],
                        many=True
                )
            else:
                serializer = RecipiesSerializer(
                        recipie,
                        many=True
                )
            return serializer.data

        def get_recipes_count(self, obj):
            return Recipies.objects.filter(author=obj.author).count()

    class SubscribeSerializer(serializers.ModelSerializer):
        class Meta:
            model = Followers
            fields = ['user', 'author']

        def validate(self, data):
            user = data.get('user')
            author = data.get('author')
            if user == author:
                raise serializers.ValidationError(
                        'You cant follow user.'
                )
            if Followers.objects.filter(user=user, author=author).exists():
                raise serializers.ValidationError(
                        'This author is followed.'
                )
            return data

        def to_representation(self, instance):
            request = self.context.get('request')
            contexts = {'Request': request}
            serializer = SubscriptionsSerializer(
                    instance,
                    context=contexts
            )
            return serializer.data
