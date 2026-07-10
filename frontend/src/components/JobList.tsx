import { useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

type Row = {
  jobId: string;
  candidateId: string;
  candidateName: string;
  jobTitle: string;
  cvFileId: string | null;
  jdFileId: string | null;
  score: number | null;
  status: string;
  createdAt: string | null;
};

type PreviewTarget = {
  fileId: string;
  title: string;
  filename: string;
  fallbackText: string;
};

const statusText: Record<string, string> = {
  uploaded: 'Đã tải lên',
  queued: 'Trong hàng đợi',
  processing: 'Đang xử lý',
  completed: 'Hoàn tất',
  partial_completed: 'Hoàn tất một phần',
  failed: 'Thất bại',
  cancelled: 'Đã hủy',
};

function statusLabelFor(status: string) {
  const friendly: Record<string, string> = {
    uploaded: 'Đã tải lên',
    queued: 'Đang chờ phân tích',
    processing: 'Đang phân tích',
    completed: 'Hoàn tất',
    partial_completed: 'Hoàn tất một phần',
    failed: 'Cần kiểm tra',
    cancelled: 'Đã hủy',
  };
  return friendly[status] || statusText[status] || status;
}

function badgeToneForStatus(status?: string | null) {
  if (status === 'completed') return 'green';
  if (status === 'partial_completed') return 'warning';
  if (status === 'failed') return 'red';
  return 'default';
}

function scoreTone(score: number | null) {
  if (typeof score !== 'number') return 'muted';
  if (score >= 85) return 'success';
  if (score >= 70) return 'info';
  if (score >= 55) return 'warning';
  return 'danger';
}

const IMAGE_EXT = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'];
function fileExt(name: string): string {
  const i = name.lastIndexOf('.');
  return i >= 0 ? name.slice(i + 1).toLowerCase() : '';
}

/**
 * Danh sách công việc: mỗi dòng là một lần test (CV so với JD). Hỗ trợ xem
 * trước file/ảnh thật của CV/JD trong một modal gọn, và xóa nhiều lần test
 * cùng lúc (chọn ô + "Xóa") hoặc "Xóa tất cả".
 */
export default function JobList({
  accessToken,
  onReview,
}: {
  accessToken: string;
  onReview: (jobId: string, candidateId: string) => void;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);

  // Modal xem trước file/ảnh thật.
  const [preview, setPreview] = useState<PreviewTarget | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  // Cache văn bản trích xuất theo candidateId (dùng làm fallback khi không
  // render được file gốc, ví dụ DOCX/TXT).
  const [extractedCache, setExtractedCache] = useState<Record<string, { cv: string; jd: string }>>({});

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
  }, [accessToken]);

  async function load() {
    if (!accessToken) return;
    setLoading(true);
    setError('');
    setSelected(new Set());
    try {
      const jobsRes = await fetch(`${API_BASE}/jobs?limit=100`, { headers: authHeaders() });
      const jobsData = await handleJson(jobsRes);
      const jobs: any[] = jobsData.items || [];

      const perJob = await Promise.all(
        jobs.map(async (job) => {
          try {
            const res = await fetch(`${API_BASE}/jobs/${job.id}/candidates`, { headers: authHeaders() });
            const data = await handleJson(res);
            const candidates: any[] = data.items || [];
            return candidates.map((c) => ({
              jobId: job.id,
              candidateId: c.id,
              candidateName: c.name || c.id.slice(0, 8),
              jobTitle: job.title || 'Công việc chưa đặt tên',
              cvFileId: c.cv_file_id || null,
              jdFileId: job.jd_file_id || null,
              score: typeof c.overall_score === 'number' ? c.overall_score : null,
              status: c.status,
              createdAt: c.created_at || job.created_at || null,
            })) as Row[];
          } catch {
            return [] as Row[];
          }
        }),
      );

      const flat = perJob.flat().sort((a, b) => {
        const ta = a.createdAt ? Date.parse(a.createdAt) : 0;
        const tb = b.createdAt ? Date.parse(b.createdAt) : 0;
        return tb - ta;
      });
      setRows(flat);
    } catch (err: any) {
      setError(err.message || 'Không tải được danh sách công việc');
    } finally {
      setLoading(false);
    }
  }

  async function fetchExtracted(row: Row): Promise<{ cv: string; jd: string }> {
    if (extractedCache[row.candidateId]) return extractedCache[row.candidateId];
    try {
      const res = await fetch(`${API_BASE}/jobs/${row.jobId}/candidates/${row.candidateId}/result`, {
        headers: authHeaders(),
      });
      const data = await handleJson(res);
      const ex = data.extracted_text || {};
      const val = { cv: (ex.cv || '').trim(), jd: (ex.jd || '').trim() };
      setExtractedCache((prev) => ({ ...prev, [row.candidateId]: val }));
      return val;
    } catch {
      return { cv: '', jd: '' };
    }
  }

  async function openPreview(row: Row, type: 'cv' | 'jd') {
    const fileId = type === 'cv' ? row.cvFileId : row.jdFileId;
    const extracted = await fetchExtracted(row);
    const fallbackText = type === 'cv' ? extracted.cv : extracted.jd;
    const title = type === 'cv' ? `CV · ${row.candidateName}` : `JD · ${row.jobTitle}`;

    if (!fileId) {
      // Không có file gốc (ví dụ CV cũ) -> chỉ hiện text.
      setPreview({ fileId: '', title, filename: '', fallbackText });
      setPreviewUrl('');
      setPreviewError(fallbackText ? '' : 'Không có tệp để xem trước');
      return;
    }

    setPreview({ fileId, title, filename: '', fallbackText });
    setPreviewUrl('');
    setPreviewError('');
    setPreviewLoading(true);
    try {
      // Lấy metadata để biết tên/định dạng, rồi tải nội dung thật.
      const metaRes = await fetch(`${API_BASE}/uploads/${fileId}`, { headers: authHeaders() });
      const meta = await handleJson(metaRes);
      const contentRes = await fetch(`${API_BASE}/uploads/${fileId}/content`, { headers: authHeaders() });
      if (!contentRes.ok) throw new Error('Không tải được nội dung tệp');
      const blob = await contentRes.blob();
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setPreview({ fileId, title, filename: meta.original_filename || '', fallbackText });
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

  function toggleOne(candidateId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(candidateId)) next.delete(candidateId);
      else next.add(candidateId);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) => (prev.size === rows.length ? new Set() : new Set(rows.map((r) => r.candidateId))));
  }

  async function deleteRows(targets: Row[]) {
    if (targets.length === 0) return;
    setDeleting(true);
    setError('');
    try {
      // Xóa tuần tự để lỗi một mục không chặn các mục khác.
      for (const row of targets) {
        try {
          await fetch(`${API_BASE}/jobs/${row.jobId}/candidates/${row.candidateId}`, {
            method: 'DELETE',
            headers: authHeaders(),
          });
        } catch {
          // bỏ qua, tiếp tục các mục còn lại
        }
      }
      await load();
    } finally {
      setDeleting(false);
    }
  }

  function handleDeleteSelected() {
    const targets = rows.filter((r) => selected.has(r.candidateId));
    if (targets.length === 0) return;
    if (!window.confirm(`Xóa ${targets.length} lần test đã chọn? Thao tác này không thể hoàn tác.`)) return;
    void deleteRows(targets);
  }

  function handleDeleteAll() {
    if (rows.length === 0) return;
    if (!window.confirm(`Xóa TẤT CẢ ${rows.length} lần test? Thao tác này không thể hoàn tác.`)) return;
    void deleteRows(rows);
  }

  const allChecked = rows.length > 0 && selected.size === rows.length;
  const ext = preview?.filename ? fileExt(preview.filename) : '';
  const isImage = IMAGE_EXT.includes(ext);
  const isPdf = ext === 'pdf';

  return (
    <section className="panel job-list-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Danh sách công việc</p>
          <h2>Lịch sử test CV &amp; JD</h2>
        </div>
        <div className="detail-actions">
          <button className="danger" disabled={selected.size === 0 || deleting} onClick={handleDeleteSelected}>
            {deleting ? 'Đang xóa…' : `Xóa${selected.size ? ` (${selected.size})` : ''}`}
          </button>
          <button className="danger-ghost" disabled={rows.length === 0 || deleting} onClick={handleDeleteAll}>
            Xóa tất cả
          </button>
        </div>
      </div>

      {error && <div className="inline-message">{error}</div>}

      {!error && rows.length === 0 && !loading ? (
        <div className="empty-state">
          <strong>Chưa có công việc nào</strong>
          <span>Sau khi bạn tạo công việc và phân tích CV/JD, lịch sử sẽ hiển thị tại đây.</span>
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
                <th>Tên</th>
                <th>Tên công việc</th>
                <th>CV</th>
                <th>JD</th>
                <th>Độ phù hợp</th>
                <th>Trạng thái</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={row.candidateId} className={selected.has(row.candidateId) ? 'selected' : ''}>
                  <td className="col-check">
                    <input
                      type="checkbox"
                      checked={selected.has(row.candidateId)}
                      onChange={() => toggleOne(row.candidateId)}
                      aria-label={`Chọn ${row.candidateName}`}
                    />
                  </td>
                  <td>{idx + 1}</td>
                  <td><strong>{row.candidateName}</strong></td>
                  <td>{row.jobTitle}</td>
                  <td>
                    <button className="doc-chip-btn cv" onClick={() => openPreview(row, 'cv')}>
                      <span className="doc-chip-icon">CV</span> Xem trước
                    </button>
                  </td>
                  <td>
                    <button className="doc-chip-btn jd" disabled={!row.jdFileId} onClick={() => openPreview(row, 'jd')}>
                      <span className="doc-chip-icon">JD</span> Xem trước
                    </button>
                  </td>
                  <td><span className={`score-badge ${scoreTone(row.score)}`}>{row.score ?? '-'}</span></td>
                  <td>
                    <span className={`badge badge-${badgeToneForStatus(row.status)}`}>
                      {statusLabelFor(row.status)}
                    </span>
                  </td>
                  <td>
                    <button className="secondary compact" disabled={row.score === null} onClick={() => onReview(row.jobId, row.candidateId)}>
                      Xem lại kết quả
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
                  <p className="doc-preview-empty">Trình duyệt không hiển thị được PDF. Dùng "Xem lại kết quả" để xem văn bản.</p>
                </object>
              )}
              {!previewLoading && previewUrl && !isImage && !isPdf && (
                // Định dạng không render trực tiếp (DOCX, TXT, PPTX) -> hiện văn bản trích xuất.
                preview.fallbackText
                  ? <pre className="doc-preview-text">{preview.fallbackText.slice(0, 4000)}{preview.fallbackText.length > 4000 ? '…' : ''}</pre>
                  : <p className="doc-preview-empty">Không xem trước trực tiếp được định dạng {ext.toUpperCase()}. Hãy dùng "Xem lại kết quả".</p>
              )}
              {!previewLoading && !previewUrl && (
                preview.fallbackText
                  ? <pre className="doc-preview-text">{preview.fallbackText.slice(0, 4000)}{preview.fallbackText.length > 4000 ? '…' : ''}</pre>
                  : <p className="doc-preview-empty">{previewError || 'Không có nội dung để xem trước.'}</p>
              )}
            </div>
            {preview.filename && <div className="preview-modal-foot">{preview.filename}</div>}
          </div>
        </div>
      )}
    </section>
  );
}
