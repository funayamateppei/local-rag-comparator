import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../src/App';

vi.mock('react-force-graph-2d', () => ({
  default: () => <div data-testid="force-graph" />,
}));

describe('App', () => {
  it('renders the app title', () => {
    render(<App />);
    expect(screen.getByText('Local RAG Comparator')).toBeInTheDocument();
  });

  it('renders navigation tabs', () => {
    render(<App />);
    expect(screen.getByText('ドキュメントアップロード')).toBeInTheDocument();
    expect(screen.getByText('検索・比較')).toBeInTheDocument();
  });

  it('shows upload section by default', () => {
    render(<App />);
    expect(screen.getByLabelText('ファイルドロップゾーン')).toBeInTheDocument();
  });

  it('switches to query tab', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByText('検索・比較'));
    expect(screen.getByLabelText('検索クエリ')).toBeInTheDocument();
    expect(screen.getByText('ナレッジグラフ可視化')).toBeInTheDocument();
  });
});
