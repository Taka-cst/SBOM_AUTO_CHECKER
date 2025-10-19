# アーキテクチャ設計書

## 📐 システムアーキテクチャ

### 1. 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│                      ユーザー (Browser)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (React + Vite)                     │
│                    Port: 3000                                │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                Backend API (FastAPI)                         │
│                    Port: 8000                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • SBOM Parser (CycloneDX/SPDX)                        │  │
│  │ • Trivy Integration Service                           │  │
│  │ • Report Generator                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────┬─────────────────────────┬───────────────────────┘
            │                         │
            ▼                         ▼
┌───────────────────────┐  ┌──────────────────────────────────┐
│   PostgreSQL DB       │  │  Trivy Scanner Service           │
│   Port: 5432          │  │  (Background Task)               │
│                       │  │                                  │
│ • SBOM Records        │  │ • Trivy CLI                      │
│ • Scan Results        │  │ • Trivy DB Updater (12h)         │
│ • Vulnerability Data  │  │ • SBOM Scanner                   │
│ • User Data           │  │ • Result Parser                  │
└───────────────────────┘  └──────────────────────────────────┘
```

## 🏗️ コンポーネント設計

### 2.1 Frontend (React)

**技術スタック:**
- React 18.2
- TypeScript 5.0
- Vite 4.0
- Tailwind CSS 3.3
- React Query (データフェッチング)
- Recharts (グラフ表示)
- React Dropzone (ファイルアップロード)

**主要コンポーネント:**

```
src/
├── components/
│   ├── UploadZone.tsx          # SBOMアップロード
│   ├── Dashboard.tsx           # メインダッシュボード
│   ├── VulnerabilityList.tsx   # 脆弱性一覧
│   ├── VulnerabilityChart.tsx  # グラフ表示
│   └── ReportExport.tsx        # レポートエクスポート
├── pages/
│   ├── Home.tsx                # ホーム画面
│   ├── ScanHistory.tsx         # スキャン履歴
│   └── Settings.tsx            # 設定画面
├── services/
│   └── api.ts                  # API通信
├── hooks/
│   └── useScan.ts              # カスタムフック
└── types/
    └── index.ts                # TypeScript型定義
```

### 2.2 Backend API (FastAPI)

**技術スタック:**
- Python 3.11
- FastAPI 0.104
- SQLAlchemy 2.0 (ORM)
- Pydantic 2.0 (バリデーション)
- Celery (非同期タスク)
- Redis (Celeryブローカー)

**ディレクトリ構造:**

```
backend/
├── app/
│   ├── main.py                 # アプリケーションエントリポイント
│   ├── config.py               # 設定管理
│   ├── database.py             # DB接続
│   ├── models/
│   │   ├── sbom.py             # SBOMモデル
│   │   ├── vulnerability.py    # 脆弱性モデル
│   │   └── scan.py             # スキャン結果モデル
│   ├── schemas/
│   │   ├── sbom.py             # Pydanticスキーマ
│   │   ├── vulnerability.py
│   │   └── scan.py
│   ├── routers/
│   │   ├── sbom.py             # SBOMエンドポイント
│   │   ├── scan.py             # スキャンエンドポイント
│   │   └── report.py           # レポートエンドポイント
│   ├── services/
│   │   ├── sbom_parser.py      # SBOMパーサー
│   │   ├── trivy_service.py    # Trivy統合サービス
│   │   └── report_generator.py # レポート生成
│   └── utils/
│       ├── security.py         # セキュリティユーティリティ
│       └── logger.py           # ログ設定
├── tests/
│   └── ...                     # テストコード
├── requirements.txt
└── Dockerfile
```

**主要API機能:**
1. **SBOM管理**: アップロード、解析、保存
2. **脆弱性スキャン**: Trivyを使用したSBOMスキャン
3. **レポート生成**: JSON/CSV形式でエクスポート
4. **履歴管理**: 過去のスキャン結果の保存と取得

### 2.3 Trivy Scanner Service

**技術スタック:**
- Trivy (Aqua Security製の脆弱性スキャナー)
- Python 3.11
- Celery 5.3 (タスクキュー)
- Redis (メッセージブローカー)

**Trivyの特徴:**
- 高精度な脆弱性検出
- 複数のデータソース (NVD, GitHub Advisory, etc.)
- SBOM形式のネイティブサポート (CycloneDX, SPDX)
- オフラインスキャン可能
- 高速なスキャン処理

**主要機能:**

```python
# celery_worker.py
@celery_app.task
def update_trivy_db():
    """12時間ごとにTrivyデータベースを更新"""
    # trivy db --download-db-only
    # 1. Trivyの脆弱性DBを更新
    # 2. ローカルキャッシュに保存
    # 3. 更新ログを記録
    pass

