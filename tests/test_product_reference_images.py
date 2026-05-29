import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from organizations.models import Organization
from products.models import ProductReference, ProductReferenceImage
from suppliers.models import Supplier

User = get_user_model()


@pytest.mark.django_db
class TestProductReferenceImageAPI:
    def setup_method(self):
        self.org_one = Organization.objects.create(name="Org One")
        self.org_two = Organization.objects.create(name="Org Two")
        self.supplier = Supplier.objects.create(name="Acme Pharma")

        self.product_one = ProductReference.objects.create(
            organization=self.org_one,
            name="Product A",
            sku="A001",
            supplier=self.supplier,
        )
        self.product_two = ProductReference.objects.create(
            organization=self.org_two,
            name="Product B",
            sku="B002",
            supplier=self.supplier,
        )

        self.user_one = User.objects.create_user(
            username="user-one",
            password="pass",
            role="inspector",
            organization=self.org_one,
        )
        self.admin = User.objects.create_user(
            username="admin-user",
            password="pass",
            role="admin",
            organization=self.org_one,
        )
        self.no_org_user = User.objects.create_user(username="no-org", password="pass")

        self.image_one = self._sample_image("front.gif")
        self.image_two = self._sample_image("back.gif")
        self.other_image = self._sample_image("other.gif")

        self.reference_image_one = ProductReferenceImage.objects.create(
            product_reference=self.product_one,
            image=self.image_one,
            image_type="front_packaging",
            display_order=1,
            source="manual",
            notes="Front packaging image",
            uploaded_by=self.user_one,
        )
        self.reference_image_two = ProductReferenceImage.objects.create(
            product_reference=self.product_two,
            image=self.image_two,
            image_type="barcode",
            display_order=1,
            source="import",
            notes="Barcode image",
            uploaded_by=self.admin,
        )

    def _sample_image(self, name="sample.gif"):
        tiny_gif = (
            b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
            b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
        )
        return SimpleUploadedFile(name, tiny_gif, content_type="image/gif")

    def _get_token(self, username, password):
        client = APIClient()
        response = client.post("/api/auth/token/", {"username": username, "password": password}, format="json")
        assert response.status_code == status.HTTP_200_OK
        return response.json()["access"]

    def test_list_is_org_scoped(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/product-reference-images/")
        assert response.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in response.json()}
        assert ids == {self.reference_image_one.id}

    def test_retrieve_and_update_are_org_scoped(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        own_detail = client.get(f"/api/product-reference-images/{self.reference_image_one.id}/")
        assert own_detail.status_code == status.HTTP_200_OK
        assert own_detail.json()["product_reference"] == self.product_one.id

        other_detail = client.get(f"/api/product-reference-images/{self.reference_image_two.id}/")
        assert other_detail.status_code == status.HTTP_404_NOT_FOUND

        patch_response = client.patch(
            f"/api/product-reference-images/{self.reference_image_one.id}/",
            {"notes": "Updated front packaging image"},
            format="json",
        )
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.json()["notes"] == "Updated front packaging image"

    def test_create_product_reference_image(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "product_reference": self.product_one.id,
            "image": self._sample_image("label.gif"),
            "image_type": "label",
            "display_order": 2,
            "source": "manual",
            "notes": "Label photo",
        }
        response = client.post("/api/product-reference-images/", payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["product_reference"] == self.product_one.id
        assert body["image_type"] == "label"
        assert body["uploaded_by_display"]["username"] == "user-one"
        assert body["checksum"]
        assert body["image_url"]

    def test_create_rejects_cross_org_reference(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "product_reference": self.product_two.id,
            "image": self._sample_image("blocked.gif"),
            "image_type": "label",
        }
        response = client.post("/api/product-reference-images/", payload, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_extension_is_rejected(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "product_reference": self.product_one.id,
            "image": SimpleUploadedFile("bad.txt", b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff", content_type="image/gif"),
            "image_type": "label",
        }
        response = client.post("/api/product-reference-images/", payload, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_can_filter_by_organization_and_product_reference(self):
        token = self._get_token("admin-user", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get(f"/api/product-reference-images/?organization={self.org_two.id}")
        assert response.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in response.json()}
        assert ids == {self.reference_image_two.id}

        response_by_product = client.get(f"/api/product-reference-images/?product_reference={self.product_one.id}")
        assert response_by_product.status_code == status.HTTP_200_OK
        ids_by_product = {item["id"] for item in response_by_product.json()}
        assert ids_by_product == {self.reference_image_one.id}
