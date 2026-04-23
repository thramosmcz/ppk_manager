from django.db import migrations


NIVEIS = [
    (1,   100,    200,  20, 0),
    (2,   100,    200,  20, 0),
    (3,   200,    400,  20, 0),
    (4,   200,    400,  20, 0),
    (5,   300,    600,  20, 0),
    (6,   300,    600,  20, 0),
    (7,   500,   1000,  20, 0),
    (8,   500,   1000,  20, 0),
    (9,  1000,   2000,  20, 0),
    (10, 1500,   3000,  20, 0),
    (11, 2000,   4000,  20, 10),
    (12, 2500,   5000,  20, 0),
    (13, 3000,   6000,  20, 0),
    (14, 4000,   8000,  20, 0),
    (15, 5000,  10000,  20, 0),
    (16, 10000, 20000,  20, 0),
    (17, 15000, 30000,  20, 0),
    (18, 20000, 40000,  20, 0),
]


def seed(apps, schema_editor):
    EstruturaBlinds = apps.get_model('pkapp', 'EstruturaBlinds')
    NivelBlind      = apps.get_model('pkapp', 'NivelBlind')

    eb = EstruturaBlinds.objects.create(
        nome='Padrão 18 Níveis',
        descricao='Estrutura padrão com 18 níveis, break de 10min após o nível 11.',
    )
    for nivel, sb, bb, dur, brk in NIVEIS:
        NivelBlind.objects.create(
            estrutura=eb,
            nivel=nivel,
            small_blind=sb,
            big_blind=bb,
            ante=0,
            duracao_minutos=dur,
            break_apos_minutos=brk,
        )


def unseed(apps, schema_editor):
    EstruturaBlinds = apps.get_model('pkapp', 'EstruturaBlinds')
    EstruturaBlinds.objects.filter(nome='Padrão 18 Níveis').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pkapp', '0005_estruturablinds_torneios_estrutura_blinds_nivelblind'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
