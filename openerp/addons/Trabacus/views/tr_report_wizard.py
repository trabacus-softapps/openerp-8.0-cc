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
from openerp.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta


TRAVEL_TYPES = [
        ('package', 'Holiday Package'),
        ('dom_flight', 'Domestic Flight'),
        ('int_flight', 'International Flight'),
        ('dom_hotel', 'Domestic Hotel'),
        ('int_hotel', 'International Hotel'),
        ('car','Transfers'),
        ('activity', 'Activities'),
        ('add_on', 'Add On'),
        ('visa','Visa'),
        ('insurance','Insurance'),
        ('railway','Railway'),
        ('cruise','Cruise'),
        ('direct','Miscellaneous'),
        
    ]

class tr_payment_receipt(osv.osv_memory):
    _name = 'tr.payment.receipt'
    _description = "Daily Payment Receipt Report"
    _columns={
              'start_dt'    : fields.date('Start Date'),
              'end_dt'      : fields.date('End Date'),
              'type'        : fields.selection([('payment','Payment'),('receipt','Receipt'),],'Type'),
              'partner_id'  : fields.many2one('res.partner', 'Partner', change_default=1),
              'group_id'    : fields.many2one('tr.group', 'Group'),
              'company_id'  : fields.many2one('res.company', 'Company'),
              }
    
    
    _defaults = {
                'type' : 'receipt'
                }
    
    def print_report(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = 'pdf'
            data['variables'] = {                                
                                'start_dt'      : case.start_dt or '',
                                'end_dt'        : case.end_dt or '',
                                'voucher_type'  : case.type or '',
                                'partner_id'    : case.partner_id and case.partner_id.id or 0,
                                }
            return {'type': 'ir.actions.report.xml',
                    'report_name':'payment_receipt',
                    'datas':data,
                    }
            
    def onchange_type(self, cr, uid, ids, type, group_id, company_id, context=None):
        res = {'domain': {'group_id': []}}
        if type == 'receipt':
            res['domain'] = {'group_id': [('customer','=','1'), ('company_id', '=', company_id)]}
        elif type == 'payment':    
            res['domain'] = {'group_id': [('supplier','=','1'), ('company_id', '=', company_id)]}
            
        return res
        
tr_payment_receipt ()      
      
class tr_sales_detail(osv.osv_memory):
    _name = 'tr.sales.detail'
    _description = "Sales Detail"
    _columns={
              'start_date'    : fields.date('Start Date', required=True),
              'end_date'      : fields.date('End Date', required=True),
              'company_id'    : fields.many2one('res.company','Company' , required=True),
              'type'          : fields.selection([('out_invoice','Invoice'),('out_refund','Refund'),('inv_ref','Invoice and Refund')],'Type', required=True),
              'travel_type'   : fields.selection(TRAVEL_TYPES,'Service Type'),
              'airline_id'    : fields.many2one('tr.airlines', 'Airline'),
              'product_id'  : fields.many2one('product.product', 'Product'),
              'consultant_id' : fields.many2one('res.users', 'Consultant'),
              'group_id'      : fields.many2one('tr.group','Group'),
              'customer_id'   : fields.many2one('res.partner', 'Customer'),
              'account_analytic_id' : fields.many2one('account.analytic.account', 'Analytic Account')
              }
    
#     def onchange_group_id(self, cr, uid, ids, group_id, company_id, context=None):
#         res = {'domain': {'group_id': []}}
#         if company_id:
#             res['domain'] = {'group_id': [('customer','=','1')]}
#         return res
       
    def print_report(self, cr, uid, ids, context=None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = 'pdf'
            data['variables'] = {                                
                                'start_date'  : case.start_date,
                                'end_date'    : case.end_date,
                                'type'        : case.type in ('out_invoice','out_refund') and case.type or '',
                                'travel_type' : case.travel_type or '',
                                'airline_id' : case.airline_id and case.airline_id.id or 0,
                                'product_id' : case.product_id and case.product_id.id or 0,
                                'customer_id' : case.customer_id and case.customer_id.id or 0,
                                'consultant_id': case.consultant_id and case.consultant_id.id or 0,
                                'group_id' : case.group_id and case.group_id.id or 0,
                                'company_id':case.company_id and case.company_id.id or 0,
                                'account_analytic_id' : case.account_analytic_id and case.account_analytic_id.id or 0,
                                }
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name':'sales_detail0',
                    'datas':data,
                    }
tr_sales_detail()

class tr_outstanding_report(osv.osv_memory):
    
    _name = 'tr.outstanding.report' 
    _description = "Outstanding Report -Summary & Detail Wizard"
    _columns = {  
                'rpt_type'      : fields.selection( [('summary','Summary Report'),('detail','Detailed Report')],'Type'), 
                'type'          : fields.selection( [('supplier','Travel Partner'),('customer','Customer')],'Type'),
                'category_id'   : fields.many2one('res.partner.category','Category'), 
                'tpartner_ids'  : fields.many2many('res.partner','outstanding_partner_rel','outstand_id','partner_id','Travel Partner'),
                'customer_ids'  : fields.many2many('res.partner','outstanding_customer_rel','outstand_id','customer_id','Customer'),
                'end_date'      : fields.date('As On'),
                'company_id'    : fields.many2one('res.company','Company'),
                'group_id'      : fields.many2one('tr.group','Group'),
                'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account'),
                }
    _defaults ={
                'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
                'rpt_type'      : 'summary',
                'type'          : 'customer',
                }
    
    def _get_mvlnResidualAmt(self, cr, uid, ids, enddate, acctype, context=None):
        """
           This function returns the residual amount on a receivable or payable account.move.line.
            as on the date
        """
        moveln_obj = self.pool.get('account.move.line')
        res = {
                'amount_residual': 0.0,
                'amount_residual_currency': 0.0,
            }
        
        if context is None:
            context = {}
        cur_obj = self.pool.get('res.currency')
                
        for move_line in moveln_obj.browse(cr, uid, ids, context=context):

            if not move_line.account_id.type in ('payable', 'receivable'):
                #this function does not suport to be used on move lines not related to payable or receivable accounts
                continue

            if move_line.currency_id:
                move_line_total = move_line.amount_currency
                sign = move_line.amount_currency < 0 and -1 or 1
            else:
                move_line_total = move_line.debit - move_line.credit
                sign = (move_line.debit - move_line.credit) < 0 and -1 or 1
            line_total_in_company_currency =  move_line.debit - move_line.credit
            context_unreconciled = context.copy()
            
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #         Reconciled Records
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if move_line.reconcile_id: 
                reconids = moveln_obj.search(cr, uid, [('reconcile_id','=',move_line.reconcile_id.id), ('id','!=', move_line.id), ('date','<=',enddate)])
                for payment_line in moveln_obj.browse(cr, uid, reconids):
                    
                    if payment_line.currency_id and move_line.currency_id and payment_line.currency_id.id == move_line.currency_id.id:
                            move_line_total += payment_line.amount_currency
                    else:
                        if move_line.currency_id:
                            context_unreconciled.update({'date': payment_line.date})
                            amount_in_foreign_currency = cur_obj.compute(cr, uid, move_line.company_id.currency_id.id, move_line.currency_id.id, (payment_line.debit - payment_line.credit), round=False, context=context_unreconciled)
                            move_line_total += amount_in_foreign_currency
                        else:
                            move_line_total += (payment_line.debit - payment_line.credit)
                    line_total_in_company_currency += (payment_line.debit - payment_line.credit)
                
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #         Partial Reconciled Records
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
            if move_line.reconcile_partial_id:
                reconids = moveln_obj.search(cr, uid, [('reconcile_partial_id','=',move_line.reconcile_partial_id.id), ('id','!=', move_line.id), ('date','<=',enddate)])
                for payment_line in moveln_obj.browse(cr, uid, reconids):
                    
                    if payment_line.id == move_line.id:
                        continue
                    if payment_line.currency_id and move_line.currency_id and payment_line.currency_id.id == move_line.currency_id.id:
                            move_line_total += payment_line.amount_currency
                    else:
                        if move_line.currency_id:
                            context_unreconciled.update({'date': payment_line.date})
                            amount_in_foreign_currency = cur_obj.compute(cr, uid, move_line.company_id.currency_id.id, move_line.currency_id.id, (payment_line.debit - payment_line.credit), round=False, context=context_unreconciled)
                            move_line_total += amount_in_foreign_currency
                        else:
                            move_line_total += (payment_line.debit - payment_line.credit)
                    line_total_in_company_currency += (payment_line.debit - payment_line.credit)

            result = move_line_total
            res['amount_residual_currency'] =  sign * (move_line.currency_id and self.pool.get('res.currency').round(cr, uid, move_line.currency_id, result) or result)
            res['amount_residual'] = sign * line_total_in_company_currency
        return res
    
    def report_outstandinglines(self, cr, uid, ids, context=None): 
        res = {}    
        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        usr_obj = self.pool.get("res.users")
        voucher_pool = self.pool.get('account.voucher')
        partnerids = []
        
        for case in self.browse(cr, uid, ids): 
            
            if case.customer_ids: 
                partnerids = [x.id for x in case.customer_ids]
                
            if case.tpartner_ids:        
                partnerids = [x.id for x in case.tpartner_ids]
                
            if not partnerids:
                if case.type == 'customer':
                    if case.group_id:
                       partnerids = partner_pool.search(cr, uid, [('customer','=',True), ('group_id','=',case.group_id.id)]) #To Do :check the search domain
                    else:    
                       partnerids = partner_pool.search(cr, uid, [('customer','=',True)])
                elif case.type == 'supplier':    
                    if case.group_id:
                       partnerids = partner_pool.search(cr, uid, [('supplier','=',True), ('group_id','=',case.group_id.id)]) #To Do :check the search domain
                    else:
                        partnerids = partner_pool.search(cr, uid, [('supplier','=',True)])
            
            for partn in partner_pool.browse(cr, uid, partnerids):
                
                
                jourid = journal_pool.search(cr, uid, [('type', '=', 'cash')], limit = 1)
