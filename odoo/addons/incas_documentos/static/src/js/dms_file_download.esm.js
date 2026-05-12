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

if (!window.__incasDmsDownloadBound) {
    window.__incasDmsDownloadBound = true;
    document.addEventListener(
        "click",
        (event) => {
            const link = event.target.closest("a[href*='/incas/dms/file/'][href*='download=true']");
            if (!link) {
                return;
            }
            const fileName = link.closest(".o_kanban_record, tr")?.innerText?.split("\n")[0]?.trim() || "archivo";
            setDownloadProgress(fileName, 100);
            hideDownloadProgress();
        },
        true
    );
}
