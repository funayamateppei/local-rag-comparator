import type { UploadResponse, VectorQueryResponse, GraphQueryResponse, ErrorResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.detail);
  }

  return response.json() as Promise<UploadResponse>;
}

export async function queryVector(query: string, topK?: number): Promise<VectorQueryResponse> {
  const body: Record<string, unknown> = { query };
  if (topK !== undefined) {
    body.top_k = topK;
  }

  const response = await fetch(`${API_BASE_URL}/api/query/vector`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.detail);
  }

  return response.json() as Promise<VectorQueryResponse>;
}

export async function queryGraph(query: string, topK?: number): Promise<GraphQueryResponse> {
  const body: Record<string, unknown> = { query };
  if (topK !== undefined) {
    body.top_k = topK;
  }

  const response = await fetch(`${API_BASE_URL}/api/query/graph`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.detail);
  }

  return response.json() as Promise<GraphQueryResponse>;
}
