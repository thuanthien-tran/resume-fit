import { useEffect, useState } from 'react';

const API_BASE = '/api';

type Row = {
  jobId: string;
  candidateId: string;
  candidateName: string;
  jobTitle: string;
  cvFileId: string | null;
  jdFileId: string | null;
  score: number;
  recommendation: string | null;
};

type PreviewTarget = { fileId: string; title: string; filename: string };

const IMAGE_EXT = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'];
function fileExt(name: string): string {
  const i = name.lastIndexOf('.');
  return i >= 0 ? name.slice(i + 1).toLowerCase() : '';
}

function scoreTone(score: number) {
  if (score >= 85) return 'success';
  if (score >= 70) return 'info';
  if (score >= 55) return 'warning';
  return 'danger';
}

const recommendationLabels: Record<string, string> = {
  'Rất nên tuyển': 'Rất phù hợp',
  'Nên tuyển': 'Khá phù hợp',
  'Cân nhắc thêm': 'Nên xem thêm',
  'Không ưu tiên': 'Chưa ưu tiên',
  'Từ chối': 'Chưa phù hợp',
};

function friendlyRecommendation(value?: string | null) {
  if (!value) return '-';
  return recommendationLabels[value] || value;
}

/**
 * Bảng xếp hạng tổng: gộp mọi công việc + ứng viên đã phân tích, sắp theo độ
 * phù hợp giảm dần. Xem được chi tiết cả CV lẫn JD (bản gốc) và mở lại kết quả.
 */
export default function RankingBoard({
  accessToken,
  onReview,
}: {
  accessToken: string;
  onReview: (jobId: string, candidateId: string) => void;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [preview, setPreview] = useState<PreviewTarget | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');

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
            return candidates
              .filter((c) => typeof c.overall_score === 'number')
              .map((c) => ({
                jobId: job.id,
                candidateId: c.id,
                candidateName: c.name || c.id.slice(0, 8),
                jobTitle: job.title || 'Công việc chưa đặt tên',
                cvFileId: c.cv_file_id || null,
                jdFileId: job.jd_file_id || null,
                score: c.overall_score as number,
                recommendation: c.recommendation || null,
              })) as Row[];
          } catch {
            return [] as Row[];
          }
        }),
      );

      const flat = perJob.flat().sort((a, b) => b.score - a.score);
      setRows(flat);
    } catch (err: any) {
      setError(err.message || 'Không tải được bảng xếp hạng');
    } finally {
      setLoading(false);
    }
  }

  async function openPreview(fileId: string | null, title: string) {
    if (!fileId) {
      setPreview({ fileId: '', title, filename: '' });
      setPreviewUrl('');
      setPreviewError('Không tìm thấy tệp gốc để xem.');
      return;
    }
    setPreview({ fileId, title, filename: '' });
    setPreviewUrl('');
    setPreviewError('');
    setPreviewLoading(true);
    try {
      const metaRes = await fetch(`${API_BASE}/uploads/${fileId}`, { headers: authHeaders() });
      const meta = await handleJson(metaRes);
      const contentRes = await fetch(`${API_BASE}/uploads/${fileId}/content`, { headers: authHeaders() });
      if (!contentRes.ok) throw new Error('Không mở được tệp');
      const blob = await contentRes.blob();
      setPreviewUrl(URL.createObjectURL(blob));
      setPreview({ fileId, title, filename: meta.original_filename || '' });
    } catch (err: any) {
      setPreviewError(err.message || 'Không mở được tệp');
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

  const ext = preview?.filename ? fileExt(preview.filename) : '';
  const isImage = IMAGE_EXT.includes(ext);
  const isPdf = ext === 'pdf';

  return (
    <section className="panel job-list-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Bảng xếp hạng</p>
          <h2>Ứng viên phù hợp nhất</h2>
        </div>
      </div>

      {error && <div className="inline-message">{error}</div>}

      {!error && rows.length === 0 && !loading ? (
        <div className="empty-state">
          <strong>Chưa có ứng viên nào được xếp hạng</strong>
          <span>Hãy phân tích một công việc để xem những CV phù hợp nhất tại đây.</span>
        </div>
      ) : (
        <div className="ranking-table-wrap">
          <table className="ranking-table job-list-table">
            <thead>
              <tr>
                <th>Hạng</th>
                <th>Ứng viên</th>
                <th>Công việc</th>
                <th>CV</th>
                <th>JD</th>
                <th>Độ phù hợp</th>
                <th>Gợi ý</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={row.candidateId} className={idx < 3 ? 'top-rank' : ''}>
                  <td><span className={`rank-badge rank-${idx + 1 <= 3 ? idx + 1 : 'n'}`}>{idx + 1}</span></td>
                  <td><strong>{row.candidateName}</strong></td>
                  <td>{row.jobTitle}</td>
                  <td>
                    <button className="doc-chip-btn cv" onClick={() => openPreview(row.cvFileId, `CV · ${row.candidateName}`)}>
                      <span className="doc-chip-icon">CV</span> Xem
                    </button>
                  </td>
                  <td>
                    <button className="doc-chip-btn jd" disabled={!row.jdFileId} onClick={() => openPreview(row.jdFileId, `JD · ${row.jobTitle}`)}>
                      <span className="doc-chip-icon">JD</span> Xem
                    </button>
                  </td>
                  <td><span className={`score-badge ${scoreTone(row.score)}`}>{row.score}</span></td>
                  <td>{friendlyRecommendation(row.recommendation)}</td>
                  <td>
                    <button className="secondary compact" onClick={() => onReview(row.jobId, row.candidateId)}>
                      Xem kết quả
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
              {previewLoading && <p className="doc-preview-loading">Đang mở tệp…</p>}
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
                  Không xem trực tiếp được định dạng {ext.toUpperCase()}.
                  Tải xuống: <a href={previewUrl} download={preview.filename}>{preview.filename}</a>
                </p>
              )}
              {!previewLoading && !previewUrl && (
                <p className="doc-preview-empty">{previewError || 'Không có nội dung để xem.'}</p>
              )}
            </div>
            {preview.filename && <div className="preview-modal-foot">{preview.filename}</div>}
          </div>
        </div>
      )}
    </section>
  );
}
