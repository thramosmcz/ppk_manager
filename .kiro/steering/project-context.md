# PKTOUR — Contexto do Projeto

## O que é
Sistema web de gerenciamento de torneios de poker. Controla players, torneios, etapas, ranking e usuários. Roda em produção na AWS EC2.

## Stack
- **Backend:** Python 3.8 + Django 3.0 + Django REST Framework
- **Banco:** SQLite (arquivo em `/home/thramos/pktour/db.sqlite3` no servidor)
- **Servidor:** Gunicorn + Nginx na EC2 Ubuntu 22.04 (t2.micro), usuário `thramos`
- **Frontend:** Templates Django com Bootstrap 4 + tema dark customizado. Bundle React legado em `pkapp/static/pkapp/` não é a interface principal.
- **Autenticação:** Sistema próprio sobre `django.contrib.auth`, sem usar o admin do Django na interface.

## Estrutura de Diretórios
```
pkproject/          # configurações Django (settings.py, urls.py)
pkapp/              # app principal
  models.py         # todos os models
  views.py          # todas as views (auth, CRUD, dashboard, perfil)
  urls.py           # rotas do app
  forms.py          # formulários Django
  permissions.py    # decorators login_required_custom e permission_required
  signals.py        # cria UserProfile automaticamente ao criar User
  api/              # REST API (DRF ViewSets)
    views.py        # usa request.data (não json.loads) em todos os endpoints
    serializers.py
    urls.py
  templates/pkapp/  # todos os templates HTML
  middleware/cors.py
  migrations/       # última: 0008_configuracaosom.py
data/
  db.sqlite3        # banco local de desenvolvimento
.env                # variáveis de ambiente — NÃO commitar (está no .gitignore)
.env.example        # template com as variáveis necessárias
deploy_aws_ec2.txt  # anotações de deploy — NÃO commitar (está no .gitignore)
```

## Models principais
| Model | Descrição |
|---|---|
| `Players` | Jogadores. Ordenados por `player`. Campo `participacoes` é incrementado a cada inscrição via API. |
| `Torneios` | Torneios. Ordenados por `torneio` (alfabético). FK para `EstruturaBlinds`. |
| `Etapas` | Etapas de um torneio. Status: `I`=Inativo, `A`=Aberto, `F`=Finalizado. Ordenadas por `data`. |
| `Ranking` | Resultado de cada player por etapa: buy_inn, qtd_rebuy, posicao, pontuacao, premio. |
| `UserProfile` | Extensão do User com permissões granulares. Criado via signal ao criar User. |
| `EstruturaBlinds` | Estrutura de níveis de blind vinculada a um torneio. |
| `NivelBlind` | Cada nível: SB, BB, ante, duração, break. |
| `ConfiguracaoSom` | Preferências de som do poker clock por usuário. |

## Sistema de Permissões
Decorators em `pkapp/permissions.py`:
- `@login_required_custom` — exige login
- `@permission_required('campo')` — verifica campo booleano no `UserProfile`

Superusers têm acesso total. Campos do `UserProfile`:
`can_view_players`, `can_edit_players`, `can_view_torneios`, `can_edit_torneios`, `can_view_etapas`, `can_edit_etapas`, `can_view_ranking`, `can_manage_users`

## URLs principais
```
/                               → dashboard (com filtro por torneio)
/login/ /logout/
/pkapp/players                  → lista de players
/pkapp/torneios                 → lista de torneios
/pkapp/etapas                   → lista de etapas
/pkapp/etapas/<id>/ranking/     → ranking da etapa (editável por superuser)
/pkapp/blinds/                  → estruturas de blinds
/pkapp/ranking                  → ranking por torneio (com desempate)
/pkapp/usuarios/                → gestão de usuários (requer can_manage_users)
/pkapp/perfil/                  → perfil do usuário logado (dados + senha)
/pkapp/admetapa/<id>/           → administração de etapa (inscrição, rebuy, eliminar)
/pkapp/clock/<id>/              → poker clock da etapa
/pkapp/api/                     → REST API (DRF)
```

## REST API
Base: `/pkapp/api/`
| Endpoint | Método | Descrição |
|---|---|---|
| `etapas/<id>/inscrito/` | POST | Inscreve players; incrementa `participacoes` |
| `etapas/<id>/inscrito/` | DELETE | Remove inscrição |
| `etapas/<id>/rebuy/` | POST | Adiciona rebuy |
| `etapas/<id>/rebuy/` | DELETE | Remove rebuy (desfaz erro) |
| `etapas/<id>/eliminar/` | POST | Elimina player; posição calculada automaticamente pelo nº de ativos no banco; calcula prêmio 50/30/20% do prizepool para top 3 |
| `etapas/<id>/alterar_status/` | POST | Muda status (I/A/F) |
| `torneios/<id>/ranking/` | GET | Ranking de um torneio |
| `blinds/<id>/niveis/` | GET | Níveis de uma estrutura de blinds |
| `config/som/` | GET/POST | Configuração de som do usuário logado |

