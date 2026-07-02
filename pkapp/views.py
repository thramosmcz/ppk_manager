from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Players, Torneios, Etapas, Ranking, UserProfile, EstruturaBlinds, NivelBlind
from .forms import (
    PlayersForm, TorneiosForm, EtapasForm, TorneiosRanking,
    AdmEtapaForm, LoginForm, UserCreateForm, UserProfileForm,
)
from .permissions import login_required_custom, permission_required

import pkapp.api.serializers


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'pkapp/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required_custom
def dashboard(request):
    torneio_id  = request.GET.get('torneio', '')
    torneios    = Torneios.objects.order_by('torneio')

    qs = Ranking.objects.all()
    if torneio_id and torneio_id.isdigit():
        qs = qs.filter(id_torneio_id=torneio_id)

    total_players  = Players.objects.count()
    total_torneios = Torneios.objects.count()
    total_etapas   = Etapas.objects.count()
    etapas_abertas = Etapas.objects.filter(status='A').count()

    # Top por participações
    top_participacoes = (
        qs.values('id_player__player')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    # Top por classificações (1º, 2º, 3º)
    top_classificacoes = (
        qs.filter(posicao__in=[1, 2, 3])
        .values('id_player__player')
        .annotate(
            primeiros=Count('id', filter=Q(posicao=1)),
            segundos =Count('id', filter=Q(posicao=2)),
            terceiros=Count('id', filter=Q(posicao=3)),
        )
        .order_by('-primeiros', '-segundos', '-terceiros')[:10]
    )

    # Top por resultado financeiro (premio - custo)
    top_resultado = []
    players_fin = (
        qs.values('id_player__player', 'id_player_id')
        .annotate(
            total_premio=Sum('premio'),
            total_buyins=Count('id'),
            total_rebuys=Sum('qtd_rebuy'),
        )
    )
    for p in players_fin:
        torneio_qs = Torneios.objects.filter(ranking__id_player_id=p['id_player_id'])
        if torneio_id and torneio_id.isdigit():
            torneio_qs = torneio_qs.filter(id=torneio_id)
        custo = 0.0
        for t in torneio_qs.distinct():
            r_player = qs.filter(id_player_id=p['id_player_id'], id_torneio=t)
            n_buyins = r_player.count()
            n_rebuys = r_player.aggregate(s=Sum('qtd_rebuy'))['s'] or 0
            custo += n_buyins * float(t.vlr_buyinn) + n_rebuys * float(t.vlr_rebuy)
        resultado = float(p['total_premio'] or 0) - custo
        top_resultado.append({
            'player':    p['id_player__player'],
            'premio':    float(p['total_premio'] or 0),
            'custo':     custo,
            'resultado': resultado,
        })
    top_resultado.sort(key=lambda x: x['resultado'], reverse=True)
    top_resultado = top_resultado[:10]

    context = {
        'total_players':      total_players,
        'total_torneios':     total_torneios,
        'total_etapas':       total_etapas,
        'etapas_abertas':     etapas_abertas,
        'torneios':           torneios,
        'torneio_id':         torneio_id,
        'top_participacoes':  top_participacoes,
        'top_classificacoes': top_classificacoes,
        'top_resultado':      top_resultado,
    }
    return render(request, 'pkapp/dashboard.html', context)


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

@permission_required('can_view_players')
def pkapp_players(request):
    players = Players.objects.annotate(
        total_pontos=Sum('ranking__pontuacao'),
        total_etapas=Count('ranking__id_etapa', distinct=True),
    ).order_by('player')
    return render(request, 'pkapp/players.html', {'players': players})


@permission_required('can_edit_players')
def player_create(request):
    if request.method == 'POST':
        form = PlayersForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Player adicionado com sucesso.')
        else:
            messages.error(request, 'Erro ao salvar player.')
    return redirect('pkapp_players')


@permission_required('can_edit_players')
def player_update(request, id):
    player = get_object_or_404(Players, id=id)
    if request.method == 'POST':
        form = PlayersForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, 'Player atualizado.')
        else:
            erros = '; '.join(
                f"{campo}: {', '.join(msgs)}" for campo, msgs in form.errors.items()
            )
            messages.error(request, f'Erro ao atualizar player: {erros}')
    return redirect('pkapp_players')


