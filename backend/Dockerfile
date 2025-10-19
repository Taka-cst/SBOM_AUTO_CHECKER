# =======================================
# Stage 1: ビルドステージ (依存関係とツールのインストール)
# =======================================
FROM python:3.11-slim AS builder

# 作業ディレクトリの設定
WORKDIR /app

# ビルドに必要な最小限のパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール (wheelを使用して高速化)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# =======================================
# Stage 2: Trivyダウンロードステージ (並列ビルドで高速化)
# =======================================
FROM alpine:latest AS trivy-downloader

ARG TRIVY_VERSION=0.58.2
RUN apk add --no-cache wget tar \
    && wget -q "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" \
    && tar zxf "trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" -C /usr/local/bin \
    && chmod +x /usr/local/bin/trivy \
    && rm "trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz"

# =======================================
# Stage 3: 本番ステージ (最小構成)
# =======================================
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 実行時に必要な最小限のパッケージのみインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ビルドステージからwheelをコピーしてインストール (超高速!)
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

# Trivyダウンロードステージからバイナリをコピー
COPY --from=trivy-downloader /usr/local/bin/trivy /usr/local/bin/trivy

# Trivyキャッシュディレクトリの作成
RUN mkdir -p /.cache/trivy && chmod -R 777 /.cache/trivy
ENV TRIVY_CACHE_DIR=/.cache/trivy

# アップロードディレクトリの作成
RUN mkdir -p /app/uploads

# アプリケーションコードのコピー (最後にコピーしてキャッシュを最大活用)
COPY . .

# エントリポイントスクリプトに実行権限を付与
RUN chmod +x /app/entrypoint.sh

# エントリポイント設定
ENTRYPOINT ["/app/entrypoint.sh"]

# ポートの公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーションの起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
