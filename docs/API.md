# API仕様書

## 📡 ベースURL

```
http://localhost:8000/api/v1
```

## 🔐 認証

現在のバージョンでは認証は実装されていません。将来的にJWT認証を追加予定です。

## 📋 共通仕様

### レスポンス形式

すべてのAPIレスポンスは以下の形式に従います:

**成功時:**
```json
{
  "success": true,
  "data": { ... },
  "message": "操作が成功しました"
}
```

**エラー時:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": { ... }
  }
}
```

### HTTPステータスコード

| コード | 説明 |
|--------|------|
| 200 | 成功 |
| 201 | 作成成功 |
| 400 | リクエストが不正 |
| 404 | リソースが見つからない |
| 422 | バリデーションエラー |
| 500 | サーバーエラー |

### ページネーション

リスト取得APIはページネーションをサポートします:

**リクエストパラメータ:**
```
?page=1&limit=20
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 100,
      "items_per_page": 20
    }
  }
}
```

## 🔍 エンドポイント一覧

### 1. ヘルスチェック

#### `GET /health`

システムの稼働状態を確認します。

**リクエスト:**
```http
GET /health
```

**レスポンス:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-16T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "scanner": "healthy"
  }
}
```

---

### 2. SBOM管理

#### `POST /api/v1/sbom/upload`

SBOMファイルをアップロードします。

**リクエスト:**
```http
POST /api/v1/sbom/upload
Content-Type: multipart/form-data

file: <SBOMファイル>
```

**リクエストパラメータ:**
- `file` (required): SBOMファイル (JSON or XML)
- `auto_scan` (optional): 自動スキャン実行 (default: true)

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "sbom_id": 123,
    "filename": "example-sbom.json",
    "format": "cyclonedx",
    "file_hash": "sha256:abc123...",
    "uploaded_at": "2025-10-16T12:00:00Z",
    "component_count": 45,
    "scan_status": "queued"
  },
  "message": "SBOMファイルが正常にアップロードされました"
}
```

**エラーコード:**
- `INVALID_FILE_FORMAT`: サポートされていないファイル形式
- `FILE_TOO_LARGE`: ファイルサイズが上限を超えています
- `DUPLICATE_FILE`: 同じファイルが既にアップロードされています

---

#### `GET /api/v1/sbom`

アップロード済みのSBOM一覧を取得します。

**リクエスト:**
```http
GET /api/v1/sbom?page=1&limit=20&sort=uploaded_at&order=desc
```

**クエリパラメータ:**
- `page` (optional): ページ番号 (default: 1)
- `limit` (optional): 1ページあたりの件数 (default: 20, max: 100)
- `sort` (optional): ソートフィールド (uploaded_at, filename)
- `order` (optional): ソート順 (asc, desc)
- `format` (optional): フィルタ (cyclonedx, spdx)

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 123,
        "filename": "example-sbom.json",
        "format": "cyclonedx",
        "uploaded_at": "2025-10-16T12:00:00Z",
        "component_count": 45,
        "last_scan_at": "2025-10-16T12:05:00Z",
        "vulnerability_count": 5
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 50,
      "items_per_page": 20
    }
  }
}
```

---

#### `GET /api/v1/sbom/{sbom_id}`

特定のSBOM詳細を取得します。

**リクエスト:**
```http
GET /api/v1/sbom/123
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "filename": "example-sbom.json",
    "format": "cyclonedx",
    "uploaded_at": "2025-10-16T12:00:00Z",
    "file_hash": "sha256:abc123...",
    "content": {
      "bomFormat": "CycloneDX",
      "specVersion": "1.4",
      "components": [...]
    },
    "components": [
      {
        "name": "express",
        "version": "4.18.2",
        "purl": "pkg:npm/express@4.18.2"
      }
    ],
    "scan_results": [
      {
        "scan_id": 456,
        "scan_date": "2025-10-16T12:05:00Z",
        "vulnerability_count": 5,
        "critical_count": 1,
        "high_count": 2,
        "medium_count": 2,
        "low_count": 0
      }
    ]
  }
}
```

---

#### `DELETE /api/v1/sbom/{sbom_id}`

SBOMを削除します。

**リクエスト:**
```http
DELETE /api/v1/sbom/123
```

**レスポンス:**
```json
{
  "success": true,
  "message": "SBOMが正常に削除されました"
}
```

---

### 3. 脆弱性スキャン

#### `POST /api/v1/scan/{sbom_id}`

特定のSBOMに対してスキャンを実行します。

**リクエスト:**
```http
POST /api/v1/scan/123
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "scan_id": 456,
    "sbom_id": 123,
    "status": "queued",
    "created_at": "2025-10-16T12:10:00Z"
  },
  "message": "スキャンがキューに追加されました"
}
```

---