#                To Do : Check The Parameters Passed In Onchange Function
                vals = voucher_pool.onchange_journal(cr, uid, ids, jourid and jourid[0], [], False, partn.id,datetime.today().strftime('%Y-%m-%d'), 0.00, False,case.company_id and case.company_id.id or False , context)
                vals = vals.get('value') 
                defcurrency = (currency_pool.search(cr, uid, [('name','=','INR')], limit = 1))
                currency_id = vals.get('currency_id', defcurrency and defcurrency[0])
                defcurrency = usr_obj.browse(cr, uid, uid).company_id.currency_id.id or False
                currency_id = vals.get('currency_id', defcurrency)
                
                journal = journal_pool.browse(cr, uid, jourid and jourid[0], context=context)
         
                if case.type == 'supplier':
                    acctype = 'payment'
                    account_type = 'payable' 
                else:
                    acctype = 'receipt' 
                    account_type = 'receivable'

                company_currency = journal.company_id.currency_id.id 

                cr.execute("""
                                 select id from account_move_line ml
                                 where ml.partner_id = """ + str(partn.id) + """ and ml.reconcile_id is null
                                 and ml.state = 'valid' 
                                 and ml.account_id in (select id from account_account where type = '""" + str(account_type) + """')
                                 and case when """ + str(case.account_analytic_id and case.account_analytic_id.id or 0) + """>0 
                                    then ml.analytic_account_id = """ + str(case.account_analytic_id and case.account_analytic_id.id or 0) + """ else True end                                       
                                 and ml.date <= '""" + str(case.end_date) + """'
                                 union all
                                        select id from account_move_line ml 
                                        where ml.partner_id = """ + str(partn.id) + """
                                        and ml.state = 'valid' 
                                        and ml.account_id in (select id from account_account where type = '""" + str(account_type) + """')
                                        and case when """ + str(case.account_analytic_id and case.account_analytic_id.id or 0) + """>0 
                                            then ml.analytic_account_id = """ + str(case.account_analytic_id and case.account_analytic_id.id or 0) + """ else True end                                       
                                        and ml.date <= '""" + str(case.end_date) + """'
                                        and ml.reconcile_id in (   select reconcile_id from account_move_line ml 
                                                                   where ml.partner_id = """ + str(partn.id) + """ and ml.reconcile_id is not null
                                                                   and ml.state = 'valid'
                                                                   and ml.account_id in (select id from account_account where type = '""" + str(account_type) + """')
                                                                   and case when """ + str(case.account_analytic_id and case.account_analytic_id.id or 0) + """>0 
                                                                       then ml.analytic_account_id = """ + str(case.account_analytic_id and case.account_analytic_id.id or 0) + """ else True end
                                                                   and ml.date > '""" + str(case.end_date) + """')
                        """)
                ln = cr.fetchall()
                lnids = []
                for l in ln:
                    lnids.append(l[0])

                lnids.sort()
                
                moves = move_line_pool.browse(cr, uid, lnids, context=context) 
                
                company_currency = journal.company_id.currency_id.id
                                                   
                for line in moves:
                    tot_credit = tot_debit = amount_reconciled = 0.00
                    
                    # Since all those required records are fetched in Query it self: 
