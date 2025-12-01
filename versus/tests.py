import json
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Challenge, Community, SportChoices


class VersusViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # User & Community (host)
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner", password="pass123")
        self.community = Community.objects.create(
            owner=self.owner,
            name="Public",
            primary_sport=SportChoices.SEPAK_BOLA,
            bio="Public community",
        )

        # Satu challenge default (OPEN)
        self.challenge = Challenge.objects.create(
            title="Uji Coba Match",
            sport=SportChoices.FUTSAL,
            match_category=Challenge.MatchCategory.LEAGUE,
            host=self.community,
            start_at=timezone.now() + timedelta(days=1),
            cost_per_person=0,
            prize_pool=0,
            venue_name="Gor ABC",
            players_joined=0,
            status=Challenge.Status.OPEN,
            description="Deskripsi uji",
            banner_url="https://example.com/banner.jpg",
        )

        # Simpan id & URL penting
        self.list_url = reverse("versus:list")
        self.create_url = reverse("versus:create")
        self.detail_url = reverse("versus:detail", args=[self.challenge.pk])
        self.api_list_url = reverse("versus:api_list")
        self.api_join_url = reverse("versus:api_join", args=[self.challenge.pk])

    def test_list_page_loads(self):
        #Halaman list harus 200 dan ada judul 'Versus'
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Versus")

    def test_list_page_filter_querystring_passthrough(self):
        #List page sendiri hanya render template dan JS akan fetch data.
        #Pastikan querystring tidak bikin error.
    
        resp = self.client.get(self.list_url + "?sport=futsal")
        self.assertEqual(resp.status_code, 200)

    def test_detail_valid(self):
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["ch"], self.challenge)
        self.assertContains(resp, self.challenge.title)

    def test_detail_invalid(self):
        resp = self.client.get(reverse("versus:detail", args=[999999]))
        self.assertEqual(resp.status_code, 404)

    def test_api_list_json(self):
        #API list mengembalikan JSON array berisi challenge.
        resp = self.client.get(self.api_list_url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Uji Coba Match")
        self.assertEqual(data[0]["sport"], SportChoices.FUTSAL)

    def test_api_list_filter_sport(self):
        #Filter ?sport= harus menyaring hasil.
        # Tambah satu challenge beda sport
        Challenge.create = Challenge.objects.create(
            title="Basket Fun",
            sport=SportChoices.BASKETBALL,
            match_category=Challenge.MatchCategory.LEAGUE,
            host=self.community,
            start_at=timezone.now() + timedelta(days=2),
            venue_name="Hall XYZ",
        )
        # Filter futsal -> hanya 1 (yang pertama)
        resp = self.client.get(self.api_list_url + "?sport=futsal")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["sport"], "futsal")

    def test_create_get_form(self):
        #GET create mengembalikan form.
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Buat Matchup")

    def test_create_post_valid(self):
        #POST create membuat Challenge baru dan redirect ke detail.
        payload = {
            "title": "Match Baru",
            "sport": SportChoices.SEPAK_BOLA,
            "match_category": Challenge.MatchCategory.LEAGUE,
            "start_at": (timezone.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M"),
            "venue_name": "Stadion A",
            "cost_per_person": 0,
            "prize_pool": 1000000,
            "description": "Coba deskripsi",
            "banner_url": "https://example.com/poster.jpg",
        }
        resp = self.client.post(self.create_url, data=payload, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Challenge.objects.filter(title="Match Baru").exists())

    def test_api_join_increment(self):
        #Join menambah players_joined +1 jika masih OPEN dan belum full.
        
        self.challenge.players_joined = 3
        self.challenge.status = Challenge.Status.OPEN
        self.challenge.save(update_fields=["players_joined", "status"])

        resp = self.client.post(self.api_join_url)
        self.assertIn(resp.status_code, (200, 201, 204))  
        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.players_joined, 4)
        self.assertEqual(self.challenge.status, Challenge.Status.OPEN)

    def test_api_join_close_when_full(self):
        #Saat mencapai max player, status otomatis menjadi CLOSED.
        #(Futsal max 10 -> dari 9 menjadi 10 & CLOSED)
        self.assertEqual(self.challenge.max_players, 10)  # futsal
        self.challenge.players_joined = 9
        self.challenge.status = Challenge.Status.OPEN
        self.challenge.save(update_fields=["players_joined", "status"])
        resp = self.client.post(self.api_join_url)
        self.assertIn(resp.status_code, (200, 201, 204))
        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.players_joined, 10)
        self.assertEqual(self.challenge.status, Challenge.Status.CLOSED)

    def test_api_join_ignored_if_closed(self):
        #Jika sudah CLOSED, join tidak menambah pemain.
        self.challenge.players_joined = 10
        self.challenge.status = Challenge.Status.CLOSED
        self.challenge.save(update_fields=["players_joined", "status"])

        before = self.challenge.players_joined
        resp = self.client.post(self.api_join_url)
        self.assertIn(resp.status_code, (200, 400))
        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.players_joined, before)
        self.assertEqual(self.challenge.status, Challenge.Status.CLOSED)
