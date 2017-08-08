# -*- coding: utf-8 -*-
#############################################################################
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
import openerp.addons.decimal_precision as dp
import openerp.exceptions
import time
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta
import tr_config
import os
import shutil
import logging
from openerp import workflow
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

traveltype_map = {'package': 'HP', 'dom_flight': 'DF',
                   'int_flight': 'IF', 'dom_hotel': 'DT', 'int_hotel': 'IT',
                   'car' : 'TR', 'visa': 'VI', 'insurance': 'NI',
                   'activity': 'AT', 'add_on': 'AO', 'railway': 'DR', 'cruise': 'CS',
                   'direct': 'MISC'
                   }

def get_dp_precision(cr, uid, application):
    cr.execute('select digits from decimal_precision where name=%s', (application,))
    res = cr.fetchone()
    return res[0] if res else 2
            
            
class tr_package_destination(osv.osv):
    _name = 'tr.package.destination' 
    _columns = {
                'invoice_id'    : fields.many2one('account.invoice', 'Invoice', ondelete='cascade'),
                'destination_id': fields.many2one('tr.destination', 'Destination', ondelete='restrict', required=True),
                'no_nts' : fields.integer('Nights') 
                }
    
    
class account_invoice(osv.osv): 
    _inherit = 'account.invoice'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        #override of fields_view_get in order to change the label of the process button and the separator accordingly to the shipping type
        if context is None:
            context={}
        res = super(account_invoice, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('type', False)
        if type:
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//button[@name='invoice_pay_customer']"):
                if type in ('out_invoice','in_refund') :
                    node.set('string', _('Register Receipt'))
                elif type in ('in_invoice', 'out_refund'):
                    node.set('string', _('Register Payment'))
            res['arch'] = etree.tostring(doc)
        return res
    
    def fields_get(self, cr, uid, fields=None, context=None, write_access=True):
        """
            For Sales Group: 
                Locks Sale - Invoice from editing, when it is in "draft" state... 
        """
        
        # TODO:
        # delete it.. if not used....
        # ir.needaction_mixin class // get_needaction_pending
        # to set user action
        fields = super(account_invoice, self).fields_get(cr, uid, fields, context, write_access)
        
        cr.execute("select true \
                    from res_groups_users_rel gu \
                    inner join res_groups g on g.id = gu.gid \
                    where g.name = 'Sales' and uid = " + str(uid))
        is_sales = cr.fetchone()
        
        if is_sales and is_sales[0] == True:
            states = {'draft': [('readonly', True)]}
            
            change_states = {
                             'partner_id': states,
                             'name': states,
                             'origin': states,
                             'date_invoice': states,
                             'account_id': states
                             }
            
            print "---------------------------"
            for field in fields:
                if change_states.has_key(field):
                    for key, value in change_states[field].items():
                        fields[field].setdefault('states', {})
                        fields[field]['states'][key] = value
        return fields 
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        
        for case in self.browse(cr, uid, ids, context=context):
            res[case.id] = {'amount_untaxed': 0.0, 'amount_tax': 0.0, 'amount_total': 0.0, 'amount_profit':0.0}
            untax = tax = poamt = 0.00
            
#             if case.travel_type in ('dom_flight', 'int_flight'):
#                 for line in case.flight_ids:
#                     untax += line.a_total
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#                     
#             elif case.travel_type in ('dom_hotel', 'int_hotel'):
#                 for line in case.hotel_ids:
#                     untax += line.subtotal
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#                     
#             elif case.travel_type == 'car':
#                 for line in case.car_ids:
#                     untax += line.subtotal
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#                     
#             elif case.travel_type == 'visa':
#                 for line in case.visa_ids:
#                     untax += line.subtotal
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#                     
#             elif case.travel_type == 'insurance':
#                 for line in case.insurance_ids:
#                     untax += line.subtotal
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#         
#             elif case.travel_type == 'railway':
#                 for line in case.railway_ids:
#                     untax += line.subtotal
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#                     
#             elif case.travel_type == 'cruise':
#                 for line in case.cruise_ids:
#                     untax += line.a_subtotal + line.c_subtotal + line.i_subtotal + line.e_subtotal 
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#                     
#             elif case.travel_type == 'activity':
#                 for line in case.activity_ids:
#                     untax += line.subtotal
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#                     
#             elif case.travel_type == 'add_on':
#                 for line in case.addon_ids:
#                     untax += line.subtotal
#                     tax += line.taxes
#                     poamt += line.po_subtotal
#         
#             else:  # Standard
#                 for line in case.invoice_line:
#                     untax += line.price_subtotal
#                     poamt += line.purchase_amt
#                 for line in case.tax_line:
#                     tax += line.amount
                    
            if case.travel_type != 'direct':
                for line in case.invoice_line:
                    untax += line.price_subtotal
                    poamt += line.purchase_amt
                    tax += line.taxes
            else:
                for line in case.invoice_line:
                    untax += line.price_subtotal
                    poamt += line.purchase_amt
                for line in case.tax_line:
                    tax += line.amount
                    
            res[case.id]['amount_untaxed'] += untax
            res[case.id]['amount_tax'] += tax
            res[case.id]['amount_total'] = untax + tax
            res[case.id]['amount_profit'] = case.type in ('out_invoice','out_refund') and (untax - poamt) or 0
            
        return res
    
    # Overridden:
    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        """Function of the field residua. It computes the residual amount (balance) for each invoice"""
        if context is None:
            context = {}
        ctx = context.copy()
        result = {}
        currency_obj = self.pool.get('res.currency')
        for invoice in self.browse(cr, uid, ids, context=context):
            nb_inv_in_partial_rec = max_invoice_id = 0
            result[invoice.id] = 0.0
            if invoice.move_id:
                for aml in invoice.move_id.line_id:
                    if aml.account_id.type in ('receivable','payable') and invoice.partner_id.id == aml.partner_id.id:
                        if aml.currency_id and aml.currency_id.id == invoice.currency_id.id:
                            result[invoice.id] += aml.amount_residual_currency
                        else:
                            ctx['date'] = aml.date
                            result[invoice.id] += currency_obj.compute(cr, uid, aml.company_id.currency_id.id, invoice.currency_id.id, aml.amount_residual, context=ctx)

                        if aml.reconcile_partial_id.line_partial_ids:
                            #we check if the invoice is partially reconciled and if there are other invoices
                            #involved in this partial reconciliation (and we sum these invoices)
                            for line in aml.reconcile_partial_id.line_partial_ids:
                                if line.invoice:
                                    nb_inv_in_partial_rec += 1
                                    #store the max invoice id as for this invoice we will make a balance instead of a simple division
                                    max_invoice_id = max(max_invoice_id, line.invoice.id)
            if nb_inv_in_partial_rec:
                #if there are several invoices in a partial reconciliation, we split the residual by the number
                #of invoice to have a sum of residual amounts that matches the partner balance
                new_value = currency_obj.round(cr, uid, invoice.currency_id, result[invoice.id] / nb_inv_in_partial_rec)
                if invoice.id == max_invoice_id:
                    #if it's the last the invoice of the bunch of invoices partially reconciled together, we make a
                    #balance to avoid rounding errors
                    result[invoice.id] = result[invoice.id] - ((nb_inv_in_partial_rec - 1) * new_value)
                else:
                    result[invoice.id] = new_value

            #prevent the residual amount on the invoice to be less than 0
            result[invoice.id] = max(result[invoice.id], 0.0)            
        return result
    
    # Standard:
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    # Standard:
    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    # Standard:
    def _get_invoice_from_line(self, cr, uid, ids, context=None):
        move = {}
        for line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    move[line2.move_id.id] = True
            if line.reconcile_id:
                for line2 in line.reconcile_id.line_id:
                    move[line2.move_id.id] = True
        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids

    # Standard:
    def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
        move = {}
        for r in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True

        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids

    # To Get The seervice wise Line Info Put in Invocie - Tree View
    # To Do : For All Services
    def _get_lines_info(self, cr, uid, ids, name, args, context=None):
        res = {}   
        for case in self.browse(cr, uid, ids):
            loop = 1
            sctrdt = pax = tik = pnr =''
            res[case.id] = {'ln_paxname':'', 'ln_ticketno':'','ln_pnr' : '','ln_sector':'' }
            if case.travel_type in ('dom_flight,int_flight'):
                first_ft = case.flight_ids and case.flight_ids[0]
                if first_ft:
                    if first_ft.pax_name:
                        pax = first_ft.pax_name or ''
                    if first_ft.ticket_no:
                        tik = first_ft.ticket_no or ''
                    if first_ft.airline_pnr:
                        pnr = first_ft.airline_pnr or ''
                    for sctr in first_ft.flight_lines:
                        if loop==1: 
                            if sctr.from_id.code: sctrdt += sctr.from_id.code or ''
                        if sctr.to_id.code :sctrdt +='-' + sctr.to_id.code or ''
                        loop +=1
            res[case.id]['ln_sector'] = sctrdt
            res[case.id]['ln_pnr'] =  pnr          
            res[case.id]['ln_ticketno'] = tik
            res[case.id]['ln_paxname'] = pax                        
        return res
    
    _columns = {
                # Overriden:
                'state': fields.selection([
                                ('quotation', 'New'),
                                ('order_cancel', 'Order Cancelled'),
                                ('draft', 'Confirmed'),
                                ('proforma', 'Pro-forma'),
                                ('proforma2', 'Pro-forma'),
                                ('open', 'Invoiced'),
                                ('paid', 'Paid'),
                                ('cancel', 'Cancelled'),
                                ], 'Status', select=True, readonly=True, track_visibility='onchange',
                                help=' * The \'New\' status is used while capturing a new Quotation. \
                                \n* The \'Confirmed\' status is used when a user confirms a Quotation. \
                                \n* The \'Invoiced\' status is used when invoice is confirmed,a invoice number is generated.Its in Invoiced status till user does not pay invoice. \
                                \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
                                \n* The \'Cancelled\' status is used when user cancels invoice.'),
                
                'name': fields.char('Description', size=500, select=True, readonly=True, states={'quotation':[('readonly', False)], 'draft':[('readonly', False)]}),
                'origin': fields.char('Source Document', size=64, readonly=True, states={'quotation':[('readonly', False)], 'draft':[('readonly', False)]}),
                'date_invoice': fields.date('Invoice Date', readonly=True, states={'quotation':[('readonly', False)], 'draft':[('readonly', False)]}),
                
                'partner_id': fields.many2one('res.partner', 'Partner', change_default=True, required=False, track_visibility='always'
                                              , readonly=True, states={'quotation':[('readonly', False)], 'draft':[('readonly', False)]}),
                
                'account_id': fields.many2one('account.account', 'Account', required=False, readonly=True, states={'quotation':[('readonly', False)], 'draft':[('readonly', False)]}),
                'invoice_line': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=True, states={'quotation':[('readonly', False)], 'draft':[('readonly', False)]}),
                'tax_line': fields.one2many('account.invoice.tax', 'invoice_id', 'Tax Lines', readonly=True, states={'quotation':[('readonly', False)], 'draft':[('readonly', False)]}),
                'user_id': fields.many2one('res.users', 'Sales Person', readonly=True, track_visibility='onchange'),
                'currency_id': fields.many2one('res.currency', 'Currency', required=True, readonly=True, states={'quotation':[('readonly', False)], 'draft':[('readonly',False)]}, track_visibility='always'),
                
                'create_date': fields.datetime('Order Date'),
                
                'residual': fields.function(_amount_residual, digits_compute=dp.get_precision('Account'), string='Balance',
                            store={
                                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','move_id'], 50),
                                'account.invoice.tax': (_get_invoice_tax, None, 50),
                                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 50),
                                'account.move.line': (_get_invoice_from_line, None, 50),
                                'account.move.reconcile': (_get_invoice_from_reconcile, None, 50),
                            },
                            help="Remaining amount due."),
                
