// Copyright (c) 2017, Direction and contributors
// For license information, please see license.txt
frappe.listview_settings['Payable Cheques Status'] = {
	add_fields: ["cheque_status", "transaction_date", "bank", "journal_entry", "payment_entry"],
	get_indicator: function(doc) {
		if(cheque_status=="Cheque Issued") {
			return [__("Cheque Issued"), "lightblue", "cheque_status,=,'Cheque Issued'"];
		} 
		if(cheque_status=="Cheque Cancelled") {
			return [__("Cheque Cancelled"), "black", "cheque_status,=,'Cheque Cancelled'"];
		} 
		if(cheque_status=="Cheque Deducted") {
			return [__("Cheque Deducted"), "green", "cheque_status,=,'Cheque Deducted'"];
		} 
		
 	}
};

frappe.listview_settings['Payable Cheques'] = {

	onload(listview) {
		 console.log("list js loaded");
		 listview.page.actions.find('[data-label="Cheque Issued"]').click(function()
		 {
			
			const docnames1 = listview.get_checked_items(true).map(docname => docname.toString());
			//console.log(docnames1);
			frappe.call({
				method: "cheque_management.api.update_cheque_status_pay",
				freeze: true,
				args: {
					docnames:docnames1,
					status:"Cheque Issued"
				},
				callback: function(r) {
					console.log(r.message);
				}
			});
			//setTimeout(function(){  console.log(" ajax waite");  },3000);
			
		 });

		 listview.page.actions.find('[data-label="Cheque Deducted"]').click(function()
		 {
			
			const docnames2 = listview.get_checked_items(true).map(docname => docname.toString());
			//console.log(docnames2);
			frappe.call({
				method: "cheque_management.api.update_cheque_status_pay",
				freeze: true,
				args: {
					docnames:docnames2,
					status:"Cheque Deducted"
				},
				callback: function(r) {
					console.log(r.message);
				}
			});
			//setTimeout(function(){  console.log(" ajax waite");  },3000);
			
		 });
		 listview.page.actions.find('[data-label="Cheque Cancelled"]').click(function()
		 {
			
			const docnames3 = listview.get_checked_items(true).map(docname => docname.toString());
			frappe.call({
				method: "cheque_management.api.update_cheque_status_pay",
				freeze: true,
				args: {
					docnames:docnames3,
					status:"Cheque Cancelled"
				},
				callback: function(r) {
					console.log(r.message);
				}
			});
			//setTimeout(function(){  console.log(" ajax waite");  },3000);
			
		 });

		 
   }
 }
