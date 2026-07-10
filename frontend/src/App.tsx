import { useEffect, useRef, useState } from 'react';
import ResultReport from './components/ResultReport';
import FilePreview from './components/FilePreview';
import JobList from './components/JobList';
import DocumentList from './components/DocumentList';
import RankingBoard from './components/RankingBoard';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

type WizardStep = 1 | 2 | 3;
type AppView = 'workspace' | 'jobs' | 'cvs' | 'jds' | 'ranking';
type NavIconName = 'briefcase' | 'users' | 'clipboard' | 'resume' | 'fileText';
type AuthMode = 'login' | 'register';

const wizardSteps: { step: WizardStep; label: string; hint: string }[] = [
  { step: 1, label: 'Tạo công việc', hint: 'Đặt tên vị trí cần tuyển' },
  { step: 2, label: 'Tải CV & JD', hint: 'Xem lại tài liệu trước khi chấm' },
  { step: 3, label: 'Xem kết quả', hint: 'Ứng viên phù hợp và chi tiết' },
];

type ApiResult = any;
type CandidateRankingItem = any;
type SavedDoc = { id: string; original_filename: string; display_name?: string | null; file_type: 'cv' | 'jd'; file_size: number; created_at: string };

type LoadingState = {
  register: boolean;
  login: boolean;
  createJob: boolean;
  uploadCv: boolean;
  uploadJd: boolean;
  enqueue: boolean;
  getResult: boolean;
  downloadPdf: boolean;
};

const recommendationLabels: Record<string, string> = {
  'Rất nên tuyển': 'Ưu tiên phỏng vấn',
  'Nên tuyển': 'Nên đưa vào phỏng vấn',
  'Cân nhắc thêm': 'Cần xem thêm hồ sơ',
  'Không ưu tiên': 'Chưa nên ưu tiên',
  'Từ chối': 'Chưa phù hợp',
};

const terminalJobStatuses = new Set(['completed', 'failed', 'partial_completed']);

function NavIcon({ name }: { name: NavIconName }) {
  const commonProps = {
    width: 18,
    height: 18,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 2,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };

  if (name === 'briefcase') {
    return (
      <svg {...commonProps}>
        <path d="M10 6h4" />
        <path d="M9 6V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1" />
        <rect x="3" y="6" width="18" height="14" rx="3" />
        <path d="M3 12h18" />
      </svg>
    );
  }

  if (name === 'users') {
    return (
      <svg {...commonProps}>
        <circle cx="12" cy="8" r="3" />
        <path d="M6.5 20c.8-3 2.8-4.5 5.5-4.5s4.7 1.5 5.5 4.5" />
        <path d="M5 16.5c.4-1.3 1.2-2.3 2.4-2.9" />
        <path d="M16.6 13.6c1.2.6 2 1.6 2.4 2.9" />
      </svg>
    );
  }

  if (name === 'clipboard') {
    return (
      <svg {...commonProps}>
        <rect x="6" y="4" width="12" height="17" rx="2" />
        <path d="M9 4.5A2 2 0 0 1 11 3h2a2 2 0 0 1 2 1.5" />
        <path d="M9 11h6" />
        <path d="M9 15h4" />
      </svg>
    );
  }

  if (name === 'resume') {
    return (
      <svg {...commonProps}>
        <path d="M7 3h8l4 4v14H7z" />
        <path d="M15 3v5h4" />
        <circle cx="11" cy="12" r="2" />
        <path d="M8.5 18c.6-1.7 1.7-2.5 2.5-2.5s1.9.8 2.5 2.5" />
      </svg>
    );
  }

  return (
    <svg {...commonProps}>
      <path d="M7 3h8l4 4v14H7z" />
      <path d="M15 3v5h4" />
      <path d="M10 13h5" />
      <path d="M10 17h4" />
    </svg>
  );
}

function isTerminalJobStatus(status?: string | null) {
  return Boolean(status && terminalJobStatuses.has(status));
}

function jobStatusMessage(status: string) {
  if (status === 'completed') return 'Đã hoàn tất phân tích. Danh sách ứng viên phù hợp đã được tải.';
  if (status === 'partial_completed') return 'Đã hoàn tất một phần. Một số ứng viên có kết quả, một số cần kiểm tra lại.';
  return 'Phân tích kết thúc nhưng có mục cần kiểm tra. Hãy xem lại danh sách ứng viên.';
}

function badgeToneForStatus(status?: string | null) {
  if (status === 'completed') return 'green';
  if (status === 'partial_completed') return 'warning';
  if (status === 'failed') return 'red';
  return 'default';
}

function friendlyRecommendation(value?: string | null) {
  if (!value) return '-';
  return recommendationLabels[value] || value;
}

function formatScoreValue(value: unknown) {
  return typeof value === 'number' ? `${Number(value.toFixed(2))}%` : '-';
}

function friendlyConfidence(value?: string | null) {
  if (!value) return 'Chưa rõ';
  const normalized = value.toLowerCase();
  if (normalized === 'cao' || normalized === 'high') return 'Tin cậy cao';
  if (normalized === 'trung bình' || normalized === 'medium') return 'Tin cậy vừa';
  if (normalized === 'thấp' || normalized === 'low') return 'Cần kiểm tra thêm';
  return value;
}

