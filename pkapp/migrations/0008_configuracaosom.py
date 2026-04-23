from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('pkapp', '0007_vincular_estrutura_blinds_torneios'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracaoSom',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('som_1min',    models.CharField(default='beep_low', max_length=20)),
                ('som_10sec',   models.CharField(default='tick',     max_length=20)),
                ('som_mudanca', models.CharField(default='fanfare',  max_length=20)),
                ('volume',      models.IntegerField(default=70)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='config_som',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'Configuração de Som'},
        ),
    ]
