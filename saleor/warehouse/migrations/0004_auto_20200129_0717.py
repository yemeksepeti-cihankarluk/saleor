# Generated by Django 2.2.9 on 2020-01-29 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("warehouse", "0003_warehouse_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="warehouse", name="name", field=models.CharField(max_length=250),
        ),
    ]
