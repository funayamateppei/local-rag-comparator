import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import FileUpload from '../../src/components/FileUpload';

function createTestFile(name = 'test.pdf', type = 'application/pdf') {
  return new File(['dummy content'], name, { type });
}

describe('FileUpload', () => {
  it('renders the upload area', () => {
    render(<FileUpload />);
    expect(screen.getByLabelText('ファイルドロップゾーン')).toBeInTheDocument();
    expect(screen.getByLabelText('ファイルを選択')).toBeInTheDocument();
    expect(screen.getByLabelText('アップロード')).toBeDisabled();
  });

  it('shows file name after file selection', async () => {
    const user = userEvent.setup();
    render(<FileUpload />);

    const input = screen.getByLabelText('ファイルを選択');
    const file = createTestFile('report.pdf');
    await user.upload(input, file);

    expect(screen.getByLabelText('選択されたファイル名')).toHaveTextContent('report.pdf');
    expect(screen.getByLabelText('アップロード')).toBeEnabled();
  });

  it('shows success message after successful upload', async () => {
    const user = userEvent.setup();
    render(<FileUpload />);

    const input = screen.getByLabelText('ファイルを選択');
    await user.upload(input, createTestFile());

    await user.click(screen.getByLabelText('アップロード'));

    await waitFor(() => {
      expect(screen.getByText('アップロード成功')).toBeInTheDocument();
    });
    expect(screen.getByText(/doc-abc-123/)).toBeInTheDocument();
    expect(screen.getByText(/example-document\.pdf/)).toBeInTheDocument();
  });

  it('shows error message when upload fails', async () => {
    server.use(
      http.post('*/api/upload', () => {
        return HttpResponse.json(
          { detail: 'ファイル形式が不正です' },
          { status: 400 },
        );
      }),
    );

    const user = userEvent.setup();
    render(<FileUpload />);

    const input = screen.getByLabelText('ファイルを選択');
    await user.upload(input, createTestFile());

    await user.click(screen.getByLabelText('アップロード'));

    await waitFor(() => {
      expect(screen.getByLabelText('エラーメッセージ')).toHaveTextContent(
        'ファイル形式が不正です',
      );
    });
  });

  it('shows loading indicator during upload', async () => {
    let resolveUpload!: () => void;
    server.use(
      http.post('*/api/upload', () => {
        return new Promise<Response>((resolve) => {
          resolveUpload = () =>
            resolve(
              HttpResponse.json({
                document_id: 'doc-abc-123',
                filename: 'test.pdf',
                status: 'processed',
              }),
            );
        });
      }),
    );

    const user = userEvent.setup();
    render(<FileUpload />);

    const input = screen.getByLabelText('ファイルを選択');
    await user.upload(input, createTestFile());

    await user.click(screen.getByLabelText('アップロード'));

    expect(screen.getByLabelText('アップロード中')).toBeInTheDocument();

    resolveUpload();

    await waitFor(() => {
      expect(screen.queryByLabelText('アップロード中')).not.toBeInTheDocument();
    });
  });

  it('calls onUploadComplete callback on success', async () => {
    const onUploadComplete = vi.fn();
    const user = userEvent.setup();
    render(<FileUpload onUploadComplete={onUploadComplete} />);

    const input = screen.getByLabelText('ファイルを選択');
    await user.upload(input, createTestFile());

    await user.click(screen.getByLabelText('アップロード'));

    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalledWith({
        document_id: 'doc-abc-123',
        filename: 'example-document.pdf',
        status: 'processed',
      });
    });
  });

  it('resets state when reset button is clicked', async () => {
    const user = userEvent.setup();
    render(<FileUpload />);

    const input = screen.getByLabelText('ファイルを選択');
    await user.upload(input, createTestFile());
    await user.click(screen.getByLabelText('アップロード'));

    await waitFor(() => {
      expect(screen.getByText('アップロード成功')).toBeInTheDocument();
    });

    await user.click(screen.getByText('別のファイルをアップロード'));

    expect(screen.getByLabelText('ファイルドロップゾーン')).toBeInTheDocument();
    expect(screen.queryByText('アップロード成功')).not.toBeInTheDocument();
  });
});
