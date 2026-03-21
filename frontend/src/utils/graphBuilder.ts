import type { GraphData, GraphNode, QueryResultItem } from '../types';

export function buildGraphFromResults(results: QueryResultItem[]): GraphData {
  const nodes: GraphNode[] = [];
  const links: GraphData['links'] = [];
  const nodeIds = new Set<string>();

  for (const result of results) {
    const queryId = `query:${result.query}`;
    if (!nodeIds.has(queryId)) {
      nodeIds.add(queryId);
      nodes.push({ id: queryId, name: result.query, val: 3 });
    }

    for (const source of result.sources) {
      const sourceId = `source:${source}`;
      if (!nodeIds.has(sourceId)) {
        nodeIds.add(sourceId);
        nodes.push({ id: sourceId, name: source, val: 1 });
      }
      links.push({
        source: queryId,
        target: sourceId,
        label: `score: ${result.score.toFixed(2)}`,
      });
    }
  }

  return { nodes, links };
}