#                 'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always', store=True, multi='all'),
#                 'amount_tax'    : fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax', store=True, multi='all'),
#                 'amount_total'  : fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total', store=True, multi='all'),
#                 'amount_profit' : fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Profit', store=True, multi='all'),
#                 
                
                'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
                        store={
                            'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                            'account.invoice.tax': (_get_invoice_tax, None, 20),
                            'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                        },
                        multi='all'),
                'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
                        store={
                            'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                            'account.invoice.tax': (_get_invoice_tax, None, 20),
                            'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                        },
                        multi='all'),
                'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                        store={
                            'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                            'account.invoice.tax': (_get_invoice_tax, None, 20),
                            'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                        },
                        multi='all'),
                'amount_profit' : fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Profit',
                        store={
                            'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                            'account.invoice.tax': (_get_invoice_tax, None, 20),
                            'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                        }, multi='all'),

                # New
                'travel_type' : fields.selection(tr_config.TRAVEL_TYPES, 'Service Type'),
                'lead_id'     : fields.many2one('crm.lead', 'Lead No.', ondelete='set null', readonly=True, states={'quotation':[('readonly', False)]}),
                'project_code': fields.char('Project Code', size=100),
                'auth_ref'    : fields.char('Authorization Ref', size=100),
                'psr_date'    : fields.date('PSR Date'),
                'is_ticket'   : fields.boolean('Ticketing Completed'),
                'src_id'      : fields.many2one('account.invoice', 'Source (Invoice) Reference'),
                
                'insurance_ids' : fields.one2many('tr.invoice.insurance', 'invoice_id', 'Insurance'),
                'flight_ids'    : fields.one2many('tr.invoice.flight', 'invoice_id', 'Flight'),
                'visa_ids'      : fields.one2many('tr.invoice.visa', 'invoice_id', 'Visa'),
                'cruise_ids'    : fields.one2many('tr.invoice.cruise', 'invoice_id', 'Cruise'),
                'car_ids'       : fields.one2many('tr.invoice.car', 'invoice_id', 'Transfers'),
                'railway_ids'   : fields.one2many('tr.invoice.railway', 'invoice_id', 'Railway'),
                'hotel_ids'     : fields.one2many('tr.invoice.hotel', 'invoice_id', 'Hotel'),
                'activity_ids'  : fields.one2many('tr.invoice.activity', 'invoice_id', 'Activity'),
                'addon_ids'     : fields.one2many('tr.invoice.addon', 'invoice_id', 'Add-on'),
                
                'paxtype'  : fields.selection([('fit', 'FIT'), ('group', 'Group')], 'Passenger Type', readonly=True, states={'quotation':[('readonly', False)]}),
                'purpose'  : fields.selection([('leisure', 'Leisure'), ('business', 'Business')], 'Purpose', readonly=True, states={'quotation':[('readonly', False)]}),
                'consultant_id'  : fields.many2one('res.users', 'Consultant', select=True, track_visibility='onchange'),
                'edit_invoice'   : fields.boolean('Edit Invoice Window'),
                'terms_condition': fields.text('Terms & Condition'),
                
                'adult'  : fields.integer('Adult (S)'),
                'twin'   : fields.integer('Adult (D)'),
                'triple' : fields.integer('Adult (T)'),
                'extra'  : fields.integer('Extra'),
                'cwb'    : fields.integer('CWB'),
                'cnb'    : fields.integer('CNB'),
                'infant' : fields.integer('Infant'),
                
                'start_date' : fields.date('Start Date'),
                'pkdest_ids' : fields.one2many('tr.package.destination', 'invoice_id', 'Destination'),
                'option_id'  : fields.many2one('tr.invoice.option', 'Option Confirmed', ondelete='cascade'),
                
                'option_ids' : fields.one2many('tr.invoice.option', 'invoice_id', 'Options'),
                
                'pack_image' : fields.binary('Image'),  

                'ln_paxname'   : fields.function(_get_lines_info, string='Pax', type='char', multi='line'),
                'ln_ticketno'  : fields.function(_get_lines_info, string='Ticket',type='char', multi='line'),
                'ln_pnr'       : fields.function(_get_lines_info, string='PNR', type='char',  multi='line'),
                'ln_sector'    : fields.function(_get_lines_info, string='Sector',  type='char',  multi='line'),
                
                'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account'),
                }
    
    _order = "date_invoice desc"

    _defaults = {
                 'state': 'quotation',
                 'consultant_id' : lambda obj, cr, uid, context: uid
                 }
    # Overridden:
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        types = {
                'out_invoice': _('Invoice'),
                'in_invoice': _('Supplier Invoice'),
                'out_refund': _('Credit Note'),
                'in_refund': _('Debit Note'),
                }
        lead_obj = self.pool.get('crm.lead')
        reads = self.read(cr, uid, ids, ['type', 'number', 'name', 'lead_id'], context, load='_classic_read')
        res = []
        for record in reads:
            leadno = record['lead_id'] and record['lead_id'][1] or ''
            numtyp = (record['number'] or types[record['type']])
            name = '[%s] %s ' % (leadno, numtyp)
                
            res.append((record['id'], name))
        return res

    def onchange_invoicedate(self, cr, uid, ids, date_invoice, context=None):
       psr_obj = self.pool.get('tr.flight.psr')
       res = {}
       psrto = ''
       inv = self.browse(cr,uid,ids)[0]
       if date_invoice: 
           inv_day = datetime.strptime(date_invoice, '%Y-%m-%d').strftime('%d')
           cr.execute("SELECT id FROM tr_flight_psr fp  where "+ inv_day +"::int between fp.from::int and fp.to::int limit 1")
           psr_ids = cr.fetchall()
           if psr_ids: 
               psrto = psr_obj.read(cr, 1, [str(int(psr_ids[0][0]))], ['to'])[0]['to']
               # If End Of Month: fetch the last day of the month
               if psrto == '32': 
                   cr.execute("select EXTRACT(DAY FROM (SELECT (date_trunc('MONTH','" + date_invoice + "':: date) + INTERVAL '1 MONTH - 1 day')::date))")
                   psrto = str(int(cr.fetchall()[0][0])) # [0][0] becoz [(31.0,)]
           if psrto : 
               psr_date = psrto + '-' + datetime.strptime(date_invoice, '%Y-%m-%d').strftime('%m') + '-' + datetime.strptime(date_invoice, '%Y-%m-%d').strftime('%Y')
               res = {'psr_date':datetime.strptime(psr_date, "%d-%m-%Y").strftime("%Y-%m-%d")}
           if not psrto : 
               res = {'psr_date': None}
       return {'value': res}

    def onchange_leadid(self, cr, uid, ids, lead_id, context=None):
        res = {}
        lead_obj = self.pool.get('crm.lead')  
        if lead_id :
           for record in lead_obj.read(cr, uid, [lead_id], ['partner_id','user_id'], context):
                   prtnrid = record['partner_id'] and record['partner_id'][0] or False
                   user_id = record['user_id'] and record['user_id'][0] or False
                   res = {'partner_id' : prtnrid and prtnrid or False
                          ,'user_id' : user_id and user_id or False}     
        return {'value': res}

    # Inherited:
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        context = {}
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id,date_invoice, payment_term, partner_bank_id, company_id)
        context.update({'partner_id' : partner_id, 'calledfrm' : 'func'})
        self.button_update( cr, uid, ids, context)   
        return result
    
    # Overridden:
    def _refund_cleanup_lines(self, cr, uid, lines, context=None):
        """
        Overridden:
            Convert records to dict of values suitable for one2many line creation
            :param list(browse_record) lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
            
            Note: Cleanup for Invoice Lines & Service lines
        """
        clean_lines = []
        for line in lines:
            clean_line = {}
            
            for field in line._all_columns.keys():
                if line._all_columns[field].column._type == 'many2one':
                    clean_line[field] = line[field].id
                    
                elif line._all_columns[field].column._type not in ['many2many', 'one2many']:
                    clean_line[field] = line[field]
                    
                elif field == 'invoice_line_tax_id':
                    tax_list = []
                    for tax in line[field]:
                        tax_list.append(tax.id)
                    clean_line[field] = [(6, 0, tax_list)]
                    
                elif field == 'tax_ids':
                    tax_list = []
                    if context.get('supplier_view', False) == True:
                        tax_list = []
                    else:
                        for tax in line[field]:
                            tax_list.append(tax.id)
                    clean_line[field] = [(6, 0, tax_list)]
                    
                elif field == 'flight_lines':  # Flight
                    sect = self._refund_cleanup_lines(cr, uid, line[field], context)
                    clean_line[field] = sect
                    
                elif field == 'rail_lines':  # Rail
                    sect = self._refund_cleanup_lines(cr, uid, line[field], context)
                    clean_line[field] = sect
                    
                elif field == 'airtax_ids':  # Flight - Airline Tax
                    sect = self._refund_cleanup_lines(cr, uid, line[field], context)
                    clean_line[field] = sect
                    
                elif field == 'tptax_ids':  # Sector - TP (Supplier) Tax
                    tptax_list = []
                    for tax in line[field]:
                        tptax_list.append(tax.id)
                    clean_line[field] = [(6, 0, tptax_list)] 
                    
                    # TODO:
                    # Need to delete    
#                 # Setting: 0 to irrelevant fields:
#                 if context.get('supplier_view', False) == True:
#                     if field in ('servicechrg_perc', 'a_servicechrg_perc', 'tn_servicechrg_perc', 't3_servicechrg_perc', 'e_servicechrg_perc', 'c_servicechrg_perc', 'cn_servicechrg_perc', 'i_servicechrg_perc'
#                                  , 'servicechrg', 'a_servicechrg', 'tn_servicechrg', 't3_servicechrg', 'e_servicechrg', 'c_servicechrg', 'cn_servicechrg', 'i_servicechrg' 
#                                  , 'markup', 'a_markup', 'tn_markup', 't3_markup', 'e_markup', 'c_markup', 'cn_markup', 'i_markup'
#                                  , 'markup_perc', 'a_markup_perc', 'tn_markup_perc', 't3_markup_perc', 'e_markup_perc', 'c_markup_perc', 'cn_markup_perc', 'i_markup_perc'
#                                  , 'tds1', 'a_tds1', 'tn_tds1', 't3_tds1', 'e_tds1', 'c_tds1', 'cn_tds1', 'i_tds1'
#                                  , 'tds1_perc', 'a_tds1_perc', 'tn_tds1_perc', 't3_tds1_perc', 'e_tds1_perc', 'c_tds1_perc', 'cn_tds1_perc', 'i_tds1_perc'
#                                  , 'discount', 'a_discount', 'tn_discount', 't3_discount', 'e_discount', 'c_discount', 'cn_discount', 'i_discount' 
#                                  , 'cancel_markup', 'a_cancel_markup', 'tn_cancel_markup', 't3_cancel_markup', 'e_cancel_markup', 'c_cancel_markup', 'cn_cancel_markup', 'i_cancel_markup'
#                                  , 'cancel_service', 'a_cancel_service', 'tn_cancel_service', 't3_cancel_service', 'e_cancel_service', 'c_cancel_service', 'cn_cancel_service', 'i_cancel_service'):
#                         
#                         clean_line[field] = 0.00
                
            clean_line['src_id'] = line.id    
            clean_lines.append(clean_line)
        return map(lambda x: (0, 0, x), clean_lines)
    
    # Overridden:
    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        """ 
        Overridden:
            Prepare the dict of values to create the new refund from the invoice.
            :return: dict of value to create() the refund
        """
        obj_journal = self.pool.get('account.journal')
        if context == None: context = {}
        
        type_dict = {
            'out_invoice': 'out_refund',  # Customer Invoice
            'in_invoice': 'in_refund',  # Supplier Invoice
            'out_refund': 'out_invoice',  # Customer Refund
            'in_refund': 'in_invoice',  # Supplier Refund
        }
        invoice_data = {}
        for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id', 'lead_id',
                'account_id', 'currency_id', 'payment_term', 'user_id', 'fiscal_position',
                'paxtype', 'purpose']:
            if invoice._all_columns[field].column._type == 'many2one':
                invoice_data[field] = invoice[field].id
            else:
                invoice_data[field] = invoice[field] if invoice[field] else False

        invoice_lines = []
        wiz_lines = context.get('wiz_lines',[])

        if invoice.travel_type != 'direct':  # CI => CN
            lines = self._refund_cleanup_lines(cr, uid, wiz_lines, context=context)
            line_map = {'dom_flight': 'flight_ids', 'int_flight': 'flight_ids',
                        'dom_hotel' : 'hotel_ids', 'int_hotel' : 'hotel_ids',
                        'insurance' : 'insurance_ids', 'visa' : 'visa_ids',
                        'railway' : 'railway_ids', 'cruise' : 'cruise_ids',
                        'activity': 'activity_ids', 'add_on': 'addon_ids'
                     }
            invoice_data.update({line_map[invoice.travel_type] : lines}) 
            
        else:  # Standard lines
            invoice_lines = self._refund_cleanup_lines(cr, uid, invoice.invoice_line, context=context)
            
        tax_lines = filter(lambda l: l['manual'], invoice.tax_line)
        tax_lines = self._refund_cleanup_lines(cr, uid, tax_lines, context=context)
        if journal_id:
            refund_journal_ids = [journal_id]
        elif invoice['type'] == 'in_invoice':
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_refund')], context=context)
        else:
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_refund')], context=context)

        if not date:
            date = time.strftime('%Y-%m-%d')
        invoice_data.update({
            'type': type_dict[invoice['type']],
            'travel_type': context.get('travel_type',''),
            'date_invoice': date, 
            'number' : False,
            'invoice_line': invoice_lines,
            'tax_line'  : tax_lines,
            'journal_id': refund_journal_ids and refund_journal_ids[0] or False,
            'src_id'  : invoice.id
        })
        
        if context.get('sale_view', False) == True:
            invoice_data['state'] = 'quotation'
        else:
            invoice_data['state'] = 'draft'
            
        if period_id:
            invoice_data['period_id'] = period_id
        if description:
            invoice_data['name'] = description
        return invoice_data

    # Overridden:        
    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None, context=None):
        new_ids = []
        if context == None: context = {}
        for case in self.browse(cr, uid, ids, context=context):
            invoice = self._prepare_refund(cr, uid, case,
                                                date=date,
                                                period_id=period_id,
                                                description=description,
                                                journal_id=journal_id,
                                                context=context)
            ctx = context.copy()
            ctx.update({'type':invoice.get('type'), 'travel_type': case.travel_type, 'is_invoice':False})
            
            # create the new invoice
            new_ids.append(self.create(cr, uid, invoice, context=ctx))
        return new_ids
