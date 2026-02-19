"""Tests for the ingredients API."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def ingredient_detail_url(ingredient_id):
    """Helper function to return ingredient detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email: str = 'test@example.com',
                password: str = 'testpass123'):
    """Helper function to create a new user."""
    return get_user_model().objects.create_user(
        email=email,
        password=password)  # type: ignore


class PublicIngredientsApiTests(TestCase):
    """Tests for unauthenticated ingredients API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the endpoint."""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Tests for authenticated ingredients API access."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name='Ingredient1')
        Ingredient.objects.create(user=self.user, name='Ingredient2')

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_ingredients_limited_to_user(self):
        """Test that only ingredients for the authenticated user are
           returned.
        """
        user2 = create_user(email='user2@example.com', password='testpass456')
        Ingredient.objects.create(user=self.user, name='Ingredient1')
        Ingredient.objects.create(user=user2, name='Ingredient2')

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.filter(
            user=self.user).order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore
        self.assertEqual(len(res.data), 1)  # type: ignore

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Salt')
        payload = {'name': 'Pepper'}
        url = ingredient_detail_url(ingredient.id)  # type: ignore
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Sugar')
        url = ingredient_detail_url(ingredient.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exists = Ingredient.objects.filter(
            id=ingredient.id).exists()  # type: ignore
        self.assertFalse(exists)

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients to those assigned to recipes."""
        ingredient1 = Ingredient.objects.create(
            user=self.user, name='Ingredient1')
        ingredient2 = Ingredient.objects.create(
            user=self.user, name='Ingredient2')
        recipe1 = Recipe.objects.create(
            title='Recipe1',
            time_minutes=10,
            price=Decimal('5.00'),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title='Recipe2',
            time_minutes=20,
            price=Decimal('10.00'),
            user=self.user
        )
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)  # type: ignore
        self.assertNotIn(serializer2.data, res.data)  # type: ignore

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique list."""
        ingredient = Ingredient.objects.create(user=self.user,
                                               name='Ingredient1')
        Ingredient.objects.create(user=self.user, name='Ingredient2')
        recipe1 = Recipe.objects.create(
            title='Recipe1',
            time_minutes=10,
            price=Decimal('5.00'),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title='Recipe2',
            time_minutes=20,
            price=Decimal('10.00'),
            user=self.user
        )
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)  # type: ignore
