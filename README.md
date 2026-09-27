# Answer Sheet Reader

Aplicação web para envio, leitura, revisão e correção de gabaritos. O projeto combina **Django**, **PostgreSQL**, **Docker** e uma biblioteca nativa em **C/C++** para processamento das imagens.

## Funcionalidades

- cadastro, login e logout de usuários;
- edição de perfil;
- upload de imagens de gabaritos;
- leitura automática do ID da prova, ID do participante e alternativas marcadas;
- revisão manual antes da confirmação;
- correção a partir de um gabarito oficial;
- cálculo da pontuação;
- histórico dos gabaritos enviados.

## Tecnologias

### Backend

- Python 3.12
- Django 5.2
- PostgreSQL 15
- Docker e Docker Compose

### Frontend

- Django Templates
- Bootstrap 5.3
- CSS customizado
- Bootstrap Icons

### Processamento de imagem

A leitura da imagem é realizada por uma biblioteca nativa, carregada pelo Python com `ctypes`.

- `libleitor.so`
- Raylib
- ZXing
- Pillow

A integração permite que o backend Django envie o caminho da imagem para a biblioteca nativa e receba os dados reconhecidos para revisão e armazenamento.

## Fluxo principal

1. O usuário envia uma imagem em `/upload/`.
2. A aplicação valida e salva temporariamente o arquivo.
3. A biblioteca nativa processa a imagem.
4. O sistema recupera os identificadores e as respostas reconhecidas.
5. Os dados são apresentados para revisão.
6. Após a confirmação, as respostas são comparadas com o gabarito oficial e a pontuação é salva.

## Estrutura

- `leitor_projeto/App/models.py`: modelos de perfil, upload e resultado.
- `leitor_projeto/App/views.py`: fluxo de upload, revisão, galeria e perfil.
- `leitor_projeto/App/biblioteca.py`: interface Python com a biblioteca C/C++ através de `ctypes`.
- `leitor_projeto/App/templates/`: páginas renderizadas pelo Django.
- `leitor_projeto/App/static/`: CSS, JavaScript e recursos da aplicação.

## Executando localmente

### Requisitos

- Git
- Docker
- Docker Compose

Clone o projeto:

```bash
git clone https://github.com/JamesMakarov/answer-sheet-reader.git
cd answer-sheet-reader
```

Opcionalmente, copie `.env.example` para `.env` e altere as credenciais de desenvolvimento.

Suba os containers:

```bash
docker compose up --build
```

Em outro terminal, aplique as migrações:

```bash
docker compose exec web python3 leitor_projeto/manage.py migrate
```

Para criar um superusuário:

```bash
docker compose exec web python3 leitor_projeto/manage.py createsuperuser
```

A aplicação fica disponível em `http://localhost:8000`.

Para encerrar:

```bash
docker compose down
```

## Configuração por ambiente

O projeto lê as seguintes variáveis:

- `POSTGRES_NAME`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`

Valores de desenvolvimento estão documentados em `.env.example`. O arquivo `.env` real não deve ser versionado.

Em produção, use uma `DJANGO_SECRET_KEY` própria, desative `DJANGO_DEBUG` e configure explicitamente `DJANGO_ALLOWED_HOSTS`.
