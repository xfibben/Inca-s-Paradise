async function eliminarArchivo(recordId) {
    const response = await fetch("/web/dataset/call_kw/dms.file/unlink", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify({
            id: Date.now(),
            jsonrpc: "2.0",
            method: "call",
            params: {
                model: "dms.file",
                method: "unlink_incas_safe",
                args: [recordId],
                kwargs: {},
            },
        }),
    });

    if (!response.ok) {
        throw new Error(`Delete failed with status ${response.status}`);
    }

    const payload = await response.json();
    if (payload.error) {
        throw new Error(payload.error.data?.message || payload.error.message);
    }
}

if (!window.__incasDmsActionsBound) {
    window.__incasDmsActionsBound = true;
    document.addEventListener(
        "click",
        async (event) => {
            const deleteLink = event.target.closest(".incas_dms_delete");
            if (!deleteLink) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();

            const recordId = Number(deleteLink.dataset.recordId);
            if (!recordId) {
                window.alert("No se encontro el archivo a eliminar.");
                return;
            }

            try {
                await eliminarArchivo(recordId);
                window.location.reload();
            } catch (error) {
                window.alert(error.message || "No se pudo eliminar el archivo.");
            }
        },
        true
    );
}
