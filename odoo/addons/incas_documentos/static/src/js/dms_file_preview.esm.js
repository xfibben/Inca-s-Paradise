function getRecordIdFromPreview(target) {
    const link = target.closest(".o_kanban_dms_file_preview");
    if (!link) {
        return null;
    }
    const href =
        link.getAttribute("href") ||
        link.querySelector("[href]")?.getAttribute("href") ||
        "";
    const match = href.match(/id=(\d+)/);
    return match ? match[1] : null;
}

if (!window.__incasDmsPreviewBound) {
    window.__incasDmsPreviewBound = true;
    document.addEventListener(
        "click",
        (event) => {
            const recordId = getRecordIdFromPreview(event.target);
            if (!recordId) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            const previewUrl = `/incas/dms/file/${recordId}/content?download=false`;
            window.open(previewUrl, "_blank", "noopener");
        },
        true
    );
}
