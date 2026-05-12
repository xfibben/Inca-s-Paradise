import {patch} from "@web/core/utils/patch";
import {ListController} from "@web/views/list/list_controller";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {_t} from "@web/core/l10n/translation";

function crearUploadPorArchivo() {
    return {
        async onChangeFileInput() {
            const files = [...this.fileInput.el.files];
            const attachments = [];

            for (const file of files) {
                const params = {
                    csrf_token: odoo.csrf_token,
                    ufile: [file],
                    model: "dms.file",
                    id: 0,
                };

                const fileData = await this.http.post(
                    "/web/binary/upload_attachment",
                    params,
                    "text"
                );
                const uploaded = JSON.parse(fileData);
                if (uploaded.error) {
                    throw new Error(uploaded.error);
                }
                attachments.push(...uploaded);
            }

            await this.onUpload(attachments);
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
