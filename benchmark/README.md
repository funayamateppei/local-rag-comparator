# Benchmark

RAG Comparator のベンチマークツール。Vector RAG と Graph RAG の性能を比較する。

## 前提条件

- `make up` でサービスが起動していること
- Backend が `http://localhost:8000` で応答すること

## 実行方法

```bash
# Makefile 経由で実行
make benchmark

# または直接実行
python benchmark/run.py --base-url http://localhost:8000

# オプション一覧
python benchmark/run.py --help
```

## オプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--base-url` | `http://localhost:8000` | Backend API の URL |
| `--data-dir` | `./benchmark/data` | テスト文書のディレクトリ |
| `--output` | `./benchmark/results` | 結果出力先ディレクトリ |
| `--top-k` | `3` | 各クエリで取得する結果数 |

## 出力

- `benchmark/results/results_{timestamp}.json` - 詳細な JSON 結果
- `benchmark/results/summary_{timestamp}.md` - Markdown 形式のサマリー（ブログ記事向け）

## テストデータ

- `benchmark/data/hashire_melos.txt` - 太宰治「走れメロス」（パブリックドメイン）
- `benchmark/queries.json` - テストクエリ一覧（5問、各カテゴリ別）
