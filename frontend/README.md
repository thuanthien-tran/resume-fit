# Frontend

Giao diện web (React + Vite + TypeScript) cho nền tảng phân tích CV ↔ JD:
đăng nhập, tạo job, upload JD + nhiều CV, xem xếp hạng ứng viên và báo cáo
kết quả matching.

## Cấu trúc

```text
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── style.css
│   └── components/     # ResultReport, ...
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Lệnh thường dùng

```bash
npm install      # cài dependencies
npm run dev      # chạy dev server (Vite)
npm run build    # build production -> dist/
npm run preview  # xem thử bản build
```
