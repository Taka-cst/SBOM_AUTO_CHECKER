# 開発ガイド

## 🎯 このドキュメントについて

このガイドは、SBOM Vulnerability Checkerの開発に参加する開発者向けのドキュメントです。

## 📋 開発環境のセットアップ

### 前提条件

- Docker & Docker Compose
- Git
- テキストエディタ(VS Code推奨)
- Python 3.11以降(ローカル開発の場合)
- Node.js 18以降(フロントエンド開発の場合)

### ローカル開発環境

**リポジトリのクローン:**
```bash
git clone <repository-url>
cd SBOM_AUTO_CHECKER
```

**環境変数の設定:**
```bash
cp .env.example .env
# .envファイルを編集
```

**開発モードで起動:**
```bash
docker-compose up --build
```

### VS Code設定

**推奨拡張機能:**
- Python
- Pylance
- Docker
- ESLint
- Prettier
- GitLens

**.vscode/settings.json:**
```json
{
  "python.defaultInterpreterPath": "/usr/local/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## 🏗️ プロジェクト構造

```
SBOM_AUTO_CHECKER/
├── backend/              # FastAPI バックエンド
│   ├── app/
│   │   ├── main.py      # エントリポイント
│   │   ├── config.py    # 設定
│   │   ├── database.py  # DB設定
│   │   ├── models/      # SQLAlchemyモデル
│   │   ├── schemas/     # Pydanticスキーマ
│   │   ├── routers/     # APIエンドポイント
│   │   ├── services/    # ビジネスロジック
│   │   └── utils/       # ユーティリティ
│   ├── tests/           # テストコード
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # React フロントエンド
│   ├── src/
│   │   ├── components/  # Reactコンポーネント
│   │   ├── pages/       # ページコンポーネント
│   │   ├── services/    # API通信
│   │   ├── hooks/       # カスタムフック
│   │   └── types/       # TypeScript型定義
│   ├── package.json
│   └── Dockerfile
├── scanner/             # Celeryワーカー
│   └── tasks.py         # バックグラウンドタスク
├── database/            # DB初期化
│   └── init.sql
├── docs/                # ドキュメント
└── docker-compose.yml
```

## 🔧 バックエンド開発

### 新しいAPIエンドポイントの追加

**1. スキーマの定義 (app/schemas/example.py):**
```python
from pydantic import BaseModel

class ExampleRequest(BaseModel):
    name: str
    value: int

class ExampleResponse(BaseModel):
    id: int
    name: str
    value: int
    created_at: datetime
```

**2. モデルの定義 (app/models/example.py):**
```python
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Example(Base):
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    value = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**3. ルーターの作成 (app/routers/example.py):**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.example import ExampleRequest, ExampleResponse

router = APIRouter(prefix="/api/v1/example", tags=["Example"])

@router.post("/", response_model=ExampleResponse)
async def create_example(
    request: ExampleRequest,
    db: Session = Depends(get_db)
):
    # ビジネスロジック
    pass

@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(example_id: int, db: Session = Depends(get_db)):
    # ビジネスロジック
    pass
```

**4. メインアプリに登録 (app/main.py):**
```python
from app.routers import example

app.include_router(example.router)
```

### データベースマイグレーション

**Alembicの初期化:**
```bash
docker-compose exec backend alembic init alembic
```

**マイグレーションの作成:**
```bash
docker-compose exec backend alembic revision --autogenerate -m "Add example table"
```

**マイグレーションの適用:**
```bash
docker-compose exec backend alembic upgrade head
```

**ロールバック:**
```bash
docker-compose exec backend alembic downgrade -1
```

### テストの作成

**tests/test_example.py:**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_example():
    response = client.post(
        "/api/v1/example/",
        json={"name": "test", "value": 123}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test"
    assert data["value"] == 123

def test_get_example():
    response = client.get("/api/v1/example/1")
    assert response.status_code == 200
```

**テストの実行:**
```bash
docker-compose exec backend pytest
```

## 💻 フロントエンド開発

### 新しいコンポーネントの作成

**src/components/ExampleComponent.tsx:**
```typescript
import React from 'react';

interface ExampleComponentProps {
  title: string;
  onAction: () => void;
}

const ExampleComponent: React.FC<ExampleComponentProps> = ({ 
  title, 
  onAction 
}) => {
  return (
    <div className="p-4 border rounded">
      <h2 className="text-xl font-bold">{title}</h2>
      <button 
        onClick={onAction}
        className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
      >
        実行
      </button>
    </div>
  );
};

export default ExampleComponent;
```

### APIサービスの追加

**src/services/api.ts:**
```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const exampleApi = {
  getAll: async () => {
    const response = await apiClient.get('/api/v1/example');
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/api/v1/example', data);
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await apiClient.get(`/api/v1/example/${id}`);
    return response.data;
  },
};
```

### カスタムフックの作成

**src/hooks/useExample.ts:**
```typescript
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { exampleApi } from '../services/api';

export const useExamples = () => {
  return useQuery('examples', exampleApi.getAll);
};

export const useCreateExample = () => {
  const queryClient = useQueryClient();
  
  return useMutation(exampleApi.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('examples');
    },
  });
};
```

