import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from organizations.models import Organization
from products.models import ProductReference, ProductReferenceImage, DatasetGroup
from suppliers.models import Supplier

User = get_user_model()


@pytest.mark.django_db
class TestDatasetGroupAPI:
    def setup_method(self):
        self.org_one = Organization.objects.create(name="Dataset Org One")
        self.org_two = Organization.objects.create(name="Dataset Org Two")
        self.supplier = Supplier.objects.create(name="Dataset Supplier")

        self.product_one = ProductReference.objects.create(organization=self.org_one, name="Dataset Product One", sku="D-1", supplier=self.supplier)
        self.product_two = ProductReference.objects.create(organization=self.org_two, name="Dataset Product Two", sku="D-2", supplier=self.supplier)

        self.user_one = User.objects.create_user(username="dataset-user", password="pass", role="inspector", organization=self.org_one)
        self.admin = User.objects.create_user(username="dataset-admin", password="pass", role="admin", organization=self.org_one)

        self.image_one = ProductReferenceImage.objects.create(
            product_reference=self.product_one,
            image=self._sample_image("dataset-one.gif"),
            image_type="front_packaging",
            source="manual",
            uploaded_by=self.user_one,
        )
        self.image_two = ProductReferenceImage.objects.create(
            product_reference=self.product_two,
            image=self._sample_image("dataset-two.gif"),
            image_type="barcode",
            source="manual",
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

    def test_create_dataset_group_with_reference_images(self):
        token = self._get_token("dataset-user", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "name": "Training Set A",
            "description": "Reference images ready for annotation",
            "labeling_ready": True,
            "annotation_status": "in_progress",
            "quality_flag": "good",
            "reference_images": [self.image_one.id],
        }
        response = client.post("/api/dataset-groups/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["name"] == "Training Set A"
        assert body["labeling_ready"] is True
        assert body["reference_images_display"][0]["id"] == self.image_one.id

    def test_list_and_filter_dataset_groups_are_org_scoped(self):
        DatasetGroup.objects.create(
            organization=self.org_one,
            name="Org One Group",
            description="Scoped group",
            labeling_ready=False,
            annotation_status="pending",
            quality_flag="needs_review",
            created_by=self.user_one,
        )
        DatasetGroup.objects.create(
            organization=self.org_two,
            name="Org Two Group",
            description="Other scoped group",
            labeling_ready=True,
            annotation_status="completed",
            quality_flag="good",
            created_by=self.admin,
        )

        token = self._get_token("dataset-user", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/dataset-groups/")
        assert response.status_code == status.HTTP_200_OK
        names = {item["name"] for item in response.json()}
        assert names == {"Org One Group"}

        filtered = client.get("/api/dataset-groups/?labeling_ready=false")
        assert filtered.status_code == status.HTTP_200_OK
        assert len(filtered.json()) == 1

    def test_update_dataset_group_reference_images(self):
        token = self._get_token("dataset-user", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp = client.post(
            "/api/dataset-groups/",
            {
                "name": "Editable Group",
                "description": "Initial set",
                "reference_images": [self.image_one.id],
            },
            format="json",
        )
        assert create_resp.status_code == status.HTTP_201_CREATED
        group_id = create_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/dataset-groups/{group_id}/",
            {"reference_images": [self.image_one.id], "labeling_ready": True, "quality_flag": "good"},
            format="json",
        )
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.json()["labeling_ready"] is True
        assert patch_resp.json()["reference_images_display"][0]["id"] == self.image_one.id

    def test_cross_org_dataset_group_create_is_rejected(self):
        token = self._get_token("dataset-user", "pass")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            "/api/dataset-groups/",
            {
                "name": "Blocked Group",
                "reference_images": [self.image_two.id],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