@permission_required('can_edit_players')
def player_delete(request, id):
    player = get_object_or_404(Players, id=id)
    if request.method == 'POST':
        participacoes = Ranking.objects.filter(id_player=player).count()
        if participacoes > 0:
            messages.error(request, f'"{player.player}" não pode ser removido: possui {participacoes} participação(ões) registrada(s).')
        else:
            player.delete()
            messages.success(request, f'Player "{player.player}" removido.')
    return redirect('pkapp_players')


# ---------------------------------------------------------------------------
# Torneios
# ---------------------------------------------------------------------------

@permission_required('can_view_torneios')
def pkapp_torneios(request):
    torneios = Torneios.objects.annotate(
        num_etapas=Count('etapas', distinct=True),
        num_players=Count('ranking__id_player', distinct=True),
    ).order_by('torneio')
    estruturas_blinds = EstruturaBlinds.objects.all()
    return render(request, 'pkapp/torneios.html', {
        'torneios': torneios,
        'estruturas_blinds': estruturas_blinds,
    })


@permission_required('can_edit_torneios')
def torneio_create(request):
    if request.method == 'POST':
        form = TorneiosForm(request.POST)
        if form.is_valid():
            torneio = form.save(commit=False)
            eb_id = request.POST.get('estrutura_blinds')
            torneio.estrutura_blinds = EstruturaBlinds.objects.filter(id=eb_id).first() if eb_id else None
            torneio.save()
            messages.success(request, 'Torneio criado com sucesso.')
        else:
            messages.error(request, 'Erro ao criar torneio.')
    return redirect('pkapp_torneios')


@permission_required('can_edit_torneios')
def torneio_update(request, id):
    torneio = get_object_or_404(Torneios, id=id)
    if request.method == 'POST':
        form = TorneiosForm(request.POST, instance=torneio)
        if form.is_valid():
            t = form.save(commit=False)
            eb_id = request.POST.get('estrutura_blinds')
            t.estrutura_blinds = EstruturaBlinds.objects.filter(id=eb_id).first() if eb_id else None
            t.save()
            messages.success(request, 'Torneio atualizado.')
        else:
            messages.error(request, 'Erro ao atualizar torneio.')
    return redirect('pkapp_torneios')


@permission_required('can_edit_torneios')
def torneio_delete(request, id):
    torneio = get_object_or_404(Torneios, id=id)
    if request.method == 'POST':
        try:
            torneio.delete()
            messages.success(request, f'Torneio "{torneio.torneio}" removido.')
        except Exception:
            messages.error(request, 'Não é possível remover: torneio possui registros vinculados.')
    return redirect('pkapp_torneios')


# ---------------------------------------------------------------------------
# Etapas
# ---------------------------------------------------------------------------

@permission_required('can_view_etapas')
def pkapp_etapas(request):
    torneios   = Torneios.objects.all()
    torneio_id = request.GET.get('torneio', '').strip()
    if not torneio_id or not torneio_id.isdigit():
        torneio_id = None
    etapas = Etapas.objects.select_related('id_torneio').order_by('-data')
    if torneio_id:
        etapas = etapas.filter(id_torneio=torneio_id)
    return render(request, 'pkapp/etapas.html', {
        'etapas': etapas, 'torneios': torneios, 'torneio_id': torneio_id,
    })


@permission_required('can_view_etapas')
def ranking_etapa(request, id):
    etapa   = get_object_or_404(Etapas.objects.select_related('id_torneio'), id=id)
    torneio = etapa.id_torneio

    if request.method == 'POST' and request.user.is_superuser:
        # Salva edições linha a linha
        for key, val in request.POST.items():
            if key.startswith('posicao_'):
                rid = key.split('_')[1]
                try:
                    r = Ranking.objects.get(id=rid, id_etapa=etapa)
                    r.posicao   = int(request.POST.get(f'posicao_{rid}', r.posicao) or 0)
                    r.pontuacao = int(request.POST.get(f'pontuacao_{rid}', r.pontuacao) or 0)
                    premio_raw  = request.POST.get(f'premio_{rid}', str(r.premio)) or '0'
                    r.premio    = float(premio_raw.replace(',', '.'))
                    r.save()
                except (Ranking.DoesNotExist, ValueError):
                    pass
        messages.success(request, 'Ranking da etapa atualizado.')
        return redirect('ranking_etapa', id=id)

    inscritos = (
        Ranking.objects
        .filter(id_etapa=etapa)
        .select_related('id_player')
        .order_by('posicao', 'id_player__player')
    )

    # Financeiro
    from django.db.models import Sum as _Sum
    total_buyins = inscritos.count()
    total_rebuys = inscritos.aggregate(t=_Sum('qtd_rebuy'))['t'] or 0
    vlr_buyinn  = float(torneio.vlr_buyinn)
    vlr_rebuy   = float(torneio.vlr_rebuy)
    vlr_txadm   = float(torneio.vlr_txadm)
    vlr_jackpot = float(torneio.vlr_jackpot)
    txadm       = total_buyins * vlr_txadm
    # Arrecadado = (buyins × vlr_buyinn) + (rebuys × vlr_rebuy) + (buyins × vlr_txadm)
    arrecadado  = total_buyins * vlr_buyinn + total_rebuys * vlr_rebuy + txadm
    jackpot     = (total_buyins + total_rebuys) * vlr_jackpot
    prizepool   = arrecadado - jackpot - txadm

    return render(request, 'pkapp/ranking_etapa.html', {
        'etapa':      etapa,
        'torneio':    torneio,
        'inscritos':  inscritos,
        'prizepool':  prizepool,
        'payout_1':   round(prizepool * 0.50, 2),
        'payout_2':   round(prizepool * 0.30, 2),
        'payout_3':   round(prizepool * 0.20, 2),
    })