# TODO:
# Need to delete       
#     def _prepare_supplierInvoice(self, cr, uid, invoice, date=None, period_id=None, description=None, context=None):
#         """
#             Grouping Invoice data for every Travel Partner(Customer Invoice line)
#             Prepares the dict of values to create the new Supplier Invoice, on confirming the Sale Order..
#             return: dict of value to create() the Supplier Invoice
#         """
#         invoice_group = {}
#         invoice_data = {}
#         obj_journal = self.pool.get('account.journal')
# 
#         
#         for field in ['name', 'reference', 'comment', 'date_due', 'company_id', 'travel_type',
#                 'currency_id', 'payment_term', 'user_id', 'fiscal_position', 'lead_id']:
#             if invoice._all_columns[field].column._type == 'many2one':
#                 invoice_data[field] = invoice[field].id
#             else:
#                 invoice_data[field] = invoice[field] if invoice[field] else False
#                  
#         if invoice['type'] == 'out_invoice':
#             journal_ids = obj_journal.search(cr, uid, [('type', '=', 'purchase')], context=context)
#         else:
#             journal_ids = obj_journal.search(cr, uid, [('type', '=', 'purchase_refund')], context=context)
#          
#         type_dict = {
#             'out_invoice': 'in_invoice',  # Supplier Invoice
#             'out_refund': 'in_refund',  # Debit Note
#         }
#  
#         if not date:
#             date = time.strftime('%Y-%m-%d')
#         invoice_data.update({
#             'type'  : type_dict[invoice['type']],
#             'date_invoice': date,
#             'state'  : 'quotation',
#             'number' : False,
#             'journal_id' : journal_ids and journal_ids[0] or False,
#             'src_id'  : invoice.id
#         })
#         if period_id:
#             invoice_data['period_id'] = period_id
#         if description:
#             invoice_data['name'] = description
#          
#         line_map = {'dom_flight': 'flight_ids', 'int_flight': 'flight_ids',
#                      'dom_hotel' : 'hotel_ids', 'int_hotel' : 'hotel_ids',
#                      'insurance' : 'insurance_ids', 'visa' : 'visa_ids',
#                      'railway' : 'railway_ids', 'cruise' : 'cruise_ids',
#                      'activity': 'activity_ids', 'add_on':'addon_ids',
#                      
#                      }
#          
#         lines = invoice.flight_ids or invoice.hotel_ids or invoice.visa_ids or invoice.insurance_ids or invoice.cruise_ids \
#                 or invoice.railway_ids or invoice.activity_ids or invoice.addon_ids
#          
#         for line in lines:
#             invln_vals = {}
#             vals = invoice_data.copy()
#             vals['partner_id'] = line.tpartner_id.id
#             vals.update(self.onchange_partner_id(cr, uid, [invoice.id], type_dict[invoice['type']], line.tpartner_id.id,
#                                     date, vals.get('payment_term', False), False, vals.get('company_id', False))['value'])
#              
#             ctx = context.copy()
#             ctx['supplier_view'] = True
#              
#             if invoice.travel_type != 'direct':
#                 invln_vals = self._refund_cleanup_lines(cr, uid, [line], context=ctx)
#                  
#             if invoice.travel_type == 'direct':
#                 return invoice_group
#             
#             key = (vals['partner_id'], vals['account_id'], vals['lead_id'])
#             if not key in invoice_group:
#                 vals[line_map[invoice_data['travel_type']]] = invln_vals
#                 invoice_group[key] = vals
#             else:
#                 invoice_group[key][line_map[invoice_data['travel_type']]] += invln_vals
#                   
#         return invoice_group
     
    def button_order_confirm(self, cr, uid, ids, context=None):
        if context == None: context = {}
        users_obj = self.pool.get('res.users')
        lead_obj = self.pool.get('crm.lead')
        ft_obj = self.pool.get('tr.invoice.flight')
        ftln_obj = self.pool.get('tr.invoice.flight.lines')
        
        usid = users_obj.browse(cr,uid,uid)
        psrdt = self.onchange_invoicedate(cr, uid, ids, datetime.today().strftime("%Y-%m-%d"), context)
                    
        for case in self.browse(cr, uid, ids):
            name = case.name 
            first_line = case.invoice_line and case.invoice_line[0]
            if first_line: name = first_line.name
                            
            # Checking for the group user cannot validate if cl exceeds
            if usid.tr_sale == 'sale_user':
                if case.partner_id and case.partner_id.credit_limit:
                    if (case.partner_id.credit - case.partner_id.debit + case.amount_total) > case.partner_id.credit_limit:            
                        raise osv.except_osv(_('warning'),_('Credit limit exceeded for this Customer!!'))
                        return False
                 
            if not case.invoice_line: 
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
                return False
            
            # Check For The Refunded Invoice ? Mark refunded true Sector And Passenger wise
            if case.type == 'out_refund':
                for ft in case.flight_ids:
                    for ftln in ft.flight_lines:
                        if ftln.src_id.is_refunded == True:
                            raise osv.except_osv(_('Warning!'), _('Refund for the passenger-'+ft.pax_name +', sector:'+ftln.from_id.name +'-' + ftln.to_id.name+' already confirmed'))
                            return False
                        else:
                            ftln_obj.write(cr,uid,[ftln.src_id.id],{'is_refunded':True})
                        ftln_ids = ftln_obj.search(cr,uid,[('flight_id','=',ft.src_id.id),('is_refunded','=',False)])
                        if not ftln_ids:
                            ft_obj.write(cr,uid,[ft.src_id.id],{'is_refunded':True})
             
            if case.type == 'out_invoice':

                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # Creation of Lead:
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                
                if not case.lead_id :
                    ttype = case.travel_type
                     
                    ttype_map = { 'package': 'is_package', 'dom_flight': 'is_domflight',
                                   'int_flight' : 'is_intflight', 'dom_hotel': 'is_domhotel', 'int_hotel': 'is_inthotel',
                                   'car': 'is_car', 'activity': 'is_activity', 'add_on': 'is_addon', 'visa':'is_visa',
                                   'insurance':'is_insurance', 'railway':'is_railway', 'cruise':'is_cruise'
                                  }
                    leadvals = {
                                  'name': name,
                                  'paxtype': case.paxtype or False,
                                  'purpose': case.purpose or False,
                                  'type': 'opportunity',
                                  'partner_id': case.partner_id and case.partner_id.id or False,
                                  'user_id':uid and uid or False,
                                  }
                    if ttype_map.get(ttype, False):
                        leadvals[ttype_map[ttype]] = True
                         
                    leadvals.update(lead_obj.on_change_partner_id(cr, uid, [], case.partner_id and case.partner_id.id or False)['value'])
                    lead_id = lead_obj.create(cr, uid, leadvals)
                    if lead_id: 
                        self.write(cr, uid, ids, {'lead_id':lead_id}, context)
                       # self.onchange_leadid(cr, uid, ids, lead_id, context=None)
                # TODO:
                # Need to delete    
#                 suppinv_vals = self._prepare_supplierInvoice(cr, uid, case,
#                                                     date=case.date_invoice,
#                                                     period_id=case.period_id.id,
#                                                     description=case.name,
#                                                     context=context)
#                 ctx = context.copy()
#                 ctx.update({'type':'in_invoice', 'default_type':'in_invoice'})
                 
#                 for si in suppinv_vals.keys():
#                     newid = self.create(cr, uid, suppinv_vals[si], context=ctx)
#                     self.button_reset_taxes(cr, uid, [newid], context=ctx)
#                     
#                     if usid.skip_con4mpo: # Confirming Purcase Order
#                         self.button_order_confirm(cr, uid, [newid], context=ctx)
#                         
#                     elif usid.skip_con4msi: # Validating Supplier Invoice
#                        workflow.trg_validate(uid, 'account.invoice', newid , 'invoice_open', cr) 
                
                # Confirming Sale Order
                if usid.validate_ok == True:
                   workflow.trg_validate(uid, 'account.invoice', case.id, 'invoice_open', cr) 
                   if psrdt:   
                       return self.write(cr, uid, ids,{'psr_date':psrdt['value']['psr_date']})
                    
#             if case.type == 'in_invoice':
#                 # Validating Supplier Invoice
#                 if usid.skip_con4msi:
#                    workflow.trg_validate(uid, 'account.invoice', case.id , 'invoice_open', cr) 
#                    return self.write(cr, uid, ids,{'psr_date':psrdt['value']['psr_date']})
                
        return self.write(cr, uid, ids, {'state':'draft','date_invoice': datetime.today(),'psr_date':psrdt['value']['psr_date']})
     
# TODO:
# Need to delete    
#     def action_create_debitnote(self, cr, uid, ids, context=None):
#         if context == None: context = {}
#         
#         for case in self.browse(cr, uid, ids):
#                     
#             # Credit Note => Debit Note
#             if case.type == 'out_refund':
#                 suppinv_vals = self._prepare_supplierInvoice(cr, uid, case,
#                                                     date=case.date_invoice,
#                                                     period_id=case.period_id.id,
#                                                     description=case.name,
#                                                     context=context)
#                 ctx = context.copy()
#                 ctx.update({'type':'in_refund'})
#                 for si in suppinv_vals.keys():
#                     newid = self.create(cr, uid, suppinv_vals[si], context=ctx)
#                     self.button_reset_taxes(cr, uid, [newid], context=ctx)
#                 
#         return True

    def print_invoice(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        rep_obj = self.pool.get('ir.actions.report.xml')
        attachment_obj = self.pool.get('ir.attachment') 
        res = rep_obj.pentaho_report_action(cr, uid, 'account_cusinvoice', ids,None,None)
        InvNum = self.browse(cr,uid,ids)[0]
        if InvNum.number and InvNum.type=='out_invoice': res.update({'name' : 'Invoice - ' + InvNum.number})
        elif InvNum.number and InvNum.type=='out_refund': res.update({'name' : 'Credit Note - ' + InvNum.number})
        self.write(cr, uid, ids, {'sent': True}, context=context)
        return res
    
    
    def print_voucher(self, cr, uid, ids, context=None):
        '''
        This function prints the voucher , so that we can see more easily the next step of the workflow
        '''
        rep_obj = self.pool.get('ir.actions.report.xml')

        ttype_map = {'package':'pk_voucher','dom_flight': 'ft_voucher', 'int_flight': 'ft_voucher',
                     'dom_hotel': 'ht_voucher', 'int_hotel': 'ht_voucher','add_on': 'ao_voucher',
                     'activity': 'act_voucher', 'car':'car_voucher',
                     'insurance': 'ins_voucher', 'railway': 'rl_voucher','visa': 'vi_voucher', 'cruise': 'cs_voucher'
                     }
        name_map = {'package':'Holiday Package ','dom_flight': 'Flight ', 'int_flight': 'Flight ',
                     'dom_hotel': 'Hotel ', 'int_hotel': 'Hotel ','add_on': 'Add-on ',
                     'activity': 'Activity ', 'car':'Transport ',
                     'insurance': 'Insurance ', 'railway': 'Railway ','visa': 'Visa ', 'cruise': 'Cruise '
                     }
         # To Do : For All Services
        params_map = {
                      'dom_hotel': 'hotel_id', 'int_hotel': 'hotel_id','add_on': 'addon_id',
                     'activity': 'activity_id', 'car':'transfer_id','cruise':'cruise_id'}
        
        res = {}
        for case in self.browse(cr, uid, ids):
            params = {}
            vals = {params_map.get(case.travel_type):0,'invoice_id':case.id}
            if case.travel_type in ('dom_hotel', 'int_hotel', 'cruise'): 
                vals['uid'] = uid
            
            res = rep_obj.pentaho_report_action(cr, uid, ttype_map.get(case.travel_type), [case.id], vals, None)
            res.update({'name' : name_map.get(case.travel_type) + str('Voucher - ') + case.number})  
            
        return res

    def button_order_cancel(self, cr, uid, ids, context=None):
        FT_obj  = self.pool.get('tr.invoice.flight')
        ftln_obj = self.pool.get('tr.invoice.flight.lines')
        # Delete: Supplier Invoice
        draft_suppids = self.search(cr, uid, [('src_id', 'in', ids), ('state','in', ('quotation','order_cancel')), ('type','=', 'in_invoice')])
        self.unlink(cr, uid, draft_suppids)
        
        cnf4m_suppids = self.search(cr, uid, [('src_id', 'in', ids), ('state','not in', ('quotation','order_cancel')), ('type','=', 'in_invoice')])
        if cnf4m_suppids:
            raise osv.except_osv(_('warning'), _('Purchase Orders related to this Sale Order are already confimed. You cannot CANCEL this record..!!'))

        for case in self.browse(cr,uid,ids):
            for ft in case.flight_ids:
                for sctr in ft.flight_lines:
                    if sctr.src_id.is_refunded and ft.inv_type == 'out_refund':
                        ftln_obj.write(cr, uid, [sctr.src_id.id],{'is_refunded':False}, context)
                        FT_obj.write(cr, uid, [ft.src_id.id],{'is_refunded':False}, context)
                        
        return self.write(cr, uid, ids, {'state':'order_cancel'})
   
    def button_set_quotation(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'quotation', 'internal_number':''})
    
    def button_update(self, cr, uid, ids, context=None):
        """
            To update the customer discount in Flight
        """
         
        FT_obj = self.pool.get('tr.invoice.flight')
        FTln_obj=self.pool.get('tr.invoice.flight.lines')
         
        for case in self.browse(cr, uid, ids): 
            for f in case.flight_ids:
                # updating Discounts, markup and servicechrg from Commission structure For Invoices
                if case.type=='out_invoice':
                    if case.partner_id.id :context.update({'partner_id':case.partner_id.id, 'calledfrm' : 'func'})
                    if f.a_basic > 0:
                        fvals = FT_obj.onchange_FT_airline(cr, uid, ids, f.tpartner_id.id, f.flight_lines, context)['value']
                        fvals.update(FT_obj.onchange_FT_subTotal(cr, uid, [f.id], f.inv_type,'all',f.a_basic, fvals.get('a_other',False)
                                    , fvals.get('a_servicechrg_perc',0), fvals.get('a_servicechrg',0),0, fvals.get('a_markup',0), 0, 0, 0,0,0,0,0 
                                    , fvals.get('a_tac_perc',0), 0, fvals.get('a_tac_select',False), fvals.get('a_tac_basic', False), fvals.get('a_tac_other', False)
                                    , False, fvals.get('a_tac_perc1', 0), fvals.get('a_tac_basic1', False), fvals.get('a_tac_other1', False), False
                                    , fvals.get('a_tac_perc2', 0), fvals.get('a_tac_basic2',False), fvals.get('a_tac_other2',False), False
                                    , fvals.get('tptax_basic', False), fvals.get('tptax_airtax', False), fvals.get('tptax_tac', False)
                                    , fvals.get('tptax_tds',False), fvals.get('tptax_other', False), fvals.get('airtax_ids',[]), fvals.get('tptax_ids',[])
                                    , 0, fvals.get('a_disc_select', False), fvals.get('a_disc_perc',0), fvals.get('a_disc_basic',False)
                                    , fvals.get('a_disc_other', False), False,fvals.get('a_disc_perc1',0), fvals.get('a_disc_basic1', False)
                                    , fvals.get('a_disc_other1', False), False, fvals.get('a_disc_perc2',0), fvals.get('a_disc_basic2',False)
                                    , fvals.get('a_disc_other2', False), False, f.a_cancel_markup, f.a_cancel_charges, f.a_cancel_service, context=context)['value'])
                        FT_obj.write(cr, uid, [f.id], fvals)
                        
                # updating Cancellation Chrg from Commission structure For Credit Notes
