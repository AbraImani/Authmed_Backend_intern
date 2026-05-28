import pytest
from rest_framework.test import APIClient
from rest_framework import status

from organizations.models import Organization
from suppliers.models import Supplier
from products.models import ProductReference
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestProductReferenceAPI:
    def setup_method(self):
        self.org_one = Organization.objects.create(name="Org One")
        self.org_two = Organization.objects.create(name="Org Two")
        self.supplier = Supplier.objects.create(name="Acme Pharma")

        self.prod_one = ProductReference.objects.create(
            organization=self.org_one, name="Product A", sku="A001", supplier=self.supplier
        )
        self.prod_two = ProductReference.objects.create(
            organization=self.org_two, name="Product B", sku="B002", supplier=self.supplier
        )

        self.user_one = User.objects.create_user(username="user-one", password="pass", role="inspector", organization=self.org_one)
        self.user_no_org = User.objects.create_user(username="no-org", password="pass")

    def _get_token(self, username, password):
        client = APIClient()
        response = client.post("/api/auth/token/", {"username": username, "password": password}, format="json")
        assert response.status_code == status.HTTP_200_OK
        return response.json()["access"]

    def test_inspector_sees_only_own_organization_products(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = client.get("/api/products/")
        assert resp.status_code == status.HTTP_200_OK
        names = {p["name"] for p in resp.json()}
        assert names == {"Product A"}

    def test_product_payload_is_simple_and_predictable(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = client.get(f"/api/products/{self.prod_one.id}/")
        assert resp.status_code == status.HTTP_200_OK
        payload = resp.json()
        assert payload["id"] == self.prod_one.id
        assert payload["organization"] == self.org_one.id
        assert payload["organization_display"] == self.org_one.name
        assert payload["supplier"] == self.supplier.id
        assert payload["supplier_display"] == self.supplier.name
        assert payload["name"] == "Product A"
        assert payload["sku"] == "A001"
        assert payload["is_active"] is True

    def test_create_product_sets_organization_and_prevents_duplicate(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {"name": "New Ref", "sku": "NR-01", "form": "tablet", "strength": "500 mg"}
        resp = client.post("/api/products/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "New Ref"
        # organization should be set to the authenticated user's organization
        assert data["organization"] == self.user_one.organization.id

        # Attempt to create duplicate name in same org
        resp2 = client.post("/api/products/", {"name": "New Ref"}, format="json")
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_without_organization_cannot_create(self):
        token = self._get_token("no-org", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = client.post("/api/products/", {"name": "Orphan"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_scoping_blocks_cross_organization_detail_and_updates(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        own_detail = client.get(f"/api/products/{self.prod_one.id}/")
        assert own_detail.status_code == status.HTTP_200_OK

        other_detail = client.get(f"/api/products/{self.prod_two.id}/")
        assert other_detail.status_code == status.HTTP_404_NOT_FOUND

        patch_own = client.patch(f"/api/products/{self.prod_one.id}/", {"name": "Product A Updated"}, format="json")
        assert patch_own.status_code == status.HTTP_200_OK
        assert patch_own.json()["name"] == "Product A Updated"

        patch_other = client.patch(f"/api/products/{self.prod_two.id}/", {"name": "Should Not Work"}, format="json")
        assert patch_other.status_code == status.HTTP_404_NOT_FOUND
