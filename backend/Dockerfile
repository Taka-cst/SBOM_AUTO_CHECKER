# Python 3.11ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新とインストール
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Trivyのインストール (バイナリダウンロード)
RUN TRIVY_VERSION=$(curl -s "https://api.github.com/repos/aquasecurity/trivy/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/') \
    && wget -q "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" \
    && tar zxvf "trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" \
    && mv trivy /usr/local/bin/ \
    && rm "trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" \
    && chmod +x /usr/local/bin/trivy

# Trivyキャッシュディレクトリの作成
RUN mkdir -p /.cache/trivy && chmod -R 777 /.cache/trivy
ENV TRIVY_CACHE_DIR=/.cache/trivy

# 依存関係のコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# エントリポイントスクリプトに実行権限を付与
RUN chmod +x /app/entrypoint.sh

# アップロードディレクトリの作成
RUN mkdir -p /app/uploads

# エントリポイント設定
ENTRYPOINT ["/app/entrypoint.sh"]

# ポートの公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーションの起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