#                                          
                    if line.credit and (line.reconcile_partial_id) and acctype == 'receipt':
                        continue
                    if line.debit and (line.reconcile_partial_id) and acctype == 'payment':
                        continue
                     
                    original_amount = line.credit or line.debit or 0.0
                    
                    residual = line.amount_residual_currency
                    if line.reconcile_id or line.reconcile_partial_id:
                        getamt = self._get_mvlnResidualAmt(cr, uid, [line.id], case.end_date, acctype, context)
                        residual = getamt['amount_residual_currency']
                        
                    amount_unreconciled = currency_pool.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, abs(residual), context={})
                                                            
                    original_amount = currency_pool.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, line.currency_id and abs(line.amount_currency) or original_amount, context={})
                    if original_amount != amount_unreconciled:
                       amount_reconciled = original_amount - amount_unreconciled
                        
                    amount = currency_pool.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, line.currency_id and abs(line.amount_currency) or original_amount, context={})
                    
                    amttyp = line.credit and 'dr' or 'cr'
                    if amttyp == 'cr':
                        tot_debit = amount
                    else:
                        tot_credit = amount
                        
                    narration = line.name.replace("'",'\'')
                     
                    cr.execute(""" insert into table_outstanding(id, userid, moveln_id, partner_id, inv_date, amt_original, amt_reconciled, amttype, tot_credit, tot_debit, narration) 
                                    (select  """ + str(line.id) + """ as id
                                            , """ + str(uid) + """ as userid
                                            , """ + str(line.id) + """ as moveln_id
                                            , """ + str(partn.id) + """ as partner_id
                                            , '""" + str(line.date) + """' as inv_date
                                            , """ + str(original_amount) + """ as amt_original
                                            , """ + str(amount_reconciled) +""" as amt_reconciled
                                            , '""" + str(amttyp) + """' as amttype
                                            , """ + str(tot_credit) + """ as tot_credit
                                            , """ + str(tot_debit) + """ as tot_debit
                                            , '""" + str(narration) + """' as narration
                                    )
                                    """)
        return True

    def print_report(self, cr, uid, ids, context=None):  
        
        for case in self.browse(cr,uid,ids): 
            
            cr.execute("Delete from table_outstanding where userid = %d"%(uid))
            self.report_outstandinglines(cr, uid, ids, context=None)
            res = []
            data = {}
            data['ids'] = ids
            data['model'] = 'tr.outstanding.report'
            
            data['output_type'] = 'pdf'
            data['variables'] = {                                
                'rpt_type'      : case.rpt_type and case.rpt_type ,
                'type'          : case.type and case.type or '',
                'category_id'   : case.group_id and case.group_id.name or 'For All Groups',
                'tpartner_ids'  : [x.id for x in case.tpartner_ids] or [],
                'customer_ids'  : [x.id for x in case.customer_ids] or [],
                'end_date'      : case.end_date and case.end_date or '',
                'company_id'    : case.company_id and case.company_id.id or False,
                'uid'           : uid and uid or False
                                }
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name' :'outstanding_report ',
                    'datas':data,
                    }
            
    def onchange_type(self, cr, uid, ids, type, group_id, context=None):
        res = {'domain': {'group_id': []}}
        if type == 'customer':
            res['domain'] = {'group_id': [('customer','=','1')]}
        elif type == 'supplier':    
            res['domain'] = {'group_id': [('supplier','=','1')]}
            
        return res