## 🎨 コーディング規約

### Python (バックエンド)

**PEP 8準拠:**
```python
# 良い例
def calculate_vulnerability_score(cve_data: dict) -> float:
    """CVSSスコアを計算"""
    base_score = cve_data.get("baseScore", 0.0)
    temporal_score = cve_data.get("temporalScore", 0.0)
    return (base_score + temporal_score) / 2

# 悪い例
def calc(d):
    return (d.get("baseScore",0)+d.get("temporalScore",0))/2
```

**型ヒントの使用:**
```python
from typing import List, Optional, Dict

def process_sbom(
    sbom_data: Dict[str, Any],
    include_dev: bool = False
) -> List[Component]:
    pass
```

**docstringの記述:**
```python
def scan_vulnerabilities(sbom_id: int) -> ScanResult:
    """
    SBOMに対して脆弱性スキャンを実行
    
    Args:
        sbom_id: スキャン対象のSBOM ID
        
    Returns:
        ScanResult: スキャン結果
        
    Raises:
        SBOMNotFoundException: SBOMが見つからない場合
    """
    pass
```

### TypeScript (フロントエンド)

**型の明示:**
```typescript
// 良い例
interface User {
  id: number;
  name: string;
  email: string;
}

const user: User = {
  id: 1,
  name: "John",
  email: "john@example.com"
};

// 悪い例
const user = {
  id: 1,
  name: "John",
  email: "john@example.com"
};
```

**コンポーネントの型定義:**
```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}

const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  disabled = false,
  variant = 'primary'
}) => {
  // ...
};
```

## 🧪 テスト戦略

### バックエンドテスト

**ユニットテスト:**
```python
# tests/unit/test_sbom_parser.py
def test_parse_cyclonedx():
    parser = CycloneDXParser()
    result = parser.parse(sample_sbom)
    assert len(result.components) == 10
    assert result.format == "cyclonedx"
```

**統合テスト:**
```python
# tests/integration/test_scan_flow.py
def test_full_scan_flow(client, db):
    # SBOMアップロード
    response = client.post("/api/v1/sbom/upload", files={"file": sbom_file})
    sbom_id = response.json()["data"]["sbom_id"]
    
    # スキャン実行
    response = client.post(f"/api/v1/scan/{sbom_id}")
    scan_id = response.json()["data"]["scan_id"]
    
    # 結果確認
    response = client.get(f"/api/v1/scan/{scan_id}")
    assert response.status_code == 200
```

### フロントエンドテスト

**コンポーネントテスト (Jest):**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import ExampleComponent from './ExampleComponent';

test('renders component and handles click', () => {
  const mockAction = jest.fn();
  render(<ExampleComponent title="Test" onAction={mockAction} />);
  
  expect(screen.getByText('Test')).toBeInTheDocument();
  
  fireEvent.click(screen.getByText('実行'));
  expect(mockAction).toHaveBeenCalled();
});
```

## 🔄 Git ワークフロー

### ブランチ戦略

```
main          (本番環境)
  ↑
develop       (開発環境)
  ↑
feature/*     (機能開発)
bugfix/*      (バグ修正)
hotfix/*      (緊急修正)
```

### コミットメッセージ

```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
style: コードフォーマット
refactor: リファクタリング
test: テスト追加
chore: ビルド・設定変更

例:
feat: Add PDF export functionality for scan results
fix: Resolve database connection timeout issue
docs: Update API documentation for vulnerability endpoints
```

### プルリクエスト

**テンプレート:**
```markdown
## 変更内容
- 変更の概要

## 関連Issue
- Closes #123

## テスト
- [ ] ユニットテスト追加
- [ ] 統合テスト実施
- [ ] 手動テスト完了

## チェックリスト
- [ ] コードレビュー依頼済み
- [ ] ドキュメント更新済み
- [ ] 変更ログ更新済み
```

## 📦 リリースプロセス

1. **開発ブランチでの作業完了**
2. **テスト実行**
   ```bash
   docker-compose run backend pytest
   docker-compose run frontend npm test
   ```
3. **バージョン番号の更新**
4. **CHANGELOG.mdの更新**
5. **mainブランチへのマージ**
6. **タグの作成**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```
7. **Docker イメージのビルドとpush**

## 🐛 デバッグのヒント

### バックエンドデバッグ

**ログレベルの変更:**
```python
# app/config.py
LOG_LEVEL = "DEBUG"
```

**pdbの使用:**
```python
import pdb; pdb.set_trace()
```

**Dockerコンテナ内でのデバッグ:**
```bash
docker-compose exec backend python
>>> from app.services.sbom_parser import parse_sbom
>>> result = parse_sbom(data)
```

### フロントエンドデバッグ

**React DevToolsの使用**

**コンソールログ:**
```typescript
console.log('Debug:', data);
console.table(arrayData);
```

**ネットワークタブでAPI確認**

## 📞 質問とサポート

- GitHub Issues
- 開発者Slack
- 週次ミーティング

---

**Happy Coding! 🎉**

**最終更新: 2025年10月16日**