#                 if case.type=='out_refund':
#                     FT_obj.update_cancelcharges(cr,uid,[f.id])
            
        return self.write(cr, uid, ids, {})
    
   
    # Tax grouping for Airfile Tax Component
    def _tax_grouping(self, cr, uid, ids, txname, txamt, context=None):
        tax = {}
        comp_obj = self.pool.get('tr.airlines.taxcomp')
        
        cmp_ids = comp_obj.search(cr, uid, [('name', '=', txname)])
        if not cmp_ids:
            tax['component_id'] = comp_obj.create(cr, uid, {'name': txname})
        else:
            tax['component_id'] = cmp_ids[0]
            
        tax['amount'] = float(txamt)
        return tax
   
    def _compute_serviceLines(self, cr, uid, ids, context=None):
        
        OPT_obj = self.pool.get('tr.invoice.option')
        OPTln_obj = self.pool.get('tr.invoice.option.lines')
        FT_obj = self.pool.get('tr.invoice.flight')
        HT_obj = self.pool.get('tr.invoice.hotel')
        RL_obj = self.pool.get('tr.invoice.railway')
        CS_obj = self.pool.get('tr.invoice.cruise')
        TR_obj = self.pool.get('tr.invoice.car')
        VI_obj = self.pool.get('tr.invoice.visa')
        IN_obj = self.pool.get('tr.invoice.insurance')
        AC_obj = self.pool.get('tr.invoice.activity')
        AD_obj = self.pool.get('tr.invoice.addon')
        
        def _all_services(obj):
            FT_obj.write(cr, uid, map(lambda x: x.id, obj.flight_ids), {})
            HT_obj.write(cr, uid, map(lambda x: x.id, obj.hotel_ids), {})
            TR_obj.write(cr, uid, map(lambda x: x.id, obj.car_ids), {})
            CS_obj.write(cr, uid, map(lambda x: x.id, obj.cruise_ids), {})
            VI_obj.write(cr, uid, map(lambda x: x.id, obj.visa_ids), {})
            IN_obj.write(cr, uid, map(lambda x: x.id, obj.insurance_ids), {})
            AC_obj.write(cr, uid, map(lambda x: x.id, obj.activity_ids), {})
            AD_obj.write(cr, uid, map(lambda x: x.id, obj.addon_ids), {})
        
        for case in self.browse(cr, uid, ids):
            if case.travel_type == 'package':
               for op in case.option_ids:
                   _all_services(op)
                   for l in op.opt_lines:
                       OPTln_obj.write(cr, uid, [l.id], {})
                   OPT_obj.write(cr, uid, [op.id], {})
                   
            else:
               _all_services(case)
               RL_obj.write(cr, uid, map(lambda x: x.id, case.railway_ids), {})
                
        return True
       
    # Inherited:
    def button_reset_taxes(self, cr, uid, ids, context=None):
        self._compute_serviceLines(cr, uid, ids, context)
        return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)
#     
#     # Overridden:
#     def action_move_create(self, cr, uid, ids, context=None):
#         """ Creates invoice related analytics and financial move lines
#         """
#         ait_obj = self.pool.get('account.invoice.tax')
#         cur_obj = self.pool.get('res.currency')
#         period_obj = self.pool.get('account.period')
#         payment_term_obj = self.pool.get('account.payment.term')
#         journal_obj = self.pool.get('account.journal')
#         move_obj = self.pool.get('account.move')
#         account_obj = self.pool.get('account.account')
# 
#         comp = self.pool.get('res.users').browse(cr, uid, uid).company_id
#         if context is None: context = {}
#          
#         discount_id = comp.discount_id and comp.discount_id.id or False
#         tac_id      = comp.tac_id and comp.tac_id.id or False
#         tdsreceive_id = comp.tds_receivable_id and comp.tds_receivable_id.id or False
#         tdspayable_id = comp.tds_payable_id and comp.tds_payable_id.id or False
#         
#         for inv in self.browse(cr, uid, ids, context=context):
#             if not inv.journal_id.sequence_id:
#                 raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
#             if not inv.invoice_line:
#                 raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
#             if inv.move_id:
#                 continue
#  
#             ctx = context.copy()
#             ctx.update({'lang': inv.partner_id.lang})
#             if not inv.date_invoice:
#                 self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
#             company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
#             # create the analytical lines
#             # one move line per invoice line
#             iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
#             # check if taxes are all computed
#             compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
#             self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)
#  
#             # I disabled the check_total feature
#             group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
#             group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
#             if group_check_total and uid in [x.id for x in group_check_total.users]:
#                 if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
#                     raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))
#  
#             if inv.payment_term:
#                 total_fixed = total_percent = 0
#                 for line in inv.payment_term.line_ids:
#                     if line.value == 'fixed':
#                         total_fixed += line.value_amount
#                     if line.value == 'procent':
#                         total_percent += line.value_amount
#                 total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
#                 if (total_fixed + total_percent) > 100:
#                     raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))
#  
#             # one move line per tax line
#             iml += ait_obj.move_line_get(cr, uid, inv.id)
#  
#             entry_type = ''
#             if inv.type in ('in_invoice', 'in_refund'):
#                 ref = inv.reference
#                 entry_type = 'journal_pur_voucher'
#                 if inv.type == 'in_refund':
#                     entry_type = 'cont_voucher'
#             else:
#                 ref = self._convert_ref(cr, uid, inv.number)
#                 entry_type = 'journal_sale_vou'
#                 if inv.type == 'out_refund':
#                     entry_type = 'cont_voucher'
#  
#             name = inv['name'] or inv['supplier_invoice_number'] or '/'
#             
#             tds_amt = discount = tac = 0.00
#             for line in inv.invoice_line:
#                  tds_amt += line.tds
#                  discount += line.discount
#                  tac += line.tac
#             # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
#             #      TDS: passing to Journal Entry 
#             # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#             tds_account = inv.type in ('in_invoice', 'in_refund') and tdsreceive_id or tdspayable_id 
#             
#             if tds_amt and tds_account:
#                 tds_account = int(tds_account)
#                 iml.append({
#                         'type'  : 'src',
#                         'name'  : '(TDS) ' + name,
#                         'price' : tds_amt,
#                         'account_id': tds_account,
#                       })
#                 
#             # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
#             #      Discount: passing to Journal Entry 
#             # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# #             
#             if discount and discount_id and inv.type in ('out_invoice', 'out_refund'):
#                 discount_id = int(discount_id)
#                 iml.append({
#                         'type'  : 'src',
#                         'name'  : '(Discount) ' + name,
#                         'price' : discount * -1,
#                         'account_id': discount_id,
#                       })
#                 
#             # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
#             #      TAC: passing to Journal Entry 
#             # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# #             
#             if tac and tac_id and inv.type in ('in_invoice', 'in_refund'):
#                 tac_id = int(tac_id)
#                 iml.append({
#                         'type'  : 'src',
#                         'name'  : '(TDS) ' + name,
#                         'price' : tac,
#                         'account_id': tac_id,
#                       })
#                 
#             diff_currency_p = inv.currency_id.id <> company_currency
#             # create one move line for the total and possibly adjust the other lines amount
#             total = 0
#             total_currency = 0
#             total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
#             acc_id = inv.account_id.id
#  
#             totlines = False
#             if inv.payment_term:
#                 totlines = payment_term_obj.compute(cr,
#                         uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
#             
#             if totlines:
#                 res_amount_currency = total_currency
#                 i = 0
#                 ctx.update({'date': inv.date_invoice})
#                 for t in totlines:
#                     if inv.currency_id.id != company_currency:
#                         amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
#                     else:
#                         amount_currency = False
#  
#                     # last line add the diff
#                     res_amount_currency -= amount_currency or 0
#                     i += 1
#                     if i == len(totlines):
#                         amount_currency += res_amount_currency
#  
#                     iml.append({
#                         'type': 'dest',
#                         'name': name,
#                         'price': t[1],
#                         'account_id': acc_id,
#                         'date_maturity': t[0],
#                         'amount_currency': diff_currency_p \
#                                 and amount_currency or False,
#                         'currency_id': diff_currency_p \
#                                 and inv.currency_id.id or False,
#                         'ref': ref,
#                     })
#             else:
#                 iml.append({
#                     'type': 'dest',
#                     'name': name,
#                     'price': total,
#                     'account_id': acc_id,
#                     'date_maturity': inv.date_due or False,
#                     'amount_currency': diff_currency_p \
#                             and total_currency or False,
#                     'currency_id': diff_currency_p \
#                             and inv.currency_id.id or False,
#                     'ref': ref
#             })
#  
#             date = inv.date_invoice or time.strftime('%Y-%m-%d')
#  
#             part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)
#  
#             line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)
#  
#             line = self.group_lines(cr, uid, iml, line, inv)
#  
#             journal_id = inv.journal_id.id
#             journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
#             if journal.centralisation:
#                 raise osv.except_osv(_('User Error!'),
#                         _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))
#  
#             line = self.finalize_invoice_move_lines(cr, uid, inv, line)
#  
#             move = {
#                 'ref': inv.reference and inv.reference or inv.name,
#                 'line_id': line,
#                 'journal_id': journal_id,
#                 'date': date,
#                 'narration': inv.comment,
#                 'company_id': inv.company_id.id,
#             }
#             period_id = inv.period_id and inv.period_id.id or False
#             ctx.update(company_id=inv.company_id.id)
#             if not period_id:
#                 period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
#                 period_id = period_ids and period_ids[0] or False
#             if period_id:
#                 move['period_id'] = period_id
#                 for i in line:
#                     i[2]['period_id'] = period_id
#  
#             ctx.update(invoice=inv)
#             move_id = move_obj.create(cr, uid, move, context=ctx)
#             new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
#             # make the invoice point to that move
#             self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
#             # Pass invoice in context in method post: used if you want to get the same
#             # account move reference when creating the same invoice after a cancelled one:
#             move_obj.post(cr, uid, [move_id], context=ctx)
#         self._log_event(cr, uid, ids)
#         return True
     
    # Inherited:
    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(account_invoice, self).line_get_convert(cr, uid, x, part, date, context)
        res['name'] = x['name']
        res['partner_id'] = x.get('partner_id',part)
        return res

    # Overridden:
    def invoice_validate(self, cr, uid, ids, context=None):
        ft_obj = self.pool.get('tr.invoice.flight')
        ftln_obj = self.pool.get('tr.invoice.flight.lines')
        # Check For The Refunded Invoice ? Mark refunded true Sector And Passenger wise
        