@permission_required('can_edit_etapas')
def etapa_create(request):
    torneio_id = request.POST.get('torneio_filtro') or request.GET.get('torneio')
    if request.method == 'POST':
        form = EtapasForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Etapa criada com sucesso.')
        else:
            messages.error(request, 'Erro ao criar etapa.')
    url = f'/pkapp/etapas?torneio={torneio_id}' if torneio_id else '/pkapp/etapas'
    return redirect(url)


@permission_required('can_edit_etapas')
def etapa_update(request, id):
    etapa      = get_object_or_404(Etapas, id=id)
    torneio_id = request.POST.get('torneio_filtro')
    if request.method == 'POST':
        form = EtapasForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Etapa atualizada.')
        else:
            messages.error(request, 'Erro ao atualizar etapa.')
    url = f'/pkapp/etapas?torneio={torneio_id}' if torneio_id else '/pkapp/etapas'
    return redirect(url)


@permission_required('can_edit_etapas')
def etapa_delete(request, id):
    etapa      = get_object_or_404(Etapas, id=id)
    torneio_id = request.POST.get('torneio_filtro')
    if request.method == 'POST':
        try:
            etapa.delete()
            messages.success(request, f'Etapa "{etapa.etapa}" removida.')
        except Exception:
            messages.error(request, 'Não é possível remover: etapa possui registros vinculados.')
    url = f'/pkapp/etapas?torneio={torneio_id}' if torneio_id else '/pkapp/etapas'
    return redirect(url)


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
         'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']


