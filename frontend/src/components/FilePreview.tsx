import { useEffect, useState } from 'react';

const IMAGE_EXT = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'];

function fileExt(name: string): string {
  const i = name.lastIndexOf('.');
  return i >= 0 ? name.slice(i + 1).toLowerCase() : '';
}

export function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/**
 * Xem trước một tệp người dùng vừa chọn (trước khi tải lên) để họ kiểm tra
 * đúng CV/JD chưa. Ảnh và PDF render trực tiếp từ File qua object URL;
 * các định dạng khác (DOCX, TXT, PPTX...) hiển thị thẻ icon + tên + kích thước.
 */
export default function FilePreview({ file, onRemove }: { file: File; onRemove?: () => void }) {
  const [url, setUrl] = useState('');

  useEffect(() => {
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  const ext = fileExt(file.name);
  const isImage = IMAGE_EXT.includes(ext);
  const isPdf = ext === 'pdf';

  return (
    <div className="file-preview-card">
      <div className="file-preview-body">
        {isImage && url && <img src={url} alt={file.name} className="file-preview-img" />}
        {isPdf && url && (
          <object data={`${url}#toolbar=0&navpanes=0`} type="application/pdf" className="file-preview-pdf" aria-label={file.name}>
            <div className="file-preview-icon">PDF</div>
          </object>
        )}
        {!isImage && !isPdf && <div className="file-preview-icon">{ext.toUpperCase() || 'FILE'}</div>}
      </div>
      <div className="file-preview-meta">
        <span className="file-preview-name" title={file.name}>{file.name}</span>
        <span className="file-preview-size">{humanSize(file.size)} · {ext.toUpperCase() || 'FILE'}</span>
      </div>
      {onRemove && (
        <button className="file-preview-remove" onClick={onRemove} aria-label="Bỏ chọn tệp" title="Bỏ chọn">×</button>
      )}
    </div>
  );
}
