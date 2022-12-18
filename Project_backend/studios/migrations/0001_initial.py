# Generated by Django 4.1.2 on 2022-12-09 06:42

import creditcards.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields
import phonenumber_field.modelfields
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0005_auto_20220424_2025'),
    ]

    operations = [
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('coach', models.CharField(max_length=100)),
                ('capacity', models.PositiveIntegerField()),
                ('description', models.TextField(blank=True, null=True)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('recurrences', multiselectfield.db.fields.MultiSelectField(choices=[('MO', 'Monday'), ('TU', 'Tuesday'), ('WE', 'Wednesday'), ('TH', 'Thursday'), ('FR', 'Friday'), ('SA', 'Saturday'), ('SU', 'Sunday')], max_length=20)),
                ('end_date', models.DateField()),
                ('keywords', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name_plural': 'classes',
            },
        ),
        migrations.CreateModel(
            name='ClassOccurrence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('day', models.CharField(max_length=2)),
                ('available', models.PositiveIntegerField()),
                ('cancelled', models.BooleanField()),
                ('class_fk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='occurrences', to='studios.class')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Studio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.CharField(max_length=200)),
                ('lon', models.DecimalField(decimal_places=6, max_digits=9)),
                ('lat', models.DecimalField(decimal_places=6, max_digits=9)),
                ('postal_code', models.CharField(max_length=6)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('frequency', models.CharField(choices=[('yearly', 'Yearly'), ('monthly', 'Monthly')], max_length=7)),
                ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('studio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='studios.studio')),
                ('subscribers', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StudioImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='studio_images/')),
                ('studio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='studios.studio')),
            ],
        ),
        migrations.CreateModel(
            name='StudioAmenity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField()),
                ('studio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amenities', to='studios.studio')),
            ],
            options={
                'verbose_name_plural': 'amenities',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cc_number', creditcards.models.CardNumberField(max_length=25)),
                ('cc_expiry', creditcards.models.CardExpiryField()),
                ('cc_code', creditcards.models.SecurityCodeField(max_length=4)),
                ('date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=6)),
                ('paid', models.BooleanField(default=False)),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='studios.subscription')),
            ],
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('all_occurrences', models.BooleanField()),
                ('available_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='studios.class')),
                ('occurrence', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='studios.classoccurrence')),
                ('user', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='class',
            name='studio',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='classes', to='studios.studio'),
        ),
    ]