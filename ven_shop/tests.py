import uuid
import json
from xml.etree import ElementTree as ET
from django.test import TestCase, Client
from django.urls import reverse
from ven_shop.models import Product


class ProductViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        
        self.product1 = Product.objects.create(
            title="Test Product 1",
            content="Test content 1",
            category="badminton",
            thumbnail="https://example.com/image1.jpg",
            price=10000,
            stock=50,
            rating=4.0,
            reviewer=10,
            brand="TestBrand"
        )
        
        self.product2 = Product.objects.create(
            title="Test Product 2",
            content="Test content 2",
            category="basketball",
            thumbnail="https://example.com/image2.jpg",
            price=20000,
            stock=0,
            rating=3.5,
            reviewer=5,
            brand="Brand2"
        )

    def test_show_main(self):
        response = self.client.get(reverse('ven_shop:show_main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

    def test_show_xml(self):
        response = self.client.get(reverse('ven_shop:show_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_show_xml_by_id(self):
        response = self.client.get(
            reverse('ven_shop:show_xml_by_id', args=[self.product1.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_show_json(self):
        response = self.client.get(reverse('ven_shop:show_json'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)

    def test_show_json_by_id(self):
        response = self.client.get(
            reverse('ven_shop:show_json_by_id', args=[self.product1.id])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['title'], "Test Product 1")

    def test_create_product_get(self):
        response = self.client.get(reverse('ven_shop:create_product'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_create_product_post(self):
        data = {
            'title': 'New Product',
            'content': 'New content',
            'category': 'tennis',
            'thumbnail': 'https://example.com/new.jpg',
            'price': 15000,
            'stock': 30,
            'brand': 'NewBrand'
        }
        response = self.client.post(reverse('ven_shop:create_product'), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(title='New Product').exists())

    def test_show_product(self):
        response = self.client.get(
            reverse('ven_shop:show_product', args=[self.product1.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'].title, "Test Product 1")

    def test_edit_product(self):
        data = {
            'title': 'Updated Product',
            'content': 'Updated content',
            'category': 'badminton',
            'thumbnail': 'https://example.com/updated.jpg',
            'price': 12000,
            'stock': 40,
            'brand': 'UpdatedBrand'
        }
        response = self.client.post(
            reverse('ven_shop:edit_product', args=[self.product1.id]),
            data=data
        )
        self.assertEqual(response.status_code, 302)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.title, 'Updated Product')

    def test_delete_product(self):
        product_id = self.product1.id
        response = self.client.post(
            reverse('ven_shop:delete_product', args=[product_id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(id=product_id).exists())

    def test_checkout_product(self):
        initial_stock = self.product1.stock
        response = self.client.post(
            reverse('ven_shop:checkout_product', args=[self.product1.id])
        )
        self.assertEqual(response.status_code, 302)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, initial_stock - 1)

    def test_checkout_out_of_stock(self):
        response = self.client.post(
            reverse('ven_shop:checkout_product', args=[self.product2.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    def test_rating(self):
        initial_reviewer = self.product1.reviewer
        initial_rating = self.product1.rating
        
        response = self.client.post(
            reverse('ven_shop:submit_rating', args=[self.product1.id]),
            data={'rating': 5}
        )
        self.assertEqual(response.status_code, 302)
        
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.reviewer, initial_reviewer + 1)
        
        expected_rating = (initial_rating * initial_reviewer + 5) / (initial_reviewer + 1)
        self.assertAlmostEqual(self.product1.rating, expected_rating, places=2)