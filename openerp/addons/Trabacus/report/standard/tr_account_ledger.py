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
from openerp.osv import fields, osv
import time 
import re
from openerp.report import report_sxw
from openerp.addons.account.report import common_report_header as crh
from openerp.tools.translate import _
from lxml import etree

class account_report_general_ledger(osv.osv_memory):
    _inherit='account.report.general.ledger'
    _columns={'partner_id':fields.many2one('res.partner','Partner'),
              'account_id':fields.many2one('account.account','Account'),
              'client_heading' : fields.boolean('Client Heading'),
              'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account'),
              }
    _defaults={
               'client_heading' : False,
               'landscape' : False,
               'filter':'filter_date',}

# Overriden 
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['landscape',  'initial_balance', 'amount_currency', 'sortby'])[0])
#         data['form'].update(self.read(cr, uid, ids, ['account_id'], context=context)[0])
        for case in self.browse(cr,uid,ids):
            data['form'].update({'chart_account_id':case.account_id and case.account_id.id or 1})
        data['form'].update(self.read(cr, uid, ids, ['partner_id'], context=context)[0])
        data['form'].update(self.read(cr, uid, ids, ['account_analytic_id'], context=context)[0])
        if 'client_heading' in context: 
            data['form'].update({'client_heading':True})
        else:
            data['form'].update({'client_heading':False})     
        if not data['form']['fiscalyear_id']:# GTK client problem onchange does not consider in save record
            data['form'].update({'initial_balance': False})
        if 'client_heading' in context:
            if data['form']['landscape']:
                return { 'type': 'ir.actions.report.xml', 'report_name': 'account.general.ledger_landscape','name' : 'Client Satement', 'datas': data}
            return { 'type': 'ir.actions.report.xml', 'report_name': 'account.general.ledger','name' : 'Client Satement', 'datas': data}
        if data['form']['landscape']:
            return { 'type': 'ir.actions.report.xml', 'report_name': 'account.general.ledger_landscape', 'datas': data}
        return { 'type': 'ir.actions.report.xml', 'report_name': 'account.general.ledger', 'datas': data}

    def onchange_account(self,cr,uid,ids,account_id):
        result = {}  
        acc_obj = self.pool.get('account.account')
        prop_obj = self.pool.get('ir.property')
        
        if account_id:
            acc_id = 'account.account'+','+str(account_id)
            if acc_id:
                ir_ids = prop_obj.search(cr,uid,[('value_reference','=',acc_id)], limit=1)
                ir_id = ir_ids and ir_ids[0] or False 
                if not ir_id:
                    return False#return {'value':{'partner_id' : False}}
                
                prop = prop_obj.browse(cr,uid,ir_id)
                res = prop.res_id
                if res and res[0:res.find(',')+1] == 'res.partner,' or False:
                    p_id  = int(res[res.find(',')+1:].strip())
                    result = {
                           'partner_id' : p_id and p_id or False
                          }
        return {'value':result}
    
    def onchange_partner_id(self, cr, uid, ids,  partner_id):
        result ={}        
        opt = [('uid', str(uid))]
        acc_id = False
        if partner_id:

            opt.insert(0, ('id', partner_id))
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if p.customer:
                acc_id = p.property_account_receivable and p.property_account_receivable.id or False
            elif p.supplier:
                acc_id = p.property_account_payable and p.property_account_payable.id or False
        result = {'value': {'account_id': acc_id,}}

        return result

     
account_report_general_ledger()

class account_print_journal(osv.osv_memory):
    _inherit = 'account.print.journal'
    _description = 'Account Print Journal'

    _columns = {
        'journal_type': fields.selection([('sale_pur', 'Sales/Purchase'),('cash', 'Cash'),('bank', 'Bank'),
                                  ('receipt', 'Receipt'),('payment', 'Payment'),('all_other', 'All/Others'),],'Type'),
           'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account'),
                }
    
    _defaults = {
                 'filter'  : 'filter_date'
                 }
    def onchange_journaltype(self, cr, uid, ids, journal_type, context=None):
        journal_obj = self.pool.get('account.journal')
        res = {}
        jids = []
        if journal_type == 'sale_pur':
            jids = journal_obj.search(cr,uid,[('type','in',('sale','sale_refund'))])
        elif journal_type == 'cash':
            jids = journal_obj.search(cr,uid,[('type', '=', 'cash')])
        elif journal_type == 'bank':
            jids = journal_obj.search(cr,uid,[('type', '=', 'bank')])
        elif journal_type == 'receipt':
            jids = journal_obj.search(cr,uid,[('type', 'in', ('cash','bank'))])
        elif journal_type == 'payment':
            jids = journal_obj.search(cr,uid,[('type', 'in', ('cash','bank'))])
        elif journal_type == 'all_other':
            jids = journal_obj.search(cr,uid,[])
        res['journal_ids'] =  [(6,0,jids)]
        return {'value' : res}

    # Inherited
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        '''
        used to set the domain on 'journal_ids' field: we exclude or only propose the journals of type 
        sale/purchase (+refund) accordingly to the presence of the key 'sale_purchase_only' in the context.
        '''
        if context is None: 
            context = {}
        res = super(account_print_journal, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])

        if context.get('sale_purchase_only'):
            domain =""
        else:
            domain =""
        nodes = doc.xpath("//field[@name='journal_ids']")
        for node in nodes:
            node.set('domain', domain)
        res['arch'] = etree.tostring(doc)
        return res
 
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['journal_type'], context=context)[0])
        data['form'].update(self.read(cr, uid, ids, ['account_analytic_id'], context=context)[0])
#         for case in self.browse(cr,uid,ids):
#             data['form'].update({'chart_account_id':case.account_id and case.account_id.id or 1})
        if context.get('sale_purchase_only'):
            report_name = 'account.journal.period.print.sale.purchase'
        else:
            report_name = 'account.journal.period.print'
        return {'type': 'ir.actions.report.xml', 'report_name': report_name, 'datas': data}

account_print_journal()




















