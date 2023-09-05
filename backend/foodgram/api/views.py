from core.pagination import CustomPagination
from core.pdf_download import getpdf
from django.contrib.auth import get_user_model
from django.db.models import Sum
from food_recipie.models import Followers, Ingredients, Tags
from food_recipies.models import (Favorite, IngredientAndItsQuantity, Recipies,
                                  ShoppingCart)
from rest_framework import filters, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from serializers import (AddRecipiesSerializer, RecipeSerializer,
                         RecipiesSerializer)

from ..permissions import IsOwnerOrReadOnly
from .mixins import NoPUTViewSet, PatchViewSet
from .permissions import UserIsAdmin
from .serializers import (IngredientsSerializer, PasswordSerializer,
                          SubscribeSerializer, SubscriptionsSerializer,
                          TagsSerializer, UserSerializer)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    class CustomSearchFilter(filters.SearchFilter):
        search_param = 'name'

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = [CustomSearchFilter]
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipies.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipiesSerializer
        return AddRecipiesSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe(Favorite, request, pk)

        return self.delete_recipe(Favorite, request, pk)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(ShoppingCart, request, pk)

        return self.delete_recipe(ShoppingCart, request, pk)

    @action(detail=False, permission_classes=[IsAuthenticated, ])
    def download_shopping_cart(self, request):
        ingredients = IngredientAndItsQuantity.objects.filter(
                recipe__carts__user=request.user).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                ingredient_amount=Sum('amount'))
        return getpdf(ingredients)

    def add_recipe(self, model, pk):
        recipie = get_object_or_404(Recipies, pk=pk)
        user = self.request.user
        if model.objects.filter(recipe=recipie, user=user).exists():
            raise ValidationError('Object exists.')
        model.objects.create(recipe=recipie, user=user)
        serializer = RecipeSerializer(recipie)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, pk):
        recipie = get_object_or_404(Recipies, pk=pk)
        user = self.request.user
        obj = get_object_or_404(model, recipe=recipie, user=user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer


class UserViewSet(NoPUTViewSet, PatchViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    permission_classes = (UserIsAdmin,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(detail=False,
            methods=['PATCH'],
            permission_classes=(IsAuthenticated,),
            url_path='me',
            )
    def patch_method_for_me(self, request):
        serializer = UserSerializer(request.user,
                                    data=request.data,
                                    partial=True
                                    )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @patch_method_for_me.mapping.get
    def get_method_for_me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def set_password(self, request):
        user = self.request.user
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(
                    serializer.validated_data['new_password']
            )
            user.save()
            return Response(
                    {'Response': 'Success!'}
            )
        return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = self.request.user.follower.all()
        if not queryset.exists():
            return Response('None', status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page:
            serializer = SubscriptionsSerializer(
                    page,
                    many=True,
                    context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionsSerializer(queryset, many=True,
                                             context={'request': request})
        return Response(serializer.data)


class FollowingView(views.APIView):
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        user = self.request.user
        data = {'author': author.id, 'user': user.id}
        serializer = SubscribeSerializer(
                data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data,
                        status=status.HTTP_201_CREATED)

    def delete(self, pk):
        author = get_object_or_404(User, pk=pk)
        user = self.request.user
        following = get_object_or_404(
                Followers, user=user, author=author
        )
        following.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
