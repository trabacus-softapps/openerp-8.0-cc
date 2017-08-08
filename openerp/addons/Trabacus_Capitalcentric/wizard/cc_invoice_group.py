# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _

class account_invoice_group(osv.osv_memory):
    _name = "account.invoice.group"
    _description = "Invoice Merge"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
         Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view.
        """
        if context is None:
            context={}
        res = super(account_invoice_group, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context.get('active_model','') == 'account.invoice' and len(context['active_ids']) < 2:
            raise osv.except_osv(_('Warning!'),
            _('Please select multiple order to merge in the list view.'))
        return res
    def merge_invoices(self, cr, uid, ids, context=None):
        """
             To merge similar type of purchase orders.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: purchase order view

        """
        invoice_obj = self.pool.get('account.invoice')
        mod_obj =self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        result = mod_obj._get_id(cr, uid, 'account', 'view_account_invoice_filter')
        id = mod_obj.read(cr, uid, result, ['res_id'])
        
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_tree')
        res_id = res and res[1] or False,

        allinvoices = invoice_obj.do_merge(cr, uid, context.get('active_ids',[]), context)

        inv_type = ''
        for inv in invoice_obj.browse(cr,uid,allinvoices.keys()):
            inv_type = inv.type
                    
        xml_id = (inv_type == 'out_invoice') and 'action_invoice_tree1' or \
                 (inv_type == 'in_invoice') and 'action_invoice_tree2' or \
                 (inv_type == 'out_refund') and 'action_invoice_tree3' or \
                 (inv_type == 'in_refund') and 'action_invoice_tree4'
        result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
        id = result and result[1] or False
        result = act_obj.read(cr, uid, id, context=context)
        invoice_domain = eval(result['domain'])
        invoice_domain.append(('id', 'in', allinvoices.keys()))
        result['domain'] = invoice_domain
        return result
#         return {
#             'domain': "[('id','in', [" + ','.join(map(str, allinvoices.keys())) + "])]",
#             'name': _('Customer Invoices'),
#             'view_type': 'form',
#             'view_mode': 'tree,form',
#             'res_model': 'account.invoice',
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#             'search_view_id': id['res_id'],
#             'context': "{'type':'out_invoice'}",
#         }
        
#        return {
#                'name': _('Customer Invoices'),
#                'view_type': 'form',
#                'view_mode': 'form',
#                'view_id': [res_id],
#                'res_model': 'account.invoice',
#                'context': "{'type':'out_invoice'}",
#                'type': 'ir.actions.act_window',
#                'nodestroy': True,
#                'target': 'current',
#                'res_id': inv_ids and inv_ids[0] or False,
#        }
account_invoice_group()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
