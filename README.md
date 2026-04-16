# BigPDF — Free Online PDF Toolkit

A complete, privacy-focused PDF toolkit built with FastAPI and vanilla JavaScript. All files are encrypted at rest and auto-deleted within 30 minutes.

## 🔒 Privacy & Security

- **Fernet (AES-128) encryption** at rest — uploaded files are immediately encrypted and unreadable on disk
- **Auto-delete** — all files and encryption keys are permanently deleted after 30 minutes
- **Zero access** — the server never reads or stores your document content
- **No accounts** — no sign-up, no tracking, no data collection

## 🛠️ Tools

| Tool | Description |
|------|-------------|
| **Merge PDF** | Combine up to 5 PDFs into one with drag-to-reorder |
| **Split PDF** | Visual page selector — click to keep/remove pages |
| **Compress PDF** | Reduce file size (low/medium/high quality) |
| **Extract Text** | Pull all text content from a PDF into a `.txt` file |
| **PDF to Image** | Convert pages to PNG or JPG (150/200/300 DPI) |
| **Image to PDF** | Combine images into a single PDF |
| **Word to PDF** | Convert DOC/DOCX via LibreOffice |
| **PPT to PDF** | Convert PPT/PPTX via LibreOffice |
| **Excel to PDF** | Convert XLS/XLSX via LibreOffice |
| **HTML to PDF** | Convert HTML files via Puppeteer |
| **URL to PDF** | Convert public web page URLs via Puppeteer |
| **Watermark** | Add text watermark with live before/after preview |
| **Rotate PDF** | Rotate pages 90°/180°/270° with live preview |
| **Filter PDF** | Apply visual filters (Grayscale, Invert, Brighter, Darker) with live preview |
| **Flatten PDF** | Consolidate all layers, annotations, and form fields into a single flattened layer |
| **Protect PDF** | Password-encrypt a PDF |
| **Unlock PDF** | Remove password from a PDF |
| **Page Numbers** | Add page numbers at any position |

## 📦 Tech Stack

**Backend**
- Python 3.10+
- FastAPI + Uvicorn
- PyPDF2, pikepdf, ReportLab
- LibreOffice (headless) for Office document conversion
- Node.js + Puppeteer for HTML and URL to PDF
- Fernet symmetric encryption (cryptography)

**Frontend**
- Vanilla HTML/CSS/JavaScript (SPA)
- PDF.js for page previews
- Lucide icons
- Inter font (Google Fonts)

## 🚀 Local Development

### Prerequisites

- Python 3.10+
- LibreOffice (for document conversion tools)
- Poppler (`poppler-utils` for PDF to Image)
- Node.js + npm (for HTML and URL to PDF)

### Setup

```bash
# Clone the repo
git clone <your-repo-url>
cd bigpdf

# Install Python dependencies
cd backend
pip install -r requirements.txt
npm install

# Start the dev server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in your browser.

## 🐧 Production Deployment (Linux VPS)

### System Dependencies

```bash
sudo apt update
sudo apt install -y poppler-utils libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress nodejs npm
npm install --prefix backend
```

### Run with Gunicorn

```bash
pip install gunicorn

gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

## 📁 Project Structure

```
bigpdf/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt
│   ├── routers/
│   │   ├── merge.py            # Merge PDF endpoint
│   │   ├── split.py            # Split PDF endpoint
│   │   ├── compress.py         # Compress PDF endpoint
│   │   ├── convert.py          # Convert + Extract Text endpoints
│   │   ├── watermark.py        # Watermark endpoint
│   │   ├── rotate.py           # Rotate endpoint
│   │   ├── security.py         # Protect/Unlock endpoints
│   │   └── page_numbers.py     # Page Numbers endpoint
│   └── services/
│       ├── file_service.py     # File management + encryption
│       ├── pdf_service.py      # Core PDF operations
│       └── convert_service.py  # File format conversions
├── frontend/
│   ├── index.html              # SPA shell
│   ├── css/style.css           # Design system
│   └── js/
│       ├── app.js              # SPA router + page rendering
│       ├── tools.js            # Tool definitions
│       ├── upload.js           # File upload handler
│       └── api.js              # API client
└── .gitignore
```

## ⚙️ Configuration

| Setting | Default | Location |
|---------|---------|----------|
| Max file size | 100MB | `file_service.py` |
| Auto-cleanup interval | 30 minutes | `file_service.py` |
| Cleanup check frequency | 5 minutes | `file_service.py` |
| Max merge files | 5 | `merge.py` + `tools.js` |
| Request timeout | 5 minutes | `api.js` |
| API docs | Disabled | `main.py` |
| Extra frontend origins | Same-origin only | `BIGPDF_ALLOWED_ORIGINS` env var |
| Direct API calls | Disabled | `BIGPDF_ALLOW_DIRECT_API=1` env var |

For production, serve the frontend and API from the same origin when possible. If the frontend is on a different trusted origin, set `BIGPDF_ALLOWED_ORIGINS=https://yourdomain.com` before starting the backend.

## 📄 License

MIT