class tr_rpt_bspreconcilation(osv.osv_memory):
    _name = 'tr.rpt.bspreconcilation'
    _description = "BSP Reconcilation Report"
    _columns={
              'start_dt'    : fields.date('Start Date'),
              'end_dt'      : fields.date('End Date'),
              'bsp_type'    : fields.selection([('all','ALL'),('discrepancy','DISCREPANCY'),('correct','RECONCILED')],'Type'),
              'airline_id'  : fields.many2one('tr.airlines', 'Airline'),
              }
    _defaults = {
                'bsp_type' : 'all'
                }
    
    def print_report(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = 'pdf'
            data['variables'] = {                                
                                'start_date'      : case.start_dt or '',
                                'end_date'        : case.end_dt or '',
                                'bsp_type'        : case.bsp_type or '',
                                'airline_id'      : case.airline_id and case.airline_id.id or 0,
                                }
            return {'type': 'ir.actions.report.xml',
                    'report_name':'bsp_report6',
                    'datas':data,
                    }
tr_rpt_bspreconcilation () 

class tr_wiz_ticket_stock(osv.osv_memory):
    _name = 'tr.wiz.ticket.stock'
    _description = "Ticket Stock"
    _columns={
              'start_date'    : fields.date('Start Date', required=True),
              'end_date'      : fields.date('End Date', required=True),
              'company_id'    : fields.many2one('res.company','Company'),
              'tpartner_id'   : fields.many2one('res.partner', 'Travel Partner')
              }
    
    def print_report(self, cr, uid, ids, context=None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = 'pdf'
            data['variables'] = {                                
                                'start_date'  : case.start_date,
                                'end_date'    : case.end_date,
                                'company_id':case.company_id and case.company_id.id or 0,
                                'tpartner_id':case.tpartner_id and case.tpartner_id.id or 0
                                }
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name':'ticket_stock',
                    'datas':data,
                    }
tr_wiz_ticket_stock()  

class tr_wiz_client_statement(osv.osv_memory):
    _name = 'tr.wiz.client.statement'
    _description = "Client Statement"
    _columns={
              'start_date'    : fields.date('Start Date', required=True),
              'end_date'      : fields.date('End Date', required=True),
              'company_id'    : fields.many2one('res.company','Company' , required=True),
              'customer_id'   : fields.many2one('res.partner', 'Customer', required=True),
              'account_analytic_id' : fields.many2one('account.analytic.account', 'Analytic Account')
              }
    
    def print_report(self, cr, uid, ids, context=None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = 'pdf'
            data['variables'] = {                                
                                'start_date'  : case.start_date,
                                'end_date'    : case.end_date,
                                'company_id':case.company_id and case.company_id.id or 0,
                                'customer_id':case.customer_id and case.customer_id.id or 0,
                                'account_analytic_id':case.account_analytic_id and case.account_analytic_id.id or 0
                                }
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name':'client_statement',
                    'datas':data,
                    }
tr_wiz_client_statement()  

class tr_transmittal_form(osv.osv_memory):
    _name = 'tr.transmittal.form'
    _description = "Transmittal Form"
    _columns={
              'start_date'    : fields.date('Start Date', required=True),
              'end_date'      : fields.date('End Date', required=True),
              'company_id'    : fields.many2one('res.company','Company'),
              'tpartner_id'   : fields.many2one('res.partner', 'Travel Partner')
              }
    
    def print_report(self, cr, uid, ids, context=None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = 'pdf'
            data['variables'] = {                                
                                'start_date'  : case.start_date,
                                'end_date'    : case.end_date,
                                'company_id':case.company_id and case.company_id.id or 0,
                                'tpartner_id':case.tpartner_id and case.tpartner_id.id or 0
                                }
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name':'transmittal_form',
                    'datas':data,
                    }
tr_transmittal_form()         
      

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
