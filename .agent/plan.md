# Local RAG Comparator (GraphRAG vs Vector RAG) - TDD & Docker Edition

## 1. プロジェクトの目的
完全ローカル環境（Mac M4 24GB）において、「通常のVector RAG」と「Microsoft GraphRAG」の検索精度・取得アプローチを比較検証するWebアプリケーションを構築する。
t-wada氏の提唱するTDD（テスト駆動開発：Red-Green-Refactor）を実践し、クリーンアーキテクチャ（DDD準拠）とDockerを採用。堅牢かつ変更に強いモダンなAIアプリケーションのベストプラクティスとして、Zenn/Qiitaでの技術記事化を目指す。

## 2. システムアーキテクチャ (Docker + Native Mac + TDD)
- **開発者体験 (DX) の統合**:
  - `Makefile` を起点とし、`make setup` でAIモデルのPullからコンテナビルドまで一括完了。
  - `make up` 実行時にMacホスト上のOllamaの生存確認と自動バックグラウンド起動を行う。
- **Host (Mac Native - GPU活用)**:
  - Ollama (LLM: qwen2.5:14b / Embedding: avr/sfr-embedding-mistral:f16)
- **Docker Compose Network**:
  - **backend**: FastAPI, GraphRAG CLI連携, PyMuPDF (Python 3.11)
  - **frontend**: React + Vite + react-force-graph (Node.js)
  - **vectordb**: ChromaDB Server
- **コア処理 (GraphRAG)**:
  - Microsoft公式 graphrag パッケージ (Python)
  - 公式リポジトリ: [microsoft/graphrag](https://github.com/microsoft/graphrag)
- **Testing Frameworks**:
  - Backend: pytest, pytest-mock, pytest-asyncio
  - Frontend: Vitest, React Testing Library, MSW (APIモック)

## 3. ディレクトリ構成
```txt
/ (root)
 ├── Makefile             # 開発環境のセットアップ・起動・テスト用コマンド集
 ├── docker-compose.yml   # BE, FE, VectorDB のコンテナ定義
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

### Phase 1: 開発基盤の構築とセットアップ自動化
- [ ] バックエンドディレクトリの作成 (`backend/`) と `Dockerfile`, `requirements.txt` の配置
- [ ] フロントエンドのVite初期化 (`npm create vite@latest frontend -- --template react-ts`) と `Dockerfile` の配置
- [ ] ルートディレクトリに `docker-compose.yml` を作成
- [ ] ルートディレクトリに `Makefile` を作成 (`setup`, `check-ollama`, `up`, `down`, `test-backend` コマンドを定義)
- [ ] ターミナルで `make setup` を実行し、OllamaモデルのPullとDockerイメージのビルドを完了させる
- [ ] ターミナルで `make up` を実行し、全環境が立ち上がるか確認する

### Phase 2: ドメイン層 & アプリケーション層の実装 (TDD実践)
- [ ] 【Red】Domain: Document, QueryResult, GraphData の振る舞いに対するテストを `tests/unit/` に記述
- [ ] 【Green-Refactor】Domain: エンティティとインターフェース (IDocumentParser 等) の実装
- [ ] 【Red】Application: モック (pytest-mock) を使用した UploadDocumentUseCase, CompareRAGUseCase のテストを記述
- [ ] 【Green-Refactor】Application: ユースケースのビジネスロジック実装

### Phase 3: インフラストラクチャ層の実装 (外部結合)
- [ ] 【Red-Green】PyMuPDF を用いた IDocumentParser 実装と統合テスト
- [ ] 【Red-Green】ChromaDB と通信する IVectorRepository 実装と統合テスト
- [ ] 【Red-Green】IGraphRepository 実装 (host.docker.internal:11434 を向く settings.yaml 動的生成とCLIラッパー)

### Phase 4: インターフェース層 (FastAPI) と DI
- [ ] ルーター設定 (/api/upload, /api/query/vector, /api/query/graph) とE2Eテスト
- [ ] main.py にてDI構成を行い FastAPI を起動
- [ ] `make test-backend` を実行して全テストが通るか確認

### Phase 5: React フロントエンドの開発 (TDD実践)
- [ ] 【Red-Green】UIコンポーネント (アップロード、チャット画面) のテストを記述 (React Testing Library)
- [ ] Vite環境でのUI実装 (API通信先を backend コンテナに設定)
- [ ] react-force-graph を用いたネットワーク図のレンダリング実装
- [ ] 全体の動作確認 (`make up`)

### Phase 6: テスト・比較検証と記事執筆
- [ ] 走れメロス等の文書で動作テスト
- [ ] 精度比較・レスポンス速度の計測
- [ ] Zenn/Qiita向け記事執筆 (TDD×クリーンアーキテクチャ×AIハイブリッド構成の設計思想・DXの工夫を熱く語る)