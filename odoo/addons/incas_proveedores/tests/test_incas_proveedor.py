from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIncasProveedor(TransactionCase):
    def test_crud_proveedor(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Hotel Sol del Valle",
                "email": "maria@solvalle.test",
                "phone": "+51 84 123456",
                "mobile": "+51 999888777",
                "city": "Cusco",
            }
        )

        proveedor = self.env["incas.proveedor"].create(
            {
                "name": "Hotel Sol del Valle",
                "partner_id": partner.id,
                "tipo_proveedor": "hotel",
                "contact_name": "Maria Quispe",
                "email": "maria@solvalle.test",
                "phone": "+51 84 123456",
                "city": "Cusco",
            }
        )

        self.assertTrue(proveedor.exists())
        self.assertEqual(proveedor.name, "Hotel Sol del Valle")
        self.assertEqual(proveedor.tipo_proveedor, "hotel")
        self.assertEqual(proveedor.partner_id, partner)

        proveedor.write(
            {
                "mobile": "+51 999888777",
                "tipo_proveedor": "operacion",
            }
        )
        self.assertEqual(proveedor.mobile, "+51 999888777")
        self.assertEqual(proveedor.tipo_proveedor, "operacion")

        encontrados = self.env["incas.proveedor"].search(
            [("name", "ilike", "Sol del Valle")]
        )
        self.assertIn(proveedor, encontrados)

        proveedor.unlink()
        self.assertFalse(proveedor.exists())
