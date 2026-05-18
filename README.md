# Bolão Copa do Mundo 2026

Site em Streamlit + Supabase para um bolão entre amigos da Copa do Mundo de 2026.

## Estrutura

```
bolao-copa-2026/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── schema.sql              # DDL do Supabase (setup do zero)
├── seed_matches.py         # Popula as 104 partidas
├── migrations/
│   └── 001_adiciona_senha.sql
├── app/
│   ├── __init__.py
│   ├── streamlit_app.py    # Ponto de entrada com navegação
│   ├── auth.py             # Validações + sessão (login/logout)
│   ├── db.py               # Acesso ao Supabase
│   ├── ranking.py          # Cálculo da classificação geral
│   ├── scoring.py          # Lógica de pontuação (pura)
│   ├── utils.py            # Deadline, timezone, helpers
│   └── screens/            # Telas do app (não 'pages' - ver nota abaixo)
│       ├── __init__.py
│       ├── login.py
│       ├── palpites_grupos.py
│       ├── palpites_mata_mata.py   # 🚧 Entrega 5
│       ├── classificacao.py
│       ├── regras.py
│       └── admin.py                # 🚧 Entrega 5
└── tests/
    ├── __init__.py
    ├── test_scoring.py     # 32 testes da pontuação
    ├── test_auth.py        # 30 testes das validações
    └── test_ranking.py     # 11 testes do ranking
```

## Setup inicial

1. **Crie um projeto no Supabase** em https://supabase.com (plano free).
2. **Rode o schema**: abra o SQL Editor no Supabase, cole o conteúdo de `schema.sql` e execute.
3. **Copie as credenciais**:
   - Vá em *Project Settings → API*.
   - Copie *Project URL* e *anon public key*.
4. **Configure o ambiente local** (Windows + Anaconda):
   ```bash
   conda create -n bolao python=3.11 -y
   conda activate bolao
   pip install -r requirements.txt
   copy .env.example .env
   ```
   Em seguida, edite o `.env` com as credenciais do Supabase.
5. **Selecione o interpretador no VS Code**:
   - Aperte `Ctrl+Shift+P`
   - Digite `Python: Select Interpreter`
   - Escolha o que mostra `('bolao': conda)`
6. **Popule as partidas**:
   ```bash
   python seed_matches.py
   ```
   Deve imprimir "104 partidas inseridas".
7. **Rode os testes**:
   ```bash
   pytest -v
   ```
   Todos os **73 testes** (pontuação + auth + ranking) devem passar.
8. **Inicie o app**:
   ```bash
   streamlit run app/streamlit_app.py
   ```
   Acesse http://localhost:8501.

## Migrations (apenas se já rodou versão anterior do schema)

Se o seu banco foi criado antes da Entrega 2, rode no SQL Editor:

```sql
-- conteúdo de migrations/001_adiciona_senha.sql
```

Cada migration é cumulativa e pode ser rodada de forma idempotente
(usa `IF NOT EXISTS` / `DROP CONSTRAINT IF EXISTS`).

## Configuração do `.env`

Além das credenciais do Supabase:
- `ADMIN_TELEFONE`: seu telefone (11 dígitos). Quando logar com este
  número, o menu **Admin** aparece automaticamente na sidebar.
- `ADMIN_PIN`: PIN extra exigido dentro da tela admin (futura entrega).
- `TIMEZONE`: fuso para deadlines (padrão `America/Sao_Paulo`).

> Para reativar o ambiente em sessões futuras: `conda activate bolao`.
> Para sair: `conda deactivate`.

## Deploy no Streamlit Community Cloud

1. Suba o repositório no GitHub.
2. Acesse https://share.streamlit.io e conecte sua conta GitHub.
3. Clique em **New app** e selecione:
   - Repositório
   - Branch (geralmente `main`)
   - Main file path: `app/streamlit_app.py`
4. Antes de clicar em Deploy, vá em **Advanced settings → Secrets**
   e cole o conteúdo de `.streamlit/secrets.toml.example` ajustado
   com as credenciais reais.
5. Clique em **Deploy** e aguarde alguns minutos.

O app já é construído para ler segredos de `st.secrets` no Cloud com
fallback para `.env` localmente, então o mesmo código funciona nos dois
ambientes sem ajustes.

## Telas previstas

- **Login** (telefone + nome no primeiro acesso)
- **Palpites - Fase de grupos** (72 partidas, paginadas por grupo)
- **Palpites - Mata-mata** (32 partidas, liberada após a fase de grupos)
- **Classificação** (ranking dos participantes, com detalhamento)
- **Regras de pontuação** (estática)
- **Admin** (lançar resultados oficiais, abrir fases)

## Regras de pontuação

**Fase de grupos** (excludente e hierárquica - aplica-se a faixa mais alta):

| Pontos | Critério |
|-------:|----------|
| 18 | Placar exato |
| 15 | Acertou vencedor e o número de gols de um dos lados |
| 12 | Acertou vencedor (errando ambos os gols) ou empate (não exato) |
|  3 | Errou o resultado, mas acertou o número de gols de um dos lados |
|  0 | Demais casos |

**Mata-mata** (mesmas regras, com adição do campo "quem avança"):

- Se o palpite tem **vencedor**: aplicam-se as regras da fase de grupos. Quem avança é redundante com o palpite.
- Se o palpite é **empate**:
  - 18: placar exato + quem avançou correto
  - 15: empate não-exato + quem avançou correto
  - 12: placar exato + quem avançou errado
  -  9: empate não-exato + quem avançou errado
  -  3: errou resultado mas acertou apenas quem passou

**Critério de desempate no ranking**: placares exatos → vencedores acertados → ordem alfabética.

**Deadline**: até 0h (horário de Brasília) do dia do jogo.