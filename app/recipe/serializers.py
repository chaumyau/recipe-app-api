"""Serializers for the recipe app."""
from rest_framework import serializers

from core.models import (
    Recipe,
    Tag,
    Ingredient,
    )


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects."""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient objects."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name')
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects."""

    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'title',
            'time_minutes',
            'price',
            'link',
            'tags',
            'ingredients',
        )
        read_only_fields = ('id',)

    def _get_or_create_tags(self, tags_data, recipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user  # type: ignore

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(
                user=auth_user,
                **tag_data
            )
            recipe.tags.add(tag)

    def _get_or_create_ingredients(self, ingredients_data, recipe):
        """Handle getting or creating ingredients as needed."""
        auth_user = self.context['request'].user  # type: ignore

        for ingredient_data in ingredients_data:
            ingredient, _ = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient_data
            )
            recipe.ingredients.add(ingredient)

    def create(self, validated_data):
        """Create and return a new recipe."""
        tags_data = validated_data.pop('tags', [])  # type: ignore
        ingredients_data = validated_data.pop(
            'ingredients', [])  # type: ignore
        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_tags(tags_data, recipe)
        self._get_or_create_ingredients(ingredients_data, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Update and return an existing recipe."""
        tags_data = validated_data.pop('tags', None)  # type: ignore
        ingredients_data = validated_data.pop(
            'ingredients', None)  # type: ignore

        if tags_data is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags_data, instance)

        if ingredients_data is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients_data, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ('description',)
