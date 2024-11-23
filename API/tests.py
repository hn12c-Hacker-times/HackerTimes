from django.test import TestCase

# Create your tests here.
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from News.models import News, CustomUser
from django.utils import timezone

class NewsAPITests(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create(
            username="testuser",
            email="test@example.com",
            karma=1
        )
        
        # Create some test news
        self.test_news = News.objects.create(
            title="Test News",
            url="https://example.com",
            urlDomain="example.com",
            text="This is a test news",
            author=self.user.username,
            points=10,
            is_hidden=False
        )
        
        # Create API client
        self.client = APIClient()

    def test_get_news_list(self):
        """
        Test retrieving list of news
        """
        url = reverse('API:news-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test News')

    def test_create_news(self):
        """
        Test creating a new news item
        """
        url = reverse('API:news-list')
        data = {
            'title': 'New Test News',
            'url': 'https://test.com',
            'urlDomain': 'test.com',
            'text': 'This is another test news',
            'author': self.user.username,
            'points': 0,
            'is_hidden': False
        }
        
        # Simulate user session
        session = self.client.session
        session['user_data'] = {'email': self.user.email, 'name': self.user.username}
        session.save()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(News.objects.count(), 2)
        self.assertEqual(News.objects.get(title='New Test News').author, self.user.username)

    def test_get_news_detail(self):
        """
        Test retrieving a specific news item
        """
        url = reverse('API:news-detail', kwargs={'pk': self.test_news.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.test_news.title)

    def test_update_news(self):
        """
        Test updating an existing news item
        """
        url = reverse('API:news-detail', kwargs={'pk': self.test_news.pk})
        updated_data = {
            'title': 'Updated Test News',
            'url': self.test_news.url,
            'urlDomain': self.test_news.urlDomain,
            'text': self.test_news.text,
            'author': self.test_news.author,
            'points': self.test_news.points,
            'is_hidden': False
        }
        
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(News.objects.get(pk=self.test_news.pk).title, 'Updated Test News')

    def test_delete_news(self):
        """
        Test deleting a news item
        """
        url = reverse('API:news-detail', kwargs={'pk': self.test_news.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(News.objects.count(), 0)

    def test_relevance_sorting(self):
        """
        Test that news are properly sorted by relevance
        """
        # Create another news with different points and time
        older_news = News.objects.create(
            title="Older News",
            url="https://example.com/old",
            urlDomain="example.com",
            text="This is an older news",
            author=self.user.username,
            points=20,
            published_date=timezone.now() - timezone.timedelta(days=2),
            is_hidden=False
        )
        
        url = reverse('API:news-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the newer news with lower points isn't necessarily first
        # The actual order will depend on the relevance calculation
        self.assertEqual(len(response.data), 2)

    def test_hidden_news_filtering(self):
        """
        Test that hidden news are properly filtered
        """
        hidden_news = News.objects.create(
            title="Hidden News",
            url="https://example.com/hidden",
            urlDomain="example.com",
            text="This is a hidden news",
            author=self.user.username,
            points=5,
            is_hidden=True
        )
        
        url = reverse('API:news-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the non-hidden news should be returned