from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from blog.models import Blog
import json

class BlogViewsTest(TestCase):
    def setUp(self):
        # Setup client, user, admin
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')

        # Buat contoh blog
        self.blog = Blog.objects.create(
            title='Test Blog',
            content='This is a test blog.',
            category='e-sports',
            user=self.user
        )

    # ------------------ SHOW ------------------
    def test_show_blogmain_accessible(self):
        response = self.client.get(reverse('blog:show_blogmain'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_blog.html')

    def test_show_blogmain_with_filter(self):
        response = self.client.get(reverse('blog:show_blogmain') + '?filter=e-sports')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Blog')

    # ------------------ ADD BLOG ------------------
    def test_add_blog_requires_login(self):
        response = self.client.get(reverse('blog:add_blog'))
        self.assertEqual(response.status_code, 302)  # redirect ke login

    def test_add_blog_ajax_non_superuser(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:add_blog_ajax'), {
            'title': 'Ajax Blog',
            'content': 'Testing AJAX blog creation',
            'category': 'sports'  # harus otomatis ke 'community posts'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['category'], 'community posts')

    def test_add_blog_ajax_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('blog:add_blog_ajax'), {
            'title': 'Admin Blog',
            'content': 'Admin test content',
            'category': 'sports'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['category'], 'sports')

    def test_add_blog_ajax_invalid_data(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:add_blog_ajax'), {
            'title': '',  # invalid
            'content': ''
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('title', data['errors'])
        self.assertIn('content', data['errors'])

    # ------------------ EDIT BLOG ------------------
    def test_edit_blog_owner(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:edit_blog', args=[self.blog.id]), {
            'title': 'Updated Title',
            'content': 'Updated content',
            'category': 'sports'
        })
        self.assertEqual(response.status_code, 302)
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.title, 'Updated Title')

    def test_edit_blog_forbidden_for_other_user(self):
        other_user = User.objects.create_user(username='other', password='123')
        self.client.login(username='other', password='123')
        response = self.client.get(reverse('blog:edit_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 403)
    def test_edit_blog_invalid_data(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:edit_blog', args=[self.blog.id]), {
            'title': '',
            'content': ''
        })
        self.assertEqual(response.status_code, 302)


    # ------------------ DELETE BLOG ------------------
    def test_delete_blog_post_request(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:delete_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Blog.objects.filter(pk=self.blog.id).exists())

    def test_delete_blog_forbidden_for_other_user(self):
        other_user = User.objects.create_user(username='other', password='123')
        self.client.login(username='other', password='123')
        response = self.client.post(reverse('blog:delete_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 403)

    def test_delete_blog_guest_redirect(self):
        response = self.client.post(reverse('blog:delete_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 302)  # redirect login

    # ------------------ JSON ------------------
    def test_show_json_returns_valid_json(self):
        response = self.client.get(reverse('blog:show_json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_show_json_by_id(self):
        response = self.client.get(reverse('blog:show_json_by_id', args=[self.blog.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Blog', response.content.decode())

    def test_show_json_by_id_not_found(self):
        response = self.client.get(reverse('blog:show_json_by_id', args=[999]))
        self.assertEqual(response.status_code, 404)

        
    def test_show_blog_post_comment_guest_redirect(self):
        response = self.client.post(reverse('blog:show_blog', args=[self.blog.id]), {
            'content': 'Nice blog!'
        })
        self.assertEqual(response.status_code, 302)  # redirect login

    def test_show_blog_post_comment_user(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:show_blog', args=[self.blog.id]), {
            'content': 'Nice blog!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.blog.comments.filter(content='Nice blog!').exists())

    def test_add_blog_ajax_get_request(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('blog:add_blog_ajax'))
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_show_xml_by_id_not_found(self):
        response = self.client.get(reverse('blog:show_xml_by_id', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_show_blogmain_other_filters(self):
        # sports
        response = self.client.get(reverse('blog:show_blogmain') + '?filter=sports')
        self.assertEqual(response.status_code, 200)
        # community posts
        response = self.client.get(reverse('blog:show_blogmain') + '?filter=community posts')
        self.assertEqual(response.status_code, 200)
        # my_blog sebagai guest
        response = self.client.get(reverse('blog:show_blogmain') + '?filter=my_blog')
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['posts'], [])
        # my_blog sebagai user
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('blog:show_blogmain') + '?filter=my_blog')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.blog, response.context['posts'])
        # unknown filter
        response = self.client.get(reverse('blog:show_blogmain') + '?filter=unknown')
        self.assertEqual(response.status_code, 200)

    def test_edit_blog_non_superuser_category_override(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:edit_blog', args=[self.blog.id]), {
            'title': 'Edited Title',
            'content': 'Edited content',
            'category': 'sports'  # akan di-override
        })
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.category, 'community posts')

    def test_show_blogmain_comment_count_annotation(self):
        response = self.client.get(reverse('blog:show_blogmain'))
        self.assertEqual(response.status_code, 200)
        for post in response.context['posts']:
            self.assertTrue(hasattr(post, 'comment_count'))
    def test_show_blog_get_request(self):
        response = self.client.get(reverse('blog:show_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog_detail.html')
        self.assertIn('form', response.context)
        self.assertIn('comments', response.context)


    def test_show_xml_returns_valid_xml(self):
        response = self.client.get(reverse('blog:show_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_add_blog_get_request(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('blog:add_blog'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_blog.html')
        self.assertIn('form', response.context)

    def test_edit_blog_superuser_category_kept(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('blog:edit_blog', args=[self.blog.id]), {
            'title': 'Admin Edited',
            'content': 'Admin content',
            'category': 'sports'
        })
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.category, 'sports') 

    def test_delete_blog_guest_object_not_deleted(self):
        response = self.client.post(reverse('blog:delete_blog', args=[self.blog.id]))
        self.assertTrue(Blog.objects.filter(pk=self.blog.id).exists())

    def test_show_xml_by_id_valid(self):
        response = self.client.get(reverse('blog:show_xml_by_id', args=[self.blog.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('<title>Test Blog</title>', response.content.decode())

    def test_add_blog_invalid_data_normal(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:add_blog'), {
            'title': '',
            'content': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'title', 'This field is required.')
        self.assertFormError(response, 'form', 'content', 'This field is required.')
    def test_show_json_empty(self):
        Blog.objects.all().delete()
        response = self.client.get(reverse('blog:show_json'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, [])

    def test_show_xml_empty(self):
        Blog.objects.all().delete()
        response = self.client.get(reverse('blog:show_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('<blogs></blogs>', response.content.decode())

    def test_show_blog_comment_count_annotation(self):
        response = self.client.get(reverse('blog:show_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(hasattr(response.context['comments'][0], 'blog'))

    def test_add_blog_normal_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('blog:add_blog'), {
            'title': 'Normal Superuser',
            'content': 'Content',
            'category': 'sports'
        })
        self.assertEqual(response.status_code, 302)
        blog = Blog.objects.get(title='Normal Superuser')
        self.assertEqual(blog.category, 'sports')

    def test_show_blogmain_filter_case_insensitive(self):
        response = self.client.get(reverse('blog:show_blogmain') + '?filter=Community Posts')
        self.assertEqual(response.status_code, 200)

    def test_delete_blog_get_request(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('blog:delete_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 302) 

    def test_add_blog_ajax_wrong_header(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:add_blog_ajax'), {
            'title': 'Test',
            'content': 'Test'
        }, HTTP_X_REQUESTED_WITH='WrongHeader')
        self.assertEqual(response.status_code, 400)

    def test_edit_blog_invalid_data_non_ajax(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('blog:edit_blog', args=[self.blog.id]), {
            'title': '',
            'content': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'title', 'This field is required.')

    def test_edit_blog_get_owner(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('blog:edit_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_blog.html')
        self.assertIn('form', response.context)