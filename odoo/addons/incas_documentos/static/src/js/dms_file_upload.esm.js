import {patch} from "@web/core/utils/patch";
import {ListController} from "@web/views/list/list_controller";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {_t} from "@web/core/l10n/translation";
import {useState} from "@odoo/owl";
import {FileKanbanRenderer} from "../../../dms/static/src/js/views/file_kanban_renderer.esm";
import {FileListRenderer} from "../../../dms/static/src/js/views/file_list_renderer.esm";

function leerEntradaArchivo(entry) {
    return new Promise((resolve, reject) => {
        entry.file(resolve, reject);
    });
}

function leerDirectorio(reader) {
    return new Promise((resolve, reject) => {
        reader.readEntries(resolve, reject);
    });
}

async function extraerArchivosDesdeEntrada(entry) {
    if (entry.isFile) {
        return [await leerEntradaArchivo(entry)];
    }
    if (!entry.isDirectory) {
        return [];
    }

    const reader = entry.createReader();
    const files = [];

    while (true) {
        const entries = await leerDirectorio(reader);
        if (!entries.length) {
            break;
        }
        for (const child of entries) {
            files.push(...(await extraerArchivosDesdeEntrada(child)));
        }
    }

    return files;
}

async function extraerArchivosDrop(dataTransfer) {
    const items = [...(dataTransfer?.items || [])];
    const files = [];

    for (const item of items) {
        const entry = item.webkitGetAsEntry?.();
        if (entry) {
            files.push(...(await extraerArchivosDesdeEntrada(entry)));
            continue;
        }
        const file = item.getAsFile?.();
        if (file) {
            files.push(file);
        }
    }

    if (files.length) {
        return files;
    }
    return [...(dataTransfer?.files || [])];
}

function construirFileList(files) {
    const dataTransfer = new DataTransfer();
    for (const file of files) {
        dataTransfer.items.add(file);
    }
    return dataTransfer.files;
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
            this.uploadState = useState({
                active: false,
                fileName: "",
                percent: 0,
            });
            this.pendingFiles = null;
        },

        async onChangeFileInput() {
            const files = this.pendingFiles || [...this.fileInput.el.files];
            const attachments = [];

            try {
                for (const file of files) {
                    this.uploadState.active = true;
                    this.uploadState.fileName = file.name;
                    this.uploadState.percent = 0;

                    const fileData = await subirArchivoConProgreso(file, (percent) => {
                        this.uploadState.percent = percent;
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
                this.uploadState.active = false;
                this.uploadState.fileName = "";
                this.uploadState.percent = 0;
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

function crearDropZoneCarpetas() {
    return {
        async onDrop(ev) {
            ev.preventDefault();
            this.dragState.showDragZone = false;
            const files = await extraerArchivosDrop(ev.dataTransfer);
            await this.env.bus.trigger("change_file_input", {
                files: construirFileList(files),
            });
        },
    };
}

patch(FileKanbanRenderer.prototype, crearDropZoneCarpetas());
patch(FileListRenderer.prototype, crearDropZoneCarpetas());
