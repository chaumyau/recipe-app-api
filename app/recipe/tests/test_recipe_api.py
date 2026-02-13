"""Test for recipe APIs."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    Recipe,
    Tag,
    )
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Helper function to create and return a sample recipe."""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.50'),
        'description': 'Sample recipe description.',
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Helper function to create a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Tests for unauthenticated recipe API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the endpoint."""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Tests for authenticated recipe API access."""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = create_user(
            email='other@example.com',
            password='testpass123',
        )  # type: ignore
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore
        self.assertEqual(len(res.data), 1)  # type: ignore

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': Decimal('5.50'),
            'description': 'Sample recipe description.',
            'link': 'http://example.com/recipe.pdf',
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])  # type: ignore
        for key in payload.keys():
            self.assertEqual(getattr(recipe, key), payload[key])

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch."""
        recipe = create_recipe(user=self.user)

        payload = {'title': 'Updated recipe title'}
        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])

    def test_full_update_recipe(self):
        """Test updating a recipe with put."""
        recipe = create_recipe(user=self.user)

        payload = {
            'title': 'Updated recipe title',
            'time_minutes': 20,
            'price': Decimal('10.00'),
            'description': 'Updated recipe description.',
            'link': 'http://example.com/updated-recipe.pdf',
        }
        url = detail_url(recipe.id)  # type: ignore
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key in payload.keys():
            self.assertEqual(getattr(recipe, key), payload[key])

    def test_update_recipe_user_returns_error(self):
        """Test changing the recipe user results in an error."""
        other_user = create_user(
            email='other@example.com',
            password='testpass123',
        )
        recipe = create_recipe(user=other_user)

        payload = {'user': self.user.id}  # type: ignore
        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user.id, other_user.id)  # type: ignore

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(
            id=recipe.id).exists())  # type: ignore

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another user's recipe gives error."""
        other_user = create_user(
            email='other@example.com',
            password='testpass123',
        )
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(
            id=recipe.id).exists())  # type: ignore

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': Decimal('5.50'),
            'description': 'Sample recipe description.',
            'link': 'http://example.com/recipe.pdf',
            'tags': [
                {'name': 'Tag1'},
                {'name': 'Tag2'},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])  # type: ignore
        tags_in_recipe = recipe.tags.all()
        self.assertEqual(tags_in_recipe.count(), 2)
        for tag in payload['tags']:
            self.assertTrue(tags_in_recipe.filter(name=tag['name']).exists())
        tags_in_db = Tag.objects.filter(user=self.user)
        self.assertEqual(tags_in_db.count(), 2)
        for tag in payload['tags']:
            self.assertTrue(tags_in_db.filter(name=tag['name']).exists())

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags."""
        tag = Tag.objects.create(user=self.user, name='Tag1')
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': Decimal('5.50'),
            'description': 'Sample recipe description.',
            'link': 'http://example.com/recipe.pdf',
            'tags': [
                {'name': tag.name},
                {'name': 'Tag2'},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])  # type: ignore
        tags_in_recipe = recipe.tags.all()
        self.assertEqual(tags_in_recipe.count(), 2)
        self.assertTrue(tags_in_recipe.filter(name=tag.name).exists())
        tags_in_db = Tag.objects.filter(user=self.user)
        self.assertEqual(tags_in_db.count(), 2)
        self.assertIn(tag, tags_in_db)

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {
            'tags': [{'name': 'NewTag'}],
        }
        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='NewTag')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {
            'tags': [{'name': tag_lunch.name}],
        }
        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe's tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
