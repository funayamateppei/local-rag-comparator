import { useState } from 'react';
import type { VectorQueryResponse, GraphQueryResponse, GraphData } from './types';
import FileUpload from './components/FileUpload';
import QueryPanel from './components/QueryPanel';
import GraphView from './components/GraphView';
import { buildGraphFromResults } from './utils/graphBuilder';
import './App.css';

function App() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [activeTab, setActiveTab] = useState<'upload' | 'query'>('upload');

  const handleQueryResult = (vector: VectorQueryResponse, graph: GraphQueryResponse) => {
    const allResults = [...vector.results, ...graph.results];
    setGraphData(buildGraphFromResults(allResults));
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Local RAG Comparator</h1>
        <p className="app-subtitle">Vector RAG vs Graph RAG 比較検証ツール</p>
      </header>

      <nav className="app-tabs">
        <button
          className={`app-tab${activeTab === 'upload' ? ' app-tab--active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          ドキュメントアップロード
        </button>
        <button
          className={`app-tab${activeTab === 'query' ? ' app-tab--active' : ''}`}
          onClick={() => setActiveTab('query')}
        >
          検索・比較
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'upload' && (
          <section className="app-section">
            <FileUpload />
          </section>
        )}

        {activeTab === 'query' && (
          <>
            <section className="app-section">
              <QueryPanel onQueryResult={handleQueryResult} />
            </section>
            <section className="app-section">
              <h2 className="app-section-title">ナレッジグラフ可視化</h2>
              <GraphView data={graphData} width={800} height={450} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
