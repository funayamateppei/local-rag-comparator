NODE_VERSION := $(shell cat .node-version)
OLLAMA_MODELS  := qwen2.5:14b bge-m3

.PHONY: setup check-deps check-ollama up down dev dev-be dev-fe lint lint-be lint-fe format format-be format-fe test test-be test-fe logs benchmark

## 必要な外部ツールの存在とバージョンを確認する
check-deps:
	@echo "==> 必要なツールを確認中..."
	@command -v ollama >/dev/null 2>&1 || { echo "❌ ollama が見つかりません。https://ollama.com からインストールしてください。"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "❌ node が見つかりません。https://nodejs.org からインストールしてください。"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "❌ docker が見つかりません。https://docs.docker.com/get-docker/ からインストールしてください。"; exit 1; }
	@ACTUAL_NODE=$$(node -v | sed 's/^v//; s/\..*//'); \
	EXPECTED_NODE=$$(cat .node-version); \
	if [ "$$ACTUAL_NODE" != "$$EXPECTED_NODE" ]; then \
		echo "❌ Node.js メジャーバージョンが一致しません (期待: v$$EXPECTED_NODE.x, 実際: $$(node -v))"; \
		exit 1; \
	fi
	@echo "✅ すべてのツールが確認できました。"

## すべての初期セットアップを実行する
setup: check-deps check-ollama
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
	@echo "==> ChromaDB イメージを取得中..."
	docker compose pull
	@echo ""
	@echo "✅ セットアップ完了！"
	@echo ""
	@echo "  起動するには："
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

## ChromaDB + Backend + Frontend をすべて起動する (Ctrl+C で一括停止)
up: check-ollama
	@docker compose up -d
	@echo ""
	@echo "✅ 起動中..."
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  ChromaDB: http://localhost:8001"
	@echo ""
	@echo "  Ctrl+C で全プロセスを停止します"
	@echo ""
	@trap 'echo ""; echo "==> 停止中..."; docker compose down; echo "✅ 停止完了"; exit 0' INT TERM; \
	cd backend && .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 | sed 's/^/💧 /' & \
	cd frontend && npx vite --host 0.0.0.0 2>&1 | sed 's/^/🔥 /' & \
	wait

## すべて停止する
down:
	docker compose down
	@echo "✅ 停止完了"

## Backend のみローカル起動する (フォアグラウンド)
dev-be: check-ollama
	cd backend && .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

## Frontend のみローカル起動する (フォアグラウンド)
dev-fe:
	cd frontend && npm run dev

## すべてのリントをローカル環境で実行する
lint: lint-be lint-fe

## バックエンドのリントを実行する
lint-be:
	cd backend && .venv/bin/ruff check src/ tests/
	cd backend && .venv/bin/ruff format --check src/ tests/

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

## ベンチマークを実行する (Vector RAG vs Graph RAG)
benchmark:
	cd backend && .venv/bin/python ../benchmark/run.py --base-url http://localhost:8000
