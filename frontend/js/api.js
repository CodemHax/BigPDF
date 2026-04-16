

const API_BASE = window.location.origin;

function getApiErrorMessage(error) {
  const detail = error && error.detail !== undefined ? error.detail : error;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const loc = Array.isArray(item.loc)
            ? item.loc.filter((part) => part !== "body").join(".")
            : "";
          const message = item.msg || JSON.stringify(item);
          return loc ? `${loc}: ${message}` : message;
        }
        return String(item);
      })
      .join("\n");
  }

  if (detail && typeof detail === "object") {
    return detail.msg || JSON.stringify(detail);
  }

  return "Processing failed";
}

const API = {

  async process(endpoint, files, options = {}, onProgress = null, requestOptions = {}) {
    const formData = new FormData();
    const fileField = requestOptions.fileField || (files.length === 1 ? "file" : "files");

    files.forEach((file) => {
      formData.append(fileField, file);
    });

    for (const [key, value] of Object.entries(options)) {
      if (value !== "" && value !== null && value !== undefined) {
        formData.append(key, value);
      }
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE}${endpoint}`, true);
      xhr.responseType = "blob";

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          const percent = Math.round((e.loaded / e.total) * 100);
          onProgress(percent);
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {

          const disposition = xhr.getResponseHeader("Content-Disposition");
          let filename = "output";
          if (disposition) {
            const match = disposition.match(/filename="?(.+?)"?$/);
            if (match) filename = match[1];
          }

          resolve({
            blob: xhr.response,
            filename: filename,
            headers: {
              originalSize: xhr.getResponseHeader("X-Original-Size"),
              compressedSize: xhr.getResponseHeader("X-Compressed-Size"),
              reductionPercent: xhr.getResponseHeader("X-Reduction-Percent"),
            },
          });
        } else {

          const reader = new FileReader();
          reader.onload = () => {
            try {
              const error = JSON.parse(reader.result);
              reject(new Error(getApiErrorMessage(error)));
            } catch {
              reject(new Error(`Server error (${xhr.status})`));
            }
          };
          reader.onerror = () => reject(new Error(`Server error (${xhr.status})`));
          reader.readAsText(xhr.response);
        }
      };

      xhr.onerror = () => reject(new Error("Network error. Is the server running?"));
      xhr.ontimeout = () => reject(new Error("Request timed out"));
      xhr.timeout = 300000; 

      xhr.send(formData);
    });
  },

  download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  async healthCheck() {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      return res.ok;
    } catch {
      return false;
    }
  },
};

window.API = API;
