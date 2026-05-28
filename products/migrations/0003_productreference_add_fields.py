# Generated manual migration for ProductReference additions
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0002_rename_product_productreference"),
        ("suppliers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="productreference",
            name="supplier",
            field=models.ForeignKey(to="suppliers.Supplier", null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AddField(
            model_name="productreference",
            name="form",
            field=models.CharField(max_length=64, blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="productreference",
            name="strength",
            field=models.CharField(max_length=64, blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="productreference",
            name="pack_size",
            field=models.CharField(max_length=64, blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="productreference",
            name="packaging_notes",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="productreference",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="productreference",
            name="reference_image",
            field=models.ImageField(upload_to="product_references/", null=True, blank=True),
        ),
        migrations.AddField(
            model_name="productreference",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name="productreference",
            unique_together={("organization", "name")},
        ),
    ]
