

class UploadHandler {
  constructor(zoneEl, options = {}) {
    this.zone = zoneEl;
    this.input = zoneEl.querySelector('input[type="file"]');
    this.files = [];
    this.accept = options.accept || "*";
    this.multiple = options.multiple || false;
    this.maxFiles = options.maxFiles || 20;
    this.maxSize = options.maxSize || 100 * 1024 * 1024; 
    this.onChange = options.onChange || (() => {});

    this.input.accept = this.accept;
    this.input.multiple = this.multiple;

    this._bindEvents();
  }

  _bindEvents() {

    this.zone.addEventListener("click", (e) => {
      if (e.target.closest(".file-item-remove")) return;
      this.input.click();
    });

    this.input.addEventListener("change", (e) => {
      this._addFiles(Array.from(e.target.files));
      this.input.value = "";
    });

    this.zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      this.zone.classList.add("drag-over");
    });

    this.zone.addEventListener("dragleave", (e) => {
      e.preventDefault();
      this.zone.classList.remove("drag-over");
    });

    this.zone.addEventListener("drop", (e) => {
      e.preventDefault();
      this.zone.classList.remove("drag-over");
      const droppedFiles = Array.from(e.dataTransfer.files);
      this._addFiles(droppedFiles);
    });
  }

  _addFiles(newFiles) {
    for (const file of newFiles) {
      if (file.size > this.maxSize) {
        alert(`"${file.name}" exceeds the 100MB file size limit.`);
        continue;
      }

      if (!this.multiple) {
        this.files = [file];
      } else {
        if (this.files.length >= this.maxFiles) {
          alert(`Maximum ${this.maxFiles} files allowed.`);
          break;
        }

        if (!this.files.find((f) => f.name === file.name && f.size === file.size)) {
          this.files.push(file);
        }
      }
    }

    this.onChange(this.files);
  }

  removeFile(index) {
    this.files.splice(index, 1);
    this.onChange(this.files);
  }

  clear() {
    this.files = [];
    this.onChange(this.files);
  }

  getFiles() {
    return this.files;
  }

  reorderFiles(fromIndex, toIndex) {
    const [item] = this.files.splice(fromIndex, 1);
    this.files.splice(toIndex, 0, item);
    this.onChange(this.files);
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + units[i];
}

window.UploadHandler = UploadHandler;
window.formatFileSize = formatFileSize;
