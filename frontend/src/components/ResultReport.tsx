import { useState } from 'react';

interface ScoreItem {
  score: number;
  weight: number;
  description: string;
}

interface ResultData {
  compatibility?: {
    overall_score: number;
    level: string;
    recommendation: string;
    message: string;
    confidence: number;
  };
  score_breakdown?: Record<string, ScoreItem>;
  skills_analysis?: {
    matched_skills: string[];
    missing_skills: string[];
    extra_skills: string[];
    skill_match_ratio: number;
    matched_must_have?: string[];
    missing_must_have?: string[];
    matched_nice_to_have?: string[];
    missing_nice_to_have?: string[];
  };
  candidate_summary?: {
    summary: string | null;
    strengths: string[];
    weaknesses: string[];
    risk_flags: string[];
  };
  recommendations?: {
    for_recruiter: string[];
    for_candidate: string[];
  };
  interview_questions?: string[];
  alternative_roles?: string[];
  warnings?: string[];
  extracted_text?: {
    cv?: string;
    jd?: string;
    cv_truncated?: boolean;
    jd_truncated?: boolean;
  } | null;
  metadata?: {
    ai_provider: string | null;
    ai_model: string | null;
    processing_time_seconds: number | null;
    confidence_level?: string | null;
    role_match?: number | null;
    domain_match?: number | null;
    candidate_years?: number | null;
    required_years?: number | null;
    cv_role_level?: string | null;
    jd_role_level?: string | null;
    cv_domains?: string[];
    jd_domains?: string[];
  };
}

type TabKey = 'overview' | 'skills' | 'experience' | 'recommendations' | 'interview' | 'extracted';

const ROLE_LEVEL_LABELS: Record<string, string> = {
  intern: 'Thực tập',
  junior: 'Junior',
  mid: 'Trung cấp',
  senior: 'Senior',
  manager: 'Quản lý',
  unknown: 'Không rõ',
};

function roleLevelLabel(value?: string | null): string {
  if (!value) return 'Không rõ';
  return ROLE_LEVEL_LABELS[value] || value;
}

const SCORE_LABELS: Record<string, string> = {
  skill_match: 'Mức độ khớp kỹ năng',
  role_match: 'Mức độ phù hợp cấp bậc',
  domain_match: 'Mức độ phù hợp lĩnh vực',
  experience_match: 'Mức độ phù hợp kinh nghiệm',
  education_match: 'Mức độ phù hợp học vấn',
  keyword_match: 'Mức độ khớp từ khóa',
  cv_quality: 'Chất lượng CV',
};

const RECOMMENDATION_LABELS: Record<string, string> = {
  'Rất nên tuyển': 'Ưu tiên phỏng vấn',
  'Nên tuyển': 'Nên đưa vào phỏng vấn',
  'Cân nhắc thêm': 'Cần xem thêm hồ sơ',
  'Không ưu tiên': 'Chưa nên ưu tiên',
  'Từ chối': 'Chưa phù hợp',
};

function formatLabel(value: string): string {
  return SCORE_LABELS[value] || value.replace(/_/g, ' ').replace(/\b\w/g, (char: string) => char.toUpperCase());
}

function friendlyRecommendation(value?: string | null): string {
  if (!value) return 'Chưa có nhận định';
  return RECOMMENDATION_LABELS[value] || value;
}

function getScoreClass(score: number): string {
  if (score >= 85) return 'excellent';
  if (score >= 70) return 'strong';
  if (score >= 55) return 'medium';
  if (score >= 40) return 'weak';
  return 'bad';
}

// Thanh điểm dùng tông hồng chủ đạo (đậm dần theo điểm) thay cho thang
// xanh/lá cũ, đúng phong cách màu #FFB6C1.
function getBarColor(score: number): string {
  if (score >= 85) return '#9f344f';
  if (score >= 70) return '#c75b72';
  if (score >= 55) return '#d97a8e';
  if (score >= 40) return '#e59aa9';
  return '#ecb3bf';
}

