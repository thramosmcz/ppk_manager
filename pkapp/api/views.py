from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
import json

from pkapp.api.serializers import *
from pkapp.models import *


@api_view(['GET'])
def blinds_niveis(request, id):
    eb = get_object_or_404(EstruturaBlinds, id=id)
    niveis = list(eb.niveis.values(
        'nivel', 'small_blind', 'big_blind', 'ante',
        'duracao_minutos', 'break_apos_minutos'
    ))
    return Response(niveis)


@api_view(['GET', 'POST'])
def config_som(request):
    cfg, _ = ConfiguracaoSom.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        data = json.loads(request.body)
        cfg.som_1min    = data.get('som_1min',    cfg.som_1min)
        cfg.som_10sec   = data.get('som_10sec',   cfg.som_10sec)
        cfg.som_mudanca = data.get('som_mudanca', cfg.som_mudanca)
        cfg.volume      = int(data.get('volume',  cfg.volume))
        cfg.save()
    return Response({
        'som_1min':    cfg.som_1min,
        'som_10sec':   cfg.som_10sec,
        'som_mudanca': cfg.som_mudanca,
        'volume':      cfg.volume,
    })

PONTUACAO_POR_POSICAO = {1: 95, 2: 80, 3: 70, 4: 60, 5: 50, 6: 40, 7: 30, 8: 20, 9: 10}


class EtapaViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Etapas.objects.all()
        serializer = EtapaSerializer(queryset, many=True)

        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Etapas.objects.all()
        etapa = get_object_or_404(queryset, pk=pk)
        serializer = EtapaSerializer(etapa)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ranking(self, request, pk=None):
        qset_etapa = Etapas.objects.all()
        etapa = get_object_or_404(qset_etapa, pk=pk)

        qset_ranking = Ranking.objects.filter(id_etapa=etapa.id)
        serializer = RankingSerializer(qset_ranking, many=True)

        return Response(serializer.data)

    # @ranking.mapping.post
    # def update_ranking(self, request, pk=None):
    #     json_data = json.loads(request.body)
    #     body_ids = list(map(lambda j: j['id'], json_data))
    #
    #     qset_etapa = Etapas.objects.all()
    #     etapa = get_object_or_404(qset_etapa, pk=pk)
    #     db_ranking = Ranking.objects.filter(id_etapa=etapa.id).values()
    #     db_ids = list(map(lambda j: j['id'], db_ranking))
    #     print(body_ids)
    #     print(db_ids)
    #     print(set(body_ids).intersection(db_ids))
    #
    #     return Response("OK")

    @action(detail=True, methods=['post'])
    def inscrito(self, request, pk=None):
        json_data = json.loads(request.body)
        body_players_ids = list(map(lambda j: j['id'], json_data))

        qset_etapa = Etapas.objects.all()
        etapa = get_object_or_404(qset_etapa, pk=pk)

        qset_existing = Ranking.objects.filter(id_etapa=etapa.id, id_player__in=body_players_ids).values()
        to_create = body_players_ids.copy()
        for x in qset_existing:
            try:
                to_create.remove(x['id_player_id'])
            except ValueError:
                pass

        for id in to_create:
            r = Ranking(id_etapa=etapa, id_torneio=etapa.id_torneio, id_player=Players.objects.get(pk=id),
                        buy_inn=1, qtd_rebuy=0, posicao=0, pontuacao=0, premio=0)
            r.save()

        qset_ranking = Ranking.objects.filter(id_etapa=etapa.id, id_player__in=body_players_ids)
        serializer = RankingSerializer(qset_ranking, many=True)

        return Response(serializer.data)

    @inscrito.mapping.delete
    def inscrito_del(self, request, pk=None):
        json_data = json.loads(request.body)
        if isinstance(json_data, list):
            body_players_ids = list(map(lambda j: j['id'], json_data))
        else:
            body_players_ids = [json_data['id']]

        qset_etapa = Etapas.objects.all()
        etapa = get_object_or_404(qset_etapa, pk=pk)

        qset_existing = Ranking.objects.filter(id_etapa=etapa.id, id_player__in=body_players_ids).delete()

        qset_ranking = Ranking.objects.filter(id_etapa=etapa.id)
        serializer = RankingSerializer(qset_ranking, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def abrir(self, request, pk=None):
        """Abre a etapa (status I -> A)."""
        etapa = get_object_or_404(Etapas, pk=pk)
        if etapa.status != 'I':
            return Response({'error': 'Etapa não está inativa.'}, status=status.HTTP_400_BAD_REQUEST)
        etapa.status = 'A'
        etapa.save()
        return Response({'status': etapa.status})

    @action(detail=True, methods=['post'])
    def alterar_status(self, request, pk=None):
        """Altera o status da etapa para I, A ou F."""
        etapa = get_object_or_404(Etapas, pk=pk)
        novo  = json.loads(request.body).get('status')
        if novo not in ('I', 'A', 'F'):
            return Response({'error': 'Status inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        etapa.status = novo
        etapa.save()
        return Response({'status': etapa.status})

    @action(detail=True, methods=['post'])
    def rebuy(self, request, pk=None):
        """Adiciona rebuy a um player inscrito."""
        etapa = get_object_or_404(Etapas, pk=pk)
        torneio = etapa.id_torneio
        json_data = json.loads(request.body)
        player_id = json_data.get('player_id')

        ranking = get_object_or_404(Ranking, id_etapa=etapa, id_player_id=player_id)

        if ranking.qtd_rebuy >= torneio.qtd_rebuy:
            return Response({'error': 'Limite de rebuys atingido.'}, status=status.HTTP_400_BAD_REQUEST)

        ranking.qtd_rebuy += 1
        ranking.save()
        serializer = RankingSerializer(ranking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def eliminar(self, request, pk=None):
        """Elimina um player registrando posição e pontuação."""
        etapa = get_object_or_404(Etapas, pk=pk)
        json_data = json.loads(request.body)
        player_id = json_data.get('player_id')
        posicao   = json_data.get('posicao')

        if not posicao or posicao < 1:
            return Response({'error': 'Posição inválida.'}, status=status.HTTP_400_BAD_REQUEST)

        ranking = get_object_or_404(Ranking, id_etapa=etapa, id_player_id=player_id)

        if ranking.posicao != 0:
            return Response({'error': 'Player já foi eliminado.'}, status=status.HTTP_400_BAD_REQUEST)

        pontuacao = PONTUACAO_POR_POSICAO.get(posicao, 0)
        ranking.posicao   = posicao
        ranking.pontuacao = pontuacao
        ranking.save()

        # Verifica se todos os inscritos foram eliminados -> finaliza etapa
        todos_eliminados = not Ranking.objects.filter(id_etapa=etapa, posicao=0).exists()
        if todos_eliminados and Ranking.objects.filter(id_etapa=etapa).exists():
            etapa.status = 'F'
            etapa.save()

        serializer = RankingSerializer(ranking)
        resp = serializer.data
        resp['etapa_finalizada'] = todos_eliminados
        return Response(resp)

    def create(self, request):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass


class PlayerViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Players.objects.all().order_by('-participacoes')
        serializer = PlayerSerializer(queryset, many=True)

        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Players.objects.all()
        player = get_object_or_404(queryset, pk=pk)
        serializer = PlayerSerializer(player)
        return Response(serializer.data)

    def create(self, request):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass


class RankingViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Torneios.objects.all()
        serializer = TorneioSerializer(queryset, many=True)

        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Torneios.objects.all()
        torneio = get_object_or_404(queryset, pk=pk)
        serializer = TorneioSerializer(torneio)
        return Response(serializer.data)

    def create(self, request):
        print("create")
        return Response(json.dumps({'method': 'create'}))

    def update(self, request, pk=None):
        # print("update")
        json_data = json.loads(request.body)
        body_ranking_ids = list(map(lambda j: j['id'], json_data))
        for j in json_data:
            try:
                # print(j)
                r = Ranking.objects.get(pk=j['id'])
                r.buy_inn = j['buy_inn']
                r.qtd_rebuy = j['qtd_rebuy']
                r.posicao = j['posicao']
                r.pontuacao = j['pontuacao']
                r.premio = j['premio']
                r.save()
            except Ranking.DoesNotExist:
                pass

        # print(json_data)
        # print(body_ranking_ids)

        qset_ranking = Ranking.objects.filter(id__in=body_ranking_ids)
        serializer = RankingSerializer(qset_ranking, many=True)

        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        print("partial_update")
        return Response(json.dumps({'method': 'partial_update'}))

    def destroy(self, request, pk=None):
        print("destroy")
        return Response(json.dumps({'method': 'destroy'}))

    @action(methods=['get'], detail=True)
    def etapas(self, request, pk=None):
        qset_torneio = Torneios.objects.all()
        torneio = get_object_or_404(qset_torneio, pk=pk)

        qset_etapa = Etapas.objects.filter(id_torneio=torneio.id)
        serializer = EtapaSerializer(qset_etapa, many=True)

        return Response(serializer.data)


class TorneioViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Torneios.objects.all()
        serializer = TorneioSerializer(queryset, many=True)

        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Torneios.objects.all()
        torneio = get_object_or_404(queryset, pk=pk)
        serializer = TorneioSerializer(torneio)
        return Response(serializer.data)

    @action(methods=['get'], detail=True)
    def etapas(self, request, pk=None):
        qset_torneio = Torneios.objects.all()
        torneio = get_object_or_404(qset_torneio, pk=pk)

        qset_etapa = Etapas.objects.filter(id_torneio=torneio.id)
        serializer = EtapaSerializer(qset_etapa, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ranking(self, request, pk=None):
        qset_torneio = Torneios.objects.all()
        torneio = get_object_or_404(qset_torneio, pk=pk)

        qset_ranking = Ranking.objects.filter(id_torneio=torneio.id).order_by('id_etapa_id')
        serializer = RankingSerializer(qset_ranking, many=True)

        return Response(serializer.data)

    def create(self, request):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
