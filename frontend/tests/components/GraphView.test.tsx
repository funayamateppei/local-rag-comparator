import { render, screen } from '@testing-library/react';
import type { GraphData, QueryResultItem } from '../../src/types';
import GraphView from '../../src/components/GraphView';
import { buildGraphFromResults } from '../../src/utils/graphBuilder';

vi.mock('react-force-graph-2d', () => ({
  default: (props: Record<string, unknown>) => (
    <div data-testid="force-graph" data-nodes={JSON.stringify((props.graphData as { nodes: unknown[] })?.nodes)} />
  ),
}));

describe('GraphView', () => {
  const sampleData: GraphData = {
    nodes: [
      { id: '1', name: 'Node A', val: 1 },
      { id: '2', name: 'Node B', val: 2 },
    ],
    links: [{ source: '1', target: '2', label: 'relates' }],
  };

  it('renders the graph container', () => {
    const { container } = render(<GraphView data={sampleData} />);
    expect(container.querySelector('.graph-view-container')).toBeInTheDocument();
  });

  it('passes correct data to ForceGraph2D', () => {
    render(<GraphView data={sampleData} />);
    const graph = screen.getByTestId('force-graph');
    const nodes = JSON.parse(graph.getAttribute('data-nodes')!);
    expect(nodes).toHaveLength(2);
    expect(nodes[0].name).toBe('Node A');
    expect(nodes[1].name).toBe('Node B');
  });

  it('shows empty message when no data', () => {
    render(<GraphView data={{ nodes: [], links: [] }} />);
    expect(screen.getByText('グラフデータがありません')).toBeInTheDocument();
    expect(screen.queryByTestId('force-graph')).not.toBeInTheDocument();
  });
});

describe('buildGraphFromResults', () => {
  it('creates correct graph structure', () => {
    const results: QueryResultItem[] = [
      {
        query: 'What is RAG?',
        answer: 'RAG is retrieval augmented generation.',
        sources: ['doc1.pdf', 'doc2.pdf'],
        score: 0.95,
        rag_type: 'vector',
      },
      {
        query: 'What is RAG?',
        answer: 'Another answer.',
        sources: ['doc1.pdf', 'doc3.pdf'],
        score: 0.88,
        rag_type: 'graph',
      },
    ];

    const graph = buildGraphFromResults(results);

    // One query node (deduplicated), three unique source nodes
    expect(graph.nodes).toHaveLength(4);
    expect(graph.nodes.find((n) => n.name === 'What is RAG?')).toBeDefined();
    expect(graph.nodes.find((n) => n.name === 'doc1.pdf')).toBeDefined();
    expect(graph.nodes.find((n) => n.name === 'doc2.pdf')).toBeDefined();
    expect(graph.nodes.find((n) => n.name === 'doc3.pdf')).toBeDefined();

    // 4 links: 2 from first result + 2 from second result
    expect(graph.links).toHaveLength(4);
    expect(graph.links[0].label).toBe('score: 0.95');
  });
});
