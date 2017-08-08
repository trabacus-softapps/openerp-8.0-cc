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
import openerp.addons.decimal_precision as dp

from dateutil import parser
import time
# TODO:
# Tax Base: not required remove it




def get_dp_precision(cr, uid, application):
    cr.execute('select digits from decimal_precision where name=%s', (application,))
    res = cr.fetchone()
    return res[0] if res else 2

class tr_invoice_insurance(osv.osv):
    _name = 'tr.invoice.insurance' 
    _description = "Invoice - Insurance"
    
    def calc_INS_total(self, cr, uid, id, inv_type, context=None):   
        res = {}
        tpamt4tax = tptax = 0.00
        if context == None: context = {}
        ctx = context.copy()
        ctx['calledfrm'] = 'func'
        
        
        case = self.browse(cr, uid, id)
        inv_type = inv_type and inv_type or case.inv_type
        res = self.onchange_INS_Total(cr, uid, [id], inv_type, 'all', case.no_policy, case.basic, case.markup_perc, case.markup, case.tac_perc, case.tac
                                      , case.tds_perc, case.tds, case.tds1_perc, case.tds1, case.servicechrg_perc, case.servicechrg, case.discount
                                      , case.cancel_charges, case.cancel_markup, case.cancel_service
                                      , case.tptax_basic, case.tptax_tac, case.tptax_tds, case.tptax_ids, context=ctx)['value']
      
        res['tac'] = case.tac * case.no_policy
        res['tds'] = case.tds * case.no_policy
        res['tds1'] = case.tds1 * case.no_policy
        res['basic'] = case.basic * case.no_policy
        res['other'] = res.get('tptax',0) * case.no_policy
        res['discount'] = case.discount * case.no_policy
        res['markup'] = case.markup * case.no_policy
        res['servicechrg'] = case.servicechrg * case.no_policy
        res['cancel_markup'] = case.cancel_markup * case.no_policy
        res['cancel_charges'] = case.cancel_charges * case.no_policy
        res['cancel_service'] = case.cancel_service * case.no_policy
        
        return res
    
    def _get_AllTotal(self, cr, uid, ids, field_name, arg, context):
        
        res = {}
        
        for case in self.browse(cr, uid, ids):
            
            res[case.id] = {'subtotal':0.00, 'tptax':0.00, 'tax_base':0.00, 'taxes':0.00, 'total':0.00}
            
            getamt = self.calc_INS_total(cr, uid, case.id, case.inv_type)
            res[case.id]['subtotal'] = getamt.get('subtotal',0)
            res[case.id]['po_subtotal'] = getamt.get('po_subtotal',0)
            res[case.id]['tptax'] = getamt.get('tptax',0)
            chkd_amt = TAX_amt = 0.00
              
            if case.tax_basic: chkd_amt += case.basic * case.no_policy
            if case.tax_tac: chkd_amt += case.tac * case.no_policy
            if case.tax_tds: chkd_amt += case.tds * case.no_policy
            if case.tax_tds1: chkd_amt += case.tds1 * case.no_policy
            if case.tax_mark: chkd_amt += case.markup * case.no_policy
            if case.tax_tptax: chkd_amt += getamt.get('tptax',0) * case.no_policy
            if case.tax_servicechrg: chkd_amt += case.servicechrg * case.no_policy
                    
            for t in case.tax_ids:
                TAX_amt += round((chkd_amt * t.amount),2) 
                  
            res[case.id]['tax_base'] = chkd_amt  
            res[case.id]['taxes'] = TAX_amt
            res[case.id]['total'] = (res[case.id]['subtotal'] + TAX_amt)
        return res
    
    def _default_account_id(self, cr, uid, context=None):
        if context is None: context = {}
        if context.get('type') in ('out_invoice','out_refund'):
            prop = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
        else:
            prop = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category', context=context)
        return prop and prop.id or False
    
    
    def _get_currency(self, cr, uid, ctx):
        comp = self.pool.get('res.users').browse(cr, uid, uid).company_id
        if not comp:
            comp_id = self.pool.get('res.company').search(cr, uid, [])[0]
            comp = self.pool.get('res.company').browse(cr, uid, comp_id)
        return comp.currency_id.id
    
    _columns = {
                
                'invoice_id'  : fields.many2one('account.invoice', 'Invoice', ondelete='cascade'), 
                'inv_type'    : fields.related('invoice_id', 'type', string='Invoice type', type='selection'
                                           , selection=[('out_invoice','Customer Invoice'),
                                            ('in_invoice','Supplier Invoice'),
                                            ('out_refund','Customer Refund'),
                                            ('in_refund','Supplier Refund')], store=True), 
                'opt_id'  : fields.many2one('tr.invoice.option', 'Option', ondelete='cascade'),
                
                'product_id'  : fields.many2one('product.product', 'Product', domain="[('travel_type','=','insurance')]", ondelete='restrict'),
                'name'        : fields.char('Description', size=30, required=True), 
                'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict'), 
                'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                , help="The income or expense account related to the selected product."),
                'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
                'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
                'src_id'      : fields.many2one('tr.invoice.insurance', 'Source Reference'),
                
                'passenger'   : fields.char('Passenger', size=500),
                'no_policy'   : fields.integer('No of Policies'), 
                'basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'discount'    : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'tac_perc'    : fields.float('TAC (%)', digits_compute=dp.get_precision('Account')),
                'tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'markup_perc' : fields.float('Markup (%)', digits_compute=dp.get_precision('Account')),
                'markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'tds_perc'    : fields.float('TDS(T) (%)', digits_compute=dp.get_precision('Account')),
                'tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'tds1_perc'   : fields.float('TDS(D) (%)', digits_compute=dp.get_precision('Account')),
                'tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'cancel_markup'   : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'cancel_charges'  : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'cancel_service'  : fields.float('Cancel Service Charges', digits_compute=dp.get_precision('Account')),
                
                'servicechrg' : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'servicechrg_perc' : fields.float('Service Charge (%)', digits_compute=dp.get_precision('Account')),
                
                'subtotal'  : fields.function(_get_AllTotal, type='float', string='SubTotal', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'tptax'     : fields.function(_get_AllTotal, type='float', string='T.P.Tax', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),  
                'tax_base'  : fields.function(_get_AllTotal, type='float', string='Taxes Base', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'taxes'     : fields.function(_get_AllTotal, type='float', string='Taxes', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'total'     : fields.function(_get_AllTotal, type='float', string='Total', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'po_subtotal'  : fields.function(_get_AllTotal, type='float', string='PO SubTotal', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                'tptax_basic' : fields.boolean('On Basic'),
                'tptax_tac'   : fields.boolean('On TAC'),
                'tptax_tds'   : fields.boolean('On TDS(T)'),
                'tptax_ids'   : fields.many2many('account.tax', 'insurance_tptax_rel', 'ins_id', 'tax_id', 'T.P. Taxes'),
                
                'tax_basic'      : fields.boolean('On Basic'),
                'tax_tac'     : fields.boolean('On TAC'),
                'tax_tds'     : fields.boolean('On TDS(T)'),
                'tax_tds1'    : fields.boolean('On TDS(D)'),
                'tax_mark'    : fields.boolean('On Mark Up'),
                'tax_tptax'   : fields.boolean('On T.P. Tax'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                'tax_ids'   : fields.many2many('account.tax', 'insurance_tax_rel', 'ins_id', 'tax_id', 'Taxes'),
                 
                'age_criteria': fields.selection([('below_40', '6 Mts to 40 Yrs'), ('frm40_60yrs', '41 to 60 Yrs'),
                                                  ('frm61_70yrs','61 to 71 Yrs'),('above_70', 'Above 70 Yrs')], "Age Criteria"),
                'remarks': fields.text('Remarks'),
                
        }  
    _defaults = {
                 'no_policy': 1,
                 'age_criteria': 'below_40',
                 'account_id': _default_account_id,
                 'inv_type' : lambda self,cr,uid,c: c.get('type', ''),
                 'currency_id': _get_currency
                 }
    
    def onchange_product(self, cr, uid, ids, product_id):        
        res = {}  
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id)
            
            user = self.pool.get('res.users').browse(cr, uid, uid)
            taxon_obj = self.pool.get('tr.prod.taxon')
            taxon_ids = taxon_obj.search(cr, uid, [('product_id','=',product_id), ('company_id','=',user.company_id.id)], limit = 1)
            taxon_vals = taxon_obj.read(cr, uid, taxon_ids)
            taxon_vals = taxon_vals and taxon_vals[0] or {}
            if taxon_vals:
                del taxon_vals['id']
                del taxon_vals['product_id']
                del taxon_vals['company_id']
                
            res = {'name' : prod.name_template,
                 'tax_ids': map(lambda x: x.id, prod.taxes_id),
                 'currency_id': prod.currency_id.id,
#                  'tax_tac': prod.tax_tac and prod.tax_tac[0] or {},
#                  'tax_servicechrg': prod.tax_servicechrg and prod.tax_servicechrg[0] or {},
                }
            res.update(taxon_vals)  
            
        return {'value':res}
  
    
    # Individual
    def onchange_INS_Total(self, cr, uid, ids, inv_type, calledby, no_policy, basic, markup_perc, markup, tac_perc, tac, tds_perc, tds, tds1_perc, tds1
                           , servicechrg_perc, servicechrg, discount, cancel_charges, cancel_markup, cancel_service
                           , tptax_basic, tptax_tac, tptax_tds, tptax_ids, is_sc=False, context=None):  
        """ 
            Method  :: for Individual Service
            Used    :: Invoice
            Returns :: Subtotal
        """        
        res = {} 
        dp = get_dp_precision(cr, uid, 'Account')
        tptax = tpamt4tax = 0.00
        
        if calledby == 'all':
            if tac_perc:
                tac = round(((tac_perc * basic) / 100.00), dp)
                res['tac'] = tac
            
            if markup_perc:
                markup = round(((markup_perc * basic) / 100.00), dp)
                res['markup'] = markup 
                
            if tds_perc:
                tds = round(((tds_perc * tac) / 100.00), dp)
                res['tds'] = tds
            
            if tds1_perc:
                tds1 = round(((tds1_perc * discount) / 100.00), dp)
                res['tds1'] = tds1  
            
        if tptax_basic == True : tpamt4tax += basic
        if tptax_tac == True   : tpamt4tax += tac
        if tptax_tds == True   : tpamt4tax += tds
        
        if context and context.get('calledfrm', False) == 'func':
            for ttx in tptax_ids:
                tptax += round((tpamt4tax * ttx.amount),dp)
        else:
            for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
                tptax += round((tpamt4tax * ttx['amount']),dp)
            
        res['tptax'] = tptax
        
        if inv_type in ('out_invoice', 'out_refund'):
            subtot = (basic + tptax + markup + tds1 - discount)
            if not is_sc and servicechrg_perc:
                servicechrg = round(((servicechrg_perc * subtot) / 100.00), dp)
                res['servicechrg'] = servicechrg
            subtot = (subtot + servicechrg - cancel_charges - cancel_markup - cancel_service) * no_policy
            res['po_subtotal'] = (basic + tptax - tac + tds - cancel_charges) * no_policy
        else:
            subtot = (basic + tptax - tac + tds - cancel_charges) * no_policy
            
        res['subtotal'] = subtot
        return {'value':res}
    
    def invoice_line_create(self, cr, uid, ids, chkwhich, context=None):
        """
            Create / Update Invoice Line in accordance 
            with Service Lines...
        """
        if context is None: context = {}
        inv_obj = self.pool.get('account.invoice')
        invln_obj = self.pool.get('account.invoice.line')
        cur_obj = self.pool.get('res.currency')
        
        for case in self.browse(cr, uid, ids):
            
            nartn = 'Insurance : ' + str(case.name) + ", " + str(case.passenger)
            getamt = self.calc_INS_total(cr, uid, case.id, case.inv_type)
            subtot = getamt.get('subtotal',0)
          
            inv_currency = case.invoice_id.currency_id.id
            subtot = cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, subtot, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                
            vals = {
                'name'       : nartn,
                'passenger'  : case.passenger,
                'tpartner_id': case.tpartner_id.id,
                'product_id' : case.product_id.id or False,
                'origin'     : case.invoice_id.name,
                'account_id' : case.account_id.id,
                'account_analytic_id' : case.invoice_id and case.invoice_id.account_analytic_id and case.invoice_id.account_analytic_id.id or False,                'currency_id': case.currency_id.id,
                'currency_id': case.currency_id.id,
                'price_unit' : subtot,
                'quantity'   : 1,
                'price_subtotal': subtot,
                'basic'   : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('basic',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'other'   : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('other',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'tac'     : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('tac',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'tds'     : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('tds',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'tds1'    : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('tds1',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'markup'  : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('markup',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'discount'      : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('discount',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'servicechrg'   : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('servicechrg',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'cancel_markup' : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('cancel_markup',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'cancel_charges': cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('cancel_charges',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'cancel_service': cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('cancel_service',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'purchase_amt'  : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('po_subtotal',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                    }
            
            if chkwhich == 'to_create':
                vals.update({
                             'ins_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('ins_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True
     
    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_insurance, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
     
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_insurance, self).write(cr, uid, ids, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result
    
tr_invoice_insurance()



    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: