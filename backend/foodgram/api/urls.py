from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter
from views import (FollowingView, IngredientsSerializer, RecipeViewSet,
                   TagsSerializer, UserViewSet)

router_v1_user = DefaultRouter()

router_v1_user.register('users', UserViewSet, basename='users')

router_v1_user.register('ingredients', IngredientsSerializer,
                        basename='ingredients')
router_v1_user.register('recipies', RecipeViewSet, basename='recipies')
router_v1_user.register('tags', TagsSerializer, basename='tags')

auth_urls = [
    path('token/login/', TokenCreateView.as_view(), name='login'),
    path('token/logout/', TokenDestroyView.as_view(), name='signup')]

urlpatterns = [
    path('users/subscriptions/', UserViewSet.as_view()),
    path('users/<int:pk>/subscribe/', FollowingView.as_view()),
    path('', include(router_v1_user.urls)),
    path('auth/', include(auth_urls)),
    path('', include(router_v1_user.urls)),

]
