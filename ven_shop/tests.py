import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ven_shop.models import Product
from ven_shop.forms import ProductForm
import json


class ProductViewTest(TestCase):
    # Comprehensive test for all product views
    
    def setUp(self):
        # Setup test data
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        self.product = Product.objects.create(
            id=uuid.UUID('11111111-1111-1111-1111-111111111111'),
            title='Test Product',
            content='Test Content',
            category='badminton',
            thumbnail='http://example.com/image.jpg',
            price=100,
            rating=4.0,
            stock=10,
            reviewer=5,
            brand='TestBrand',
            user=self.user
        )
        
        self.invalid_uuid = uuid.UUID('99999999-9999-9999-9999-999999999999')
        self.client.login(username='testuser', password='testpass123')
    
    # Main view tests
    def test_show_main(self):
        # Test main page displays products
        response = self.client.get(reverse('ven_shop:show_main'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
    
    def test_show_main_with_filter(self):
        # Test category filtering
        response = self.client.get(reverse('ven_shop:show_main') + '?category=badminton')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['Product_list']), 1)
    
    # XML tests
    def test_show_xml(self):
        # Test XML serialization
        response = self.client.get(reverse('ven_shop:show_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/xml')
    
    def test_show_xml_by_id(self):
        # Test XML by ID
        response = self.client.get(reverse('ven_shop:show_xml_by_id', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
    
    # JSON tests
    def test_show_json(self):
        # Test JSON serialization
        response = self.client.get(reverse('ven_shop:show_json'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Product')
    
    def test_show_json_by_id_valid(self):
        # Test JSON by valid ID
        response = self.client.get(reverse('ven_shop:show_json_by_id', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['title'], 'Test Product')
    
    def test_show_json_by_id_invalid(self):
        # Test JSON by invalid ID
        response = self.client.get(reverse('ven_shop:show_json_by_id', args=[self.invalid_uuid]))
        self.assertEqual(response.status_code, 404)
    
    # Product detail tests
    def test_show_product_valid(self):
        # Test product detail page
        response = self.client.get(reverse('ven_shop:show_product', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'], self.product)
    
    def test_show_product_invalid(self):
        # Test product detail with invalid ID
        response = self.client.get(reverse('ven_shop:show_product', args=[self.invalid_uuid]))
        self.assertEqual(response.status_code, 404)
    
    # Create product tests
    def test_create_product_get(self):
        # Test create product form
        response = self.client.get(reverse('ven_shop:create_product'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ProductForm)
    
    def test_create_product_post(self):
        # Test create product submission
        data = {
            'title': 'New Product',
            'content': 'New Content',
            'category': 'tennis',
            'thumbnail': 'http://example.com/new.jpg',
            'price': 150,
            'rating': 5.0,
            'stock': 20,
            'reviewer': 1,
            'brand': 'NewBrand',
            'user': self.user.id
        }
        response = self.client.post(reverse('ven_shop:create_product'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(title='New Product').exists())
    
    # Edit product tests
    def test_edit_product_get(self):
        # Test edit product form
        response = self.client.get(reverse('ven_shop:edit_product', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_edit_product_post(self):
        # Test edit product submission
        data = {
            'title': 'Updated Product',
            'content': self.product.content,
            'category': self.product.category,
            'thumbnail': self.product.thumbnail,
            'price': self.product.price,
            'rating': self.product.rating,
            'stock': self.product.stock,
            'reviewer': self.product.reviewer,
            'brand': self.product.brand,
            'user': self.user.id
        }
        response = self.client.post(reverse('ven_shop:edit_product', args=[self.product.id]), data)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, 'Updated Product')
    
    def test_edit_product_invalid_id(self):
        # Test edit with invalid ID
        response = self.client.get(reverse('ven_shop:edit_product', args=[self.invalid_uuid]))
        self.assertEqual(response.status_code, 404)
    
    # Delete product tests
    def test_delete_product(self):
        # Test delete product
        product_id = self.product.id
        response = self.client.post(reverse('ven_shop:delete_product', args=[product_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(id=product_id).exists())
    
    def test_delete_product_invalid(self):
        # Test delete with invalid ID
        response = self.client.post(reverse('ven_shop:delete_product', args=[self.invalid_uuid]))
        self.assertEqual(response.status_code, 404)
    
    # Checkout tests
    def test_checkout_get(self):
        # Test checkout page
        response = self.client.get(reverse('ven_shop:checkout_product', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_checkout_post_success(self):
        # Test successful checkout
        initial_stock = self.product.stock
        response = self.client.post(reverse('ven_shop:checkout_product', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 1)
    
    def test_checkout_no_stock(self):
        # Test checkout with no stock
        self.product.stock = 0
        self.product.save()
        response = self.client.post(reverse('ven_shop:checkout_product', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
    
    # Purchase success test
    def test_purchase_success(self):
        # Test purchase success page
        response = self.client.get(reverse('ven_shop:purchase_success', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'], self.product)
    
    # Rating tests
    def test_rating_valid(self):
        # Test add valid rating
        initial_reviewer = self.product.reviewer
        data = {'rating': 5}
        response = self.client.post(reverse('ven_shop:submit_rating', args=[self.product.id]), data)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.reviewer, initial_reviewer + 1)
    
    def test_rating_out_of_range(self):
        # Test rating out of valid range
        initial_reviewer = self.product.reviewer
        response = self.client.post(reverse('ven_shop:submit_rating', args=[self.product.id]), {'rating': 6})
        self.product.refresh_from_db()
        self.assertEqual(self.product.reviewer, initial_reviewer)
    
    def test_rating_invalid_value(self):
        # Test rating with invalid value
        initial_reviewer = self.product.reviewer
        response = self.client.post(reverse('ven_shop:submit_rating', args=[self.product.id]), {'rating': 'invalid'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.reviewer, initial_reviewer)