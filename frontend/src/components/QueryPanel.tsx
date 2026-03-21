import { useState } from 'react';
import type { FormEvent } from 'react';
import type { VectorQueryResponse, GraphQueryResponse, QueryResultItem } from '../types';
import { queryVector, queryGraph } from '../api/client';
import './QueryPanel.css';

export interface QueryPanelProps {
  onQueryResult?: (vector: VectorQueryResponse, graph: GraphQueryResponse) => void;
}

interface HistoryEntry {
  query: string;
  vector: VectorQueryResponse;
  graph: GraphQueryResponse;
}

function getScoreClass(score: number): string {
  if (score >= 0.8) return 'query-panel-score-high';
  if (score >= 0.5) return 'query-panel-score-medium';
  return 'query-panel-score-low';
}

function ResultCard({ item }: { item: QueryResultItem }) {
  return (
    <div className="query-panel-card">
      <div className="query-panel-card-header">
        <span
          className={`query-panel-badge ${
            item.rag_type === 'vector' ? 'query-panel-badge-vector' : 'query-panel-badge-graph'
          }`}
        >
          {item.rag_type}
        </span>
        <span className={`query-panel-score ${getScoreClass(item.score)}`}>
          {Math.round(item.score * 100)}%
        </span>
      </div>
      <p className="query-panel-answer">{item.answer}</p>
      <div className="query-panel-sources">
        {item.sources.map((source) => (
          <span key={source} className="query-panel-source-tag">
            {source}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function QueryPanel({ onQueryResult }: QueryPanelProps) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);

    try {
      const [vectorRes, graphRes] = await Promise.all([
        queryVector(trimmed),
        queryGraph(trimmed),
      ]);

      setHistory((prev) => [{ query: trimmed, vector: vectorRes, graph: graphRes }, ...prev]);
      setInput('');
      onQueryResult?.(vectorRes, graphRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : '検索中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="query-panel">
      <form className="query-panel-form" onSubmit={handleSubmit}>
        <input
          className="query-panel-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="質問を入力してください..."
          aria-label="検索クエリ"
          disabled={loading}
        />
        <button
          className="query-panel-submit"
          type="submit"
          aria-label="検索"
          disabled={loading || !input.trim()}
        >
          検索
        </button>
      </form>

      {loading && (
        <div className="query-panel-loading">
          <div className="query-panel-spinner" />
          <span>検索中...</span>
        </div>
      )}

      {error && <div className="query-panel-error" role="alert">{error}</div>}

      <div className="query-panel-history">
        {history.map((entry) => (
          <div key={`${entry.query}-${history.indexOf(entry)}`} className="query-panel-entry">
            <div className="query-panel-query-text">Q: {entry.query}</div>
            <div className="query-panel-comparison">
              <div className="query-panel-column" aria-label="Vector RAG結果">
                <div className="query-panel-column-title">Vector RAG</div>
                {entry.vector.results.map((item, i) => (
                  <ResultCard key={`v-${i.toString()}`} item={item} />
                ))}
              </div>
              <div className="query-panel-column" aria-label="Graph RAG結果">
                <div className="query-panel-column-title">Graph RAG</div>
                {entry.graph.results.map((item, i) => (
                  <ResultCard key={`g-${i.toString()}`} item={item} />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
