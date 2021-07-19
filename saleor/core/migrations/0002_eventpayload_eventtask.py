# Generated by Django 3.2.5 on 2021-07-16 15:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("webhook", "0007_auto_20210319_0945"),
        ("core", "0001_migrate_metadata"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventPayload",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("payload", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="EventTask",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("task_id", models.CharField(max_length=254)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("deleted", "Deleted"),
                        ],
                        max_length=50,
                    ),
                ),
                ("error", models.CharField(blank=True, max_length=254, null=True)),
                ("duration", models.FloatField()),
                ("event_type", models.CharField(max_length=254)),
                (
                    "event_payload",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="event_tasks",
                        to="core.eventpayload",
                    ),
                ),
                (
                    "webhook",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="webhook.webhook",
                    ),
                ),
            ],
        ),
    ]