function ScoreBar({ label, score, description }: { label: string; score: number; description?: string }) {
  return (
    <div className="score-bar-row">
      <div className="score-bar-header">
        <span>{label}</span>
        <strong style={{ color: getBarColor(score) }}>{score}%</strong>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${Math.min(score, 100)}%`, background: getBarColor(score) }} />
      </div>
      {description && <div className="score-bar-desc">{description}</div>}
    </div>
  );
}

function TagList({ title, items, kind }: { title: string; items?: string[]; kind: 'success' | 'danger' | 'neutral' }) {
  const cleanItems = (items || []).map((item) => item.trim()).filter(Boolean);
  if (cleanItems.length === 0) return null;
  return (
    <div className="tag-section">
      <h4>{title}</h4>
      <div className="tags">
        {cleanItems.map((item) => <span className={`tag ${kind}`} key={item}>{item}</span>)}
      </div>
    </div>
  );
}

function PrintList({ title, items, ordered = false }: { title: string; items?: string[]; ordered?: boolean }) {
  const hasItems = Boolean(items && items.length > 0);

  return (
    <div className="print-list-block">
      <h4>{title}</h4>
      {hasItems ? (
        ordered ? (
          <ol className="interview-list">{items!.map((item, index) => <li key={index}>{item}</li>)}</ol>
        ) : (
          <ul>{items!.map((item, index) => <li key={index}>{item}</li>)}</ul>
        )
      ) : (
        <p className="print-empty">Chưa có dữ liệu.</p>
      )}
    </div>
  );
}

export default function ResultReport({ result }: { result: ResultData | null }) {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');

  if (!result || !result.compatibility) return null;

  const {
    compatibility,
    score_breakdown,
    skills_analysis,
    candidate_summary,
    recommendations,
    interview_questions,
    alternative_roles,
    warnings,
    extracted_text,
    metadata,
  } = result;
  const scoreClass = getScoreClass(compatibility.overall_score);

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'overview', label: 'Tổng quan' },
    { key: 'skills', label: 'Kỹ năng' },
    { key: 'experience', label: 'Kinh nghiệm' },
    { key: 'recommendations', label: 'Khuyến nghị' },
    { key: 'interview', label: 'Phỏng vấn' },
    { key: 'extracted', label: 'Văn bản trích xuất' },
  ];

  return (
    <div className="result-report">
      {warnings && warnings.length > 0 && (
        <div className="warnings-banner">
          <div className="warning-icon">!</div>
          <div className="warning-content">
            <strong>Lưu ý chất lượng phân tích</strong>
            <ul>{warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
          </div>
        </div>
      )}

      <div className={`score-card ${scoreClass}`}>
        <div className="score-card-content">
          <div className="score-card-label">Mức độ phù hợp tổng thể</div>
          <div className="big-score">{compatibility.overall_score}%</div>
          <div className="score-card-level">{compatibility.level}</div>
          <div className="score-card-rec">{friendlyRecommendation(compatibility.recommendation)}</div>
          <div className="score-card-confidence">Độ tin cậy: {metadata?.confidence_level || 'Không rõ'} ({Math.round(compatibility.confidence * 100)}%)</div>
        </div>
        <div className="score-card-message">{compatibility.message}</div>
      </div>

      <div className="print-report">
        <div className="print-report-header">
          <div>
            <p className="eyebrow">Báo cáo PDF</p>
            <h2>Báo cáo chi tiết ứng viên</h2>
            <p>Đánh giá độ phù hợp giữa CV ứng viên và mô tả công việc.</p>
          </div>
          <div className="print-report-score">
            <span>Điểm phù hợp</span>
            <strong>{compatibility.overall_score}%</strong>
          </div>
        </div>

        <section className="report-card print-summary-card">
            <p className="print-section-label">01. Tổng quan</p>
            <h3>Tổng quan đánh giá</h3>
          <div className="print-summary-grid">
            <div><span>Mức đánh giá</span><strong>{compatibility.level}</strong></div>
            <div><span>Nhận định</span><strong>{friendlyRecommendation(compatibility.recommendation)}</strong></div>
            <div><span>Độ tin cậy</span><strong>{metadata?.confidence_level || 'Không rõ'} ({Math.round(compatibility.confidence * 100)}%)</strong></div>
          </div>
          {compatibility.message && <p className="summary-text">{compatibility.message}</p>}
          {candidate_summary ? (
            <>
              <h4>Tóm tắt ứng viên</h4>
              {candidate_summary.summary ? <p className="summary-text">{candidate_summary.summary}</p> : <p className="print-empty">Chưa có tóm tắt ứng viên.</p>}
              <TagList title="Điểm mạnh" items={candidate_summary.strengths} kind="success" />
              <TagList title="Cần cải thiện" items={candidate_summary.weaknesses} kind="danger" />
              <TagList title="Lưu ý khi xem hồ sơ" items={candidate_summary.risk_flags} kind="danger" />
            </>
          ) : (
            <p className="print-empty">Chưa có tóm tắt ứng viên.</p>
          )}

          {score_breakdown && (
            <div className="print-score-breakdown">
              <h4>Điểm thành phần</h4>
              {Object.entries(score_breakdown).map(([key, item]) => (
                <ScoreBar key={key} label={formatLabel(key)} score={item.score} description={item.description} />
              ))}
            </div>
          )}

          {warnings && warnings.length > 0 && <PrintList title="Lưu ý chất lượng phân tích" items={warnings} />}
        </section>

        <section className="report-card">
          <p className="print-section-label">02. Kỹ năng</p>
          <h3>Phân tích kỹ năng</h3>
          {skills_analysis ? (
            <>
              <ScoreBar label="Mức độ khớp kỹ năng" score={skills_analysis.skill_match_ratio} />
              <TagList title="Kỹ năng bắt buộc đã có" items={skills_analysis.matched_must_have} kind="success" />
              <TagList title="Kỹ năng bắt buộc còn thiếu" items={skills_analysis.missing_must_have} kind="danger" />
              <TagList title="Kỹ năng ưu tiên đã có" items={skills_analysis.matched_nice_to_have} kind="success" />
              <TagList title="Kỹ năng ưu tiên còn thiếu" items={skills_analysis.missing_nice_to_have} kind="danger" />
              <TagList title="Tất cả kỹ năng khớp" items={skills_analysis.matched_skills} kind="success" />
              <TagList title="Tất cả kỹ năng còn thiếu" items={skills_analysis.missing_skills} kind="danger" />
              <TagList title="Kỹ năng bổ sung" items={skills_analysis.extra_skills} kind="neutral" />
            </>
          ) : (
            <p className="print-empty">Chưa có dữ liệu phân tích kỹ năng.</p>
          )}
        </section>

        <section className="report-card">
          <p className="print-section-label">03. Kinh nghiệm</p>
          <h3>Kinh nghiệm, cấp bậc và lĩnh vực</h3>
          <div className="meta-grid">
            <div><span>Số năm KN ứng viên</span><strong>{metadata?.candidate_years ?? 'Không rõ'}</strong></div>
            <div><span>Số năm KN yêu cầu</span><strong>{metadata?.required_years ?? 'Không rõ'}</strong></div>
            <div><span>Cấp bậc ứng viên</span><strong>{roleLevelLabel(metadata?.cv_role_level)}</strong></div>
            <div><span>Cấp bậc JD</span><strong>{roleLevelLabel(metadata?.jd_role_level)}</strong></div>
            <div><span>Khớp cấp bậc</span><strong>{metadata?.role_match ?? 'N/A'}%</strong></div>
            <div><span>Khớp lĩnh vực</span><strong>{metadata?.domain_match ?? 'N/A'}%</strong></div>
          </div>
          <TagList title="Lĩnh vực của ứng viên" items={metadata?.cv_domains} kind="neutral" />
          <TagList title="Lĩnh vực của JD" items={metadata?.jd_domains} kind="neutral" />
        </section>

        <section className="report-card">
          <p className="print-section-label">04. Khuyến nghị</p>
          <h3>Khuyến nghị hành động</h3>
          {recommendations ? (
            <>
              <PrintList title="Dành cho nhà tuyển dụng" items={recommendations.for_recruiter} />
              <PrintList title="Dành cho ứng viên" items={recommendations.for_candidate} />
            </>
          ) : (
            <p className="print-empty">Chưa có khuyến nghị.</p>
          )}
          <TagList title="Vị trí thay thế phù hợp" items={alternative_roles} kind="success" />
        </section>

        <section className="report-card">
          <p className="print-section-label">05. Phỏng vấn</p>
          <h3>Câu hỏi phỏng vấn đề xuất</h3>
          <PrintList title="Danh sách câu hỏi" items={interview_questions} ordered />
        </section>

        <section className="report-card print-extracted-card">
          <p className="print-section-label">06. Văn bản trích xuất</p>
          <h3>Văn bản trích xuất</h3>
          <h4>Văn bản CV {extracted_text?.cv_truncated ? '(đã cắt bớt)' : ''}</h4>
          <pre className="extracted-text-block print-extracted-text">{extracted_text?.cv || 'Không có văn bản CV được lưu.'}</pre>
          <h4>Văn bản JD {extracted_text?.jd_truncated ? '(đã cắt bớt)' : ''}</h4>
          <pre className="extracted-text-block print-extracted-text">{extracted_text?.jd || 'Không có văn bản JD được lưu.'}</pre>
        </section>

        {metadata && (
          <div className="print-report-meta">
            AI: {metadata.ai_provider || 'N/A'} / {metadata.ai_model || 'N/A'} | Thời gian xử lý: {metadata.processing_time_seconds?.toFixed(2) || 'N/A'}s
          </div>
        )}
      </div>

      <div className="tab-bar">
        {tabs.map((tab) => (
          <button key={tab.key} className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`} onClick={() => setActiveTab(tab.key)}>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {activeTab === 'overview' && (
          <>
            {score_breakdown && (
              <div className="report-card">
                <h3>Phân tích điểm số</h3>
                {Object.entries(score_breakdown).map(([key, item]) => (
                  <ScoreBar key={key} label={formatLabel(key)} score={item.score} description={item.description} />
                ))}
              </div>
            )}

            {candidate_summary && (
              <div className="report-card">
                <h3>Tóm tắt ứng viên</h3>
                {candidate_summary.summary && <p className="summary-text">{candidate_summary.summary}</p>}
                <TagList title="Điểm mạnh" items={candidate_summary.strengths} kind="success" />
                <TagList title="Cần cải thiện" items={candidate_summary.weaknesses} kind="danger" />
                <TagList title="Lưu ý khi xem hồ sơ" items={candidate_summary.risk_flags} kind="danger" />
              </div>
            )}
          </>
        )}

        {activeTab === 'skills' && skills_analysis && (
          <div className="report-card">
            <h3>Phân tích kỹ năng</h3>
            <ScoreBar label="Mức độ khớp kỹ năng" score={skills_analysis.skill_match_ratio} />
            <TagList title="Kỹ năng bắt buộc đã có" items={skills_analysis.matched_must_have} kind="success" />
            <TagList title="Kỹ năng bắt buộc còn thiếu" items={skills_analysis.missing_must_have} kind="danger" />
            <TagList title="Kỹ năng ưu tiên đã có" items={skills_analysis.matched_nice_to_have} kind="success" />
            <TagList title="Kỹ năng ưu tiên còn thiếu" items={skills_analysis.missing_nice_to_have} kind="danger" />
            <TagList title="Tất cả kỹ năng khớp" items={skills_analysis.matched_skills} kind="success" />
            <TagList title="Tất cả kỹ năng còn thiếu" items={skills_analysis.missing_skills} kind="danger" />
            <TagList title="Kỹ năng bổ sung" items={skills_analysis.extra_skills} kind="neutral" />
          </div>
        )}

        {activeTab === 'experience' && (
          <div className="report-card">
            <h3>Mức độ phù hợp kinh nghiệm, cấp bậc và lĩnh vực</h3>
            <div className="meta-grid">
              <div><span>Số năm KN ứng viên</span><strong>{metadata?.candidate_years ?? 'Không rõ'}</strong></div>
              <div><span>Số năm KN yêu cầu</span><strong>{metadata?.required_years ?? 'Không rõ'}</strong></div>
              <div><span>Cấp bậc ứng viên</span><strong>{roleLevelLabel(metadata?.cv_role_level)}</strong></div>
              <div><span>Cấp bậc JD</span><strong>{roleLevelLabel(metadata?.jd_role_level)}</strong></div>
              <div><span>Khớp cấp bậc</span><strong>{metadata?.role_match ?? 'N/A'}%</strong></div>
              <div><span>Khớp lĩnh vực</span><strong>{metadata?.domain_match ?? 'N/A'}%</strong></div>
            </div>
            <TagList title="Lĩnh vực của ứng viên" items={metadata?.cv_domains} kind="neutral" />
            <TagList title="Lĩnh vực của JD" items={metadata?.jd_domains} kind="neutral" />
          </div>
        )}

        {activeTab === 'recommendations' && recommendations && (
          <>
            <div className="report-card">
              <h3>Dành cho nhà tuyển dụng</h3>
              <ul>{recommendations.for_recruiter.map((item, index) => <li key={index}>{item}</li>)}</ul>
            </div>
            <div className="report-card">
              <h3>Dành cho ứng viên</h3>
              <ul>{recommendations.for_candidate.map((item, index) => <li key={index}>{item}</li>)}</ul>
            </div>
            <div className="report-card">
              <h3>Vị trí thay thế phù hợp</h3>
              <TagList title="Vị trí gợi ý" items={alternative_roles} kind="success" />
            </div>
          </>
        )}

        {activeTab === 'interview' && interview_questions && interview_questions.length > 0 && (
          <div className="report-card">
            <h3>Câu hỏi phỏng vấn</h3>
            <ol className="interview-list">{interview_questions.map((question, index) => <li key={index}>{question}</li>)}</ol>
          </div>
        )}

        {activeTab === 'extracted' && (
          <div className="report-card">
            <h3>Văn bản trích xuất</h3>
            <h4>Văn bản CV {extracted_text?.cv_truncated ? '(đã cắt bớt)' : ''}</h4>
            <pre className="extracted-text-block">{extracted_text?.cv || 'Không có văn bản CV được lưu.'}</pre>
            <h4>Văn bản JD {extracted_text?.jd_truncated ? '(đã cắt bớt)' : ''}</h4>
            <pre className="extracted-text-block">{extracted_text?.jd || 'Không có văn bản JD được lưu.'}</pre>
          </div>
        )}
      </div>

      {metadata && (
        <div className="report-meta">
          AI: {metadata.ai_provider || 'N/A'} / {metadata.ai_model || 'N/A'} | Thời gian xử lý: {metadata.processing_time_seconds?.toFixed(2) || 'N/A'}s
        </div>
      )}
    </div>
  );
}
