import {patch} from "@web/core/utils/patch";
import {ListController} from "@web/views/list/list_controller";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {_t} from "@web/core/l10n/translation";

function ensureUploadOverlay() {
    let overlay = document.getElementById("incas-dms-upload-overlay");
    if (overlay) {
        return overlay;
    }
    overlay = document.createElement("div");
    overlay.id = "incas-dms-upload-overlay";
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
        <div id="incas-dms-upload-name" style="font-size:12px;color:#4b5563;margin-bottom:8px;"></div>
        <div style="width:100%;height:10px;background:#e5e7eb;border-radius:999px;overflow:hidden;">
            <div id="incas-dms-upload-bar" style="width:0%;height:100%;background:#1aa093;"></div>
        </div>
        <div id="incas-dms-upload-percent" style="font-size:12px;color:#4b5563;margin-top:8px;">0%</div>
    `;
    document.body.appendChild(overlay);
    return overlay;
}

function setUploadProgress(fileName, percent) {
    const overlay = ensureUploadOverlay();
    overlay.style.display = "block";
    overlay.querySelector("#incas-dms-upload-name").textContent = fileName;
    overlay.querySelector("#incas-dms-upload-bar").style.width = `${percent}%`;
    overlay.querySelector("#incas-dms-upload-percent").textContent = `${percent}%`;
}

function hideUploadProgress() {
    const overlay = ensureUploadOverlay();
    overlay.style.display = "none";
}

function parsearRespuestaSubida(fileData) {
    try {
        return JSON.parse(fileData);
    } catch {
        throw new Error(
            "La subida no devolvio JSON valido. Revisa tamano, sesion o respuesta HTML del servidor."
        );
    }
}

function subirArchivoConProgreso(file, onProgress) {
    return new Promise((resolve, reject) => {
        const formData = new FormData();
        formData.append("csrf_token", odoo.csrf_token);
        formData.append("ufile", file);
        formData.append("model", "dms.file");
        formData.append("id", "0");

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/web/binary/upload_attachment");
        xhr.responseType = "text";

        xhr.upload.addEventListener("progress", (event) => {
            if (event.lengthComputable) {
                onProgress(Math.round((event.loaded / event.total) * 100));
            }
        });

        xhr.addEventListener("load", () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(xhr.responseText);
                return;
            }
            reject(new Error(`Upload failed with status ${xhr.status}`));
        });

        xhr.addEventListener("error", () => {
            reject(new Error("No se pudo completar la subida del archivo."));
        });

        xhr.addEventListener("abort", () => {
            reject(new Error("La subida del archivo fue cancelada."));
        });

        xhr.send(formData);
    });
}

function crearUploadPorArchivo() {
    return {
        setup() {
            super.setup(...arguments);
            this.pendingFiles = null;
        },

        async onChangeFileInput() {
            const files = this.pendingFiles || [...this.fileInput.el.files];
            const attachments = [];

            try {
                for (const file of files) {
                    setUploadProgress(file.name, 0);

                    const fileData = await subirArchivoConProgreso(file, (percent) => {
                        setUploadProgress(file.name, percent);
                    });
                    const uploaded = parsearRespuestaSubida(fileData);
                    if (uploaded.error) {
                        throw new Error(uploaded.error);
                    }
                    attachments.push(...uploaded);
                }

                await this.onUpload(attachments);
            } catch (error) {
                this.notification.add(
                    error.message ||
                        _t("No se pudo completar la subida del archivo pesado."),
                    {
                        type: "danger",
                    }
                );
            } finally {
                hideUploadProgress();
                this.pendingFiles = null;
                this.fileInput.el.value = "";
            }
        },

        async onUpload(attachments) {
            const attachmentIds = attachments.map((attachment) => attachment.id);
            const controllerID = this.actionService.currentController.jsId;

            if (!attachmentIds.length) {
                this.notification.add(_t("An error occurred during the upload"));
                return;
            }

            let directory_id = false;
            if (this.props.domain) {
                for (const domain_item of this.props.domain) {
                    if (
                        domain_item.length === 3 &&
                        domain_item[0] === "directory_id" &&
                        ["=", "child_of"].includes(domain_item[1])
                    ) {
                        directory_id = domain_item[2];
                    }
                }
            }

            if (directory_id === false) {
                this.actionService.restore(controllerID);
                return this.notification.add(_t("You must select a directory first"), {
                    type: "danger",
                });
            }

            try {
                await this.orm.call(
                    "dms.file",
                    "crear_desde_adjuntos_subidos",
                    [attachmentIds, directory_id]
                );
            } catch (error) {
                this.notification.add(error.data?.message || error.message, {
                    type: "danger",
                });
            } finally {
                this.actionService.restore(controllerID);
            }
        },
    };
}

patch(ListController.prototype, crearUploadPorArchivo());
patch(KanbanController.prototype, crearUploadPorArchivo());
