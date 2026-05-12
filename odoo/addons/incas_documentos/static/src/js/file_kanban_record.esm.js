import {FileKanbanRecord} from "../../../dms/static/src/js/views/file_kanban_record.esm";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(FileKanbanRecord.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
    },

    async onGlobalClick(ev) {
        const deleteLink = ev.target.closest(".incas_dms_delete");
        if (deleteLink) {
            ev.preventDefault();
            ev.stopPropagation();
            try {
                await this.orm.unlink(this.props.record.resModel, [this.props.record.resId]);
                await this.action.doAction({type: "ir.actions.client", tag: "reload"});
            } catch (error) {
                this.notification.add(error.message || "No se pudo eliminar el archivo.", {
                    type: "danger",
                });
            }
            return;
        }
        return super.onGlobalClick(ev);
    },
});
