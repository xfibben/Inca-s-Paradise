import {FileKanbanRecord} from "../../../dms/static/src/js/views/file_kanban_record.esm";
import {patch} from "@web/core/utils/patch";

function getPreviewUrl(record) {
    return `/incas/dms/file/${record.data.id}/content?download=false`;
}

patch(FileKanbanRecord.prototype, {
    onGlobalClick(ev) {
        if (ev.target.closest(".o_kanban_dms_file_preview")) {
            const previewUrl = getPreviewUrl(this.props.record);
            window.open(previewUrl, "_blank", "noopener");
            return;
        }
        return super.onGlobalClick(ev);
    },
});