**Importante:** todos os endpoints usam `request.data` (DRF) em vez de `json.loads(request.body)`.
**DRF config:** `AllowAny` (autenticação feita pelas views Django) + `SessionAuthentication`.

## Regras de Negócio
- **Pontuação por posição:** 1º=95, 2º=80, 3º=70, 4º=60, 5º=50, 6º=40, 7º=30, 8º=20, 9º=10, demais=0
- **Ranking com descarte:** pontuação mensal por player, descarta as 3 menores, soma o restante
- **Desempate no ranking:** total de pontos → 1º lugares → 2º lugares → 3º lugares
- **Prêmio automático:** calculado na eliminação — 50%/30%/20% do prizepool para 1º/2º/3º
- **Prizepool:** (buyins × vlr_buyinn + rebuys × vlr_rebuy) − jackpot − txadm
- **Jackpot:** (buyins + rebuys) × vlr_jackpot
- **Etapa finaliza automaticamente** quando todos os inscritos são eliminados via API
- **Participações:** incrementadas a cada inscrição, decrementadas em remoção não está implementado

## Templates e Layout
- Base: `_base_dark.html` — tema dark Bootstrap 4, navbar dinâmica, mensagens Django
- Badge do usuário no navbar é link para `/pkapp/perfil/`
- `poker_clock.html` é template standalone (não herda do base) — precisa de `{% load static %}` e `{% csrf_token %}` próprios
- CSS customizado: `.card-dark`, `.btn-gold`, `.section-title`, `.chip`, `.badge-status-A/I/F`

## Poker Clock — funcionalidades
- Timer por nível com estrutura de blinds vinculada ao torneio
- Barra de progresso (seek) arrastável para ajustar o tempo manualmente
- Rebuy e eliminação de players direto na tela (sem sair do clock)
- Posição de eliminação calculada automaticamente (nº de ativos no banco)
- Estatísticas atualizadas em tempo real a cada rebuy: rebuys, vlr rebuys, tx adm, total arrecadado, jackpot, prizepool, payouts
- Sons de alerta: 1 minuto restante, últimos 10 segundos, mudança de blind
- AudioContext com init lazy e unlock em touchstart/click (compatível com Android/tablet)
- Editor de estrutura de blinds inline (sem recarregar)
- Configuração de sons persistida no banco por usuário

## Dashboard
- Filtro por torneio no topo (afeta os 3 rankings)
- Top 10 por participações
- Top 10 por classificações (1º/2º/3º lugares)
- Top 10 por resultado financeiro (prêmios − custos de buy-in e rebuy)

## Configuração (variáveis de ambiente — arquivo `.env`)
```
SECRET_KEY      → chave secreta Django
DEBUG           → True/False (default False)
ALLOWED_HOSTS   → hosts separados por vírgula (incluir IP da rede local para acesso de tablets)
DB_ENGINE       → sqlite (default) ou postgres
SQLITE_PATH     → caminho absoluto do arquivo SQLite
```

## Deploy — Produção
- **Servidor:** AWS EC2 t2.micro, Ubuntu 22.04, IP 52.23.91.204, usuário `thramos`
- **Domínio:** pkbovino.com.br
- **Repositório:** https://github.com/thramosmcz/ppk_manager.git
- **Caminho:** `/home/thramos/pktour/`
- **Venv:** `/home/thramos/pktour/bin/` (não em `venv/bin/`)
- **Serviço:** `sudo systemctl restart pktour` (arquivo: `/etc/systemd/system/pktour.service`)
- **Chave SSH:** `data/ubuntu_aws_key.pem`

Fluxo de deploy:
```bash
# local
git add . && git commit -m "mensagem" && git push origin main

# servidor
ssh -i data/ubuntu_aws_key.pem thramos@52.23.91.204
cd /home/thramos/pktour
git pull origin main
source bin/activate
python manage.py migrate
sudo systemctl restart pktour
```

Para acesso de outras máquinas na rede local (tablet, etc.):
```bash
# descobrir IP
hostname -I
# iniciar com binding na rede
python manage.py runserver 0.0.0.0:8000
# adicionar IP no ALLOWED_HOSTS do .env
```

## Observações importantes
- `deploy_aws_ec2.txt` e `.env` estão no `.gitignore` — nunca commitar
- Backup do banco: `scp -i data/ubuntu_aws_key.pem thramos@52.23.91.204:/home/thramos/pktour/db.sqlite3 ./backup_db.sqlite3`
- Não usar `/admin/` para gestão — o sistema tem interface própria
- Migrations cobrem até `0008_configuracaosom.py` — novas mudanças de model exigem `makemigrations` + `migrate`
- O `poker_clock.html` usa `{% load static %}` no topo e o CSRF token via `<meta name="csrf-token" content="{{ csrf_token }}">` lido pelo JS
- Decimais do Django em JS: sempre usar `parseFloat("{{ valor|stringformat:'f' }}")` para evitar vírgula do locale pt-br
