from odoo import SUPERUSER_ID, api


def post_init_hook(env):
    if not isinstance(env, api.Environment):
        env = api.Environment(env, SUPERUSER_ID, {})

    admin_group = env.ref("base.group_system", raise_if_not_found=False)
    dms_manager_group = env.ref("dms.group_dms_manager", raise_if_not_found=False)

    if admin_group and dms_manager_group and dms_manager_group not in admin_group.implied_ids:
        admin_group.write({"implied_ids": [(4, dms_manager_group.id)]})
