import { useEffect, useRef, useState } from 'react';

const API_BASE = '/api';

type Doc = {
  id: string;
  original_filename: string;
  display_name?: string | null;
  file_type: 'cv' | 'jd';
  file_size: number;
  created_at: string | null;
  job_id: string | null;
  job_title: string | null;
};

type PreviewTarget = { fileId: string; title: string; filename: string };

const IMAGE_EXT = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'];
function fileExt(name: string): string {
  const i = name.lastIndexOf('.');
  return i >= 0 ? name.slice(i + 1).toLowerCase() : '';
}
function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

const ACCEPT = '.pdf,.docx,.pptx,.txt,.rtf';

function fallbackDisplayName(filename: string): string {
  const dotIndex = filename.lastIndexOf('.');
  const name = dotIndex > 0 ? filename.slice(0, dotIndex) : filename;
  return name.replace(/[_-]+/g, ' ').trim() || filename;
}

/**
 * Danh sách CV hoặc JD dùng chung (tham số hóa theo fileType). Cho phép:
 * tạo (upload), xóa (chọn nhiều + xóa tất cả), và xem chi tiết bản gốc trong
 * modal (ảnh/PDF render trực tiếp).
 */
export default function DocumentList({
  accessToken,
  fileType,
  onChanged,
}: {
  accessToken: string;
  fileType: 'cv' | 'jd';
  onChanged?: () => void;
}) {
  const label = fileType.toUpperCase();
  const titleLabel = fileType === 'cv' ? 'Tên CV' : 'Tên JD';
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);

  const [preview, setPreview] = useState<PreviewTarget | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [draftName, setDraftName] = useState('');
  const [draftFile, setDraftFile] = useState<File | null>(null);
  const [createError, setCreateError] = useState('');

  const uploadRef = useRef<HTMLInputElement>(null);

  function authHeaders() {
    return { Authorization: `Bearer ${accessToken}` };
  }
  async function handleJson(res: Response) {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const d = data.detail;
      throw new Error(typeof d === 'string' ? d : d?.message || 'Request failed');
    }
    return data;
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, fileType]);

  async function load() {
    if (!accessToken) return;
    setLoading(true);
    setError('');
    setSelected(new Set());
    try {
      const res = await fetch(`${API_BASE}/uploads?file_type=${fileType}`, { headers: authHeaders() });
      const data = await handleJson(res);
      const items: Doc[] = Array.isArray(data) ? data : data.items || [];
      setDocs(items);
    } catch (err: any) {
      setError(err.message || 'Không tải được danh sách');
    } finally {
      setLoading(false);
    }
  }

  function documentName(doc: Doc): string {
    return doc.display_name?.trim() || fallbackDisplayName(doc.original_filename);
  }

  function openCreateModal() {
    setDraftName('');
    setDraftFile(null);
    setCreateError('');
    setCreateOpen(true);
  }

  function closeCreateModal() {
    if (busy) return;
    setCreateOpen(false);
    setDraftName('');
    setDraftFile(null);
    setCreateError('');
  }

  async function handleCreateUpload() {
    if (!draftName.trim()) {
      setCreateError(`Hãy nhập ${titleLabel.toLowerCase()}.`);
      return;
    }
    if (!draftFile) {
      setCreateError(`Hãy chọn tệp ${label} để tải lên.`);
      return;
    }
    setBusy(true);
    setMessage('');
    setError('');
    setCreateError('');
    try {
      const name = draftName.trim();
      const form = new FormData();
      form.append('file_type', fileType);
      form.append('display_name', name);
      form.append('file', draftFile);
      const res = await fetch(`${API_BASE}/uploads/standalone`, {
        method: 'POST',
        headers: authHeaders(),
        body: form,
      });
      await handleJson(res);
      setCreateOpen(false);
      setDraftName('');
      setDraftFile(null);
      setMessage(`Đã tạo ${label}: ${name}`);
      await load();
      onChanged?.();
    } catch (err: any) {
      setCreateError(err.message || `Không tạo được ${label}.`);
    } finally {
      setBusy(false);
    }
  }

  async function handleUploadFiles(files: File[]) {
    if (files.length === 0) return;
    setBusy(true);
    setMessage('');
    setError('');
    let ok = 0;
    let fail = 0;
    for (const file of files) {
      try {
        const form = new FormData();
        form.append('file_type', fileType);
        form.append('file', file);
        const res = await fetch(`${API_BASE}/uploads/standalone`, {
          method: 'POST',
          headers: authHeaders(),
          body: form,
        });
        await handleJson(res);
        ok += 1;
      } catch {
        fail += 1;
      }
    }
    setBusy(false);
    setMessage(`Đã tải lên ${ok} tệp${fail ? `, ${fail} tệp lỗi` : ''}`);
    await load();
  }

  async function openPreview(doc: Doc) {
    setPreview({ fileId: doc.id, title: documentName(doc), filename: doc.original_filename });
    setPreviewUrl('');
    setPreviewError('');
    setPreviewLoading(true);
    try {
      const res = await fetch(`${API_BASE}/uploads/${doc.id}/content`, { headers: authHeaders() });
      if (!res.ok) throw new Error('Không tải được nội dung tệp');
      const blob = await res.blob();
      setPreviewUrl(URL.createObjectURL(blob));
    } catch (err: any) {
      setPreviewError(err.message || 'Không xem trước được tệp');
    } finally {
      setPreviewLoading(false);
    }
  }

  function closePreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl('');
    setPreview(null);
    setPreviewError('');
  }

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }
  function toggleAll() {
    setSelected((prev) => (prev.size === docs.length ? new Set() : new Set(docs.map((d) => d.id))));
  }

  async function deleteDocs(targets: Doc[]) {
    if (targets.length === 0) return;
    setBusy(true);
    setError('');
    for (const doc of targets) {
      try {
        await fetch(`${API_BASE}/uploads/${doc.id}`, { method: 'DELETE', headers: authHeaders() });
      } catch {
        // bỏ qua, tiếp tục
      }
    }
    setBusy(false);
    await load();
    onChanged?.();
  }

  function handleDeleteSelected() {
    const targets = docs.filter((d) => selected.has(d.id));
    if (targets.length === 0) return;
    if (!window.confirm(`Xóa ${targets.length} ${label} đã chọn? Thao tác này không thể hoàn tác.`)) return;
    void deleteDocs(targets);
  }
  function handleDeleteAll() {
    if (docs.length === 0) return;
    if (!window.confirm(`Xóa TẤT CẢ ${docs.length} ${label}? Thao tác này không thể hoàn tác.`)) return;
    void deleteDocs(docs);
  }

  const allChecked = docs.length > 0 && selected.size === docs.length;
  const ext = preview?.filename ? fileExt(preview.filename) : '';
  const isImage = IMAGE_EXT.includes(ext);
  const isPdf = ext === 'pdf';

  return (
    <section className="panel job-list-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Danh sách {label}</p>
          <h2>Thư viện {label}</h2>
        </div>
        <div className="detail-actions">
          <input
            ref={uploadRef}
            type="file"
            multiple
            accept={ACCEPT}
            className="hidden-input"
            onChange={(e) => { void handleUploadFiles(Array.from(e.target.files || [])); e.target.value = ''; }}
          />
          <button className="primary" disabled={busy} onClick={openCreateModal}>
            {busy ? 'Đang xử lý…' : `Tạo ${label} mới`}
          </button>
          <button className="danger" disabled={selected.size === 0 || busy} onClick={handleDeleteSelected}>
            Xóa{selected.size ? ` (${selected.size})` : ''}
          </button>
          <button className="danger-ghost" disabled={docs.length === 0 || busy} onClick={handleDeleteAll}>
            Xóa tất cả
          </button>
        </div>
      </div>

      {error && <div className="inline-message">{error}</div>}
      {message && <div className="message-bar"><span>{message}</span><button className="message-close" onClick={() => setMessage('')} aria-label="Close">x</button></div>}

      {!error && docs.length === 0 && !loading ? (
        <div className="empty-state">
          <strong>Chưa có {label} nào</strong>
          <span>Bấm "Tạo {label} mới" để tải lên tài liệu đầu tiên.</span>
        </div>
      ) : (
        <div className="ranking-table-wrap">
          <table className="ranking-table job-list-table">
            <thead>
              <tr>
                <th className="col-check">
                  <input type="checkbox" checked={allChecked} onChange={toggleAll} aria-label="Chọn tất cả" />
                </th>
                <th>STT</th>
                <th>Tên tệp gốc</th>
                <th>{titleLabel}</th>
                <th>Kích thước</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc, idx) => (
                <tr key={doc.id} className={selected.has(doc.id) ? 'selected' : ''}>
                  <td className="col-check">
                    <input
                      type="checkbox"
                      checked={selected.has(doc.id)}
                      onChange={() => toggleOne(doc.id)}
                      aria-label={`Chọn ${doc.original_filename}`}
                    />
                  </td>
                  <td>{idx + 1}</td>
                  <td><strong>{doc.original_filename}</strong></td>
                  <td><strong>{documentName(doc)}</strong></td>
                  <td>{humanSize(doc.file_size)}</td>
                  <td>
                    <button className="secondary compact" onClick={() => openPreview(doc)}>Xem chi tiết</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {createOpen && (
        <div className="preview-modal-backdrop" onClick={closeCreateModal}>
          <div className="create-doc-modal" onClick={(e) => e.stopPropagation()}>
            <div className="preview-modal-head">
              <strong>Tạo {label} mới</strong>
              <button className="preview-modal-close" onClick={closeCreateModal} aria-label="Đóng">×</button>
            </div>
            <div className="create-doc-body">
              <label>{titleLabel}</label>
              <input
                value={draftName}
                onChange={(e) => setDraftName(e.target.value)}
                placeholder={fileType === 'cv' ? 'Ví dụ: CV Nguyễn Văn A - Backend' : 'Ví dụ: JD Backend Engineer'}
                autoFocus
              />
              <label>Tệp {label}</label>
              <input
                type="file"
                accept={ACCEPT}
                onChange={(e) => setDraftFile(e.target.files?.[0] || null)}
              />
              {draftFile && <p className="create-doc-file">Đã chọn: <strong>{draftFile.name}</strong></p>}
              {createError && <div className="inline-message">{createError}</div>}
            </div>
            <div className="mismatch-modal-foot">
              <button className="secondary" onClick={closeCreateModal} disabled={busy}>Hủy</button>
              <button className="primary" onClick={handleCreateUpload} disabled={busy}>
                {busy ? 'Đang tạo...' : `Tạo ${label}`}
              </button>
            </div>
          </div>
        </div>
      )}

      {preview && (
        <div className="preview-modal-backdrop" onClick={closePreview}>
          <div className="preview-modal" onClick={(e) => e.stopPropagation()}>
            <div className="preview-modal-head">
              <strong>{preview.title}</strong>
              <button className="preview-modal-close" onClick={closePreview} aria-label="Đóng">×</button>
            </div>
            <div className="preview-modal-body">
              {previewLoading && <p className="doc-preview-loading">Đang tải bản xem trước…</p>}
              {!previewLoading && previewUrl && isImage && (
                <img src={previewUrl} alt={preview.filename} className="preview-modal-img" />
              )}
              {!previewLoading && previewUrl && isPdf && (
                <object data={previewUrl} type="application/pdf" className="preview-modal-pdf" aria-label={preview.filename}>
                  <p className="doc-preview-empty">Trình duyệt không hiển thị được PDF trực tiếp.</p>
                </object>
              )}
              {!previewLoading && previewUrl && !isImage && !isPdf && (
                <p className="doc-preview-empty">
                  Không xem trước trực tiếp được định dạng {ext.toUpperCase()}.
                  Bạn có thể tải xuống: <a href={previewUrl} download={preview.filename}>{preview.filename}</a>
                </p>
              )}
              {!previewLoading && !previewUrl && (
                <p className="doc-preview-empty">{previewError || 'Không có nội dung để xem trước.'}</p>
              )}
            </div>
            {preview.filename && <div className="preview-modal-foot">{preview.filename}</div>}
          </div>
        </div>
      )}
    </section>
  );
}
