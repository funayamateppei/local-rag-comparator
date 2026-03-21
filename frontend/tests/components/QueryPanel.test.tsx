import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import QueryPanel from '../../src/components/QueryPanel';

describe('QueryPanel', () => {
  it('renders query input and submit button', () => {
    render(<QueryPanel />);

    expect(screen.getByLabelText('検索クエリ')).toBeInTheDocument();
    expect(screen.getByLabelText('検索')).toBeInTheDocument();
  });

  it('submits query and shows both vector and graph results', async () => {
    const user = userEvent.setup();
    render(<QueryPanel />);

    const input = screen.getByLabelText('検索クエリ');
    const button = screen.getByLabelText('検索');

    await user.type(input, 'What is retrieval augmented generation?');
    await user.click(button);

    await waitFor(() => {
      expect(screen.getByLabelText('Vector RAG結果')).toBeInTheDocument();
      expect(screen.getByLabelText('Graph RAG結果')).toBeInTheDocument();
    });

    // Vector result content
    expect(
      screen.getByText(/Retrieval Augmented Generation \(RAG\) is a technique/),
    ).toBeInTheDocument();
    expect(screen.getByText('92%')).toBeInTheDocument();

    // Graph result content
    expect(
      screen.getByText(/RAG connects a retrieval system with a generative model/),
    ).toBeInTheDocument();
    expect(screen.getByText('89%')).toBeInTheDocument();
  });

  it('shows loading state during query', async () => {
    // Delay the responses to observe loading state
    server.use(
      http.post('*/api/query/vector', async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return HttpResponse.json({
          query: 'test',
          results: [],
        });
      }),
      http.post('*/api/query/graph', async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return HttpResponse.json({
          query: 'test',
          results: [],
        });
      }),
    );

    const user = userEvent.setup();
    render(<QueryPanel />);

    await user.type(screen.getByLabelText('検索クエリ'), 'test query');
    await user.click(screen.getByLabelText('検索'));

    expect(screen.getByText('検索中...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText('検索中...')).not.toBeInTheDocument();
    });
  });

  it('shows error message on failure', async () => {
    server.use(
      http.post('*/api/query/vector', () => {
        return HttpResponse.json({ detail: 'Vector search failed' }, { status: 500 });
      }),
      http.post('*/api/query/graph', () => {
        return HttpResponse.json({ detail: 'Graph search failed' }, { status: 500 });
      }),
    );

    const user = userEvent.setup();
    render(<QueryPanel />);

    await user.type(screen.getByLabelText('検索クエリ'), 'failing query');
    await user.click(screen.getByLabelText('検索'));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('disables input during loading', async () => {
    server.use(
      http.post('*/api/query/vector', async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return HttpResponse.json({ query: 'test', results: [] });
      }),
      http.post('*/api/query/graph', async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return HttpResponse.json({ query: 'test', results: [] });
      }),
    );

    const user = userEvent.setup();
    render(<QueryPanel />);

    const input = screen.getByLabelText('検索クエリ');
    await user.type(input, 'test query');
    await user.click(screen.getByLabelText('検索'));

    expect(input).toBeDisabled();

    await waitFor(() => {
      expect(input).not.toBeDisabled();
    });
  });

  it('calls onQueryResult callback with results', async () => {
    const onQueryResult = vi.fn();
    const user = userEvent.setup();
    render(<QueryPanel onQueryResult={onQueryResult} />);

    await user.type(screen.getByLabelText('検索クエリ'), 'What is RAG?');
    await user.click(screen.getByLabelText('検索'));

    await waitFor(() => {
      expect(onQueryResult).toHaveBeenCalledTimes(1);
    });

    const [vectorArg, graphArg] = onQueryResult.mock.calls[0];
    expect(vectorArg.results).toBeDefined();
    expect(graphArg.results).toBeDefined();
    expect(vectorArg.results[0].rag_type).toBe('vector');
    expect(graphArg.results[0].rag_type).toBe('graph');
  });
});
