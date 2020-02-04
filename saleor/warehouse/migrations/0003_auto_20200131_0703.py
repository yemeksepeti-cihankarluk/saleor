# Generated by Django 2.2.9 on 2020-01-31 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("warehouse", "0002_auto_20200123_0036")]

    operations = [
        migrations.AlterField(
            model_name="warehouse",
            name="shipping_zones",
            field=models.ManyToManyField(
                blank=True, related_name="warehouses", to="shipping.ShippingZone"
            ),
        )
    ]