function App() {
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [refreshToken, setRefreshToken] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [jobId, setJobId] = useState('');
  const [cvFiles, setCvFiles] = useState<File[]>([]);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [cvUploadedCount, setCvUploadedCount] = useState(0);
  const [jdUploaded, setJdUploaded] = useState(false);
  const [jobStatus, setJobStatus] = useState('');
  const [ranking, setRanking] = useState<CandidateRankingItem[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [result, setResult] = useState<ApiResult>(null);
  const [message, setMessageText] = useState('');
  const [messageTone, setMessageTone] = useState<'info' | 'success'>('info');
  const [showDebug, setShowDebug] = useState(false);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [savedCvs, setSavedCvs] = useState<SavedDoc[]>([]);
  const [savedJds, setSavedJds] = useState<SavedDoc[]>([]);
  const [step, setStep] = useState<WizardStep>(1);
  const [view, setView] = useState<AppView>('workspace');
  // Mở/đóng panel chọn CV/JD đã lưu ở bước 2.
  const [showSavedCvs, setShowSavedCvs] = useState(false);
  const [showSavedJds, setShowSavedJds] = useState(false);
  // Modal cảnh báo khi tải sai loại tệp (CV vào ô JD hoặc ngược lại).
  const [mismatchModal, setMismatchModal] = useState<{
    expectedType: 'cv' | 'jd';
    items: { filename: string; detected: string; reasons: string[] }[];
  } | null>(null);
  const [loading, setLoading] = useState<LoadingState>({
    register: false,
    login: false,
    createJob: false,
    uploadCv: false,
    uploadJd: false,
    enqueue: false,
    getResult: false,
    downloadPdf: false,
  });

  const cvInputRef = useRef<HTMLInputElement>(null);
  const jdInputRef = useRef<HTMLInputElement>(null);
  const messageTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchSavedDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  useEffect(() => {
    if (accessToken && view === 'workspace' && step === 2) void fetchSavedDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, view, step]);

  useEffect(() => {
    function handleScroll() {
      setShowBackToTop(window.scrollY > 180);
    }
    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    return () => {
      if (messageTimerRef.current) clearTimeout(messageTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (!sidebarOpen || !window.matchMedia('(max-width: 900px)').matches) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [sidebarOpen]);

  function showMessage(text: string, tone: 'info' | 'success' = 'info', autoHideMs?: number) {
    if (messageTimerRef.current) {
      clearTimeout(messageTimerRef.current);
      messageTimerRef.current = null;
    }
    setMessageTone(tone);
    setMessageText(text);
    if (text && autoHideMs) {
      messageTimerRef.current = setTimeout(() => {
        setMessageText((current) => (current === text ? '' : current));
        messageTimerRef.current = null;
      }, autoHideMs);
    }
  }

  function setMessage(text: string) {
    showMessage(text);
  }

  function showSuccessMessage(text: string) {
    showMessage(text, 'success', 4000);
  }

  function closeSidebarOnMobile() {
    if (window.matchMedia('(max-width: 900px)').matches) {
      setSidebarOpen(false);
    }
  }

  function goToView(nextView: AppView) {
    setView(nextView);
    closeSidebarOnMobile();
  }

  function authHeaders() {
    return { Authorization: `Bearer ${accessToken}` };
  }

  async function handleJson(res: Response) {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      // detail có thể là chuỗi, object {message, reasons,...} hoặc mảng lỗi validation của FastAPI.
      const d = data.detail;
      const validationMsg = Array.isArray(d)
        ? d.map((item) => item?.msg).filter(Boolean).join('; ')
        : '';
      const msg = typeof d === 'string' ? d : d?.message || validationMsg || 'Request failed';
      const err = new Error(msg) as Error & { detail?: any };
      if (d && typeof d === 'object') err.detail = d;
      throw err;
    }
    return data;
  }

  function setLoadingKey(key: keyof LoadingState, val: boolean) {
    setLoading((prev) => ({ ...prev, [key]: val }));
  }

  const statusText: Record<string, string> = {
    uploaded: 'Đã tải lên',
    queued: 'Đang chờ phân tích',
    processing: 'Đang phân tích',
    completed: 'Đã có kết quả',
    partial_completed: 'Hoàn tất một phần',
    failed: 'Cần kiểm tra',
    cancelled: 'Đã hủy',
  };

  function statusLabel() {
    if (!jobId) return 'Chưa có công việc';
    return statusText[jobStatus] || statusText.uploaded;
  }

  function scoreTone(score: number | null | undefined) {
    if (typeof score !== 'number') return 'muted';
    if (score >= 85) return 'success';
    if (score >= 70) return 'info';
    if (score >= 55) return 'warning';
    return 'danger';
  }

  function validateAuthFields(mode: AuthMode) {
    if (!email.trim()) return 'Hãy nhập email.';
    if (!password) return 'Hãy nhập mật khẩu.';
    if (mode === 'register') {
      if (password.length < 8) return 'Mật khẩu cần có ít nhất 8 ký tự.';
      if (password !== confirmPassword) return 'Mật khẩu xác nhận chưa khớp.';
    }
    return '';
  }

  async function performLogin(successMessage = 'Đăng nhập thành công') {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.trim(), password }),
    });
    const data = await handleJson(res);
    setAccessToken(data.access_token);
    setRefreshToken(data.refresh_token || '');
    showSuccessMessage(successMessage);
  }

  async function register() {
    const validationError = validateAuthFields('register');
    if (validationError) {
      setMessage(validationError);
      return;
    }

    setLoadingKey('register', true);
    try {
      await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password,
          full_name: fullName.trim() || null,
        }),
      }).then(handleJson);
      await performLogin('Đăng ký thành công. Bạn đã được đăng nhập.');
    } catch (err: any) {
      setMessage(err.message);
    } finally {
      setLoadingKey('register', false);
    }
  }

  async function login() {
    const validationError = validateAuthFields('login');
    if (validationError) {
      setMessage(validationError);
      return;
    }

    setLoadingKey('login', true);
    try {
      await performLogin();
    } catch (err: any) {
      setMessage(err.message);
    } finally {
      setLoadingKey('login', false);
    }
  }

  function switchAuthMode(mode: AuthMode) {
    setAuthMode(mode);
    setMessage('');
    setConfirmPassword('');
  }

  async function createJob() {
    const title = jobTitle.trim();
    if (!title) {
      setMessage('Hãy nhập tên vị trí cần tuyển trước khi tiếp tục.');
      return;
    }
    setLoadingKey('createJob', true);
    try {
      const res = await fetch(`${API_BASE}/jobs`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      const data = await handleJson(res);
      setJobId(data.job_id);
      setJobStatus(data.status);
      setCvUploadedCount(0);
      setJdUploaded(false);
      setRanking([]);
      setResult(null);
      setSelectedCandidateId('');
      setStep(2);
      showSuccessMessage('Đã tạo công việc. Hãy tải lên JD và CV ứng viên.');
    } catch (err: any) {
      setMessage(err.message);
    } finally {
      setLoadingKey('createJob', false);
    }
  }

  async function uploadWithPresignedUrl(fileType: 'cv' | 'jd', file: File) {
    const mimeType = file.type || 'application/octet-stream';
    const presignRes = await fetch(`${API_BASE}/uploads/presign`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: jobId,
        file_type: fileType,
        filename: file.name,
        content_type: mimeType,
      }),
    });
    const presign = await handleJson(presignRes);

    const uploadRes = await fetch(presign.upload_url, {
      method: 'PUT',
      headers: { 'Content-Type': mimeType },
      body: file,
    });
    if (!uploadRes.ok) {
      throw new Error(`Không tải được tệp "${file.name}" lên kho lưu trữ.`);
    }

    const completeRes = await fetch(`${API_BASE}/uploads/complete`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: jobId,
        file_type: fileType,
        storage_path: presign.storage_path,
        original_filename: file.name,
        mime_type: mimeType,
      }),
    });
    return handleJson(completeRes);
  }

  async function uploadJd() {
    setLoadingKey('uploadJd', true);
    try {
      if (!jdFile) throw new Error('Hãy chọn tệp JD trước');
      if (!jobId) throw new Error('Hãy tạo công việc trước');

      await uploadWithPresignedUrl('jd', jdFile);
      setJdFile(null);
      setMessage('Tải lên JD thành công');
      fetchSavedDocs();
      await syncReadiness();
    } catch (err: any) {
      // Sai loại tệp -> hiện modal cảnh báo thay vì chỉ báo dòng chữ.
      if (err.detail?.detected_type) {
        setMismatchModal({
          expectedType: 'jd',
          items: [{
            filename: jdFile?.name || 'tệp',
            detected: err.detail.detected_type,
            reasons: err.detail.reasons || [],
          }],
        });
      } else {
        setMessage(err.message);
      }
    } finally {
      setLoadingKey('uploadJd', false);
    }
  }

  async function uploadCvs() {
    setLoadingKey('uploadCv', true);
    try {
      if (cvFiles.length === 0) throw new Error('Hãy chọn ít nhất một CV trước');
      if (!jobId) throw new Error('Hãy tạo công việc trước');

      const succeeded: any[] = [];
      const failed: any[] = [];
      for (const file of cvFiles) {
        try {
          succeeded.push(await uploadWithPresignedUrl('cv', file));
        } catch (err: any) {
          failed.push({
            original_filename: file.name,
            error: err.detail || err.message || 'Không tải được tệp',
          });
        }
      }
      // Các tệp bị từ chối vì sai loại (error là object có detected_type).
      const mismatched = failed.filter((f) => f?.error && typeof f.error === 'object' && f.error.detected_type);
      const succeededCount = succeeded.length;

      setCvFiles([]);
      fetchSavedDocs();
      await syncReadiness();

      if (mismatched.length > 0) {
        setMismatchModal({
          expectedType: 'cv',
          items: mismatched.map((f) => ({
            filename: f.original_filename || 'tệp',
            detected: f.error.detected_type,
            reasons: f.error.reasons || [],
          })),
        });
        setMessage(succeededCount > 0 ? `Đã tải lên ${succeededCount} CV hợp lệ` : '');
      } else if (failed.length > 0) {
        setMessage(`Đã tải lên ${succeededCount} CV, ${failed.length} tệp chưa tải được.`);
      } else {
        setMessage(`Tải lên thành công ${succeededCount || cvFiles.length} CV`);
      }
    } catch (err: any) {
      setMessage(err.message);
    } finally {
      setLoadingKey('uploadCv', false);
    }
  }

  async function enqueueJob() {
    setLoadingKey('enqueue', true);
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/enqueue`, {
        method: 'POST',
        headers: authHeaders(),
      });
      const data = await handleJson(res);
      setJobStatus(data.status);
      setStep(3);
      setMessage(`Đã đưa ${data.enqueued_candidates || 0} ứng viên vào phân tích`);
      pollStatus();
    } catch (err: any) {
      setMessage(err.message);
    } finally {
      setLoadingKey('enqueue', false);
    }
  }

  async function pollStatus() {
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/jobs/${jobId}`, { headers: authHeaders() });
        const data = await handleJson(res);
        setJobStatus(data.status);
        if (isTerminalJobStatus(data.status)) {
          clearInterval(poll);
          await loadRanking();
          if (data.status === 'completed') {
            showSuccessMessage(jobStatusMessage(data.status));
          } else {
            setMessage(jobStatusMessage(data.status));
          }
        }
      } catch {
        clearInterval(poll);
      }
    }, 2000);
  }

  async function loadRanking() {
    if (!jobId) return;
    const res = await fetch(`${API_BASE}/jobs/${jobId}/candidates`, { headers: authHeaders() });
    const data = await handleJson(res);
    const items = data.items || [];
    setRanking(items);
    const firstCompleted = items.find((item: CandidateRankingItem) => item.overall_score !== null && item.overall_score !== undefined);
    if (firstCompleted) await loadCandidateResult(firstCompleted.id);
  }

  async function loadCandidateResult(candidateId: string) {
    setLoadingKey('getResult', true);
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/candidates/${candidateId}/result`, { headers: authHeaders() });
      const data = await handleJson(res);
      setSelectedCandidateId(candidateId);
      setResult(data);
      setMessage('');
    } catch (err: any) {
      setMessage(err.message);
    } finally {
      setLoadingKey('getResult', false);
    }
  }

  async function downloadCandidatePdf() {
    if (!jobId || !selectedCandidateId) return;
    setLoadingKey('downloadPdf', true);
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/candidates/${selectedCandidateId}/report.pdf`, { headers: authHeaders() });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = data.detail;
        throw new Error(typeof detail === 'string' ? detail : 'Không tải được PDF');
      }

      const blob = await res.blob();
      const disposition = res.headers.get('Content-Disposition') || '';
      const filenameMatch = disposition.match(/filename="?([^"]+)"?/i);
      const filename = filenameMatch?.[1] || `candidate-report-${selectedCandidateId.slice(0, 8) || jobId.slice(0, 8)}.pdf`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      setMessage('Đã tải báo cáo PDF');
    } catch (err: any) {
      setMessage(err.message);
    } finally {
      setLoadingKey('downloadPdf', false);
    }
  }

  async function reviewFromList(targetJobId: string, candidateId: string) {
    // Mở lại một lần test từ Danh sách công việc: nạp công việc, bảng xếp hạng
    // và kết quả ứng viên rồi chuyển về không gian làm việc ở bước 3.
    try {
      const [jobRes, candsRes, resultRes] = await Promise.all([
        fetch(`${API_BASE}/jobs/${targetJobId}`, { headers: authHeaders() }),
        fetch(`${API_BASE}/jobs/${targetJobId}/candidates`, { headers: authHeaders() }),
        fetch(`${API_BASE}/jobs/${targetJobId}/candidates/${candidateId}/result`, { headers: authHeaders() }),
      ]);
      const job = await handleJson(jobRes);
      const cands = await handleJson(candsRes);
      const result = await handleJson(resultRes);

      setJobId(targetJobId);
      setJobTitle(job.title || 'Công việc chưa đặt tên');
      setJobStatus(job.status);
      setCvUploadedCount(job.candidate_count || 0);
      setJdUploaded(Boolean(job.jd_file_id));
      setRanking(cands.items || []);
      setSelectedCandidateId(candidateId);
      setResult(result);
      setStep(3);
      setView('workspace');
      setMessage('');
    } catch (err: any) {
      setMessage(err.message);
    }
  }

  function handleDrop(type: 'cv' | 'jd', e: React.DragEvent) {
    e.preventDefault();
    if (type === 'cv') setCvFiles(Array.from(e.dataTransfer.files));
    else setJdFile(e.dataTransfer.files[0] || null);
  }

  function resetFlow() {
    setResult(null);
    setRanking([]);
    setSelectedCandidateId('');
    setJobId('');
    setJobStatus('');
    setCvFiles([]);
    setJdFile(null);
    setCvUploadedCount(0);
    setJdUploaded(false);
    setStep(1);
  }

  async function logout() {
    try {
      if (refreshToken) {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch {
      // Bỏ qua lỗi mạng — vẫn xóa phiên đăng nhập ở phía client.
    }
    resetFlow();
    setAccessToken('');
    setRefreshToken('');
    setSavedCvs([]);
    setSavedJds([]);
    setMessage('');
  }

  async function syncReadiness(id?: string) {
    const targetId = id || jobId;
    if (!targetId) return;
    try {
      const res = await fetch(`${API_BASE}/jobs/${targetId}`, { headers: authHeaders() });
      const data = await handleJson(res);
      // Lấy trạng thái thật từ backend thay vì cờ optimistic ở client.
      setJdUploaded(Boolean(data.jd_file_id));
      setCvUploadedCount(data.candidate_count || 0);
      setJobStatus(data.status);
    } catch {
      // Bỏ qua lỗi đồng bộ — không chặn luồng chính.
    }
  }

  async function fetchSavedDocs() {
    if (!accessToken) return;
    try {
      const res = await fetch(`${API_BASE}/uploads`, { headers: authHeaders() });
      const data = await handleJson(res);
      const items: SavedDoc[] = Array.isArray(data) ? data : data.items || [];
      setSavedCvs(items.filter((doc) => doc.file_type === 'cv'));
      setSavedJds(items.filter((doc) => doc.file_type === 'jd'));
    } catch {
      // Bỏ qua lỗi tải danh sách — không chặn luồng chính.
    }
  }

  async function chooseSavedDoc(doc: SavedDoc, fileType: 'cv' | 'jd') {
    try {
      const res = await fetch(`${API_BASE}/uploads/${doc.id}/content`, { headers: authHeaders() });
      if (!res.ok) throw new Error('Không tải được nội dung tệp đã lưu');
      const blob = await res.blob();
      const file = new File([blob], doc.original_filename, { type: blob.type || 'application/octet-stream' });

      if (fileType === 'jd') {
        setJdFile(file);
        setJdUploaded(false);
        setShowSavedJds(false);
        setMessage('Đã chọn JD đã lưu. Bấm "Tải lên" để dùng cho công việc này.');
      } else {
        setCvFiles((current) => [...current, file]);
        setShowSavedCvs(false);
        setMessage('Đã chọn CV đã lưu. Bấm "Tải lên" để thêm vào công việc này.');
      }
    } catch (err: any) {
      setMessage(err.message);
    }
  }

  if (!accessToken) {
    return (
      <div className="auth-page login-only-page">
        <div className="login-shell">
          <section className="login-intro" aria-label="Resume Fit">
            <div className="login-product-mark">
              <img src="/icon.png" alt="" />
            </div>
            <h1>Resume Fit</h1>
            <p className="login-subtitle">Đánh giá độ phù hợp giữa CV và JD nhanh, rõ, dễ quyết định.</p>
            <div className="login-feature-grid" aria-label="Tính năng chính">
              <span><strong>CV</strong> Phân tích hồ sơ ứng viên</span>
              <span><strong>JD</strong> So khớp mô tả công việc</span>
              <span><strong>AI</strong> Gợi ý phỏng vấn và khuyến nghị</span>
            </div>
          </section>

          <section className="auth-panel login-only-panel">
            <div className="auth-mode-switch" role="tablist" aria-label="Chọn đăng nhập hoặc đăng ký">
              <button
                type="button"
                className={authMode === 'login' ? 'active' : ''}
                onClick={() => switchAuthMode('login')}
                aria-selected={authMode === 'login'}
              >
                Đăng nhập
              </button>
              <button
                type="button"
                className={authMode === 'register' ? 'active' : ''}
                onClick={() => switchAuthMode('register')}
                aria-selected={authMode === 'register'}
              >
                Đăng ký
              </button>
            </div>

            <p className="eyebrow">{authMode === 'login' ? 'Đăng nhập hệ thống' : 'Tạo tài khoản mới'}</p>
            <h2>{authMode === 'login' ? 'Chào mừng trở lại' : 'Bắt đầu với Resume Fit'}</h2>
            <p className="panel-muted">
              {authMode === 'login'
                ? 'Đăng nhập để tiếp tục đánh giá CV và JD trên Resume Fit.'
                : 'Đăng ký tài khoản để lưu CV, JD và quản lý các lần phân tích của riêng bạn.'}
            </p>

            {authMode === 'register' && (
              <>
                <label>Họ tên</label>
                <input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Họ tên của bạn" autoComplete="name" />
              </>
            )}
            <label>Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="email" />
            <label>Mật khẩu</label>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              placeholder="Mật khẩu"
              autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
            />
            {authMode === 'register' && (
              <>
                <label>Xác nhận mật khẩu</label>
                <input
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  type="password"
                  placeholder="Nhập lại mật khẩu"
                  autoComplete="new-password"
                />
                <p className="auth-hint">Mật khẩu tối thiểu 8 ký tự.</p>
              </>
            )}
            <div className="auth-actions login-only-actions">
              {authMode === 'login' ? (
                <button className="primary" onClick={login} disabled={loading.login}>
                  {loading.login ? 'Đang đăng nhập...' : 'Đăng nhập'}
                </button>
              ) : (
                <button className="primary" onClick={register} disabled={loading.register}>
                  {loading.register ? 'Đang tạo tài khoản...' : 'Đăng ký'}
                </button>
              )}
            </div>
            <p className="auth-switch-note">
              {authMode === 'login' ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}{' '}
              <button type="button" onClick={() => switchAuthMode(authMode === 'login' ? 'register' : 'login')}>
                {authMode === 'login' ? 'Đăng ký ngay' : 'Đăng nhập'}
              </button>
            </p>
            {message && <div className={`inline-message ${messageTone === 'success' ? 'success' : ''}`}>{message}</div>}
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className={`app-shell ${sidebarOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}>
      <aside className="sidebar">
        <button
          type="button"
          className={`sidebar-toggle ${sidebarOpen ? 'open' : ''}`}
          onClick={() => setSidebarOpen((value) => !value)}
          aria-label={sidebarOpen ? 'Đóng menu' : 'Mở menu'}
          title={sidebarOpen ? 'Đóng menu' : 'Mở menu'}
        >
          <span />
          <span />
          <span />
        </button>
        <div className="sidebar-brand">
          <div className="brand-mark small">3T</div>
          <div className="sidebar-brand-text">
            <strong>NĐ-3T</strong>
            <span>Người xin việc</span>
          </div>
        </div>
        <nav className="side-nav">
          <button className={view === 'workspace' ? 'active' : ''} onClick={() => goToView('workspace')} title="Công việc">
            <span className="nav-icon"><NavIcon name="briefcase" /></span><span className="nav-label">Công việc</span>
          </button>
          <button className={view === 'ranking' ? 'active' : ''} onClick={() => goToView('ranking')} title="Ứng viên phù hợp">
            <span className="nav-icon"><NavIcon name="users" /></span><span className="nav-label">Ứng viên phù hợp</span>
          </button>
          <button className={view === 'jobs' ? 'active' : ''} onClick={() => goToView('jobs')} title="Danh sách công việc">
            <span className="nav-icon"><NavIcon name="clipboard" /></span><span className="nav-label">Danh sách công việc</span>
          </button>
          <button className={view === 'cvs' ? 'active' : ''} onClick={() => goToView('cvs')} title="Danh sách CV">
            <span className="nav-icon"><NavIcon name="resume" /></span><span className="nav-label">Danh sách CV</span>
          </button>
          <button className={view === 'jds' ? 'active' : ''} onClick={() => goToView('jds')} title="Danh sách JD">
            <span className="nav-icon"><NavIcon name="fileText" /></span><span className="nav-label">Danh sách JD</span>
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-account">
            <div className="account-avatar">{email.slice(0, 1).toUpperCase()}</div>
            <div className="account-info">
              <strong>{email}</strong>
              <span>Người xin việc</span>
            </div>
          </div>
          <button className="ghost sidebar-action" onClick={() => { resetFlow(); goToView('workspace'); }} title="Công việc mới">
            <span className="nav-icon">+</span><span className="nav-label">Công việc mới</span>
          </button>
          <button className="ghost logout sidebar-action" onClick={logout} title="Đăng xuất">
            <span className="nav-icon">↵</span><span className="nav-label">Đăng xuất</span>
          </button>
        </div>
      </aside>
      <button
        type="button"
        className="sidebar-backdrop"
        onClick={() => setSidebarOpen(false)}
        aria-label="Đóng menu"
      />

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Đánh giá độ phù hợp giữa CV và mô tả công việc</p>
            <h1>{
              view === 'ranking' ? 'Ứng viên phù hợp'
              : view === 'jobs' ? 'Danh sách công việc'
              : view === 'cvs' ? 'Danh sách CV'
              : view === 'jds' ? 'Danh sách JD'
              : (jobId ? jobTitle || 'Công việc chưa đặt tên' : 'ResumeFit')
            }</h1>
          </div>
          <div className="topbar-actions">
            {view === 'workspace' && <span className={`status-pill ${jobStatus || 'idle'}`}>{statusLabel()}</span>}
            <button className="primary" onClick={() => { resetFlow(); setView('workspace'); }}>Công việc mới</button>
          </div>
        </header>

        {message && (
          <div className={`message-bar ${messageTone}`}>
            <span>{message}</span>
            <button className="message-close" onClick={() => setMessage('')} aria-label="Close">x</button>
          </div>
        )}

        {mismatchModal && (
          <div className="preview-modal-backdrop" onClick={() => setMismatchModal(null)}>
            <div className="mismatch-modal" onClick={(e) => e.stopPropagation()}>
              <div className="mismatch-modal-head">
                <div className="mismatch-icon">!</div>
                <div>
                  <strong>Bạn tải nhầm loại tệp rồi</strong>
                  <p>
                    {mismatchModal.expectedType === 'cv'
                      ? 'Ô này dành cho CV (hồ sơ ứng viên), nhưng tệp bạn chọn trông giống Mô tả công việc (JD).'
                      : 'Ô này dành cho JD (mô tả công việc), nhưng tệp bạn chọn trông giống CV (hồ sơ ứng viên).'}
                  </p>
                </div>
                <button className="preview-modal-close" onClick={() => setMismatchModal(null)} aria-label="Đóng">×</button>
              </div>
              <div className="mismatch-modal-body">
                {mismatchModal.items.map((item, i) => (
                  <div className="mismatch-item" key={`${item.filename}-${i}`}>
                    <div className="mismatch-item-name">
                      <span className={`doc-chip-icon ${item.detected}`}>{item.detected.toUpperCase()}</span>
                      <strong>{item.filename}</strong>
                      <span className="mismatch-detected">
                        Có vẻ là {item.detected === 'cv' ? 'CV' : 'JD'}
                      </span>
                    </div>
                  </div>
                ))}
                <p className="mismatch-hint">
                  {mismatchModal.expectedType === 'cv'
                    ? 'Hãy chọn lại đúng tệp CV của ứng viên. Nếu đây thật sự là JD, bạn hãy tải nó vào ô JD.'
                    : 'Hãy chọn lại đúng tệp JD. Nếu đây thật sự là CV, bạn hãy tải nó vào ô CV.'}
                </p>
              </div>
              <div className="mismatch-modal-foot">
                <button className="primary" onClick={() => setMismatchModal(null)}>Đã hiểu</button>
              </div>
            </div>
          </div>
        )}

        {view === 'ranking' && <RankingBoard accessToken={accessToken} onReview={reviewFromList} />}
        {view === 'jobs' && <JobList accessToken={accessToken} onReview={reviewFromList} />}
        {view === 'cvs' && <DocumentList accessToken={accessToken} fileType="cv" onChanged={fetchSavedDocs} />}
        {view === 'jds' && <DocumentList accessToken={accessToken} fileType="jd" onChanged={fetchSavedDocs} />}

        {view === 'workspace' && (
        <>
        <section className="wizard-steps-panel" aria-label="Tiến trình">
          <nav className="wizard-steps">
            {wizardSteps.map((s) => {
              const state = step === s.step ? 'current' : step > s.step ? 'done' : 'upcoming';
              const clickable = s.step < step;
              return (
                <button
                  key={s.step}
                  type="button"
                  className={`wizard-step ${state}`}
                  disabled={!clickable}
                  onClick={() => clickable && setStep(s.step)}
                >
                  <span className="wizard-step-index">{step > s.step ? '✓' : s.step}</span>
                  <span className="wizard-step-text">
                    <strong>{s.label}</strong>
                    <small>{s.hint}</small>
                  </span>
                </button>
              );
            })}
          </nav>
        </section>

        {step === 1 && (
          <section className="panel wizard-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Bước 1</p>
                <h2>Tạo công việc tuyển dụng</h2>
              </div>
              {jobId && <span className="badge badge-info">Đã tạo</span>}
            </div>
            <p className="panel-muted">Đặt tên vị trí bạn cần tuyển, rồi bấm tiếp tục để tải CV và JD.</p>
            <div className="job-create-row">
              <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} placeholder="Ví dụ: Nhân viên Backend, Chuyên viên Marketing…" disabled={!!jobId} />
              {!jobId ? (
                <button className="primary" onClick={createJob} disabled={loading.createJob || !jobTitle.trim()}>{loading.createJob ? 'Đang tạo...' : 'Tạo và tiếp tục'}</button>
              ) : (
                <button className="primary" onClick={() => setStep(2)}>Tiếp tục →</button>
              )}
            </div>
            {jobId && <p className="panel-muted">Đã tạo công việc. Bấm tiếp tục để tải tài liệu.</p>}
          </section>
        )}

        {step === 2 && (
          <section className="panel wizard-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Bước 2</p>
                <h2>Tải lên CV & JD</h2>
              </div>
              <span className="badge badge-muted">PDF, DOCX, PPTX, TXT</span>
            </div>
            <p className="panel-muted">Chọn tệp để xem trước, kiểm tra đúng CV và JD rồi mới tải lên.</p>

            <div className="upload-columns">
              <div className="upload-col jd-column">
                <h3 className="upload-col-title">Mô tả công việc (JD)</h3>
                <div className={`dropzone jd-dropzone ${jdUploaded ? 'complete' : ''}`} onDragOver={(e) => e.preventDefault()} onDrop={(e) => handleDrop('jd', e)} onClick={() => jdInputRef.current?.click()}>
                  <input ref={jdInputRef} type="file" accept=".pdf,.docx,.pptx,.txt,.rtf" className="hidden-input" onClick={(e) => { (e.target as HTMLInputElement).value = ''; }} onChange={(e) => setJdFile(e.target.files?.[0] || null)} />
                  <div className="dropzone-icon">JD</div>
                  <div>
                    <strong>{jdUploaded ? 'Đã tải lên mô tả công việc' : 'Mô tả công việc (JD)'}</strong>
                    <span>{jdFile ? jdFile.name : 'Nhấp hoặc kéo thả một tệp JD'}</span>
                  </div>
                  <button className="secondary compact" disabled={!jobId || !jdFile || jdUploaded || loading.uploadJd} onClick={(e) => { e.stopPropagation(); uploadJd(); }}>{loading.uploadJd ? 'Đang tải...' : 'Tải lên'}</button>
                </div>

                {jdFile && !jdUploaded && (
                  <div className="preview-grid">
                    <FilePreview file={jdFile} onRemove={() => setJdFile(null)} />
                  </div>
                )}
                {jdUploaded && <p className="upload-ok">✓ JD đã sẵn sàng để phân tích</p>}

                <button
                  className="saved-toggle jd"
                  disabled={!jobId}
                  onClick={() => {
                    if (!showSavedJds) void fetchSavedDocs();
                    setShowSavedJds((v) => !v);
                  }}
                >
                  <span>JD đã lưu {savedJds.length ? `(${savedJds.length})` : ''}</span>
                  <span className={`saved-toggle-caret ${showSavedJds ? 'open' : ''}`}>▾</span>
                </button>
                {showSavedJds && (
                  <div className="saved-docs">
                    {savedJds.length === 0 ? (
                      <p className="saved-docs-empty">Chưa có JD nào được lưu. Hãy tải một JD lên hoặc tạo ở mục "Danh sách JD".</p>
                    ) : (
                      savedJds.map((doc) => (
                        <div className="saved-doc-row" key={doc.id}>
                          <span className="saved-doc-name" title={doc.original_filename}>{doc.display_name || doc.original_filename}</span>
                          <button className="secondary compact" disabled={!jobId} onClick={() => chooseSavedDoc(doc, 'jd')}>Chọn</button>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              <div className="upload-col">
                <h3 className="upload-col-title">CV ứng viên</h3>
                <div className={`dropzone ${cvUploadedCount > 0 ? 'complete' : ''}`} onDragOver={(e) => e.preventDefault()} onDrop={(e) => handleDrop('cv', e)} onClick={() => cvInputRef.current?.click()}>
                  <input ref={cvInputRef} type="file" multiple accept=".pdf,.docx,.pptx,.txt,.rtf" className="hidden-input" onClick={(e) => { (e.target as HTMLInputElement).value = ''; }} onChange={(e) => setCvFiles(Array.from(e.target.files || []))} />
                  <div className="dropzone-icon">CV</div>
                  <div>
                    <strong>{cvUploadedCount > 0 ? `Đã tải lên ${cvUploadedCount} CV` : 'CV ứng viên'}</strong>
                    <span>{cvFiles.length ? `Đã chọn ${cvFiles.length} tệp` : 'Chọn nhiều tệp CV'}</span>
                  </div>
                  <button className="secondary compact" disabled={!jobId || cvFiles.length === 0 || loading.uploadCv} onClick={(e) => { e.stopPropagation(); uploadCvs(); }}>{loading.uploadCv ? 'Đang tải...' : 'Tải lên'}</button>
                </div>

                {cvFiles.length > 0 && (
                  <div className="preview-grid">
                    {cvFiles.map((file, idx) => (
                      <FilePreview key={`${file.name}-${idx}`} file={file} onRemove={() => setCvFiles((prev) => prev.filter((_, i) => i !== idx))} />
                    ))}
                  </div>
                )}
                {cvUploadedCount > 0 && <p className="upload-ok">✓ {cvUploadedCount} CV đã sẵn sàng để phân tích</p>}

                <button
                  className="saved-toggle cv"
                  disabled={!jobId}
                  onClick={() => {
                    if (!showSavedCvs) void fetchSavedDocs();
                    setShowSavedCvs((v) => !v);
                  }}
                >
                  <span>CV đã lưu {savedCvs.length ? `(${savedCvs.length})` : ''}</span>
                  <span className={`saved-toggle-caret ${showSavedCvs ? 'open' : ''}`}>▾</span>
                </button>
                {showSavedCvs && (
                  <div className="saved-docs">
                    {savedCvs.length === 0 ? (
                      <p className="saved-docs-empty">Chưa có CV nào được lưu. Hãy tải CV lên hoặc tạo ở mục "Danh sách CV".</p>
                    ) : (
                      savedCvs.map((doc) => (
                        <div className="saved-doc-row" key={doc.id}>
                          <span className="saved-doc-name" title={doc.original_filename}>{doc.display_name || doc.original_filename}</span>
                          <button className="secondary compact" disabled={!jobId} onClick={() => chooseSavedDoc(doc, 'cv')}>Chọn</button>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="wizard-nav">
              <button className="ghost" onClick={() => setStep(1)}>← Quay lại</button>
              <button className="primary-wide" onClick={enqueueJob} disabled={!jobId || !jdUploaded || cvUploadedCount === 0 || jobStatus === 'queued' || jobStatus === 'processing' || loading.enqueue}>
                {loading.enqueue ? 'Đang gửi...' : 'Phân tích và xếp hạng ứng viên'}
              </button>
            </div>
          </section>
        )}

        {step === 3 && (
          <>
            {(jobStatus === 'queued' || jobStatus === 'processing') && (
              <div className="processing-callout">
                <div className="spinner" />
                <span>Đang phân tích các CV. Danh sách ứng viên phù hợp sẽ tự hiện khi xong.</span>
              </div>
            )}

            <section className="panel ranking-panel">
              <div className="panel-header ranking-title-row">
                <div>
                  <h2>Xếp hạng CV theo độ phù hợp</h2>
                  <p className="ranking-subtitle">Bấm vào một dòng để xem báo cáo chi tiết của ứng viên.</p>
                </div>
              </div>

              {ranking.length === 0 ? (
                <div className="empty-state">
                  <strong>Chưa có kết quả</strong>
                  <span>Danh sách ứng viên sẽ hiện ở đây ngay khi phân tích xong.</span>
                </div>
              ) : (
                <div className="ranking-table-wrap">
                  <table className="ranking-table">
                    <thead>
                      <tr>
                        <th>Xếp hạng</th>
                        <th>Tên CV</th>
                        <th>Điểm tổng</th>
                        <th>Khớp kỹ năng</th>
                        <th>Khớp cấp bậc</th>
                        <th>Khớp lĩnh vực</th>
                        <th>Độ tin cậy AI</th>
                        <th>Kết luận</th>
                        <th>Trạng thái</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ranking.map((item) => {
                        const isTopRank = typeof item.rank === 'number' && item.rank <= 3;
                        const rowClassName = [
                          selectedCandidateId === item.id ? 'selected' : '',
                          isTopRank ? `top-rank top-rank-${item.rank}` : '',
                        ].filter(Boolean).join(' ');

                        return (
                        <tr key={item.id} className={rowClassName} onClick={() => item.overall_score !== null && loadCandidateResult(item.id)}>
                          <td><span className={`rank-pill ${isTopRank ? `rank-${item.rank}` : ''}`}>{item.rank || '-'}</span></td>
                          <td><strong>{item.name || item.id.slice(0, 8)}</strong></td>
                          <td><span className={`score-badge ${scoreTone(item.overall_score)}`}>{formatScoreValue(item.overall_score)}</span></td>
                          <td>{formatScoreValue(item.skill_match)}</td>
                          <td>{formatScoreValue(item.role_match)}</td>
                          <td>{formatScoreValue(item.domain_match)}</td>
                          <td>{friendlyConfidence(item.confidence_level)}</td>
                          <td>{friendlyRecommendation(item.recommendation)}</td>
                          <td><span className={`badge badge-${badgeToneForStatus(item.status)}`}>{statusText[item.status] || item.status}</span></td>
                        </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className="detail-section">
              <div className="detail-header">
                <div>
                  <p className="eyebrow">Chi tiết</p>
                  <h2>Báo cáo chi tiết ứng viên</h2>
                </div>
                <div className="detail-actions">
                  <button className="primary" disabled={!result || !selectedCandidateId || loading.downloadPdf} onClick={downloadCandidatePdf}>
                    {loading.downloadPdf ? 'Đang tải PDF...' : 'Tải PDF'}
                  </button>
                  <button className="secondary" disabled={!result} onClick={() => {
                    if (!result) return;
                    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `candidate-report-${selectedCandidateId.slice(0, 8) || jobId.slice(0, 8)}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}>JSON</button>
                </div>
              </div>

              {result?.compatibility ? <ResultReport result={result} /> : (
                <div className="empty-state large">
                  <strong>Bấm vào một ứng viên để xem chi tiết</strong>
                  <span>Bạn sẽ thấy điểm phù hợp, điểm mạnh - điểm yếu, gợi ý và nội dung CV được đọc ra.</span>
                </div>
              )}
            </section>

            <section className="debug-section">
              <button className="debug-toggle" onClick={() => setShowDebug(!showDebug)}>{showDebug ? 'Ẩn' : 'Hiện'} thông tin gỡ lỗi</button>
              {showDebug && (
                <div className="debug-card">
                  <p>Refresh Token: <code>{refreshToken ? 'OK' : 'Không có'}</code></p>
                  <p>Mã công việc: <code>{jobId || 'Không có'}</code></p>
                  <p>Trạng thái: <code>{jobStatus || 'Không có'}</code></p>
                  <pre>{JSON.stringify({ rankingCount: ranking.length, selectedCandidateId, hasResult: Boolean(result), compatibility: result?.compatibility, metadata: result?.metadata }, null, 2)}</pre>
                </div>
              )}
            </section>
          </>
        )}
        </>
        )}
      </main>
      <button
        type="button"
        className={`back-to-top ${showBackToTop ? 'visible' : ''}`}
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        aria-label="Lên đầu trang"
        title="Lên đầu trang"
      >
        ↑
      </button>
    </div>
  );
}

export default App;
