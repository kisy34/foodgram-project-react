from django.contrib.auth import get_user_model
from django.db.models import prefetch_related_objects
from rest_framework import filters, mixins, viewsets
from rest_framework.response import Response

from .permissions import ReadOnly, UserIsAdmin

User = get_user_model()


class NoPUTViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet,
                   ):
    pass


class PatchViewSet:
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data,
                                         partial=True
                                         )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        queryset = self.filter_queryset(self.get_queryset())

        if queryset._prefetch_related_lookups:
            instance._prefetched_objects_cache = {}
            prefetch_related_objects([instance],
                                     *queryset._prefetch_related_lookups)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class CommonViewSet(
        viewsets.GenericViewSet,
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.DestroyModelMixin,
):
    permission_classes = (
            ReadOnly | UserIsAdmin,
    )

    filter_backends = (
            filters.SearchFilter,
    )

    search_fields = (
            'name',
    )

    lookup_field = 'slug'
