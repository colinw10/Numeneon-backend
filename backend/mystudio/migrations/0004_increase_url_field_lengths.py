# Generated manually - increase URL field max_length

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mystudio', '0003_alter_myspaceprofile_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myspaceprofile',
            name='profile_song_album_art',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='myspaceprofile',
            name='profile_song_preview_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='playlistsong',
            name='album_art',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='playlistsong',
            name='preview_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