def _calcular_ranking_com_descarte(torneio):
    """
    Regra de negócio extraída do poker-0.0.1-SNAPSHOT.jar:
    - Pontuação por mês (etapa) para cada jogador.
    - Preenche com 0 os meses sem participação.
    - Descarta as 3 menores pontuações.
    - Total = soma das demais.
    Critérios de desempate (em ordem): 1º lugares, 2º lugares, 3º lugares.
    Retorna também acumulado, jackpot e taxa de administração do torneio.
    """
    from collections import defaultdict

    registros = (
        Ranking.objects
        .filter(id_torneio=torneio)
        .select_related('id_player', 'id_etapa')
        .order_by('id_player', 'id_etapa__data')
    )

    # pontos_por_mes[player_id][mes(1-12)] = pontuacao
    pontos_por_mes    = defaultdict(lambda: defaultdict(int))
    premio_por_player = defaultdict(float)
    vitorias          = defaultdict(lambda: defaultdict(int))  # vitorias[player_id][posicao]
    nomes = {}

    total_buy_inn = 0
    total_rebuy   = 0

    for r in registros:
        mes = r.id_etapa.data.month
        pontos_por_mes[r.id_player.id][mes] += r.pontuacao
        premio_por_player[r.id_player.id]   += float(r.premio)
        nomes[r.id_player.id] = r.id_player.player
        total_buy_inn += r.buy_inn
        total_rebuy   += r.qtd_rebuy
        if r.posicao in (1, 2, 3):
            vitorias[r.id_player.id][r.posicao] += 1

    # Financeiro (mesma fórmula do JAR)
    vlr_buyinn  = float(torneio.vlr_buyinn)
    vlr_rebuy   = float(torneio.vlr_rebuy)
    vlr_jackpot = float(torneio.vlr_jackpot)
    vlr_txadm   = float(torneio.vlr_txadm)

    acumulado = (total_buy_inn * vlr_buyinn) + (total_rebuy * vlr_rebuy) + (total_buy_inn * vlr_txadm)
    jackpot   = (total_buy_inn + total_rebuy) * vlr_jackpot
    taxa_adm  = total_buy_inn * vlr_txadm

    ranking = []
    for player_id, meses_dict in pontos_por_mes.items():
        # Lista de 12 pontuações (índice 0 = janeiro)
        pontos_12 = [meses_dict.get(m, 0) for m in range(1, 13)]

        # Descarte: remove as 3 menores
        pontos_ordenados = sorted(pontos_12)
        total = sum(pontos_ordenados[3:])

        # Marca quais meses foram descartados
        descartados_restantes = pontos_ordenados[:3][:]
        pontos_meses_marcados = []
        for p in pontos_12:
            if p in descartados_restantes:
                pontos_meses_marcados.append((p, True))
                descartados_restantes.remove(p)
            else:
                pontos_meses_marcados.append((p, False))

        p1 = vitorias[player_id].get(1, 0)
        p2 = vitorias[player_id].get(2, 0)
        p3 = vitorias[player_id].get(3, 0)

        ranking.append({
            'player':       nomes[player_id],
            'pontos_meses': pontos_meses_marcados,
            'total_pontos': total,
            'total_premio': premio_por_player[player_id],
            'primeiros':    p1,
            'segundos':     p2,
            'terceiros':    p3,
        })

    # Ordenação: total desc, desempate por 1º, 2º, 3º lugares
    ranking.sort(key=lambda x: (x['total_pontos'], x['primeiros'], x['segundos'], x['terceiros']), reverse=True)

    return ranking, {
        'acumulado': acumulado,
        'jackpot':   jackpot,
        'taxa_adm':  taxa_adm,
    }


@permission_required('can_view_ranking')
def pkapp_ranking(request):
    torneios    = Torneios.objects.all()
    torneio_id  = request.GET.get('torneio')
    ranking     = []
    torneio_sel = None
    financeiro  = {}
    if torneio_id:
        try:
            torneio_sel = Torneios.objects.get(pk=torneio_id)
            ranking, financeiro = _calcular_ranking_com_descarte(torneio_sel)
        except Torneios.DoesNotExist:
            pass
    return render(request, 'pkapp/ranking.html', {
        'torneios':   torneios,
        'ranking':    ranking,
        'torneio_sel': torneio_sel,
        'financeiro': financeiro,
        'meses':      MESES,
    })


@login_required_custom
def pontuacao_global(request):
    return redirect('pkapp_ranking')


# ---------------------------------------------------------------------------
# Gestão de Usuários
# ---------------------------------------------------------------------------

@permission_required('can_manage_users')
def user_list(request):
    users = User.objects.select_related('profile').order_by('username')
    return render(request, 'pkapp/user_list.html', {'users': users})


@permission_required('can_manage_users')
def user_create(request):
    user_form    = UserCreateForm(request.POST or None)
    profile_form = UserProfileForm(request.POST or None)
    if request.method == 'POST' and user_form.is_valid() and profile_form.is_valid():
        user = user_form.save()
        profile = user.profile  # criado pelo signal
        profile_form = UserProfileForm(request.POST, instance=profile)
        profile_form.save()
        messages.success(request, f'Usuário {user.username} criado com sucesso.')
        return redirect('user_list')
    return render(request, 'pkapp/user_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'action': 'Criar',
    })


@permission_required('can_manage_users')
def user_edit(request, id):
    user    = get_object_or_404(User, id=id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile_form = UserProfileForm(request.POST or None, instance=profile)
    # Formulário simples para dados básicos do usuário
    if request.method == 'POST':
        # atualiza nome/email manualmente
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name', user.last_name)
        user.email      = request.POST.get('email', user.email)
        is_active       = request.POST.get('is_active')
        user.is_active  = bool(is_active)

        nova_senha = request.POST.get('nova_senha', '').strip()
        confirma   = request.POST.get('confirma_senha', '').strip()
        if nova_senha:
            if len(nova_senha) < 6:
                messages.error(request, 'A nova senha deve ter pelo menos 6 caracteres.')
                return redirect('user_edit', id=id)
            if nova_senha != confirma:
                messages.error(request, 'A confirmação de senha não confere.')
                return redirect('user_edit', id=id)
            user.set_password(nova_senha)

        user.save()
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, f'Usuário {user.username} atualizado.')
            return redirect('user_list')
    return render(request, 'pkapp/user_form.html', {
        'edit_user': user,
        'profile_form': profile_form,
        'action': 'Editar',
    })


