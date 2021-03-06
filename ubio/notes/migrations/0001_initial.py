# Generated by Django 2.1.7 on 2019-03-20 18:11

from django.db import migrations, models
import django.db.models.deletion
import notes.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('profiles', '0004_auto_20190320_1122'),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('text', models.TextField()),
                ('document', models.FileField(upload_to=notes.models.get_note_full_path)),
                ('public', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.Profile')),
            ],
        ),
    ]
