function ensureDownloadOverlay() {
    let overlay = document.getElementById("incas-dms-download-overlay");
    if (overlay) {
        return overlay;
    }

    overlay = document.createElement("div");
    overlay.id = "incas-dms-download-overlay";
    overlay.style.position = "fixed";
    overlay.style.right = "16px";
    overlay.style.bottom = "16px";
    overlay.style.zIndex = "9999";
    overlay.style.background = "#ffffff";
    overlay.style.border = "1px solid #d1d5db";
    overlay.style.borderRadius = "8px";
    overlay.style.padding = "12px";
    overlay.style.boxShadow = "0 8px 24px rgba(0,0,0,0.12)";
    overlay.style.minWidth = "320px";
    overlay.style.display = "none";
    overlay.innerHTML = `
        <div id="incas-dms-download-name" style="font-size:12px;color:#4b5563;margin-bottom:8px;"></div>
        <div style="width:100%;height:10px;background:#e5e7eb;border-radius:999px;overflow:hidden;">
            <div id="incas-dms-download-bar" style="width:0%;height:100%;background:#1aa093;"></div>
        </div>
        <div id="incas-dms-download-percent" style="font-size:12px;color:#4b5563;margin-top:8px;">0%</div>
    `;
    document.body.appendChild(overlay);
    return overlay;
}

function setDownloadProgress(fileName, percent) {
    const overlay = ensureDownloadOverlay();
    overlay.style.display = "block";
    overlay.querySelector("#incas-dms-download-name").textContent = fileName;
    overlay.querySelector("#incas-dms-download-bar").style.width = `${percent}%`;
    overlay.querySelector("#incas-dms-download-percent").textContent = `${percent}%`;
}

function hideDownloadProgress() {
    const overlay = ensureDownloadOverlay();
    window.setTimeout(() => {
        overlay.style.display = "none";
    }, 1200);
}

function parseFilename(contentDisposition) {
    if (!contentDisposition) {
        return "archivo";
    }
    const match = contentDisposition.match(/filename\*=UTF-8''([^;]+)|filename=\"?([^\";]+)\"?/i);
    if (!match) {
        return "archivo";
    }
    return decodeURIComponent(match[1] || match[2]);
}

function downloadWithProgress(url) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.responseType = "blob";

        xhr.addEventListener("progress", (event) => {
            const name = parseFilename(xhr.getResponseHeader("Content-Disposition"));
            if (event.lengthComputable) {
                setDownloadProgress(name, Math.round((event.loaded / event.total) * 100));
            } else {
                setDownloadProgress(name, 0);
            }
        });

        xhr.addEventListener("load", () => {
            if (xhr.status < 200 || xhr.status >= 300) {
                reject(new Error(`Download failed with status ${xhr.status}`));
                return;
            }
            const name = parseFilename(xhr.getResponseHeader("Content-Disposition"));
            const blobUrl = URL.createObjectURL(xhr.response);
            const link = document.createElement("a");
            link.href = blobUrl;
            link.download = name;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(blobUrl);
            setDownloadProgress(name, 100);
            hideDownloadProgress();
            resolve();
        });

        xhr.addEventListener("error", () => {
            reject(new Error("No se pudo completar la descarga del archivo."));
        });

        xhr.send();
    });
}

if (!window.__incasDmsDownloadBound) {
    window.__incasDmsDownloadBound = true;
    document.addEventListener(
        "click",
        async (event) => {
            const link = event.target.closest("a[href*='/incas/dms/file/'][href*='download=true']");
            if (!link) {
                return;
            }
            event.preventDefault();
            try {
                await downloadWithProgress(link.href);
            } catch (error) {
                window.alert(error.message || "No se pudo completar la descarga del archivo.");
            }
        },
        true
    );
}