@login_required_custom
def meu_perfil(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'dados':
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name  = request.POST.get('last_name', '').strip()
            user.email      = request.POST.get('email', '').strip()
            user.save()
            messages.success(request, 'Dados atualizados com sucesso.')

        elif action == 'senha':
            senha_atual = request.POST.get('senha_atual', '')
            nova_senha  = request.POST.get('nova_senha', '')
            confirma    = request.POST.get('confirma_senha', '')
            if not user.check_password(senha_atual):
                messages.error(request, 'Senha atual incorreta.')
            elif len(nova_senha) < 6:
                messages.error(request, 'A nova senha deve ter pelo menos 6 caracteres.')
            elif nova_senha != confirma:
                messages.error(request, 'A confirmação de senha não confere.')
            else:
                user.set_password(nova_senha)
                user.save()
                # re-autentica para não deslogar
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, 'Senha alterada com sucesso.')

        return redirect('meu_perfil')

    return render(request, 'pkapp/meu_perfil.html', {'edit_user': user})


@permission_required('can_manage_users')
def user_toggle_active(request, id):
    user = get_object_or_404(User, id=id)
    if user == request.user:
        messages.error(request, 'Você não pode desativar sua própria conta.')
    else:
        user.is_active = not user.is_active
        user.save()
        status = 'ativado' if user.is_active else 'desativado'
        messages.success(request, f'Usuário {user.username} {status}.')
    return redirect('user_list')


# ---------------------------------------------------------------------------
# Estrutura de Blinds
# ---------------------------------------------------------------------------

@permission_required('can_edit_torneios')
def estrutura_blinds_list(request):
    # Ação de vínculo em massa via POST
    if request.method == 'POST' and request.POST.get('action') == 'vincular_todos':
        eb_id = request.POST.get('eb_id')
        if eb_id:
            eb = EstruturaBlinds.objects.filter(id=eb_id).first()
            if eb:
                count = Torneios.objects.filter(estrutura_blinds__isnull=True).update(estrutura_blinds=eb)
                # Se quiser vincular TODOS (inclusive os que já têm):
                # count = Torneios.objects.update(estrutura_blinds=eb)
                messages.success(request, f'Estrutura "{eb.nome}" vinculada a {count} torneio(s).')
            else:
                messages.error(request, 'Estrutura não encontrada.')
        return redirect('estrutura_blinds_list')

    estruturas = EstruturaBlinds.objects.prefetch_related('niveis').all()
    return render(request, 'pkapp/estrutura_blinds.html', {'estruturas': estruturas})

@permission_required('can_edit_torneios')
def estrutura_blinds_create(request):
    if request.method == 'POST':
        nome      = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        if not nome:
            messages.error(request, 'Informe um nome para a estrutura.')
            return redirect('estrutura_blinds_list')
        eb = EstruturaBlinds.objects.create(nome=nome, descricao=descricao)
        _salvar_niveis(request, eb)
        messages.success(request, f'Estrutura "{eb.nome}" criada.')
    return redirect('estrutura_blinds_list')


@permission_required('can_edit_torneios')
def estrutura_blinds_update(request, id):
    eb = get_object_or_404(EstruturaBlinds, id=id)
    if request.method == 'POST':
        eb.nome      = request.POST.get('nome', eb.nome).strip()
        eb.descricao = request.POST.get('descricao', '').strip()
        eb.save()
        eb.niveis.all().delete()
        _salvar_niveis(request, eb)
        messages.success(request, f'Estrutura "{eb.nome}" atualizada.')
    return redirect('estrutura_blinds_list')


@permission_required('can_edit_torneios')
def estrutura_blinds_delete(request, id):
    eb = get_object_or_404(EstruturaBlinds, id=id)
    if request.method == 'POST':
        try:
            eb.delete()
            messages.success(request, f'Estrutura "{eb.nome}" removida.')
        except Exception:
            messages.error(request, 'Não é possível remover: estrutura está vinculada a um torneio.')
    return redirect('estrutura_blinds_list')


