from django.db import migrations


def vincular(apps, schema_editor):
    EstruturaBlinds = apps.get_model('pkapp', 'EstruturaBlinds')
    Torneios        = apps.get_model('pkapp', 'Torneios')

    eb = EstruturaBlinds.objects.filter(nome='Padrão 18 Níveis').first()
    if eb:
        Torneios.objects.update(estrutura_blinds=eb)


def desvincular(apps, schema_editor):
    Torneios = apps.get_model('pkapp', 'Torneios')
    Torneios.objects.update(estrutura_blinds=None)


class Migration(migrations.Migration):

    dependencies = [
        ('pkapp', '0006_seed_estrutura_blinds'),
    ]

    operations = [
        migrations.RunPython(vincular, desvincular),
    ]
