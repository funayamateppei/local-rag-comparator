export interface UploadResponse {
  document_id: string;
  filename: string;
  status: string;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
}

export interface QueryResultItem {
  query: string;
  answer: string;
  sources: string[];
  score: number;
  rag_type: 'vector' | 'graph';
}

export interface VectorQueryResponse {
  query: string;
  results: QueryResultItem[];
}

export interface GraphQueryResponse {
  query: string;
  results: QueryResultItem[];
}

export interface ErrorResponse {
  detail: string;
}

// For react-force-graph-2d
export interface GraphNode {
  id: string;
  name: string;
  val?: number;
}

export interface GraphLink {
  source: string;
  target: string;
  label?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}
