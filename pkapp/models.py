from django.db import models


# Create your models here.
class Players(models.Model):
    player = models.CharField(max_length=40)
    email = models.EmailField(max_length=40)
    redesocial = models.CharField(max_length=30)
    telefone = models.CharField(max_length=14)
    participacoes = models.IntegerField()

    def __str__(self):
        return self.player

    class Meta:
        ordering = ['player']


class Torneios(models.Model):
    torneio = models.CharField(max_length=30)
    qtd_etapas = models.IntegerField()
    qtd_rebuy = models.IntegerField()
    qtd_players = models.IntegerField()
    vlr_buyinn = models.DecimalField(max_digits=7, decimal_places=2)
    vlr_rebuy = models.DecimalField(max_digits=7, decimal_places=2)
    vlr_jackpot = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return self.torneio


class Etapas(models.Model):
    id_torneio = models.ForeignKey('Torneios', on_delete=models.PROTECT)
    etapa = models.CharField(max_length=30)
    local = models.CharField(max_length=30)
    data = models.DateField()
    status = models.CharField(max_length=1, default='I')

    def __str__(self):
        return self.etapa

    class Meta:
        ordering = ['data']


class Ranking(models.Model):
    id_torneio = models.ForeignKey('Torneios', on_delete=models.PROTECT)
    id_etapa = models.ForeignKey('Etapas', on_delete=models.PROTECT)
    id_player = models.ForeignKey('Players', on_delete=models.PROTECT)
    buy_inn = models.IntegerField()
    qtd_rebuy = models.IntegerField()
    posicao = models.IntegerField()
    pontuacao = models.IntegerField()
    premio = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return str(self.id)

class RankingTorneio(models.Model):
    id_torneio = models.ForeignKey('Torneios', on_delete=models.PROTECT)
    id_player  = models.ForeignKey('Players', on_delete=models.PROTECT)
    row_number = models.IntegerField()
    pontuacao = models.IntegerField()

    objects = models.Manager().raw(
             'select id_player_id, pontuacao, row_number() over '
                    '(partition by id_player_id order by pontuacao desc) '
               'from pkapp_ranking')

    def __str__(self):
        return str(self.id_torneio)

    class Meta:
        abstract = True
        managed  = False

