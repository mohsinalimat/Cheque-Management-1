# -*- coding: utf-8 -*-
# Copyright (c) 2017, Direction and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cstr, nowdate, comma_and, getdate
from frappe import throw, msgprint, _
from frappe.model.document import Document
from erpnext.accounts.utils import get_account_currency
from erpnext.setup.utils import get_exchange_rate

class PayableCheques(Document):
	def autoname(self):
		name2 = frappe.db.sql("""select left(replace(replace(replace(sysdate(6), ' ',''),'-',''),':',''),14)""")[0][0]

		if name2:
			ndx = "-" + name2
		else:
			ndx = "-"

		self.name = self.cheque_no + ndx
		
	def validate(self):
		self.cheque_status = self.get_status()

	@frappe.whitelist()
	def on_trash(self):
		if self.payment_entry:			
			if frappe.db.get_value('Payment Entry', {'name':self.payment_entry,'docstatus':'1'}, 'name'):
				frappe.throw(_(" Cheque entry have associated payment entry {0} , please cancel payment entry").format(self.payment_entry))
		if self.journal_entry:
			if frappe.db.get_value('Journal Entry', {'name':self.payment_entry,'docstatus':'1'}, 'name'):
				frappe.throw(_(" Cheque entry have associated journal entry {0} , please cancel journal entry").format(self.journal_entry))
	
	@frappe.whitelist()
	def on_cancel(self):
		if self.payment_entry:			
			if frappe.db.get_value('Payment Entry', {'name':self.payment_entry,'docstatus':'1'}, 'name'):
				frappe.throw(_(" Cheque entry have associated payment entry {0} , please cancel payment entry").format(self.payment_entry))
		if self.journal_entry:
			if frappe.db.get_value('Journal Entry', {'name':self.payment_entry,'docstatus':'1'}, 'name'):
				frappe.throw(_(" Cheque entry have associated journal entry {0} , please cancel journal entry").format(self.journal_entry))

	@frappe.whitelist()
	def on_update(self):
		notes_acc = frappe.db.get_value("Company", self.company, "payable_notes_account")
		if not notes_acc:
			frappe.throw(_("Payable Notes Account not defined in the company setup page"))
		elif len(notes_acc) < 4:
				frappe.throw(_("Payable Notes Account not defined in the company setup page"))

		rec_acc = frappe.db.get_value("Company", self.company, "default_payable_account")
		if not rec_acc:
			frappe.throw(_("Default Payable Account not defined in the company setup page"))
		elif len(rec_acc) < 4:
			frappe.throw(_("Default Payable Account not defined in the company setup page"))

		if self.cheque_status == "Cheque Deducted":
			self.make_journal_entry(notes_acc, self.bank, self.amount, self.posting_date, self.party_type, self.party, cost_center=None, 
					save=True, submit=True)
		if self.cheque_status == "Cheque Cancelled":
			self.cancel_payment_entry()
			
	
	def on_submit(self):
		self.set_status()

	def set_status(self, cheque_status=None):
		'''Get and update cheque_status'''
		if not cheque_status:
			cheque_status = self.get_status()
		self.db_set("cheque_status", cheque_status)

	def get_status(self):
		'''Returns cheque_status based on whether it is draft, submitted, scrapped or depreciated'''
		cheque_status = self.cheque_status
		if self.docstatus == 0:
			cheque_status = "Draft"
		if self.docstatus == 1 and self.cheque_status == "Draft":
			cheque_status = "Cheque Issued"
		if self.docstatus == 2:
			cheque_status = "Cancelled"

		return cheque_status

	def cancel_payment_entry(self):
		if self.payment_entry:
			remarks = frappe.db.get_value('Payment Entry', self.payment_entry, 'remarks')
			remarks=remarks+'<br>'+nowdate()+' - '+self.cheque_status
			frappe.db.set_value('Payment Entry', self.payment_entry,'remarks', remarks)  
			frappe.get_doc("Payment Entry", self.payment_entry).cancel()
			message = """<a href="#Form/Payment Entry/%s" target="_blank">%s</a>""" % (self.payment_entry, self.payment_entry)
		if self.journal_entry:
			remark = frappe.db.get_value('Journal Entry', self.journal_entry, 'remark')
			remark=remark+'<br>'+nowdate()+' - '+self.cheque_status
			frappe.db.set_value('Journal Entry', self.journal_entry,'remark', remark)
			frappe.get_doc("Journal Entry", self.journal_entry).cancel()
			message = """<a href="#Form/Journal Entry/%s" target="_blank">%s</a>""" % (self.journal_entry, self.journal_entry)
				
		self.append("status_history", {
								"status": self.cheque_status,
								"transaction_date": nowdate(),
								"bank": self.bank
							})
		self.submit()		
		msgprint(_("Payment Entry {0} Cancelled").format(comma_and(message)))

			
	def make_journal_entry(self, account1, account2, amount, posting_date=None, party_type=None, party=None, cost_center=None, 
							save=True, submit=False):
		naming_series = frappe.db.get_value("Company", self.company, "payment_journal_entry_naming_series")
		cost_center = frappe.db.get_value("Company", self.company, "cost_center")						
		jv = frappe.new_doc("Journal Entry")
		jv.posting_date = posting_date or nowdate()
		jv.company = self.company
		jv.cheque_no = self.cheque_no
		jv.cheque_date = self.cheque_date
		if naming_series:
			jv.naming_series=naming_series
		voucher=self.payment_entry or self.journal_entry
		if self.journal_entry:
			postingdate=frappe.db.get_value('Journal Entry',self.journal_entry,'posting_date')
		else:	
			postingdate=frappe.db.get_value('Payment Entry',self.payment_entry,'posting_date')
		jv.user_remark=self.remarks+" PDC Realization aganist "+voucher+" Date: "+ str(postingdate)+". "
		jv.multi_currency = 0
		jv.set("accounts", [
			{
				"account": account1,
				"party_type": party_type if (self.cheque_status == "Cheque Deducted") else None,
				"party": party if self.cheque_status == "Cheque Deducted" else None,
				"cost_center": cost_center,
				"project": self.project,
				"debit_in_account_currency": amount if amount > 0 else 0,
				"credit_in_account_currency": abs(amount) if amount < 0 else 0
			}, {
				"account": account2,
				"party_type": party_type if self.cheque_status == "Cheque Issued" else None,
				"party": party if self.cheque_status == "Cheque Issued" else None,
				"cost_center": cost_center,
				"project": self.project,
				"credit_in_account_currency": amount if amount > 0 else 0,
				"debit_in_account_currency": abs(amount) if amount < 0 else 0
			}
		])
		if save or submit:
			jv.insert(ignore_permissions=True)

			if submit:
				jv.submit()

		self.append("status_history", {
								"status": self.cheque_status,
								"transaction_date": nowdate(),
								"debit_account": account1,
								"credit_account": account2,
								"journal_entry": jv.name
							})
		self.submit()
		message = """<a href="#Form/Journal Entry/%s" target="_blank">%s</a>""" % (jv.name, jv.name)
		msgprint(_("Journal Entry {0} created").format(comma_and(message)))
		#message = _("Journal Entry {0} created").format(comma_and(message))
		
		return message
			
