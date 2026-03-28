frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		frm.add_custom_button(__("Create DTE"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Create DTE Document"),
				fields: [
					{
						fieldname: "tipo_dte",
						fieldtype: "Select",
						label: __("Tipo DTE"),
						options: [
							"03 - Credito Fiscal",
							"01 - Factura",
							"44 - Factura Sujeto Excluido",
						],
						default: "03 - Credito Fiscal",
						reqd: 1,
					},
					{
						fieldname: "receptor_nit",
						fieldtype: "Data",
						label: __("Receptor NIT"),
						description: __("14 digits, no hyphens"),
					},
					{
						fieldname: "receptor_nrc",
						fieldtype: "Data",
						label: __("Receptor NRC"),
						description: __("With hyphen, e.g. 1234-5"),
					},
					{
						fieldname: "receptor_correo",
						fieldtype: "Data",
						label: __("Receptor Email"),
						options: "Email",
					},
					{
						fieldname: "condicion_operacion",
						fieldtype: "Select",
						label: __("Condicion Operacion"),
						options: ["1", "2", "3"],
						default: "1",
						description: __("1=Contado, 2=Credito, 3=Otro"),
					},
				],
				primary_action_label: __("Create"),
				primary_action(values) {
					frappe.call({
						method: "sv_dte.sv_dte.api.create_dte_from_invoice",
						args: {
							sales_invoice: frm.doc.name,
							tipo_dte: values.tipo_dte,
							receptor_nit: values.receptor_nit,
							receptor_nrc: values.receptor_nrc,
							receptor_correo: values.receptor_correo,
							condicion_operacion: values.condicion_operacion,
						},
						callback(r) {
							if (r.message) {
								d.hide();
								frappe.set_route("Form", "DTE Document", r.message);
							}
						},
					});
				},
			});
			d.show();
		}, __("El Salvador DTE"));
	},
});