#### `GET /api/v1/scan/{scan_id}`

スキャン結果を取得します。

**リクエスト:**
```http
GET /api/v1/scan/456
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "scan_id": 456,
    "sbom_id": 123,
    "status": "completed",
    "scan_date": "2025-10-16T12:15:00Z",
    "duration_seconds": 45,
    "summary": {
      "total_components": 45,
      "vulnerable_components": 12,
      "total_vulnerabilities": 18,
      "severity_breakdown": {
        "critical": 2,
        "high": 5,
        "medium": 8,
        "low": 3
      }
    },
    "vulnerabilities": [
      {
        "id": 789,
        "cve_id": "CVE-2023-12345",
        "component_name": "express",
        "component_version": "4.18.2",
        "severity": "HIGH",
        "cvss_score": 7.5,
        "description": "Express.jsに深刻な脆弱性が発見されました...",
        "published_date": "2023-06-15T00:00:00Z",
        "references": [
          "https://nvd.nist.gov/vuln/detail/CVE-2023-12345"
        ],
        "recommendation": "バージョン 4.19.0 以降にアップグレードしてください"
      }
    ]
  }
}
```

**ステータス:**
- `queued`: スキャン待機中
- `in_progress`: スキャン実行中
- `completed`: スキャン完了
- `failed`: スキャン失敗

---

#### `GET /api/v1/scan`

スキャン履歴を取得します。

**リクエスト:**
```http
GET /api/v1/scan?sbom_id=123&page=1&limit=20
```

**クエリパラメータ:**
- `sbom_id` (optional): 特定のSBOMのスキャンのみ取得
- `status` (optional): ステータスでフィルタ
- `page`, `limit`: ページネーション

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "scan_id": 456,
        "sbom_id": 123,
        "filename": "example-sbom.json",
        "scan_date": "2025-10-16T12:15:00Z",
        "status": "completed",
        "vulnerability_count": 18,
        "critical_count": 2,
        "high_count": 5
      }
    ],
    "pagination": {...}
  }
}
```

---

### 4. 脆弱性情報

#### `GET /api/v1/vulnerabilities`

脆弱性データベースを検索します。

**リクエスト:**
```http
GET /api/v1/vulnerabilities?cve_id=CVE-2023-12345&severity=HIGH&page=1&limit=20
```

**クエリパラメータ:**
- `cve_id` (optional): CVE ID で検索
- `severity` (optional): 深刻度でフィルタ (CRITICAL, HIGH, MEDIUM, LOW)
- `keyword` (optional): キーワード検索
- `page`, `limit`: ページネーション

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 789,
        "cve_id": "CVE-2023-12345",
        "severity": "HIGH",
        "cvss_score": 7.5,
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        "description": "詳細な説明...",
        "published_date": "2023-06-15T00:00:00Z",
        "modified_date": "2023-06-20T00:00:00Z",
        "references": [
          "https://nvd.nist.gov/vuln/detail/CVE-2023-12345",
          "https://github.com/advisories/GHSA-xxxx"
        ],
        "affected_products": [
          "cpe:2.3:a:expressjs:express:4.18.2:*:*:*:*:*:*:*"
        ]
      }
    ],
    "pagination": {...}
  }
}
```

---

#### `GET /api/v1/vulnerabilities/{cve_id}`

特定のCVE詳細情報を取得します。

**リクエスト:**
```http
GET /api/v1/vulnerabilities/CVE-2023-12345
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "cve_id": "CVE-2023-12345",
    "severity": "HIGH",
    "cvss_score": 7.5,
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
    "description": "詳細な説明...",
    "published_date": "2023-06-15T00:00:00Z",
    "modified_date": "2023-06-20T00:00:00Z",
    "references": [...],
    "cpe_configurations": [...],
    "cwes": ["CWE-79"],
    "affected_sboms": [
      {
        "sbom_id": 123,
        "filename": "example-sbom.json",
        "component_name": "express",
        "component_version": "4.18.2"
      }
    ]
  }
}
```

---

### 5. レポート生成

#### `GET /api/v1/report/{scan_id}/json`

スキャン結果をJSON形式でエクスポートします。

**リクエスト:**
```http
GET /api/v1/report/456/json
```

**レスポンス:**
```json
{
  "report": {
    "metadata": {
      "report_id": "RPT-20251016-456",
      "generated_at": "2025-10-16T13:00:00Z",
      "scan_id": 456,
      "sbom_filename": "example-sbom.json"
    },
    "summary": {...},
    "vulnerabilities": [...]
  }
}
```

---

#### `GET /api/v1/report/{scan_id}/pdf`

スキャン結果をPDF形式でエクスポートします。

**リクエスト:**
```http
GET /api/v1/report/456/pdf
```

**レスポンス:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="scan-report-456.pdf"