#         for case in self.browse(cr, uid, ids):            
#             if case.type == 'out_refund':
#                 for ft in case.flight_ids:
#                     for ftln in ft.flight_lines:
#                         if ftln.src_id.is_refunded == True:
#                             raise osv.except_osv(_('Warining!'), _('Refund for the passenger-'+ft.pax_name +', sector:'+ftln.from_id.name +'-' + ftln.to_id.name+' already confirmed'))
#                             return False
#                         else:
#                             ftln_obj.write(cr,uid,[ftln.src_id.id],{'is_refunded':True})
#                         ftln_ids = ftln_obj.search(cr,uid,[('flight_id','=',ft.src_id.id),('is_refunded','=',False)])
#                         if not ftln_ids:
#                             ft_obj.write(cr,uid,[ft.src_id.id],{'is_refunded':True})

        return self.write(cr, uid, ids, {'state':'open'}, context=context)

    # Overridden:
    def action_move_create(self, cr, uid, ids, context=None):
        """ Creates invoice related analytics and financial move lines
        """
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        account_obj = self.pool.get('account.account')
        invline_obj = self.pool.get('account.invoice.line')
        
        if context is None: context = {}
          
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue
 
            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
            
            # TODO: check for analytical entry
            # create the analytical lines
            
            # one move line per invoice line
