import { http, HttpResponse } from 'msw';
import type { UploadResponse, VectorQueryResponse, GraphQueryResponse } from '../../src/types';

const mockUploadResponse: UploadResponse = {
  document_id: 'doc-abc-123',
  filename: 'example-document.pdf',
  status: 'processed',
};

const mockVectorQueryResponse: VectorQueryResponse = {
  query: 'What is retrieval augmented generation?',
  results: [
    {
      query: 'What is retrieval augmented generation?',
      answer:
        'Retrieval Augmented Generation (RAG) is a technique that combines document retrieval with language model generation to produce grounded answers.',
      sources: ['example-document.pdf', 'rag-overview.pdf'],
      score: 0.92,
      rag_type: 'vector',
    },
    {
      query: 'What is retrieval augmented generation?',
      answer:
        'RAG enhances LLM outputs by first retrieving relevant passages from a knowledge base before generating a response.',
      sources: ['example-document.pdf'],
      score: 0.87,
      rag_type: 'vector',
    },
  ],
};

const mockGraphQueryResponse: GraphQueryResponse = {
  query: 'What is retrieval augmented generation?',
  results: [
    {
      query: 'What is retrieval augmented generation?',
      answer:
        'RAG connects a retrieval system with a generative model, using a knowledge graph to traverse entity relationships for more structured answers.',
      sources: ['example-document.pdf', 'knowledge-graph-intro.pdf'],
      score: 0.89,
      rag_type: 'graph',
    },
  ],
};

export const handlers = [
  http.post('*/api/upload', () => {
    return HttpResponse.json(mockUploadResponse);
  }),

  http.post('*/api/query/vector', () => {
    return HttpResponse.json(mockVectorQueryResponse);
  }),

  http.post('*/api/query/graph', () => {
    return HttpResponse.json(mockGraphQueryResponse);
  }),
];
