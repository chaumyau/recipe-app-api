"""Serializers for the recipe app."""
from rest_framework import serializers

from core.models import (
    Recipe,
    Tag,
    )


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects."""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects."""

    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'title',
            'time_minutes',
            'price',
            'link',
            'tags',
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        """Create and return a new recipe."""
        tags_data = validated_data.pop('tags', [])  # type: ignore
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context['request'].user  # type: ignore

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(
                user=auth_user,
                **tag_data
            )
            recipe.tags.add(tag)

        return recipe

    def update(self, instance, validated_data):
        """Update and return an existing recipe."""
        tags_data = validated_data.pop('tags', None)  # type: ignore

        if tags_data is not None:
            auth_user = self.context['request'].user  # type: ignore
            instance.tags.clear()

            for tag_data in tags_data:
                tag, _ = Tag.objects.get_or_create(
                    user=auth_user,
                    **tag_data
                )
                instance.tags.add(tag)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ('description',)
