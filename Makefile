NODE_VERSION := $(shell cat .node-version)
OLLAMA_MODELS  := qwen2.5:14b bge-m3

.PHONY: setup check-ollama build up down lint lint-be lint-fe format format-be format-fe test test-be test-fe logs

## すべての初期セットアップを実行する
setup: check-ollama
	@echo "==> Ollama モデルをダウンロード中..."
	@for model in $(OLLAMA_MODELS); do \
		ollama pull $$model; \
	done
	@echo "==> Python venv を作成中..."
	python3 -m venv backend/.venv
	@echo "==> venv に開発用パッケージをインストール中..."
	backend/.venv/bin/pip install --upgrade pip
	backend/.venv/bin/pip install -r backend/requirements-dev.txt
	@echo "==> フロントエンドの依存パッケージをインストール中..."
	cd frontend && npm install
	@echo "==> Docker イメージをビルド中..."
	NODE_VERSION=$(NODE_VERSION) docker compose build
	@echo ""
	@echo "✅ セットアップ完了！"
	@echo ""
	@echo "  Python venv を有効化するには以下を実行してください："
	@echo "  source backend/.venv/bin/activate"
	@echo ""
	@echo "  コンテナを起動するには："
	@echo "  make up"

## Ollama の起動を確認し、未起動なら自動起動する
check-ollama:
	@echo "==> Ollama の起動を確認中..."
	@if ! curl -s http://localhost:11434 > /dev/null 2>&1; then \
		echo "Ollama が起動していません。バックグラウンドで起動します..."; \
		ollama serve &>/dev/null & \
		sleep 3; \
	fi
	@echo "✅ Ollama が起動中です。"

## Docker イメージをビルドする
build:
	NODE_VERSION=$(NODE_VERSION) docker compose build

## 全コンテナを起動する
up: check-ollama
	NODE_VERSION=$(NODE_VERSION) docker compose up -d
	@echo ""
	@echo "✅ 起動完了！"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  ChromaDB: http://localhost:8001"

## 全コンテナを停止する
down:
	docker compose down

## すべてのリントをローカル環境で実行する
lint: lint-be lint-fe

## バックエンドのリントを実行する
lint-be:
	cd backend && .venv/bin/ruff check src/ tests/

## フロントエンドのリントを実行する
lint-fe:
	cd frontend && npm run lint

## すべてのフォーマットをローカル環境で実行する
format: format-be format-fe

## バックエンドのフォーマットを実行する
format-be:
	cd backend && .venv/bin/ruff check --fix src/ tests/ && .venv/bin/ruff format src/ tests/

## フロントエンドのフォーマットを実行する
format-fe:
	cd frontend && npx eslint --fix .

## すべてのテストをローカル環境で実行する (make test / make test-be / make test-fe)
test: test-be test-fe

## バックエンドのテストをローカル環境で実行する
test-be:
	cd backend && .venv/bin/python -m pytest tests/ -v

## フロントエンドのテストをローカル環境で実行する
test-fe:
	cd frontend && npm test

## 全サービスのログを表示する
logs:
	docker compose logs -f