<PDFバイナリデータ>
```

---

#### `GET /api/v1/report/{scan_id}/csv`

脆弱性一覧をCSV形式でエクスポートします。

**リクエスト:**
```http
GET /api/v1/report/456/csv
```

**レスポンス:**
```csv
CVE ID,Component,Version,Severity,CVSS Score,Description
CVE-2023-12345,express,4.18.2,HIGH,7.5,"Express.js vulnerability..."
```

---

### 6. 統計情報

#### `GET /api/v1/stats/overview`

全体統計を取得します。

**リクエスト:**
```http
GET /api/v1/stats/overview
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "total_sboms": 150,
    "total_scans": 320,
    "total_vulnerabilities_found": 1250,
    "latest_nvd_update": "2025-10-16T06:00:00Z",
    "nvd_cve_count": 250000,
    "severity_distribution": {
      "critical": 45,
      "high": 180,
      "medium": 650,
      "low": 375
    },
    "top_vulnerable_components": [
      {
        "component": "express",
        "vulnerability_count": 25
      }
    ]
  }
}
```

---

#### `GET /api/v1/stats/trends`

時系列トレンドデータを取得します。

**リクエスト:**
```http
GET /api/v1/stats/trends?period=30d
```

**クエリパラメータ:**
- `period`: 期間 (7d, 30d, 90d, 1y)

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "data_points": [
      {
        "date": "2025-09-16",
        "scans_count": 12,
        "vulnerabilities_found": 45,
        "critical_count": 2
      }
    ]
  }
}
```

---

### 7. システム管理

#### `GET /api/v1/admin/nvd/status`

NVDデータベースの更新状態を確認します。

**リクエスト:**
```http
GET /api/v1/admin/nvd/status
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "last_update": "2025-10-16T06:00:00Z",
    "next_update": "2025-10-16T18:00:00Z",
    "total_cves": 250000,
    "update_status": "idle",
    "last_update_duration_seconds": 450
  }
}
```

---

#### `POST /api/v1/admin/nvd/update`

NVDデータベースの手動更新をトリガーします。

**リクエスト:**
```http
POST /api/v1/admin/nvd/update
```

**レスポンス:**
```json
{
  "success": true,
  "message": "NVD更新タスクがキューに追加されました",
  "data": {
    "task_id": "task-abc123"
  }
}
```

---

## 🔍 エラーコード一覧

| コード | 説明 |
|--------|------|
| `INVALID_FILE_FORMAT` | サポートされていないファイル形式 |
| `FILE_TOO_LARGE` | ファイルサイズ超過 |
| `DUPLICATE_FILE` | 重複ファイル |
| `SBOM_NOT_FOUND` | SBOMが見つかりません |
| `SCAN_NOT_FOUND` | スキャン結果が見つかりません |
| `SCAN_IN_PROGRESS` | スキャン実行中 |
| `INVALID_PARAMETERS` | 無効なパラメータ |
| `DATABASE_ERROR` | データベースエラー |
| `EXTERNAL_API_ERROR` | 外部API呼び出しエラー |

## 📝 使用例

### Python (requests)

```python
import requests

# SBOMアップロード
url = "http://localhost:8000/api/v1/sbom/upload"
files = {"file": open("sbom.json", "rb")}
response = requests.post(url, files=files)
sbom_data = response.json()

sbom_id = sbom_data["data"]["sbom_id"]

# スキャン実行
scan_url = f"http://localhost:8000/api/v1/scan/{sbom_id}"
scan_response = requests.post(scan_url)
scan_id = scan_response.json()["data"]["scan_id"]

# 結果取得
result_url = f"http://localhost:8000/api/v1/scan/{scan_id}"
result = requests.get(result_url)
print(result.json())
```

### JavaScript (fetch)

```javascript
// SBOMアップロード
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/v1/sbom/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
const sbomId = data.data.sbom_id;

// スキャン実行
const scanResponse = await fetch(`http://localhost:8000/api/v1/scan/${sbomId}`, {
  method: 'POST'
});

const scanData = await scanResponse.json();
console.log(scanData);
```

### cURL

```bash
# SBOMアップロード
curl -X POST http://localhost:8000/api/v1/sbom/upload \
  -F "file=@sbom.json"

# スキャン結果取得
curl http://localhost:8000/api/v1/scan/456

# レポートダウンロード
curl http://localhost:8000/api/v1/report/456/pdf -o report.pdf
```

## 🔗 関連ドキュメント

- [アーキテクチャ設計書](ARCHITECTURE.md)
- [ユーザーマニュアル](USER_MANUAL.md)
- [開発ガイド](DEVELOPMENT.md)

## 📮 フィードバック

API仕様に関するフィードバックや改善提案は、GitHubのIssueでお願いします。
