import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from organizations.models import Organization, Site
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
        resp = client.get("/api/products/products/")
        assert resp.status_code == status.HTTP_200_OK
        names = {p["name"] for p in resp.json()}
        assert names == {"Product A"}

    def test_create_product_sets_organization_and_prevents_duplicate(self):
        token = self._get_token("user-one", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {"name": "New Ref", "sku": "NR-01", "form": "tablet", "strength": "500 mg"}
        resp = client.post("/api/products/products/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "New Ref"
        # organization should be set to the authenticated user's organization
        assert data["organization"] == self.user_one.organization.id

        # Attempt to create duplicate name in same org
        resp2 = client.post("/api/products/products/", {"name": "New Ref"}, format="json")
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_without_organization_cannot_create(self):
        token = self._get_token("no-org", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = client.post("/api/products/products/", {"name": "Orphan"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
