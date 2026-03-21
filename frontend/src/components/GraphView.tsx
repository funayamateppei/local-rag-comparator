import ForceGraph2D from 'react-force-graph-2d';
import type { GraphData, GraphNode } from '../types';
import './GraphView.css';

export interface GraphViewProps {
  data: GraphData;
  width?: number;
  height?: number;
}

function getNodeColor(node: GraphNode, links: GraphData['links']): string {
  const connectionCount = links.filter(
    (l) => l.source === node.id || l.target === node.id,
  ).length;
  const brightness = Math.min(100, 40 + connectionCount * 15);
  return `hsl(210, 80%, ${brightness}%)`;
}

export default function GraphView({ data, width = 600, height = 400 }: GraphViewProps) {
  if (data.nodes.length === 0) {
    return (
      <div className="graph-view-container">
        <div className="graph-view-empty">グラフデータがありません</div>
      </div>
    );
  }

  return (
    <div className="graph-view-container">
      <ForceGraph2D
        graphData={data}
        width={width}
        height={height}
        nodeLabel="name"
        nodeColor={(node: GraphNode) => getNodeColor(node, data.links)}
        linkLabel="label"
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
      />
    </div>
  );
}
