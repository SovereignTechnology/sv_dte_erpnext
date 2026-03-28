frappe.ui.form.on("DTE Document", {
	refresh(frm) {
		if (frm.doc.status === "Draft") {
			frm.add_custom_button(__("Build JSON"), () => {
				frm.call("build_dte_json").then(() => frm.reload_doc());
			}, __("Actions"));
		}

		if (frm.doc.dte_json && frm.doc.status === "Draft") {
			frm.add_custom_button(__("Sign"), () => {
				frm.call("sign_dte").then(() => frm.reload_doc());
			}, __("Actions"));
		}

		if (frm.doc.signed_payload && frm.doc.status === "Signed") {
			frm.add_custom_button(__("Transmit to MH"), () => {
				frm.call("transmit_dte").then(() => frm.reload_doc());
			}, __("Actions"));
		}

		if (frm.doc.status === "Draft" && frm.doc.sales_invoice) {
			frm.add_custom_button(__("Build, Sign & Transmit"), () => {
				frappe.confirm(
					__("This will build, sign, and transmit the DTE to Ministerio de Hacienda. Continue?"),
					() => {
						frm.call("full_send").then(() => frm.reload_doc());
					}
				);
			}).addClass("btn-primary");
		}

		if (frm.doc.sello_recibido) {
			frm.dashboard.set_headline(
				__("Accepted - Sello: {0}", [frm.doc.sello_recibido.substring(0, 20) + "..."])
			);
		}
	},
});
