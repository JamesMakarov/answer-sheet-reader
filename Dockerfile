FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python3-pip \
    build-essential \
    libgl1 \
    libxi6 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libgomp1 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY leitor_projeto/requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY leitor_projeto/App/libs/biblioteca/*.so* /usr/local/lib/
RUN ldconfig

COPY . .

EXPOSE 8000


CMD ["gunicorn", "--chdir", "leitor_projeto", "leitor_projeto.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