@celery_app.task
def scan_sbom(sbom_id: int):
    """SBOMに対してTrivyスキャンを実行"""
    # trivy sbom /path/to/sbom.json
    # 1. SBOMファイルをTrivyでスキャン
    # 2. JSON形式で結果を取得
    # 3. 結果をパースしてDBに保存
    pass
```

**スケジュール設定:**
```python
# 12時間ごとにTrivyデータベースを更新
CELERYBEAT_SCHEDULE = {
    'update-trivy-database': {
        'task': 'app.celery_worker.update_trivy_db',
        'schedule': crontab(hour='*/12'),  # 12時間ごと
    },
}
```

**Trivyコマンド例:**
```bash
# DB更新
trivy db --download-db-only

# SBOMスキャン
trivy sbom --format json --output result.json /path/to/sbom.json

# または直接入力
trivy sbom --format json - < sbom.json
```

## 💾 データベース設計

### 3.1 ER図

```
┌─────────────────┐         ┌──────────────────┐
│     sboms       │         │  vulnerabilities │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │         │ id (PK)          │
│ filename        │         │ cve_id           │
│ format          │◄────┐   │ severity         │
│ uploaded_at     │     │   │ description      │
│ file_hash       │     │   │ cvss_score       │
│ content_json    │     │   │ published_date   │
└─────────────────┘     │   │ modified_date    │
                        │   │ cpe_match        │
                        │   └──────────────────┘
                        │            ▲
                        │            │
