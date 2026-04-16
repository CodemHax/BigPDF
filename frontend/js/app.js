
(function () {
  let currentUploader = null;
  let currentTool = null;
  let resultData = null;

  function getRoute() {
    const pathname = window.location.pathname;
    const route = pathname.startsWith('/') ? pathname.slice(1) : pathname;
    return route;
  }

  function navigate(route) {
    const path = "/" + route;
    window.history.pushState({ route }, "", path);
    handleRoute();
  }

  function handleRoute() {
    const route = getRoute();
    const app = document.getElementById("app");

    if (route && route !== "/") {
      const tool = window.TOOLS.find((t) => t.id === route);
      if (tool) {
        renderToolPage(tool, app);
        return;
      } else {
        showErrorPage(app, "Page not found. The tool you're looking for doesn't exist.");
        return;
      }
    }

    renderHomePage(app);
  }

  function showErrorPage(container, message) {
    container.innerHTML = `
      <div class="error-page">
        <div class="error-container">
          <div class="error-icon">
            <i data-lucide="alert-circle"></i>
          </div>
          <h1>Oops! Something Went Wrong</h1>
          <p class="error-message">${message}</p>
          <button class="error-action-btn" id="error-home-btn">
            <i data-lucide="home" style="width:18px;height:18px"></i>
            Back to Home
          </button>
        </div>
      </div>
    `;
    document.getElementById("error-home-btn").addEventListener("click", () => {
      navigate("");
    });
    if (window.lucide) window.lucide.createIcons();
  }

  window.addEventListener("popstate", handleRoute);
  window.addEventListener("load", handleRoute);

  function renderHomePage(container) {
    currentTool = null;
    currentUploader = null;
    resultData = null;

    container.innerHTML = `
      <section class="hero">
        <div class="hero-badge">
          <i data-lucide="shield-check" style="width:14px;height:14px"></i>
          Encrypted &bull; Private &bull; Free
        </div>
        <h1>Every PDF tool you need,<br><span class="gradient-text">all in one place</span></h1>
        <p>Merge, split, compress, convert, watermark, and do so much more with your PDF files — completely free, fully encrypted, and auto-deleted in 30 minutes.</p>
      </section>

      <section class="trust-bar">
        <div class="trust-item">
          <i data-lucide="lock" style="width:18px;height:18px"></i>
          <div>
            <strong>256-bit Encryption</strong>
            <span>Files encrypted at rest</span>
          </div>
        </div>
        <div class="trust-item">
          <i data-lucide="clock" style="width:18px;height:18px"></i>
          <div>
            <strong>Auto-Delete in 30 min</strong>
            <span>Nothing stored permanently</span>
          </div>
        </div>
        <div class="trust-item">
          <i data-lucide="eye-off" style="width:18px;height:18px"></i>
          <div>
            <strong>Zero Access</strong>
            <span>We never read your files</span>
          </div>
        </div>
        <div class="trust-item">
          <i data-lucide="infinity" style="width:18px;height:18px"></i>
          <div>
            <strong>100% Free</strong>
            <span>No limits, no sign-up</span>
          </div>
        </div>
      </section>

      <section class="tools-section">
        <h2 class="tools-section-title">All PDF Tools</h2>
        <div class="tools-grid" id="tools-grid"></div>
      </section>

      <footer class="footer">
        <p>Built with ❤️ by <a href="#">BigPDF</a> — Your complete PDF toolkit</p>
        <p class="footer-privacy">All files are encrypted and auto-deleted within 30 minutes.</p>
      </footer>
    `;

    const grid = document.getElementById("tools-grid");
    window.TOOLS.forEach((tool) => {
      const card = document.createElement("div");
      card.className = "tool-card";
      card.setAttribute("data-color", tool.color);
      card.id = `tool-${tool.id}`;
      card.innerHTML = `
        <div class="tool-card-icon">
          <i data-lucide="${tool.icon}"></i>
        </div>
        <div class="tool-card-text">
          <h3>${tool.name}</h3>
          <p>${tool.description}</p>
        </div>
      `;
      card.addEventListener("click", () => navigate(tool.id));
      grid.appendChild(card);
    });

    if (window.lucide) window.lucide.createIcons();
  }

  function renderToolPage(tool, container) {
    currentTool = tool;
    resultData = null;
    const usesUpload = tool.requiresUpload !== false;
    const uploadHtml = usesUpload
      ? `
        <!-- Upload Zone -->
        <div class="upload-zone" id="upload-zone">
          <input type="file" id="file-input" />
          <div class="upload-icon">
            <i data-lucide="upload-cloud"></i>
          </div>
          <h3>Drop your ${tool.acceptLabel} here</h3>
          <p>or <span class="browse-btn">browse files</span> &bull; Max 100MB per file</p>
        </div>

        <!-- File List -->
        <div class="file-list" id="file-list"></div>
      `
      : "";

    container.innerHTML = `
      <div class="tool-page">
        <div class="tool-page-header">
          <a href="/" class="tool-page-back" id="back-btn">
            <i data-lucide="arrow-left" style="width:16px;height:16px"></i>
            All Tools
          </a>
          <div class="tool-page-icon" data-color="${tool.color}" style="background: var(--icon-bg); color: var(--icon-color);" data-card-parent>
            <i data-lucide="${tool.icon}"></i>
          </div>
          <h1>${tool.name}</h1>
          <p>${tool.description}</p>
        </div>

        ${uploadHtml}

        <!-- PDF Preview -->
        <div id="pdf-preview-container"></div>

        <!-- Page Selector (for split tool) -->
        ${tool.pageSelector ? '<div id="page-selector-container"></div>' : ''}

        <!-- Options -->
        ${tool.options.length > 0 ? renderOptions(tool.options) : ""}

        <!-- Live Preview (watermark, rotate) -->
        ${tool.livePreview ? '<div id="live-preview-container"></div>' : ''}

        <!-- Action Button -->
        <button class="action-btn" id="action-btn" ${usesUpload ? "disabled" : ""}>
          <i data-lucide="play" style="width:20px;height:20px"></i>
          <span id="action-btn-text">${getActionText(tool)}</span>
        </button>
      </div>

      <!-- Processing Overlay -->
      <div class="processing-overlay" id="processing-overlay">
        <div class="processing-box">
          <div class="processing-spinner"></div>
          <h3>Processing your file...</h3>
          <p>This may take a moment depending on file size.</p>
        </div>
      </div>

      <!-- Success Overlay -->
      <div class="success-overlay" id="success-overlay">
        <div class="success-box">
          <div class="success-icon">
            <i data-lucide="check-circle"></i>
          </div>
          <h3>Done!</h3>
          <p id="success-message">Your file has been processed successfully.</p>
          <div class="success-info" id="success-info"></div>
          <button class="download-btn" id="download-btn">
            <i data-lucide="download" style="width:20px;height:20px"></i>
            Download File
          </button>
          <button class="reset-btn" id="reset-btn">Process another file</button>
        </div>
      </div>
    `;

    const iconParent = container.querySelector("[data-card-parent]");
    if (iconParent) {
      iconParent.closest(".tool-page-header").querySelector(".tool-page-icon").setAttribute(
        "style",
        getToolIconStyle(tool.color)
      );
    }

    currentUploader = null;
    const uploadZone = document.getElementById("upload-zone");
    if (usesUpload && uploadZone) {
      currentUploader = new UploadHandler(uploadZone, {
        accept: tool.accept,
        multiple: tool.multiple || false,
        maxFiles: tool.maxFiles || 20,
        onChange: (files) => onFilesChanged(files, tool),
      });
    }

    const actionBtn = document.getElementById("action-btn");
    actionBtn.addEventListener("click", () => processFiles(tool));

    document.getElementById("reset-btn").addEventListener("click", () => {
      document.getElementById("success-overlay").classList.remove("active");
      if (currentUploader) {
        currentUploader.clear();
        renderFileList([], tool);
      }
      clearPdfPreview();
      const psc = document.getElementById("page-selector-container");
      if (psc) psc.innerHTML = "";
      selectedPages = new Set();
      actionBtn.disabled = usesUpload;
    });

    document.getElementById("download-btn").addEventListener("click", () => {
      if (resultData) {
        API.download(resultData.blob, resultData.filename);
      }
    });

    const backBtn = document.getElementById("back-btn");
    backBtn.addEventListener("click", (e) => {
      e.preventDefault();
      window.history.back();
    });

    if (window.lucide) window.lucide.createIcons();
  }

  function getToolIconStyle(color) {
    const colors = {
      red: "background: #ffeaed; color: #e8384f;",
      pink: "background: #fce4ec; color: #e84393;",
      orange: "background: #fff3e0; color: #fd6a3e;",
      gold: "background: #fff8e1; color: #f5a623;",
      green: "background: #e8f5e9; color: #00b87a;",
      teal: "background: #e0f7fa; color: #00a3b4;",
      blue: "background: #e3f2fd; color: #4285f4;",
      indigo: "background: #e8eaf6; color: #5c6bc0;",
      cyan: "background: #e0f7fa; color: #00a3b4;",
    };
    return colors[color] || colors.blue;
  }

  function getActionText(tool) {
    const map = {
      merge: "Merge PDFs",
      split: "Split PDF",
      compress: "Compress PDF",
      "pdf-to-word": "Convert to Word",
      "pdf-to-image": "Convert to Images",
      "image-to-pdf": "Convert to PDF",
      "word-to-pdf": "Convert to PDF",
      "ppt-to-pdf": "Convert to PDF",
      "excel-to-pdf": "Convert to PDF",
      "html-to-pdf": "Convert to PDF",
      "url-to-pdf": "Convert to PDF",
      watermark: "Add Watermark",
      rotate: "Rotate PDF",
      protect: "Protect PDF",
      unlock: "Unlock PDF",
      "page-numbers": "Add Page Numbers",
    };
    return map[tool.id] || "Process";
  }

  function renderOptions(options) {
    let html = `<div class="options-panel"><div class="options-title">Options</div>`;

    for (const opt of options) {
      html += `<div class="option-group">`;
      html += `<label for="opt-${opt.id}">${opt.label}</label>`;

      if (opt.type === "text" || opt.type === "password" || opt.type === "number" || opt.type === "url") {
        html += `<input
          type="${opt.type}"
          id="opt-${opt.id}"
          data-option="${opt.id}"
          placeholder="${opt.placeholder || ""}"
          value="${opt.default || ""}"
          ${opt.min !== undefined ? `min="${opt.min}"` : ""}
          ${opt.max !== undefined ? `max="${opt.max}"` : ""}
          ${opt.required ? "required" : ""}
        />`;
      } else if (opt.type === "radio") {
        html += `<div class="option-radio-group">`;
        for (const choice of opt.choices) {
          const checked = choice.value === String(opt.default) ? "checked" : "";
          html += `
            <div class="option-radio">
              <input type="radio" id="opt-${opt.id}-${choice.value}" name="opt-${opt.id}" value="${choice.value}" data-option="${opt.id}" ${checked} />
              <label for="opt-${opt.id}-${choice.value}">${choice.label}</label>
            </div>`;
        }
        html += `</div>`;
      } else if (opt.type === "select") {
        html += `<select id="opt-${opt.id}" data-option="${opt.id}">`;
        for (const choice of opt.choices) {
          const selected = choice.value === opt.default ? "selected" : "";
          html += `<option value="${choice.value}" ${selected}>${choice.label}</option>`;
        }
        html += `</select>`;
      } else if (opt.type === "range") {
        html += `
          <div class="option-range">
            <input type="range" id="opt-${opt.id}" data-option="${opt.id}"
              min="${opt.min}" max="${opt.max}" step="${opt.step}" value="${opt.default}" 
              oninput="document.getElementById('range-val-${opt.id}').textContent = this.value" />
            <span class="range-value" id="range-val-${opt.id}">${opt.default}</span>
          </div>`;
      }

      html += `</div>`;
    }

    html += `</div>`;
    return html;
  }

  function getOptionValues() {
    const values = {};
    document.querySelectorAll("[data-option]").forEach((el) => {
      const key = el.dataset.option;
      if (el.type === "radio") {
        if (el.checked) values[key] = el.value;
      } else {
        if (!values[key]) values[key] = el.value;
      }
    });
    return values;
  }

  let selectedPages = new Set();

  function onFilesChanged(files, tool) {
    renderFileList(files, tool);
    const actionBtn = document.getElementById("action-btn");
    const minFiles = tool.minFiles || 1;
    actionBtn.disabled = files.length < minFiles;

    if (tool.pageSelector && files.length > 0) {
      clearPdfPreview();
      renderPageSelector(files[0]);
      return;
    }

    const pageSelectorContainer = document.getElementById("page-selector-container");
    if (pageSelectorContainer) pageSelectorContainer.innerHTML = "";

    if (files.length > 0 && tool.accept.includes(".pdf")) {
      renderPdfPreview(files);
    } else {
      clearPdfPreview();
    }

    if (tool.livePreview && files.length > 0) {
      loadLivePreviewPage(files[0], tool);
    } else {
      clearLivePreview();
    }
  }

  function renderFileList(files, tool) {
    const list = document.getElementById("file-list");
    if (files.length === 0) {
      list.innerHTML = "";
      return;
    }

    const isReorderable = tool.reorderable && files.length > 1;

    list.innerHTML = files
      .map(
        (file, idx) => `
      <div class="file-item${isReorderable ? ' file-item-reorderable' : ''}" draggable="${isReorderable}" data-index="${idx}">
        ${isReorderable ? `<div class="file-item-order">${idx + 1}</div>` : ''}
        <div class="file-item-icon">
          <i data-lucide="${getFileIcon(file.name)}"></i>
        </div>
        <div class="file-item-info">
          <div class="file-item-name">${file.name}</div>
          <div class="file-item-size">${formatFileSize(file.size)}</div>
        </div>
        ${isReorderable ? `
          <div class="file-item-arrows">
            <button class="file-item-arrow" data-dir="up" data-index="${idx}" title="Move up" ${idx === 0 ? 'disabled' : ''}>
              <i data-lucide="chevron-up"></i>
            </button>
            <button class="file-item-arrow" data-dir="down" data-index="${idx}" title="Move down" ${idx === files.length - 1 ? 'disabled' : ''}>
              <i data-lucide="chevron-down"></i>
            </button>
          </div>
        ` : ''}
        <button class="file-item-remove" data-index="${idx}" title="Remove">
          <i data-lucide="x"></i>
        </button>
      </div>
    `
      )
      .join("");

    list.querySelectorAll(".file-item-remove").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const index = parseInt(btn.dataset.index);
        currentUploader.removeFile(index);
      });
    });

    if (isReorderable) {
      list.querySelectorAll(".file-item-arrow").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const index = parseInt(btn.dataset.index);
          const dir = btn.dataset.dir;
          if (dir === "up" && index > 0) {
            currentUploader.reorderFiles(index, index - 1);
          } else if (dir === "down" && index < files.length - 1) {
            currentUploader.reorderFiles(index, index + 1);
          }
        });
      });

      let dragFrom = null;
      list.querySelectorAll(".file-item").forEach((item) => {
        item.addEventListener("dragstart", (e) => {
          dragFrom = parseInt(item.dataset.index);
          item.classList.add("file-item-dragging");
          e.dataTransfer.effectAllowed = "move";
        });
        item.addEventListener("dragend", () => {
          item.classList.remove("file-item-dragging");
          list.querySelectorAll(".file-item").forEach(el => el.classList.remove("file-item-dragover"));
        });
        item.addEventListener("dragover", (e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = "move";
          item.classList.add("file-item-dragover");
        });
        item.addEventListener("dragleave", () => {
          item.classList.remove("file-item-dragover");
        });
        item.addEventListener("drop", (e) => {
          e.preventDefault();
          const dragTo = parseInt(item.dataset.index);
          if (dragFrom !== null && dragFrom !== dragTo) {
            currentUploader.reorderFiles(dragFrom, dragTo);
          }
          dragFrom = null;
        });
      });
    }

    if (window.lucide) window.lucide.createIcons();
  }

  function getFileIcon(filename) {
    const ext = filename.split(".").pop().toLowerCase();
    const map = {
      pdf: "file-text",
      doc: "file-text",
      docx: "file-text",
      jpg: "image",
      jpeg: "image",
      png: "image",
      gif: "image",
      bmp: "image",
      webp: "image",
      tiff: "image",
    };
    return map[ext] || "file";
  }

  let pdfPreviewAbort = null;

  function clearPdfPreview() {
    if (pdfPreviewAbort) {
      pdfPreviewAbort = true;
    }
    const container = document.getElementById("pdf-preview-container");
    if (container) container.innerHTML = "";
  }

  async function renderPdfPreview(files) {
    const container = document.getElementById("pdf-preview-container");
    if (!container) return;

    const pdfFiles = files.filter((f) => f.name.toLowerCase().endsWith(".pdf"));
    if (pdfFiles.length === 0) {
      container.innerHTML = "";
      return;
    }

    if (typeof pdfjsLib === "undefined") {
      container.innerHTML = "";
      return;
    }

    pdfjsLib.GlobalWorkerOptions.workerSrc =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

    container.innerHTML = `
      <div class="pdf-preview-loading">
        <div class="mini-spinner"></div>
        Loading preview...
      </div>
    `;

    pdfPreviewAbort = false;

    try {
      if (pdfFiles.length > 1) {
        await renderMultiPdfPreview(pdfFiles, container);
      } else {
        await renderSinglePdfPreview(pdfFiles[0], container);
      }
    } catch (err) {
      if (!pdfPreviewAbort) {
        container.innerHTML = "";
      }
    }
  }

  async function renderSinglePdfPreview(file, container) {
    const arrayBuffer = await file.arrayBuffer();
    if (pdfPreviewAbort) return;

    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    if (pdfPreviewAbort) return;

    const totalPages = pdf.numPages;
    const maxPreview = Math.min(totalPages, 20);

    container.innerHTML = `
      <div class="pdf-preview">
        <div class="pdf-preview-header">
          <span class="pdf-preview-title">Page Preview</span>
          <span class="pdf-preview-info">${totalPages} page${totalPages > 1 ? "s" : ""}</span>
        </div>
        <div class="pdf-preview-grid" id="pdf-pages-grid"></div>
      </div>
    `;

    const grid = document.getElementById("pdf-pages-grid");

    for (let i = 1; i <= maxPreview; i++) {
      if (pdfPreviewAbort) return;

      const page = await pdf.getPage(i);
      const viewport = page.getViewport({ scale: 0.5 });

      const pageDiv = document.createElement("div");
      pageDiv.className = "pdf-preview-page";

      const canvas = document.createElement("canvas");
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const numLabel = document.createElement("span");
      numLabel.className = "pdf-preview-page-num";
      numLabel.textContent = i;

      pageDiv.appendChild(canvas);
      pageDiv.appendChild(numLabel);
      grid.appendChild(pageDiv);

      const ctx = canvas.getContext("2d");
      await page.render({ canvasContext: ctx, viewport: viewport }).promise;
    }

    if (totalPages > maxPreview) {
      const moreDiv = document.createElement("div");
      moreDiv.className = "pdf-preview-page";
      moreDiv.style.display = "flex";
      moreDiv.style.alignItems = "center";
      moreDiv.style.justifyContent = "center";
      moreDiv.style.fontSize = "0.85rem";
      moreDiv.style.color = "var(--text-muted)";
      moreDiv.style.fontWeight = "600";
      moreDiv.innerHTML = `+${totalPages - maxPreview}<br>more`;
      grid.appendChild(moreDiv);
    }
  }

  async function renderMultiPdfPreview(files, container) {
    container.innerHTML = `
      <div class="pdf-preview">
        <div class="pdf-preview-header">
          <span class="pdf-preview-title">Files Preview</span>
          <span class="pdf-preview-info">${files.length} files</span>
        </div>
        <div class="pdf-preview-grid" id="pdf-pages-grid"></div>
      </div>
    `;

    const grid = document.getElementById("pdf-pages-grid");

    for (let i = 0; i < files.length; i++) {
      if (pdfPreviewAbort) return;

      try {
        const arrayBuffer = await files[i].arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 0.5 });

        const pageDiv = document.createElement("div");
        pageDiv.className = "pdf-preview-page";

        const canvas = document.createElement("canvas");
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        const numLabel = document.createElement("span");
        numLabel.className = "pdf-preview-page-num";
        numLabel.textContent = files[i].name.split(".")[0].substring(0, 12);

        pageDiv.appendChild(canvas);
        pageDiv.appendChild(numLabel);
        grid.appendChild(pageDiv);

        const ctx = canvas.getContext("2d");
        await page.render({ canvasContext: ctx, viewport: viewport }).promise;
      } catch (e) {

      }
    }
  }

  async function renderPageSelector(file) {
    const container = document.getElementById("page-selector-container");
    if (!container) return;

    if (typeof pdfjsLib === "undefined") {
      container.innerHTML = "";
      return;
    }

    pdfjsLib.GlobalWorkerOptions.workerSrc =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

    container.innerHTML = `
      <div class="pdf-preview-loading">
        <div class="mini-spinner"></div>
        Loading pages...
      </div>
    `;

    try {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      const totalPages = pdf.numPages;

      selectedPages = new Set();
      for (let i = 1; i <= totalPages; i++) {
        selectedPages.add(i);
      }

      container.innerHTML = `
        <div class="page-selector">
          <div class="page-selector-header">
            <div>
              <span class="page-selector-title">Select Pages</span>
              <span class="page-selector-info" id="page-selector-count">${totalPages} of ${totalPages} selected</span>
            </div>
            <div class="page-selector-actions">
              <button class="page-selector-btn" id="ps-select-all">Select All</button>
              <button class="page-selector-btn" id="ps-deselect-all">Deselect All</button>
            </div>
          </div>
          <div class="page-selector-grid" id="page-selector-grid"></div>
        </div>
      `;

      const grid = document.getElementById("page-selector-grid");

      for (let i = 1; i <= totalPages; i++) {
        const page = await pdf.getPage(i);
        const viewport = page.getViewport({ scale: 0.5 });

        const pageDiv = document.createElement("div");
        pageDiv.className = "page-selector-page selected";
        pageDiv.dataset.page = i;

        const canvas = document.createElement("canvas");
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        const removeBtn = document.createElement("button");
        removeBtn.className = "page-selector-x";
        removeBtn.innerHTML = '<i data-lucide="x"></i>';
        removeBtn.title = "Remove page";

        const numLabel = document.createElement("span");
        numLabel.className = "page-selector-num";
        numLabel.textContent = i;

        pageDiv.appendChild(canvas);
        pageDiv.appendChild(removeBtn);
        pageDiv.appendChild(numLabel);
        grid.appendChild(pageDiv);

        const ctx = canvas.getContext("2d");
        await page.render({ canvasContext: ctx, viewport: viewport }).promise;

        removeBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          togglePageSelection(i, pageDiv, totalPages);
        });

        pageDiv.addEventListener("click", () => {
          togglePageSelection(i, pageDiv, totalPages);
        });
      }

      document.getElementById("ps-select-all").addEventListener("click", () => {
        for (let i = 1; i <= totalPages; i++) selectedPages.add(i);
        updatePageSelectorUI(totalPages);
      });

      document.getElementById("ps-deselect-all").addEventListener("click", () => {
        selectedPages.clear();
        updatePageSelectorUI(totalPages);
      });

      if (window.lucide) window.lucide.createIcons();
      updateActionBtnState();

    } catch (err) {
      container.innerHTML = "";
    }
  }

  function togglePageSelection(pageNum, pageDiv, totalPages) {
    if (selectedPages.has(pageNum)) {
      selectedPages.delete(pageNum);
      pageDiv.classList.remove("selected");
      pageDiv.classList.add("removed");
    } else {
      selectedPages.add(pageNum);
      pageDiv.classList.add("selected");
      pageDiv.classList.remove("removed");
    }
    updatePageCount(totalPages);
    updateActionBtnState();
  }

  function updatePageCount(totalPages) {
    const countEl = document.getElementById("page-selector-count");
    if (countEl) {
      countEl.textContent = `${selectedPages.size} of ${totalPages} selected`;
    }
  }

  function updatePageSelectorUI(totalPages) {
    const grid = document.getElementById("page-selector-grid");
    if (!grid) return;
    grid.querySelectorAll(".page-selector-page").forEach((el) => {
      const p = parseInt(el.dataset.page);
      if (selectedPages.has(p)) {
        el.classList.add("selected");
        el.classList.remove("removed");
      } else {
        el.classList.remove("selected");
        el.classList.add("removed");
      }
    });
    updatePageCount(totalPages);
    updateActionBtnState();
  }

  function updateActionBtnState() {
    const actionBtn = document.getElementById("action-btn");
    if (actionBtn && currentTool && currentTool.pageSelector) {
      actionBtn.disabled = selectedPages.size === 0;
    }
  }

  let livePreviewPageData = null; 

  function clearLivePreview() {
    livePreviewPageData = null;
    const container = document.getElementById("live-preview-container");
    if (container) container.innerHTML = "";
  }

  async function loadLivePreviewPage(file, tool) {
    const container = document.getElementById("live-preview-container");
    if (!container || !tool.livePreview) return;

    if (typeof pdfjsLib === "undefined") return;

    pdfjsLib.GlobalWorkerOptions.workerSrc =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

    container.innerHTML = `
      <div class="pdf-preview-loading">
        <div class="mini-spinner"></div>
        Loading preview...
      </div>
    `;

    try {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 1.0 });

      const offCanvas = document.createElement("canvas");
      offCanvas.width = viewport.width;
      offCanvas.height = viewport.height;
      const offCtx = offCanvas.getContext("2d");
      await page.render({ canvasContext: offCtx, viewport: viewport }).promise;

      livePreviewPageData = {
        imageData: offCtx.getImageData(0, 0, viewport.width, viewport.height),
        width: viewport.width,
        height: viewport.height,
      };

      renderLivePreview(tool);
      bindOptionChangeListeners(tool);
    } catch (err) {
      container.innerHTML = "";
    }
  }

  function renderLivePreview(tool) {
    const container = document.getElementById("live-preview-container");
    if (!container || !livePreviewPageData) return;

    const { imageData, width, height } = livePreviewPageData;
    const options = getOptionValues();

    const maxW = 240;
    const scale = maxW / width;
    const displayW = Math.round(width * scale);
    const displayH = Math.round(height * scale);

    container.innerHTML = `
      <div class="live-preview">
        <div class="live-preview-title">Preview — Page 1</div>
        <div class="live-preview-panels">
          <div class="live-preview-panel">
            <div class="live-preview-label">Before</div>
            <canvas id="lp-before" width="${displayW}" height="${displayH}"></canvas>
          </div>
          <div class="live-preview-arrow"><i data-lucide="arrow-right"></i></div>
          <div class="live-preview-panel">
            <div class="live-preview-label live-preview-label-after">After</div>
            <canvas id="lp-after" width="${tool.livePreview === 'rotate' ? (parseInt(options.rotation || 90) % 180 === 0 ? displayW : displayH) : displayW}" height="${tool.livePreview === 'rotate' ? (parseInt(options.rotation || 90) % 180 === 0 ? displayH : displayW) : displayH}"></canvas>
          </div>
        </div>
      </div>
    `;

    const beforeCanvas = document.getElementById("lp-before");
    const beforeCtx = beforeCanvas.getContext("2d");
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = width;
    tempCanvas.height = height;
    tempCanvas.getContext("2d").putImageData(imageData, 0, 0);
    beforeCtx.drawImage(tempCanvas, 0, 0, displayW, displayH);

    const afterCanvas = document.getElementById("lp-after");
    const afterCtx = afterCanvas.getContext("2d");

    if (tool.livePreview === "watermark") {

      afterCtx.drawImage(tempCanvas, 0, 0, displayW, displayH);

      const text = options.text || "CONFIDENTIAL";
      const opacity = parseFloat(options.opacity || 0.3);
      const fontSize = parseInt(options.font_size || 50) * scale;
      const rotation = parseInt(options.rotation || 45);

      afterCtx.save();
      afterCtx.globalAlpha = opacity;
      afterCtx.fillStyle = "#888888";
      afterCtx.font = `bold ${fontSize}px Inter, Helvetica, sans-serif`;
      afterCtx.textAlign = "center";
      afterCtx.textBaseline = "middle";
      afterCtx.translate(displayW / 2, displayH / 2);
      afterCtx.rotate((-rotation * Math.PI) / 180);
      afterCtx.fillText(text, 0, 0);
      afterCtx.restore();

    } else if (tool.livePreview === "rotate") {
      const rot = parseInt(options.rotation || 90);
      afterCtx.save();

      if (rot === 90) {
        afterCanvas.width = displayH;
        afterCanvas.height = displayW;
        afterCtx.translate(displayH, 0);
        afterCtx.rotate(Math.PI / 2);
      } else if (rot === 180) {
        afterCanvas.width = displayW;
        afterCanvas.height = displayH;
        afterCtx.translate(displayW, displayH);
        afterCtx.rotate(Math.PI);
      } else if (rot === 270) {
        afterCanvas.width = displayH;
        afterCanvas.height = displayW;
        afterCtx.translate(0, displayW);
        afterCtx.rotate(-Math.PI / 2);
      }

      afterCtx.drawImage(tempCanvas, 0, 0, displayW, displayH);
      afterCtx.restore();
    } else if (tool.livePreview === "filter") {
      const filterType = options.filter_type || "grayscale";
      afterCtx.drawImage(tempCanvas, 0, 0, displayW, displayH);

      const imageData = afterCtx.getImageData(0, 0, displayW, displayH);
      const data = imageData.data;

      if (filterType === "grayscale") {
        for (let i = 0; i < data.length; i += 4) {
          const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
          data[i] = data[i + 1] = data[i + 2] = gray;
        }
      } else if (filterType === "invert") {
        for (let i = 0; i < data.length; i += 4) {
          data[i] = 255 - data[i];
          data[i + 1] = 255 - data[i + 1];
          data[i + 2] = 255 - data[i + 2];
        }
      } else if (filterType === "brighter") {
        for (let i = 0; i < data.length; i += 4) {
          data[i] = Math.min(255, data[i] + 50);
          data[i + 1] = Math.min(255, data[i + 1] + 50);
          data[i + 2] = Math.min(255, data[i + 2] + 50);
        }
      } else if (filterType === "darker") {
        for (let i = 0; i < data.length; i += 4) {
          data[i] = Math.max(0, data[i] - 50);
          data[i + 1] = Math.max(0, data[i + 1] - 50);
          data[i + 2] = Math.max(0, data[i + 2] - 50);
        }
      }

      afterCtx.putImageData(imageData, 0, 0);
    }

    if (window.lucide) window.lucide.createIcons();
  }

  function bindOptionChangeListeners(tool) {

    const optionsPanel = document.querySelector(".options-panel");
    if (!optionsPanel) return;

    const inputs = optionsPanel.querySelectorAll("input, select");
    inputs.forEach((input) => {

      const eventType = (input.type === "range" || input.type === "text" || input.type === "number") ? "input" : "change";
      input.addEventListener(eventType, () => {
        renderLivePreview(tool);
      });
    });
  }

  async function processFiles(tool) {
    const usesUpload = tool.requiresUpload !== false;
    if (usesUpload && (!currentUploader || currentUploader.getFiles().length === 0)) return;

    const files = currentUploader ? currentUploader.getFiles() : [];
    const options = getOptionValues();

    if (tool.pageSelector && selectedPages.size > 0) {
      const sortedPages = Array.from(selectedPages).sort((a, b) => a - b);
      options.ranges = sortedPages.join(",");
    }

    for (const opt of tool.options) {
      if (opt.required && (!options[opt.id] || options[opt.id].trim() === "")) {
        alert(`Please fill in: ${opt.label}`);
        return;
      }
    }

    const overlay = document.getElementById("processing-overlay");
    overlay.classList.add("active");

    try {
      const result = await API.process(
        tool.endpoint,
        files,
        options,
        null,
        { fileField: tool.multiple ? "files" : "file" }
      );
      resultData = result;

      overlay.classList.remove("active");

      const successOverlay = document.getElementById("success-overlay");
      const successInfo = document.getElementById("success-info");
      const successMsg = document.getElementById("success-message");

      successMsg.textContent = `Your ${tool.name.toLowerCase()} operation completed successfully!`;

      let infoHtml = "";
      if (result.headers.originalSize) {
        const origSize = parseInt(result.headers.originalSize);
        const compSize = parseInt(result.headers.compressedSize);
        const reduction = result.headers.reductionPercent;
        infoHtml = `
          <div class="success-stat">
            <div class="label">Original</div>
            <div class="value">${formatFileSize(origSize)}</div>
          </div>
          <div class="success-stat">
            <div class="label">Compressed</div>
            <div class="value">${formatFileSize(compSize)}</div>
          </div>
          <div class="success-stat">
            <div class="label">Saved</div>
            <div class="value">${reduction}%</div>
          </div>
        `;
      } else {
        infoHtml = `
          <div class="success-stat">
            <div class="label">Output Size</div>
            <div class="value">${formatFileSize(result.blob.size)}</div>
          </div>
        `;
      }
      successInfo.innerHTML = infoHtml;

      successOverlay.classList.add("active");
      if (window.lucide) window.lucide.createIcons();
    } catch (error) {
      overlay.classList.remove("active");
      alert(`Error: ${error.message}`);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    handleRoute();

    document.querySelector(".navbar-brand")?.addEventListener("click", (e) => {
      e.preventDefault();
      navigate("");
    });

    document.querySelector("#nav-tools-link")?.addEventListener("click", (e) => {
      e.preventDefault();
      navigate("");
    });
  });
})();
