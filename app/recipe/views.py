"""Views for the recipe API."""
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Recipe,
    Tag,
)
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):  # type: ignore
        """Return objects for the current authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):  # type: ignore
        """Return appropriate serializer class."""
        if self.action == 'list':
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):  # type: ignore
        """Create a new recipe."""
        serializer.save(user=self.request.user)


class TagViewSet(mixins.ListModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    """View for manage tag APIs."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):  # type: ignore
        """Return objects for the current authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by('-name')
