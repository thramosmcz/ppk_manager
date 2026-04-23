from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pkapp', '0003_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='players',
            name='email',
            field=models.EmailField(max_length=40, blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='players',
            name='redesocial',
            field=models.CharField(max_length=30, blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='players',
            name='participacoes',
            field=models.IntegerField(default=0),
        ),
    ]
