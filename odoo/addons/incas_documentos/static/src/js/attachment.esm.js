import {Attachment} from "@mail/core/common/attachment_model";
import {patch} from "@web/core/utils/patch";

function getDmsUrl(id, download = false) {
    return `/incas/dms/file/${id}/content?download=${download ? "true" : "false"}`;
}

patch(Attachment.prototype, {
    _handleImage() {
        if (this.model_name && this.model_name === "dms.file") {
            return getDmsUrl(this.id, false);
        }
        return super._handleImage(...arguments);
    },
    _handlePdf() {
        if (this.model_name && this.model_name === "dms.file") {
            return getDmsUrl(this.id, false);
        }
        return super._handlePdf(...arguments);
    },
    get defaultSource() {
        if (this.model_name && this.model_name === "dms.file") {
            return getDmsUrl(this.id, false);
        }
        return super.defaultSource;
    },
    get downloadUrl() {
        if (this.model_name && this.model_name === "dms.file") {
            return getDmsUrl(this.id, true);
        }
        return super.downloadUrl;
    },
});