┌─────────────────┐     │   ┌──────────────────┐
│  scan_results   │     │   │ scan_vulnera-    │
├─────────────────┤     │   │ bilities         │
│ id (PK)         │     │   ├──────────────────┤
│ sbom_id (FK)    │─────┘   │ id (PK)          │
│ scan_date       │         │ scan_result_id   │
│ status          │◄────────┤    (FK)          │
│ total_components│         │ vulnerability_id │
│ vulnerable_count│         │    (FK)          │
│ critical_count  │         │ component_name   │
│ high_count      │         │ component_version│
│ medium_count    │         │ matched_cpe      │
│ low_count       │         └──────────────────┘
└─────────────────┘
```

### 3.2 テーブル定義

#### sboms テーブル
```sql
CREATE TABLE sboms (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    format VARCHAR(50) NOT NULL,  -- 'cyclonedx' or 'spdx'
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    content_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sboms_file_hash ON sboms(file_hash);
CREATE INDEX idx_sboms_uploaded_at ON sboms(uploaded_at DESC);
```

#### vulnerabilities テーブル
```sql
CREATE TABLE vulnerabilities (
    id SERIAL PRIMARY KEY,
    cve_id VARCHAR(50) UNIQUE NOT NULL,
    severity VARCHAR(20),  -- CRITICAL, HIGH, MEDIUM, LOW
    description TEXT,
    cvss_score DECIMAL(3,1),
    cvss_vector VARCHAR(100),
    published_date TIMESTAMP,
    modified_date TIMESTAMP,
    cpe_match JSONB,  -- CPE matching criteria
    references JSONB,  -- External references
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vulnerabilities_cve_id ON vulnerabilities(cve_id);
CREATE INDEX idx_vulnerabilities_severity ON vulnerabilities(severity);
CREATE INDEX idx_vulnerabilities_modified_date ON vulnerabilities(modified_date DESC);
CREATE INDEX idx_vulnerabilities_cpe_match ON vulnerabilities USING GIN (cpe_match);
```

#### scan_results テーブル
```sql
CREATE TABLE scan_results (
    id SERIAL PRIMARY KEY,
    sbom_id INTEGER REFERENCES sboms(id) ON DELETE CASCADE,
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),  -- 'completed', 'in_progress', 'failed'
    total_components INTEGER DEFAULT 0,
    vulnerable_count INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    scan_duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scan_results_sbom_id ON scan_results(sbom_id);
CREATE INDEX idx_scan_results_scan_date ON scan_results(scan_date DESC);
```

#### scan_vulnerabilities テーブル
```sql
CREATE TABLE scan_vulnerabilities (
    id SERIAL PRIMARY KEY,
    scan_result_id INTEGER REFERENCES scan_results(id) ON DELETE CASCADE,
    vulnerability_id INTEGER REFERENCES vulnerabilities(id),
    component_name VARCHAR(255) NOT NULL,
    component_version VARCHAR(100),
    matched_cpe VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scan_vulnerabilities_scan_result_id ON scan_vulnerabilities(scan_result_id);
CREATE INDEX idx_scan_vulnerabilities_vulnerability_id ON scan_vulnerabilities(vulnerability_id);
```

## 🔄 データフロー

### 4.1 SBOMアップロードとスキャンフロー

```
1. ユーザーがSBOMファイルをアップロード
   │
   ├─> Frontend: ファイル選択とアップロード
   │
   ├─> Backend: POST /api/sbom/upload
   │   │
   │   ├─> ファイルバリデーション
   │   ├─> ファイルハッシュ計算(重複チェック)
   │   ├─> SBOMパース(CycloneDX/SPDX)
   │   ├─> データベースに保存
   │   └─> scan_sbom タスクをキューに追加
   │
   ├─> Scanner: Celeryタスク実行
   │   │
   │   ├─> SBOMファイルを一時ディレクトリに保存
   │   ├─> Trivyコマンドを実行
   │   │   └─> trivy sbom --format json /path/to/sbom.json
   │   ├─> Trivyの結果(JSON)をパース
   │   ├─> 脆弱性情報を抽出
   │   └─> scan_resultsをデータベースに保存
   │
   └─> Frontend: スキャン結果を表示
       │
       ├─> 脆弱性サマリー
       ├─> 詳細リスト
       └─> グラフ表示
```

### 4.2 Trivy DB更新フロー

```
1. Celery Beat: 12時間ごとにトリガー
   │
   ├─> Trivyコマンド実行
   │   │
   │   └─> trivy db --download-db-only
   │       │
   │       ├─> Aqua Security DBから最新データダウンロード
   │       ├─> NVD, GitHub Advisory, etc.
   │       └─> ローカルキャッシュに保存
   │           (~/.cache/trivy/)
   │
   ├─> 更新ログ記録
   │   │
   │   ├─> 更新日時を記録
   │   ├─> DBバージョンを記録
   │   └─> 更新統計をログ出力
   │
   └─> 完了通知
       │
       └─> ログに記録
       ├─> 新規CVEを挿入
       ├─> 既存CVEを更新
       └─> 更新ログを記録
```

## 🔐 セキュリティ設計

### 5.1 セキュリティ対策

1. **ファイルアップロードセキュリティ**
   - ファイルサイズ制限: 最大50MB
   - 許可形式: JSON, XML のみ
   - ウイルススキャン統合可能
   - ファイル名サニタイゼーション

2. **API セキュリティ**
   - CORS設定
   - レート制限
   - 入力バリデーション
   - SQLインジェクション対策(ORM使用)

3. **データ保護**
   - データベース暗号化
   - 通信のHTTPS化
   - 機密情報のマスキング

### 5.2 認証・認可(オプション)

将来的な拡張として:
- JWT認証
- ユーザー管理
- ロールベースアクセス制御

## 📊 パフォーマンス設計

### 6.1 最適化ポイント

1. **データベース**
   - 適切なインデックス設計
   - クエリキャッシング
   - コネクションプーリング

2. **バックエンド**
   - 非同期処理(Celery)
   - レスポンスキャッシング
   - ページネーション

3. **フロントエンド**
   - コード分割
   - 遅延ロード
   - 画像最適化

### 6.2 スケーラビリティ

- 水平スケーリング対応設計
- ステートレスなAPI設計
- コンテナオーケストレーション対応(Kubernetes)

## 🔧 技術選定理由

| 技術 | 選定理由 |
|------|---------|
| FastAPI | 高速、型安全、自動ドキュメント生成 |
| React | コンポーネントベース、豊富なエコシステム |
| PostgreSQL | JSONB型サポート、信頼性、パフォーマンス |
| Docker | 環境の一貫性、デプロイの容易さ |
| Celery | 非同期タスク処理、スケジュール実行 |
| TypeScript | 型安全、コード品質向上 |

## 📈 今後の拡張案

1. **機能拡張**
   - ユーザー認証・認可
   - チーム管理機能
   - Slack/メール通知
   - カスタムレポートテンプレート

2. **技術的改善**
   - GraphQL API
   - リアルタイム更新(WebSocket)
   - マイクロサービス化
   - Kubernetes対応

3. **脆弱性データソース拡張**
   - GitHub Advisory Database
   - OSV (Open Source Vulnerabilities)
   - Snyk Database
