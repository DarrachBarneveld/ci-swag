# Generated by Django 4.2.10 on 2024-02-14 17:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(blank=True, max_length=254, null=True)),
                ('name', models.CharField(choices=[('junior_dev', 'Junior Dev'), ('mid_dev', 'Mid Dev'), ('senior_dev', 'Senior Dev')], default='junior_dev', max_length=20)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('mentor', models.BooleanField(default=False)),
                ('tutor_support', models.CharField(blank=True, choices=[('normal', 'Normal'), ('priority', 'Priority')], max_length=20)),
                ('color', models.CharField(choices=[('orange', 'Orange'), ('green', 'Green'), ('cyan', 'Cyan')], default='orange', max_length=20)),
                ('description', models.TextField(default='Junior Dev monthly subscription package')),
                ('free_delivery', models.BooleanField(default=True)),
                ('product_discount', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('program_discount', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='active_subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='active_subscription', to='profiles.subscription'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='profiles.subscription'),
        ),
    ]
