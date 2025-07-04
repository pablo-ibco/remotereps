# Generated by Django 4.2.7 on 2025-06-25 23:27

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Brand name', max_length=255, unique=True)),
                ('daily_budget', models.DecimalField(decimal_places=2, help_text='Daily budget limit in currency units', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('monthly_budget', models.DecimalField(decimal_places=2, help_text='Monthly budget limit in currency units', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Brand',
                'verbose_name_plural': 'Brands',
                'db_table': 'brands',
                'ordering': ['name'],
            },
        ),
    ]
