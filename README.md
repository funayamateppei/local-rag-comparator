# Local RAG Comparator (GraphRAG vs Vector RAG)



完全ローカル環境（Mac Apple Silicon）で動作する、「通常のVector RAG」と「Microsoft GraphRAG」の比較・検証プラットフォームです。
外部API（OpenAIなど）に一切依存せず、プライバシーを保ったまま高度なRAGの精度比較を行うことができます。

## 🌟 特徴 (Features)

- **完全ローカル稼働**: Ollamaを利用し、GPU（Metal）を活用したローカルLLMで推論とグラフ生成を実行。
- **ハイブリッド・コンテナ設計**: AIのパフォーマンスを最大化するため「OllamaはMacネイティブ起動（GPU直結）」しつつ、「API・DB・フロントエンドはDockerコンテナ化」するモダンな構成を採用。
- **GraphRAG vs Vector RAG**: ChromaDBによるチャンク検索と、Microsoft `graphrag` によるナレッジグラフ検索を並行実行し、UI上で回答を比較可能。
- **DDD & クリーンアーキテクチャ**: 複雑なAI技術（ChromaDB, GraphRAG CLI, PyMuPDF等）をインフラストラクチャ層に隠蔽し、ビジネスロジックを独立させた保守性の高い設計。
- **TDD (テスト駆動開発)**: t-wada氏の提唱するRed-Green-Refactorサイクルを前提とし、ドメイン層・ユースケース層の堅牢なテストを完備。
- **インタラクティブなUI**: React (`react-force-graph`) を用いて、抽出されたナレッジグラフの繋がりを美しく可視化。
- **Swagger UI 完備**: FastAPIの自動生成機能により、`/docs` エンドポイントでAPI仕様書（OpenAPI）を即座に確認・テスト可能。FE/BEの並行開発を強力にサポート。

## 🏗️ アーキテクチャ

* **Host (Mac Native)**: Ollama (`qwen2.5:14b`, `avr/sfr-embedding-mistral:f16`)
* **Backend (Docker)**: Python 3.11, FastAPI, Microsoft GraphRAG, PyMuPDF, pytest
* **Frontend (Docker)**: Node.js, React (Vite + TypeScript), react-force-graph, Vitest
* **Database (Docker)**: ChromaDB (Vector Search)

## 📋 動作要件 (Prerequisites)

* macOS (Apple Silicon M1/M2/M3/M4) ※推奨メモリ: 24GB以上
* [Homebrew](https://brew.sh/ja/)
* [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)

## 🚀 クイックスタート (Getting Started)

開発者体験（DX）を最大化するため、環境構築から起動までを `Makefile` で完全に自動化しています。

### 1. セットアップ（初回のみ）
Ollamaのインストール確認、LLMモデルのダウンロード（数GB）、Dockerイメージのビルドを一括で行います。
```bash
make setup
```

### 2. アプリケーションの起動
バックグラウンドでのOllamaの起動確認を行い、Dockerコンテナ群を立ち上げます。
```bash
make up
```

起動後、以下のURLにアクセスしてください：

- Frontend (UI): http://localhost:5173
- Backend API Docs: http://localhost:8000/docs

### 3. 終了とクリーンアップ
```bash
make down
```

## 🧪 テストの実行 (TDD)

バックエンド（FastAPI）のテストを実行します。Dockerコンテナ内で `pytest` が走ります。
```bash
make test-backend
```

## 📂 ディレクトリ構成
```txt
/
 ├── Makefile             # 開発用コマンド集
 ├── docker-compose.yml   # コンテナ構成
 ├── backend/             # クリーンアーキテクチャ準拠のPython API
 │    ├── src/
 │    │    ├── domain/         # エンティティ・インターフェース
 │    │    ├── application/    # ユースケース
 │    │    ├── infrastructure/ # ChromaDB, GraphRAGCLI などの実装
 │    │    └── interfaces/     # FastAPI Router
 │    └── tests/          # pytest
 └── frontend/            # React (Vite) + グラフ可視化 UI
 ```

## 📝 参考文献 & クレジット

- Microsoft GraphRAG Repository[https://github.com/microsoft/graphrag]
- Ollama[https://ollama.com/]

## 📄 ライセンス
This project is licensed under the MIT License.