#             iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)

            iml = invline_obj.move_line_get(cr, uid, inv.id, context=context)
            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)
 
            # I disabled the check_total feature
            group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
            if group_check_total and uid in [x.id for x in group_check_total.users]:
                if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
                    raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))
 
            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))
 
            
            firstline = inv.invoice_line and inv.invoice_line[0]
            lnname = firstline and firstline.name or '/'
            name = inv['name'] or lnname or inv['supplier_invoice_number']  or '/'
            if inv.type in ('out_invoice', 'in_refund'):
                sign = 1
            else:
                sign = -1
            
            # one move line per tax line            
            txl = ait_obj.move_line_get(cr, uid, inv.id) or []
            for a in txl: a['name'] = name or a['name']
            iml += txl
            
            entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    entry_type = 'cont_voucher'
 
            
            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
            acc_id = inv.account_id.id
 
            totlines = False
            if inv.payment_term:
                totlines = payment_term_obj.compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
            
            # TODO:
            # Need to check with payment_term
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.date_invoice})
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
                    else:
                        amount_currency = False
 
                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency
 
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                amount = (inv.amount_total * sign) # Need to tally
                amount_currency = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, amount, context=ctx)
                
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': amount_currency,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and amount or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })
 
            date = inv.date_invoice or time.strftime('%Y-%m-%d')
 
            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)
 
            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)
 
            line = self.group_lines(cr, uid, iml, line, inv)
 
            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))
 
            line = self.finalize_invoice_move_lines(cr, uid, inv, line)
            
            move = {
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update(company_id=inv.company_id.id)
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id
 
            ctx.update(invoice=inv)
            print 'move========',move
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True
    
    def action_create_InvNumber(self, cr, uid, ids, context=None):
        """
            Method: called from Workflow
            Sets Invoice Number
        """
        today = datetime.today()
        mon = today.strftime('%m')
        year = today.strftime('%y')
        
        partner_obj = self.pool.get('res.partner')
        
        for case in self.browse(cr, uid, ids):
            updatevals = {}
            InvNum = ''
            
            InvNum = (case.type == 'out_refund') and 'R' or \
                         (case.type == 'in_refund') and 'R' or \
                         (case.type == 'in_invoice') and 'I' or \
                         (case.type == 'out_invoice') and 'I' 
            
#             InvNum += traveltype_map.get(case.travel_type, '')
            InvNum += self.pool.get('res.company').read(cr,uid,[case.company_id.id],['comp_code'])[0]['comp_code'] or ''
            InvNum += year
            
            cr.execute(""" select id from account_invoice where internal_number ilike '""" + str(InvNum) + """%'  and id != """ + str(case.id) + """
                           order by to_number(substr(internal_number,(length('""" + str(InvNum) + """')+1)),'9999999999')
                           desc limit 1""")
            inv_rec = cr.fetchone()
            if inv_rec:
                inv = self.browse(cr, SUPERUSER_ID, inv_rec[0])
                auto_gen = inv.internal_number[len(InvNum) : ]
                InvNum = InvNum + str(int(auto_gen) + 1).zfill(5)
            else:
                InvNum = InvNum + '00001'
                
            updatevals = {'internal_number': InvNum, 'number': InvNum}
            
            first_line = case.invoice_line and case.invoice_line[0]
            if first_line:
                updatevals['name'] = first_line.name
            
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Party Ledger Account is created on First Invoice:
            if case.partner_id and not case.partner_id.has_account:
                partner_obj._create_PartyLedger(cr, uid, [case.partner_id.id]
                                                , {'name' : case.partner_id.name
                                                    , 'customer' : case.partner_id.customer
                                                    , 'supplier' : case.partner_id.supplier
                                                  })
                vals = self.onchange_partner_id(cr, uid, [case.id], case.type, case.partner_id.id, case.date_invoice 
                                         , (case.payment_term and case.payment_term.id or False)
                                         , (case.partner_bank_id and case.partner_bank_id or False)
                                         , (case.company_id and case.company_id.id or False))['value']
                updatevals.update({'account_id':vals.get('account_id', case.account_id.id)})
                                          
            self.write(cr, uid, [case.id], updatevals)
        return True
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  To create Flight Invoice from Air File
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run_scheduler_Airfile(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        """
            Called from Scheduler,
            Creates Flight Invoice for both Booking & Ticketing Airfiles..
        """
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Reading the Galileo Air File Booking 
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ft_obj = self.pool.get('tr.invoice.flight')
        path = '/home/serveradmin/Desktop/Airfile/Booking'
        for p in range(0,2):
            for dir_entry in os.listdir(path):
                dir_entry_path = os.path.join(path, dir_entry)
                if os.path.isfile(dir_entry_path):
                    
                    with open(dir_entry_path, 'rU') as airfile:
                        af_con = airfile.readlines()
                        _logger.info('Reading Airfile : %s', airfile.name)
                        inv_id = False
                        gdsPNR = af_con[1][17:23].strip()
                        
                        if gdsPNR:
                           ft_ids = ft_obj.search(cr, uid, [('pnr', '=', gdsPNR)]) 
                           if ft_ids:
                               if p == 0:
                                   _logger.error('PNR Booking Record Already Exists %s' % (gdsPNR.strip(),)) 
                                   continue 
                               ft = ft_obj.browse(cr, uid, ft_ids[0])
                               inv_id = ft and ft.invoice_id.id or False  
                        else:
                            _logger.error('Unable To Find gdsPNR Record In Ticketing Airfile %s' % (gdsPNR.strip(),))    
                        
                        if self._reading_Airfile(cr, uid, af_con, inv_id, context):
                            shutil.move(airfile.name, '/home/serveradmin/Desktop/Airfile')
            path = '/home/serveradmin/Desktop/Airfile/Ticketing'
        return True

    def _reading_Airfile(self, cr, uid, af_con, inv_id, context=None):
        """
            Reading Airfile and creation of Flight Invoice 
        """
        ft_obj = self.pool.get('tr.invoice.flight')
        ftln_obj = self.pool.get('tr.invoice.flight.lines')
        arln_obj = self.pool.get('tr.airlines')
        prod_obj = self.pool.get('product.product')
        airport_obj = self.pool.get('tr.airport')
        ft_cls_obj = self.pool.get('tr.flight.class')
        ft_faretyp_obj = self.pool.get('tr.flight.faretype')
        suppsys_obj = self.pool.get('tr.supplier.systems')
        tplogin_obj = self.pool.get('tr.suppliersys.login')
        tppcc_obj = self.pool.get('tr.suppliersys.pcc')
        comp_obj = self.pool.get('res.company')
        curr_obj = self.pool.get('res.currency')
        users_obj = self.pool.get('res.users')
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #  Reading Line 1:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        line = 0
        gdsId = af_con[line][2:4]
        ticketDate = datetime.strptime(af_con[line][20:27], "%d%b%y").strftime("%Y-%m-%d")
        travelDate = datetime.strptime(af_con[line][61:68], "%d%b%y").strftime("%Y-%m-%d")
        trvl_yr = datetime.strptime(af_con[line][61:68], "%d%b%y").strftime("%Y")
        trvl_mnth = datetime.strptime(af_con[line][61:68], "%d%b%y").strftime("%m")
        airlineCode = af_con[line][32:34] 
        airlinetkprefix = af_con[line][34:37] 
        airlineName = af_con[line][37:56]
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Reading Line 2: PNR details
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        line = 1
        branch_PCC = af_con[line][4:8]
        iataCode = af_con[line][8:16]
        gdsPNR = af_con[line][17:23]
        userID = af_con[line][32:38]
        booking_dt = af_con[line][43:50]
        Ticket_dt = af_con[line][53:60]
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Reading Line 7: Passsenger
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         line = 6
        passengers = []
        while(True):
           if af_con[line][0:3] == "A04":   break
           if af_con[line][0:3] == 'A02':
               pvals = {
                        'name'   : af_con[line][3:30].strip(),
                        'tik_no' : af_con[line][48:58].strip(),
                        'tik_count': af_con[line][58:60].strip(),
                        'type'    : af_con[line][69:70].strip(),
                        'fare_seq': af_con[line][75:77].strip()
                        }
               passengers.append(pvals)
           line += 1 
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Reading: Flight details
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        sector = []
        airport_codes = set()
        while(True):
            if af_con[line][0:3] == "A07":  break 
            svals = {}
            svals['seq'] = af_con[line][3:5].strip()          
            svals['airline_code'] = af_con[line][5:7].strip()
            svals['tik_carrier'] = af_con[line][5:10].strip()
            svals['airln_name'] = af_con[line][10:22].strip()
            svals['flight_no'] = af_con[line][22:26].strip()
            svals['fare_class'] = af_con[line][26:27].strip()
            svals['tik_status'] = af_con[line][28:30].strip()
            svals['trvl_date'] = af_con[line][30:35].strip()
            svals['dep_time'] = af_con[line][35:39].strip()
            svals['arr_time'] = af_con[line][40:44].strip()
            svals['same_diff'] = af_con[line][45:46].strip()
            svals['dep_airport_code'] = af_con[line][46:49].strip()
            svals['dep'] = af_con[line][49:62].strip()
            svals['arr_airport_code'] = af_con[line][62:65].strip()
            svals['arrival'] = af_con[line][65:78].strip()
            sector.append(svals)
            
            airport_codes.add(svals['dep_airport_code'])
            airport_codes.add(svals['arr_airport_code'])
            line += 1 
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Reading: Sector details
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        fare = []
        total_fare = 0 # To Calculate basic + Taxes
        while(True):
            fvals = {}
            if af_con[line][0:3] == "A08":
                break
            elif af_con[line][0:3] == 'IT:':  # Skipping Tax Lines
                line += 1  # Need to check
                continue
            elif not len(af_con[line][:-1]):  # Skipping Empty Lines
                line += 1  # Need to check
                continue
           
            fvals['type']       = af_con[line][3:5].strip()
            fvals['foregn_curr_code'] = af_con[line][5:8].strip()
#             fvals['basic']      = float(af_con[line][8:20].strip())
            fvals['local_curr_code'] = af_con[line][20:23].strip()
            fvals['gross']      = float(af_con[line][23:35].strip())
            fvals['tax_curr_indi']  = af_con[line][50:53].strip()
            data = []
            
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Check The Company Currency Code Is Same 
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            curr_ids = curr_obj.search(cr,uid,[('name','=',fvals['foregn_curr_code'])])
            if curr_ids:
                usrcomp_id = users_obj.read(cr,uid,[uid],['company_id'])[0]['company_id'][0]
                if usrcomp_id : 
                    usrcurr_id = comp_obj.read(cr,uid,[usrcomp_id],['currency_id'])[0]['currency_id']
                    if usrcurr_id[0] == int(curr_ids[0]):
                        fvals['basic']  = float(af_con[line][8:20].strip())
                        total_fare += fvals['basic']
                    else: # Company Currency Is Not Same As Local Currency
                        if usrcurr_id[1] != 'INR':
                            _logger.error('Currency Mismatch , Airfile Currency - ' +fvals['foregn_curr_code']+' But Company Currency - '+usrcurr_id[1])
                            return False
                        fvals['basic']  = float(af_con[line][38:50].strip())
                        total_fare += fvals['basic']
                    
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
            # Tax 1:
            if af_con[line][53:56] == 'T1:':
                at = self._tax_grouping(cr, uid, [], af_con[line][64:66], af_con[line][56:64].strip())
                total_fare += float(af_con[line][56:64].strip())
                data.append(at)
                fvals['data'] = data
                
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Tax 2:
            if af_con[line][66:69] == 'T2:':
                at = self._tax_grouping(cr, uid, [], af_con[line][77:79], af_con[line][69:77].strip())
                total_fare += float(af_con[line][69:77].strip())
                data.append(at)
                fvals['data'] = data
                
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Tax 3: [Next Line]
            # TODO: IT for second line
            
            if af_con[line][79:82] == 'T3:' and af_con[line][82:90].strip():
                if af_con[line][90:92] == 'XT' and af_con[line + 1][0:3] == 'IT:':
                    itln = af_con[line + 1][3:]  # Reading: IT Line
                    
                    while len(itln) >= 10:  # Reading: Tax for every 10 Character 
                        t3cmp = itln[0:10]
                        if t3cmp:
                            at = self._tax_grouping(cr, uid, [], t3cmp[-2:], t3cmp[0:8].strip())
                            total_fare += float(t3cmp[0:8].strip())
                            data.append(at)
                            itln = itln[10:]
                    fvals['data'] = data
                else:
                    at = self._tax_grouping(cr, uid, [], af_con[line][90:92], af_con[line][82:90].strip())
                    total_fare += float(af_con[line][82:90].strip())
                    data.append(at)
                    fvals['data'] = data
                    
            # ~~~~~~~~~~~~~~~~~~~~~
            # Check for Other Taxes
            # ~~~~~~~~~~~~~~~~~~~~~
            if (fvals['gross'] - total_fare) > 0:
                at = self._tax_grouping(cr, uid, [], 'OTH', fvals['gross'] - total_fare)
                data.append(at)
                fvals['data'] = data
            fare.append(fvals)    
            line += 1
            
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Reading: Fare Type    
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        fare_type={}
        while(True):        
            if af_con[line][0:3] == "A08":
                fare_type[af_con[line][3:7]]=af_con[line][7:15]                
            else:
                break
            line += 1

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Reading: Airline PNR    
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        while(True):        
            arln_pnr = ''
            if af_con[line][0:5] == "A14VL":
                arln_pnr = af_con[line][20:28]
                break
            line += 1
             
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Reading: Travel Partner and Consultant branch_PCC
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        tpartner_id = consul_id = company_id = False
        
        suppsys_ids = suppsys_obj.search(cr,uid,[('code','=',gdsId.strip())])
        if suppsys_ids:
            suppsys = suppsys_obj.browse(cr, uid, suppsys_ids[0])
            tpartner_id = suppsys and suppsys.partner_id and suppsys.partner_id.id or False
            supplog_ids = tplogin_obj.search(cr, uid, [('login', '=', userID.strip())])
            if supplog_ids:
                suppcc_ids = tppcc_obj.search(cr,uid,[('branch_pcc','=',branch_PCC.strip())])
                if suppcc_ids :
                    cr.execute("""select log.user_id, usr.company_id
                        from     tr_suppliersys_login log,
                                 res_users usr,
                                 tr_supplier_systems sys
                        where    log.tpsystem_id = sys.id
                        and      log.user_id = usr.id
                        and      sys.code = '""" + str(gdsId.strip()) + """'
                        and      log.login = '""" + str(userID.strip()) + """'
                        and      usr.company_id = (select company_id from tr_suppliersys_pcc where branch_pcc = '""" + str(branch_PCC.strip()) + """' order by company_id limit 1) """)
                    usr_cmpny_id = cr.fetchall()
                    print 'usr_cmpny_id',usr_cmpny_id
                    if usr_cmpny_id:
                        usr_cmpny_id = usr_cmpny_id[0]
                        consul_id =  usr_cmpny_id[0] and usr_cmpny_id[0] or False
                        company_id = usr_cmpny_id[1] and usr_cmpny_id[1] or False
                else:
                    _logger.error('Unable To Find The Branch-PCC %s' % (branch_PCC.strip(),))
                    return False
            else:
                _logger.error('Unable To Find The User-ID %s' % (userID.strip(),))
                return False 
        else:
            _logger.error('Unable To Find The Airfile GDS-ID %s' % (gdsId.strip(),))
            return False

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Checking whether any 1 airport is International
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        service_type = 'dom_flight'
        airport_ids = airport_obj.search(cr, uid, [('code', 'in', list(airport_codes)), ('type', '=', 'international')])
        if len(airport_ids) > 0: service_type = 'int_flight'
        product_ids = prod_obj.search(cr, uid, [('travel_type1', '=', service_type),('company_id','=',company_id or False)], limit=1)
        product = ''
        product_id = product_ids and product_ids[0] or False
        if product_id:
            product = prod_obj.browse(cr, uid, product_id).name_template 
                
        paxmap = {'A': 'adult', 'C': 'child', 'I': 'infant'}
        ftvals_list = []
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Looping Each Passenger With Respective Sector, Fare, Taxes      
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        for psngr in passengers:
            flight_vals = {}
            if psngr['name'] or psngr['type'] :
                flight_vals = {
                           'pax_name'   : psngr['name'],
                           'pax_type'   : paxmap[psngr['type']],
                           'tpartner_id': tpartner_id or False,
                           'product_id' : product_id or False,
                           'name'       : product,
                           }
                flight_vals.update(ft_obj.onchange_product(cr, uid, [], product_id)['value'])
                flight_vals.update({
                                    'tax_ids' : [(6, 0, flight_vals.get('tax_ids',[]))]
                                    })
            lnvals_list = []
            
            for sctr in sector:
                line_vals = {}
                if sctr['flight_no'] or sctr['dep'] or sctr['arrival'] and flight_vals['pax_type']:
                    # To Fetch Arrival And Dep Datetime
                    dep_airport_id = False
                    arr_airport_id = False
                     
                    # TODO: optimize
                    # Arrival & Departure
                    strvdt = datetime.strptime(sctr['trvl_date'], "%d%b").strftime("%m-%d")
                    strvmnt = datetime.strptime(sctr['trvl_date'], "%d%b").strftime("%m")
                     
                    if strvmnt < trvl_mnth:
                        strvdt = str(int(trvl_yr) + 1) + '-' + strvdt
                    else:    
                        strvdt = trvl_yr + '-' + strvdt
                    arr_tme = datetime.strptime(sctr['arr_time'], "%H%M").strftime("%H:%M:%S")
                    dep_tme = datetime.strptime(sctr['dep_time'], "%H%M").strftime("%H:%M:%S")
                     
                    if sctr['same_diff'] == '3': 
                        arr_date = (datetime.strptime(strvdt, '%Y-%m-%d') + relativedelta(days=1)).strftime("%Y-%m-%d")
                    else:    
                        arr_date = datetime.strptime(strvdt, '%Y-%m-%d').strftime("%Y-%m-%d")
                         
                    arr_datetime = (datetime.strptime(arr_date + ' ' + arr_tme, '%Y-%m-%d %H:%M:%S') - relativedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                    dep_datetime = (datetime.strptime(strvdt + ' ' + dep_tme, '%Y-%m-%d %H:%M:%S') - relativedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                     
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    # Fetching Airline
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    arln_ids = arln_obj.search(cr, uid, [('code', '=', sctr['airline_code'])])
                    if not arln_ids:
                        _logger.error('Unable To Find The Airline %s ' % (sctr['airln_name']+'['+sctr['airline_code']+']',))
                        return False
                    airline_id = arln_ids and arln_ids[0] or False  # Auto Populate All Values Respec to Airline From Commissionlns
                     
                    dep_ids = airport_obj.search(cr, uid, [('code', '=', sctr['dep_airport_code'])])
                    arr_ids = airport_obj.search(cr, uid, [('code', '=', sctr['arr_airport_code'])])
                    
                    if not dep_ids :
                        _logger.error('Unable To Find The Departure Airport %s' % (sctr['dep']+'['+sctr['dep_airport_code']+']',))
                        return False
                    
                    if not arr_ids :
                        _logger.error('Unable To Find The Arrival Airport %s' % (sctr['arrival']+'['+sctr['arr_airport_code']+']',))
                        return False
                    
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    # Fetching Class
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    ftcls_ids = ft_cls_obj.search(cr, uid, [('name', '=', sctr['fare_class'])])

                    if not ftcls_ids :
                        _logger.error('Unable To Find The Flight Class %s' % (sctr['fare_class'],))
                        return False
                    ftcls_id = ftcls_ids and ftcls_ids[0] or False
                    
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    # Fetching Flight Fare Type
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~       
                    farety_ids = []
                    if psngr['fare_seq'] + sctr['seq'] in fare_type:
                        farety_ids = ft_faretyp_obj.search(cr, uid, [('code', '=', fare_type[psngr['fare_seq']+sctr['seq']].strip())])
                    else:
                        farety_ids = ft_faretyp_obj.search(cr, uid, [('code', '=', fare_type['01'+sctr['seq']].strip())])    
                    if not farety_ids :
                            farety_ids.append(ft_faretyp_obj.create(cr,uid,{'code': fare_type[psngr['fare_seq']+sctr['seq']].strip(),
                                                                        'name': fare_type[psngr['fare_seq']+sctr['seq']].strip()}))
                    faretyp_id = farety_ids and farety_ids[0] or False,
                    
                    line_vals.update({
                                'airline_id'    : airline_id,
                                
                                'ftclass_id'    : ftcls_id,
                                'faretype_id'   : faretyp_id,
                                'ft_num'        : sctr['flight_no'],
                                'arr'           : arr_datetime,
                                'dep'           : dep_datetime,
                                'from_id'       : dep_ids and dep_ids[0] or False,
                                'to_id'         : arr_ids and arr_ids[0] or False,
                               
#                                 'ft_paxtype'    : flight_vals['pax_type'],
#                                 'ft_traveltype' : service_type,
                        })
                    lnvals_list.append((0, 0, line_vals))
                    
            flight_vals.update(ft_obj.onchange_FT_airline(cr, uid, [],tpartner_id,lnvals_list)['value'])
            def_airtax = {}
            
            for d in flight_vals['airtax_ids']:
                key = d[2]['component_id']
                def_airtax[key] = d[2]
                 
            del flight_vals['airtax_ids']
            # Creating fare details for 1st Sector
            for f in fare:
                # Passenger Fare Sequence wise Sector Fare is fetched (1st Sector line)
                if (f['type'] == psngr['fare_seq']) :
                    sectax_list = []
                    for t in f.get('data', []):
                        sectax = t.copy()
                        if t['component_id'] in def_airtax.keys():  # Checking Component in Supplier Commision
                            sectax.update({
                                           'tac_a'  : def_airtax[t['component_id']]['tac_a'],
                                           'tac_b'  : def_airtax[t['component_id']]['tac_b'],
                                           'tac_c'  : def_airtax[t['component_id']]['tac_c'],
                                           })
                        sectax_list.append((0, 0, sectax))
                        
                    flight_vals.update({
                           'a_basic' : f.get('basic', 0),
                           'airtax_ids':  sectax_list,
                           'ticket_no'     : psngr['tik_no'],
                           'pnr'           : gdsPNR or '',
                           'airline_pnr'   : arln_pnr,
                           'tptax_ids'   :  [(6, 0, flight_vals['tptax_ids'])], 
                           })
                    flight_vals.update(ft_obj.onchange_FT_subTotal(cr, uid, [], flight_vals.get('inv_type',False),'all',flight_vals.get('a_basic',0), 0, flight_vals.get('a_servicechrg_perc',0), flight_vals.get('a_servicechrg',0),
                                0, flight_vals.get('a_markup',0), 0, 0, 0,0,0,0,0, 
                                flight_vals.get('a_tac_perc',0), 0, flight_vals.get('a_tac_select',False), flight_vals.get('a_tac_basic', False), flight_vals.get('a_tac_other', False), False, 
                                flight_vals.get('a_tac_perc1', 0), flight_vals.get('a_tac_basic1', False), flight_vals.get('a_tac_other1', False), False,
                                 flight_vals.get('a_tac_perc2', 0), flight_vals.get('a_tac_basic2',False), flight_vals.get('a_tac_other2',False), False
                              , flight_vals.get('tptax_basic', False), flight_vals.get('tptax_airtax', False), flight_vals.get('tptax_tac', False)
                              , flight_vals.get('tptax_tds',False), flight_vals.get('tptax_other', False), flight_vals.get('airtax_ids',[]), flight_vals.get('tptax_ids',[])
                              , 0, flight_vals.get('a_disc_select', False), flight_vals.get('a_disc_perc',0), flight_vals.get('a_disc_basic',False)
                              , flight_vals.get('a_disc_other', False), False, 
                              flight_vals.get('a_disc_perc1',0), flight_vals.get('a_disc_basic1', False)
                              , flight_vals.get('a_disc_other1', False), False, flight_vals.get('a_disc_perc2',0), flight_vals.get('a_disc_basic2',False)
                              , flight_vals.get('a_disc_other2', False), False,0,0,0,context=context)['value'])
                     
            flight_vals.update({
                                'flight_lines': lnvals_list
                                })
            ftvals_list.append((0, 0, flight_vals))
            print 'ftvals_list',ftvals_list
        if consul_id:
            if not inv_id:
                inv_id = self.create(cr, uid, {
                                               'user_id'        : False,
                                              'consultant_id'   : consul_id,
                                              'state'           :'quotation',
                                              'flight_ids'      : ftvals_list,
                                              'travel_type'     : service_type,
                                              'type'            : 'out_invoice',
                                              'company_id'      : company_id and company_id or False,
                                             },context={'type':'out_invoice'})
                self.button_reset_taxes(cr, uid, [inv_id], context) 
            else:
                cr.execute("delete from tr_invoice_flight where invoice_id = %s",(inv_id,))  # TODO: Check
                self.write(cr, uid, [inv_id], {'flight_ids': ftvals_list,
                                                    'travel_type': service_type,
                                                    'is_ticket': True,
                                                }) 
                self.button_reset_taxes(cr, uid, [inv_id], context)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if context == None: context = {}
        users_obj = self.pool.get('res.users')
        usid = users_obj.browse(cr, uid, uid)
        
        for case in self.browse(cr, uid, ids):
            if case.company_id.window_inv:
                win_inv = str(case.company_id.window_inv)
                if win_inv : 
                    cr.execute("select '" +datetime.today().strftime("%Y-%m-%d") +"'::date between i.date_invoice::date and i.date_invoice::date +'" + win_inv +"'::int from account_invoice i where i.id in (" +str(case.id) +") limit 1" )
                    invdt = cr.fetchone()
                    # Checking for the group user cannot validate if cl exceeds
                    if invdt and invdt[0] == False and not context.get('xxx',False):
                        if usid.tr_accounting and usid.tr_accounting not in ('acc_manager') and uid!=1:
                            if case.state in ('open','paid') and case.edit_invoice == False:
                                raise osv.except_osv(_('warning'),_("You cannot edit this record now. Please contact your accounts manager/branch head to get access."))
                                return False
                                
            if vals.get('lead_id') or vals.get('partner_id'): # To Call onchange
                vals.update(self.onchange_leadid(cr, uid, ids, vals.get('lead_id', case.lead_id.id), context=None)['value'])
                vals.update(self.onchange_partner_id(cr, uid, ids, case.type, vals.get('partner_id', case.partner_id.id),case.date_invoice
                                                 , case.payment_term and case.payment_term.id or False
                                                 , case.partner_bank_id and case.partner_bank_id.id or False
                                                 , case.company_id and case.company_id.id or False)['value'])
                
        result = super(account_invoice, self).write(cr, uid, ids, vals, context)
        
        for case in self.browse(cr, uid, ids):
            # [Update]: Ticket No. for LCC Airlines
            if case.travel_type in ('dom_flight', 'int_flight') and case.type == 'out_invoice':
                seq = 0
                for ft in case.flight_ids:
                    sctr = ft.flight_lines and ft.flight_lines[0]
                    lowcost_airln = sctr and sctr.airline_id and sctr.airline_id.lcc
                    if lowcost_airln:
                        arlncode = sctr and sctr.airline_id and sctr.airline_id.code or ''
                        if ft.pnr: 
                            tkno = str(ft.pnr) + arlncode + str(seq + 1).zfill(3) 
                            cr.execute("update tr_invoice_flight set ticket_no = '" + tkno + "' where id = " + str(ft.id))
                        seq +=1
                
        return result
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoices = self.read(cr, uid, ids, ['state', 'internal_number'], context=context)
        unlink_ids = []

        for t in invoices:
            if t['state'] not in ('quotation', 'cancel'):
                raise openerp.exceptions.Warning(_('You cannot delete an invoice which is not new or cancelled. You should refund it instead.'))
            elif t['internal_number']:
                raise openerp.exceptions.Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "New" state and modify its content, then re-confirm it.'))
            else:
                unlink_ids.append(t['id'])

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
class account_invoice_line(osv.osv): 
    _inherit = 'account.invoice.line'
    
    # Overridden:
    def _get_amount(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        
        dp = get_dp_precision(cr, uid, 'Account')
        
        # TODO: Currency roundoff
        
        for case in self.browse(cr, uid, ids):
            amt4tax = tax = 0.00 
            res[case.id] = {'price_subtotal':0.00, 'tax_base':0.00, 'subtotal':0.00, 'taxes': 0.00}
            taxes = tax_obj.compute_all(cr, uid, case.invoice_line_tax_id, case.price_unit, case.quantity, product=case.product_id, partner=case.invoice_id.partner_id)
            res[case.id]['price_subtotal'] = taxes['total']
            res[case.id]['subtotal'] = case.price_unit * case.quantity
            
            # Direct [Miscellaneous] Tax Calculation:
            if case.invoice_id: 
                inv_cur = case.invoice_id.currency_id.id
                inv_date = case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')
                
                if case.invoice_id.travel_type == 'direct':
                    
                    if case.tax_basic == True : amt4tax += case.basic * case.quantity
                    if case.tax_tac == True   : amt4tax += case.tac * case.quantity
                    if case.tax_tds == True   : amt4tax += case.tds * case.quantity
                    if case.tax_tds1 == True  : amt4tax += case.tds1 * case.quantity
                    if case.tax_mark == True  : amt4tax += case.markup * case.quantity
                    if case.tax_other == True : amt4tax += case.other * case.quantity
                    if case.tax_servicechrg == True: amt4tax += case.servicechrg * case.quantity
                    
                    for t in case.invoice_line_tax_id:
                        tax += round((amt4tax * t.amount), dp)
                    
                elif case.invoice_id.travel_type in ('dom_flight','int_flight'):
                    tax = cur_obj.compute(cr, uid, case.flight_id.currency_id.id, inv_cur, (case.flight_id and case.flight_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.flight_id.currency_id.id, inv_cur, (case.flight_id and case.flight_id.tax_base or 0), context={'date': inv_date})
                    
                elif case.invoice_id.travel_type in ('dom_hotel','int_hotel'):
                    tax = cur_obj.compute(cr, uid, case.hotel_id.currency_id.id, inv_cur, (case.hotel_id and case.hotel_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.hotel_id.currency_id.id, inv_cur, (case.hotel_id and case.hotel_id.tax_base or 0), context={'date': inv_date})
                                        
                elif case.invoice_id.travel_type == 'car':
                    tax = cur_obj.compute(cr, uid, case.car_id.currency_id.id, inv_cur, (case.car_id and case.car_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.car_id.currency_id.id, inv_cur, (case.car_id and case.car_id.tax_base or 0), context={'date': inv_date})
                                        
                elif case.invoice_id.travel_type == 'visa':
                    tax = cur_obj.compute(cr, uid, case.visa_id.currency_id.id, inv_cur, (case.visa_id and case.visa_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.visa_id.currency_id.id, inv_cur, (case.visa_id and case.visa_id.tax_base or 0), context={'date': inv_date})
                                        
                elif case.invoice_id.travel_type == 'railway':
                    tax = cur_obj.compute(cr, uid, case.rail_id.currency_id.id, inv_cur, (case.rail_id and case.rail_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.rail_id.currency_id.id, inv_cur, (case.rail_id and case.rail_id.tax_base or 0), context={'date': inv_date})
                                        
                elif case.invoice_id.travel_type == 'insurance':
                    tax = cur_obj.compute(cr, uid, case.ins_id.currency_id.id, inv_cur, (case.ins_id and case.ins_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.ins_id.currency_id.id, inv_cur, (case.ins_id and case.ins_id.tax_base or 0), context={'date': inv_date})
                                        
                elif case.invoice_id.travel_type == 'cruise':
                    tax = cur_obj.compute(cr, uid, case.cruise_id.currency_id.id, inv_cur, (case.cruise_id and case.cruise_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.cruise_id.currency_id.id, inv_cur, (case.cruise_id and case.cruise_id.tax_base or 0), context={'date': inv_date})
                                        
                elif case.invoice_id.travel_type == 'add_on':
                    tax = cur_obj.compute(cr, uid, case.addon_id.currency_id.id, inv_cur, (case.addon_id and case.addon_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.addon_id.currency_id.id, inv_cur, (case.addon_id and case.addon_id.tax_base or 0), context={'date': inv_date})
                                        
                elif case.invoice_id.travel_type == 'activity':
                    tax = cur_obj.compute(cr, uid, case.activity_id.currency_id.id, inv_cur, (case.activity_id and case.activity_id.taxes or 0), context={'date': inv_date})
                    amt4tax = cur_obj.compute(cr, uid, case.activity_id.currency_id.id, inv_cur, (case.activity_id and case.activity_id.tax_base or 0), context={'date': inv_date})
                        
                res[case.id]['taxes'] = tax
                res[case.id]['tax_base'] = amt4tax
                
                res[case.id]['price_subtotal'] = cur_obj.round(cr, uid, case.invoice_id.currency_id, res[case.id]['price_subtotal'])
                print "after:: ", res[case.id]['price_subtotal']
        return res

    _columns = {
                 # Overridden:
                'price_subtotal': fields.function(_get_amount, string='Amount', type="float",
                                                  digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                
                'tax_base': fields.function(_get_amount, string='Tax base', type="float",
                                                  digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                'taxes'   : fields.function(_get_amount, string='Taxes', type="float",
                                                  digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                
                'subtotal': fields.function(_get_amount, string='Subtotal', type="float",
                                                  digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                # New:
                'flight_id' : fields.many2one('tr.invoice.flight', 'Flight', ondelete="cascade"),
                'hotel_id'  : fields.many2one('tr.invoice.hotel', 'Hotel', ondelete="cascade"),
                'car_id'    : fields.many2one('tr.invoice.car', 'Transfers', ondelete="cascade"),
                'visa_id'   : fields.many2one('tr.invoice.visa', 'Visa', ondelete="cascade"),
                'rail_id'   : fields.many2one('tr.invoice.railway', 'Railway', ondelete="cascade"),
                'ins_id'    : fields.many2one('tr.invoice.insurance', 'Insurance', ondelete="cascade"),
                'cruise_id' : fields.many2one('tr.invoice.cruise', 'Cruise', ondelete="cascade"),
                'activity_id' : fields.many2one('tr.invoice.activity', 'Activity', ondelete="cascade"),
                'addon_id'    : fields.many2one('tr.invoice.addon', 'Addon', ondelete="cascade"),
                
                'service_type' : fields.selection(tr_config.TRAVEL_TYPES, 'Service Type'),
                'src_id'       : fields.many2one('account.invoice.line', 'Source Reference'),
                'tpartner_id'  : fields.many2one('res.partner', 'Travel Partner', domain=[('supplier', '=', 1)], ondelete='restrict'),
                
                'passenger': fields.char('Passenger', size=500),
                'basic'   : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'other'   : fields.float('Other', digits_compute=dp.get_precision('Account')),
                'tac'     : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'tds'     : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'tds1'    : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'markup'  : fields.float('Mark Up', digits_compute=dp.get_precision('Account')),
                'discount': fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'servicechrg'  : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'purchase_amt' : fields.float('Purchase Amount', digits_compute=dp.get_precision('Account')),
                
                'cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                'cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
     
                'tax_basic'   : fields.boolean('On Basic'),
                'tax_tac'     : fields.boolean('On TAC'),
                'tax_tds'     : fields.boolean('On TDS(T)'),
                'tax_tds1'    : fields.boolean('On TDS(D)'),
                'tax_mark'    : fields.boolean('On Mark Up'),
                'tax_other'   : fields.boolean('On Other'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                
                }
    
    def onchange_Misc_total(self, cr, uid, ids, quantity, basic, other, tac, tds, tds1, markup, servicechrg, discount, cancel_markup, cancel_charges, cancel_service, context=None):
        """ 
            Used    :: in Sale- Miscellaneous
            Returns :: Total 
        """
    
        res = {}
        subtot = (basic + other + tds1 + markup + servicechrg - discount - cancel_markup - cancel_charges - cancel_service)
        res['price_unit'] = subtot
        res['subtotal'] = subtot * quantity
        res['purchase_amt'] = (basic + other + tds - tac - cancel_charges) * quantity
        return {'value':res}
 
    # Inherited:
    def move_line_get_item(self, cr, uid, line, context=None):
        res = super(account_invoice_line, self).move_line_get_item(cr, uid, line, context)
        res['name'] = line.name
        return res
    
     
    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = []
        txres = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        sacc_obj = self.pool.get('tr.services.account') 
        if context is None: context = {}
        line_grouped = {}
         
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
         
        cmplist = {}
        saids = sacc_obj.search(cr, uid, [('name','=', inv.travel_type), ('company_id','=',inv.company_id.id)])
        if saids and saids[0]:
            sacc = sacc_obj.browse(cr, uid, saids[0])
            if sacc.tds_payable_id    : cmplist['tds'] = sacc.tds_payable_id.id
            if sacc.tds_receivable_id : cmplist['tds1'] = sacc.tds_receivable_id.id
            if sacc.tac_id            : cmplist['tac'] = sacc.tac_id.id
            if sacc.discount_id       : cmplist['discount'] = sacc.discount_id.id  
            if sacc.markup_id         : cmplist['markup'] = sacc.markup_id.id 
            if sacc.servicechrg_id    : cmplist['servicechrg'] = sacc.servicechrg_id.id
            if inv.type == 'out_refund' and sacc.cancel_service_id : cmplist['cancel_service'] = sacc.cancel_service_id.id
            if inv.type == 'out_refund' and sacc.cancel_markup_id  : cmplist['cancel_markup'] = sacc.cancel_markup_id.id
             
        cmpMap = {'tds': '[TDS(TAC)]', 'tds1': '[TDS(Discount)]', 'tac': '[TAC]', 'discount': '[Discount]'
                  , 'markup': '[Markup]', 'servicechrg': '[Service Charge]', 'cancel_service':'[Cancellation ServiceCharge]'
                  , 'cancel_markup': '[Cancel Markup]'}
        
        for line in inv.invoice_line:
            qty = inv.travel_type == 'direct' and line.quantity or 1
            
            # Entry: Supplier [Payable Account]
            val = {}
            val['type'] = 'dest'
            val['partner_id'] = line.tpartner_id.id or False
            val['price'] = line.purchase_amt
            val['price_unit'] = line.purchase_amt
            val['account_id'] = line.tpartner_id.property_account_payable.id or False
            val['name'] = line.name
            
            key = (val['account_id'], val['partner_id'])
            if not key in line_grouped:
                line_grouped[key] = val
            else:
                line_grouped[key]['price'] += val['price']
                line_grouped[key]['price_unit'] += val['price_unit']
                     
            # .................................................
            # Entry: Amount, for each configured account  
            for cmp in cmplist.keys():
                sign = cmp in ('tds', 'discount', 'cancel_service', 'cancel_markup') and -1 or 1
                if line[cmp] != 0:
                    val = {}
                    val['type'] = 'src'
                    val['partner_id'] = cmp in ('tds', 'tac') and line.tpartner_id.id or inv.partner_id.id
                    val['price'] = line[cmp] * qty * sign
                    val['price_unit'] = line[cmp] * qty * sign
                    val['account_id'] = cmplist[cmp]
                    val['name'] = cmpMap[cmp] + ' ' + str(line.name)
                     
                    key = (val['account_id'], val['partner_id'])
                    if not key in line_grouped:
                        line_grouped[key] = val
                    else:
                        line_grouped[key]['price'] += val['price']
                        line_grouped[key]['price_unit'] += val['price_unit']
                         
            # TODO:
            # need to check this
#             tax_code_found= False
#             for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,
#                     (line.tax_base),line.quantity, line.product_id,
#                     inv.partner_id)['taxes']:
#  
#                 if inv.type in ('out_invoice', 'in_invoice'):
#                     tax_code_id = tax['base_code_id']
#                     tax_amount = line.price_subtotal * tax['base_sign']
#                 else:
#                     tax_code_id = tax['ref_base_code_id']
#                     tax_amount = line.price_subtotal * tax['ref_base_sign']
#  
#                 if tax_code_found:
#                     if not tax_code_id:
#                         continue
#                     txres.append(self.move_line_get_item(cr, uid, line, context))
#                     txres[-1]['price'] = 0.0
#                     txres[-1]['account_analytic_id'] = False
#                 elif not tax_code_id:
#                     continue
#                 tax_code_found = True
#  
#                 txres[-1]['tax_code_id'] = tax_code_id
#                 txres[-1]['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax_amount, context={'date': inv.date_invoice})
                 
        res = line_grouped.values()
        res = res + txres
        return res
     
account_invoice_line()


class account_invoice_tax(osv.osv):
    _inherit = "account.invoice.tax"
    
    # Overridden: 
    def compute(self, cr, uid, invoice_id, context=None):
        """
            Computes Tax amount 
            Returns Consolidated Taxes
        """
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        dp = get_dp_precision(cr, uid, 'Account')
        
        invlines = []
        standard = False        
       
        if inv.travel_type in ('dom_flight', 'int_flight') : invlines = inv.flight_ids
        elif inv.travel_type in ('dom_hotel', 'int_hotel') : invlines = inv.hotel_ids
        elif inv.travel_type == 'insurance' : invlines = inv.insurance_ids
        elif inv.travel_type == 'visa'      : invlines = inv.visa_ids
        elif inv.travel_type == 'railway'   : invlines = inv.railway_ids
        elif inv.travel_type == 'cruise'    : invlines = inv.cruise_ids
        elif inv.travel_type == 'car'       : invlines = inv.car_ids
        elif inv.travel_type == 'activity'  : invlines = inv.activity_ids
        elif inv.travel_type == 'add_on'    : invlines = inv.addon_ids
             
        # Standard Invoice Line
        if not invlines:
            if inv.travel_type != 'direct':
                standard = False 
            else:
                standard = True
            
            invlines = inv.invoice_line
             
        for line in invlines:
            taxlines = []
            pu = 0.00
            qty = 1
                         
            if inv.travel_type != 'direct':  
               taxlines = line.tax_ids
                
            # Standard
            if not taxlines and standard: 
                taxlines = line.invoice_line_tax_id
                pu = line.price_unit
                qty = line.quantity
                 
            for tax in tax_obj.compute_all(cr, uid, taxlines, pu, qty, line.product_id, inv.partner_id)['taxes']:
                Base_amt = Tax_amt = 0.0
                 
                Base_amt = cur_obj.compute(cr, uid, line.currency_id.id, inv.currency_id.id, line.tax_base, context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                tx = tax_obj.browse(cr, uid, tax['id'])
                Tax_amt = round((Base_amt * tx.amount), dp) 
                     
#                 # For Standard Invoice 
#                 if standard:
#                     Tax_amt = tax['amount']
#                     Base_amt = cur_obj.round(cr, uid, cur, tax['price_unit'] * qty)
                     
                val = {}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = Tax_amt
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = Base_amt
                 
                if inv.type in ('out_invoice', 'in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']
 
                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']
                     
                 
        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped
    
account_invoice_tax()    


class tr_invoice_option(osv.osv):
    _inherit = "tr.invoice.option"
    _columns = {
                'name': fields.char('Name', size=200),
                'invoice_id'  : fields.many2one('account.invoice', 'Invoice', ondelete='cascade'),
                
                'insurance_ids' : fields.one2many('tr.invoice.insurance', 'opt_id', 'Insurance'),
                'flight_ids'    : fields.one2many('tr.invoice.flight', 'opt_id', 'Flight'),
                'visa_ids'      : fields.one2many('tr.invoice.visa', 'opt_id', 'Visa'),
                'cruise_ids'    : fields.one2many('tr.invoice.cruise', 'opt_id', 'Cruise'),
                'car_ids'       : fields.one2many('tr.invoice.car', 'opt_id', 'Transfers'),
                'hotel_ids'     : fields.one2many('tr.invoice.hotel', 'opt_id', 'Hotel'),
                'activity_ids'  : fields.one2many('tr.invoice.activity', 'opt_id', 'Activity'),
                'addon_ids'     : fields.one2many('tr.invoice.addon', 'opt_id', 'Add-on'),
                
                'opt_lines' : fields.one2many('tr.invoice.option.lines', 'opt_id', 'Options Summary'),
                }
    
    def option_line_create(self, cr, uid, ids, chkwhich, context=None):
        OPTln_obj = self.pool.get('tr.invoice.option.lines')
        
        for case in self.browse(cr, uid, ids):
            for typ in ['adult', 'twin', 'triple', 'extra', 'cwb', 'cnb', 'infant']:
                vals = {'type': typ}
             
                if chkwhich == 'to_create':
                    vals.update({
                                 'opt_id': case.id,
                                 })
                    OPTln_obj.create(cr, uid, vals, context=context)
                else:
                    olids = OPTln_obj.search(cr, uid, [('opt_id','=', case.id), ('type','=', typ)])
                    OPTln_obj.write(cr, uid, olids, vals, context=context)
                
#             self.write(cr, uid, ids, context)
        return True
        
    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_option, self).create(cr, uid, vals, context)
        self.option_line_create(cr, uid, [result], 'to_create', context)
        return result
    
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_option, self).write(cr, uid, ids, vals, context)
        self.option_line_create(cr, uid, ids, 'to_write', context)
        return result
    
class tr_invoice_option_lines(osv.osv):
    _name = "tr.invoice.option.lines"
    _description = "Option Lines/ Summary"
    
    def _calc_optionAmount(self, cr, uid, ids, context=None):
        res = {}
        
        return res
    
    def _get_optionAmount(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        
        FT_obj = self.pool.get('tr.invoice.flight')
        
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'flight_cost': 0.00, 'hotel_cost': 0.00, 'car_cost': 0.00,
                            'cruise_cost': 0.00, 'activity_cost': 0.00, 'addon_cost': 0.00,
                            'visa_cost': 0.00, 'ins_cost': 0.00, 'opt_total': 0.00}
            
            if case.type == 'infant': paxtyp = 'infant'
            elif case.type in ('cwb', 'cnb'): paxtyp = 'child'
            else: paxtyp = 'adult'
            
            if case.type == 'infant': paxtyp1 = 'infant'
            elif case.type in ('cwb', 'cnb'): paxtyp1 = 'child'
            elif case.type == 'extra': paxtyp1 = 'extra'
            else: paxtyp1 = 'adult'
                
            if case.opt_id:
                # Flight:    
                ftids = FT_obj.search(cr, uid, [('pax_type','=', paxtyp), ('opt_id', '=', case.opt_id.id)])
                for f in FT_obj.browse(cr, uid, ftids):
                    res[case.id]['flight_cost'] += f.a_total
                 
                # Hotel:
                for h in case.opt_id.hotel_ids:
                    if case.type == 'adult'   : res[case.id]['hotel_cost'] += h.a_rate
                    elif case.type == 'twin'  : res[case.id]['hotel_cost'] += h.tn_rate
                    elif case.type == 'triple': res[case.id]['hotel_cost'] += h.t3_rate
                    elif case.type == 'extra' : res[case.id]['hotel_cost'] += h.e_rate
                    elif case.type == 'cwb'   : res[case.id]['hotel_cost'] += h.c_rate
                    elif case.type == 'cnb'   : res[case.id]['hotel_cost'] += h.cn_rate
                    elif case.type == 'infant': res[case.id]['hotel_cost'] += h.i_rate
                    
                # Transfers:
                for c in case.opt_id.car_ids:
                    if paxtyp1 == 'adult'   : res[case.id]['car_cost'] += c.a_rate
                    elif paxtyp1 == 'child' : res[case.id]['car_cost'] += c.c_rate
                    elif paxtyp1 == 'extra' : res[case.id]['car_cost'] += c.e_rate
                    elif paxtyp1 == 'infant': res[case.id]['car_cost'] += c.i_rate
                    
                # Cruise:
                for c in case.opt_id.cruise_ids:
                    if paxtyp1 == 'adult'   : res[case.id]['cruise_cost'] += c.a_subtotal
                    elif paxtyp1 == 'child' : res[case.id]['cruise_cost'] += c.c_subtotal
                    elif paxtyp1 == 'extra' : res[case.id]['cruise_cost'] += c.e_subtotal
                    elif paxtyp1 == 'infant': res[case.id]['cruise_cost'] += c.i_subtotal
                   
                # Activity: 
                for a in case.opt_id.activity_ids:
                    if paxtyp == 'adult'   : res[case.id]['activity_cost'] += a.a_subtotal
                    elif paxtyp == 'child' : res[case.id]['activity_cost'] += a.c_subtotal
                    elif paxtyp == 'infant': res[case.id]['activity_cost'] += a.i_subtotal
                    
                # Addon:
                for a in case.opt_id.addon_ids:
                    if paxtyp == 'adult'   : res[case.id]['addon_cost'] += a.a_subtotal
                    elif paxtyp == 'child' : res[case.id]['addon_cost'] += a.c_subtotal
                    elif paxtyp == 'infant': res[case.id]['addon_cost'] += a.i_subtotal
                    
                # Visa:
                for v in case.opt_id.visa_ids:
                    if paxtyp == 'adult'   : res[case.id]['visa_cost'] += v.a_rate
                    elif paxtyp == 'child' : res[case.id]['visa_cost'] += v.c_rate
                    elif paxtyp == 'infant': res[case.id]['visa_cost'] += v.i_rate
                    
                # Insurance:
                for i in case.opt_id.insurance_ids:
                    if paxtyp == 'adult': res[case.id]['ins_cost'] += i.subtotal
                    
            res[case.id]['opt_total'] = (res[case.id]['flight_cost'] + res[case.id]['hotel_cost']
                                         + res[case.id]['car_cost'] + res[case.id]['cruise_cost'] 
                                         + res[case.id]['activity_cost'] + res[case.id]['addon_cost']
                                         + res[case.id]['visa_cost'] + res[case.id]['ins_cost']
                                         + case.add_markup + case.add_servicechrg - case.add_discount)
        return res
    
    _columns = {
                'opt_id'  : fields.many2one('tr.invoice.option', 'Option', ondelete='cascade'),
                'type'    : fields.selection([('adult','Adult (S)'), ('twin','Adult (D)'), ('triple','Adult (T)')
                                            , ('extra','Extra'), ('cwb','CWB'),('cnb','CNB')
                                            , ('infant','Infant')],'Pax Type'),
                'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
                
                'flight_cost'  : fields.function(_get_optionAmount, string='Flight', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'hotel_cost'   : fields.function(_get_optionAmount, string='Hotel', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'car_cost'     : fields.function(_get_optionAmount, string='Transfer', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'cruise_cost'  : fields.function(_get_optionAmount, string='Cruise', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'activity_cost': fields.function(_get_optionAmount, string='Activities', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'addon_cost'   : fields.function(_get_optionAmount, string='Add-On', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'visa_cost'    : fields.function(_get_optionAmount, string='Visa', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'ins_cost'     : fields.function(_get_optionAmount, string='Insurance', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'opt_total'    : fields.function(_get_optionAmount, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                'add_markup'      : fields.float('Add. Markup', digits_compute=dp.get_precision('Account')),
                'add_servicechrg' : fields.float('Add. Service Charge', digits_compute=dp.get_precision('Account')),
                'add_discount'    : fields.float('Add. Discount', digits_compute=dp.get_precision('Account')),
                }
    
      
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
