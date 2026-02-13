"""Tests for tags API."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def tag_detail_url(tag_id):
    """Helper function to return tag detail URL."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email: str = 'test@example.com',
                password: str = 'testpass123'):
    """Helper function to create a new user."""
    return get_user_model().objects.create_user(
        email=email,
        password=password)  # type: ignore


class PublicTagsApiTests(TestCase):
    """Tests for unauthenticated tags API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the endpoint."""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Tests for authenticated tags API access."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name='Tag1')
        Tag.objects.create(user=self.user, name='Tag2')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user."""
        other_user = create_user(email='other@example.com',
                                 password='testpass456')
        Tag.objects.create(user=other_user, name='OtherTag')
        tag = Tag.objects.create(user=self.user, name='MyTag')

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # type: ignore
        self.assertEqual(res.data[0]['name'], tag.name)  # type: ignore
        self.assertEqual(res.data[0]['id'], tag.id)  # type: ignore

    def test_update_tag(self):
        """Test updating a tag."""
        tag = Tag.objects.create(user=self.user, name='OriginalName')
        payload = {'name': 'UpdatedName'}
        url = tag_detail_url(tag.id)  # type: ignore
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name='TagToDelete')
        url = tag_detail_url(tag.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(
            id=tag.id).exists())  # type: ignore