def _salvar_niveis(request, eb):
    """Lê os arrays de campos do POST e cria os NivelBlind."""
    sbs   = request.POST.getlist('small_blind')
    bbs   = request.POST.getlist('big_blind')
    antes = request.POST.getlist('ante')
    durs  = request.POST.getlist('duracao_minutos')
    brks  = request.POST.getlist('break_apos_minutos')
    for i, (sb, bb, ante, dur, brk) in enumerate(zip(sbs, bbs, antes, durs, brks), start=1):
        NivelBlind.objects.create(
            estrutura=eb, nivel=i,
            small_blind=int(sb or 0), big_blind=int(bb or 0),
            ante=int(ante or 0),
            duracao_minutos=int(dur or 20),
            break_apos_minutos=int(brk or 0),
        )


# ---------------------------------------------------------------------------
# Administração de Etapa
# ---------------------------------------------------------------------------

PONTUACAO_POR_POSICAO = {1: 95, 2: 80, 3: 70, 4: 60, 5: 50, 6: 40, 7: 30, 8: 20, 9: 10}


@permission_required('can_edit_etapas')
def adm_etapa(request, id):
    etapa   = get_object_or_404(Etapas.objects.select_related('id_torneio'), id=id)
    torneio = etapa.id_torneio

    inscritos = (
        Ranking.objects
        .filter(id_etapa=etapa)
        .select_related('id_player')
        .order_by('id_player__player')
    )
    inscritos_ids = inscritos.values_list('id_player_id', flat=True)

    players_disponiveis = Players.objects.exclude(id__in=inscritos_ids).order_by('player')

    context = {
        'etapa':               etapa,
        'torneio':             torneio,
        'inscritos':           inscritos,
        'players_disponiveis': players_disponiveis,
        'max_players':         torneio.qtd_players,
        'max_rebuy':           torneio.qtd_rebuy,
        'total_inscritos':     inscritos.count(),
        'pontuacao_tabela':    PONTUACAO_POR_POSICAO,
    }
    return render(request, 'pkapp/adm_etapa.html', context)


@permission_required('can_view_etapas')
def poker_clock(request, id):
    etapa   = get_object_or_404(Etapas.objects.select_related('id_torneio'), id=id)
    torneio = etapa.id_torneio

    inscritos = (
        Ranking.objects
        .filter(id_etapa=etapa)
        .select_related('id_player')
        .order_by('id_player__player')
    )

    ativos     = inscritos.filter(posicao=0)
    eliminados = inscritos.exclude(posicao=0).order_by('posicao')

    total_buyins = inscritos.count()
    total_rebuys = inscritos.aggregate(Sum('qtd_rebuy'))['qtd_rebuy__sum'] or 0

    vlr_buyinn  = float(torneio.vlr_buyinn)
    vlr_rebuy   = float(torneio.vlr_rebuy)
    vlr_txadm   = float(torneio.vlr_txadm)
    vlr_jackpot = float(torneio.vlr_jackpot)

    total_valor_buyins = total_buyins * vlr_buyinn
    total_valor_rebuys = total_rebuys * vlr_rebuy
    txadm     = total_buyins * vlr_txadm
    jackpot   = (total_buyins + total_rebuys) * vlr_jackpot
    arrecadado = total_valor_buyins + total_valor_rebuys + txadm
    prizepool  = arrecadado - txadm - jackpot

    # Estrutura de blinds vinculada ao torneio
    niveis_blinds = []
    if torneio.estrutura_blinds:
        niveis_blinds = list(
            torneio.estrutura_blinds.niveis.values(
                'nivel', 'small_blind', 'big_blind', 'ante',
                'duracao_minutos', 'break_apos_minutos'
            )
        )

    import json as _json
    context = {
        'etapa':              etapa,
        'torneio':            torneio,
        'ativos':             ativos,
        'eliminados':         eliminados,
        'total_ativos':       ativos.count(),
        'total_inscritos':    total_buyins,
        'total_rebuys':       total_rebuys,
        'total_valor_buyins': total_valor_buyins,
        'total_valor_rebuys': total_valor_rebuys,
        'txadm':              txadm,
        'total_arrecadado':   total_valor_buyins + total_valor_rebuys + txadm,
        'jackpot':            jackpot,
        'prizepool':          prizepool,
        'payout_1':           prizepool * 0.50,
        'payout_2':           prizepool * 0.30,
        'payout_3':           prizepool * 0.20,
        'niveis_blinds_json': _json.dumps(niveis_blinds),
    }
    return render(request, 'pkapp/poker_clock.html', context)


# ---------------------------------------------------------------------------
# React (mantido)
# ---------------------------------------------------------------------------

def pkapp_react(request):
    return render(request, 'pkapp/react.html')
