from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pkapp', '0002_auto_20220511_0854'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view_players',  models.BooleanField(default=True)),
                ('can_edit_players',  models.BooleanField(default=False)),
                ('can_view_torneios', models.BooleanField(default=True)),
                ('can_edit_torneios', models.BooleanField(default=False)),
                ('can_view_etapas',   models.BooleanField(default=True)),
                ('can_edit_etapas',   models.BooleanField(default=False)),
                ('can_view_ranking',  models.BooleanField(default=True)),
                ('can_manage_users',  models.BooleanField(default=False)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Perfil de Usuário',
                'verbose_name_plural': 'Perfis de Usuários',
            },
        ),
    ]
