# Generated by Django 3.0.4 on 2020-03-31 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=400, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Kernels',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kernel_name', models.TextField()),
                ('kernel_url', models.CharField(max_length=500, unique=True)),
                ('last_run', models.DateTimeField()),
                ('users', models.ManyToManyField(to='events.Users')),
            ],
        ),
        migrations.CreateModel(
            name='Datasets',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dat_name', models.TextField()),
                ('dat_url', models.CharField(max_length=500, unique=True)),
                ('last_updated', models.DateTimeField()),
                ('disc_count', models.IntegerField()),
                ('kernel_count', models.IntegerField()),
                ('users', models.ManyToManyField(to='events.Users')),
            ],
        ),
    ]
