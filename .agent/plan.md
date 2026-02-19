# Local RAG Comparator (GraphRAG vs Vector RAG) - TDD & Docker Edition

## 1. プロジェクトの目的
完全ローカル環境（Mac M4 24GB）において、「通常のVector RAG」と「Microsoft GraphRAG」の検索精度・取得アプローチを比較検証するWebアプリケーションを構築する。
t-wada氏の提唱するTDD（テスト駆動開発：Red-Green-Refactor）を実践し、クリーンアーキテクチャ（DDD準拠）とDockerを採用。堅牢かつ変更に強いモダンなAIアプリケーションのベストプラクティスとして、Zenn/Qiitaでの技術記事化を目指す。

## 2. システムアーキテクチャ (Docker + Native Mac + TDD)
- **Host (Mac Native - GPU活用)**:
  - Ollama (LLM: qwen2.5:14b / Embedding: avr/sfr-embedding-mistral:f16)
- **Docker Compose Network**:
  - **backend**: FastAPI, GraphRAG CLI連携, PyMuPDF (Python 3.11)
  - **frontend**: React + Vite + react-force-graph (Node.js)
  - **vectordb**: ChromaDB Server
- **Testing Frameworks**:
  - Backend: pytest, pytest-mock, pytest-asyncio
  - Frontend: Vitest, React Testing Library, MSW (APIモック)

## 3. ディレクトリ構成
```txt
/ (root)
 ├── docker-compose.yml
 ├── backend/
 │    ├── Dockerfile
 │    ├── requirements.txt
 │    ├── src/
 │    │    ├── domain/            # Entities, Interfaces
 │    │    ├── application/       # UseCases
 │    │    ├── infrastructure/    # ChromaDB, GraphRAG, PyMuPDF
 │    │    ├── interfaces/        # FastAPI Routers
 │    │    ├── core/              # DI, Settings
 │    │    └── main.py
 │    └── tests/                  # pytest (TDDの主戦場)
 │         ├── unit/              # Domain, Application層の高速テスト
 │         └── integration/       # Infrastructure, Interfaces層の結合テスト
 └── frontend/
      ├── Dockerfile
      ├── package.json
      ├── src/
      └── tests/                  # Vitest (コンポーネントテスト)
```

## 4. 実装フェーズ (TDDサイクル: Red -> Green -> Refactor)

### Phase 1: ホスト環境 (Mac) のAI準備
- [ ] パッケージインストール: brew install ollama
- [ ] バックグラウンド起動: brew services start ollama
- [ ] LLMとEmbeddingのPull: ollama pull qwen2.5:14b && ollama pull avr/sfr-embedding-mistral:f16
- [ ] プロジェクトフォルダ作成: mkdir local-rag-comparator && cd local-rag-comparator

### Phase 2: Dockerインフラ基盤とテスト環境の構築
- [ ] docker-compose.yml の作成 (backend, frontend, vectordb)
- [ ] backend: Dockerfile, requirements.txt (pytest等を含む) を作成
- [ ] frontend: Dockerfile, package.json (Vitest等を含む) を作成
- [ ] テストランナーの起動確認: docker-compose run --rm backend pytest

### Phase 3: ドメイン層 & アプリケーション層の実装 (TDD実践)
- [ ] 【Red】Domain: Document, QueryResult, GraphData の振る舞いに対するテストを `tests/unit/` に記述
- [ ] 【Green-Refactor】Domain: エンティティとインターフェース (IDocumentParser 等) の実装
- [ ] 【Red】Application: モック (pytest-mock) を使用した UploadDocumentUseCase, CompareRAGUseCase のテストを記述
- [ ] 【Green-Refactor】Application: ユースケースのビジネスロジック実装

### Phase 4: インフラストラクチャ層の実装 (外部結合)
- [ ] 【Red-Green】PyMuPDF を用いた IDocumentParser 実装と統合テスト
- [ ] 【Red-Green】ChromaDB と通信する IVectorRepository 実装と統合テスト
- [ ] 【Red-Green】IGraphRepository 実装 (host.docker.internal:11434 を向く settings.yaml 動的生成とCLIラッパー)

### Phase 5: インターフェース層 (FastAPI) と DI
- [ ] ルーター設定 (/api/upload, /api/query/vector, /api/query/graph) とE2Eテスト
- [ ] main.py にてDI構成を行い FastAPI を起動
- [ ] バックエンド環境の結合確認: docker-compose up --build backend vectordb

### Phase 6: React フロントエンドの開発 (TDD実践)
- [ ] 【Red-Green】UIコンポーネント (アップロード、チャット画面) のテストを記述 (React Testing Library)
- [ ] Vite環境でのUI実装 (API通信先を backend コンテナに設定)
- [ ] react-force-graph を用いたネットワーク図のレンダリング実装
- [ ] 全コンテナの起動: docker-compose up --build

### Phase 7: テスト・比較検証と記事執筆
- [ ] 走れメロス等の文書で動作テスト
- [ ] 精度比較・レスポンス速度の計測
- [ ] Zenn/Qiita向け記事執筆 (TDD×クリーンアーキテクチャ×AIハイブリッド構成の設計思想を熱く語る)