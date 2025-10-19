# Node.js 18ベースイメージ
FROM node:18-alpine as builder

# 作業ディレクトリの設定
WORKDIR /app

# package.jsonのコピー
COPY package*.json ./

# 依存関係のインストール
RUN npm install

# ソースコードのコピー
COPY . .

# ビルド
RUN npm run build

# 本番用イメージ
FROM nginx:alpine

# ビルド成果物のコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx設定のコピー
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ポートの公開
EXPOSE 3000

# Nginxの起動
CMD ["nginx", "-g", "daemon off;"]
