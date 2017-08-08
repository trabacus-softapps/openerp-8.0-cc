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
import time

def get_dp_precision(cr, uid, application):
    cr.execute('select digits from decimal_precision where name=%s', (application,))
    res = cr.fetchone()
    return res[0] if res else 2

class tr_invoice_visa(osv.osv):
    _name = 'tr.invoice.visa'
    _description = 'Invoice - Visa'
    
    
    def calc_VISA_total(self, cr, uid, id, inv_type, context=None):   
        res = {}
        if context == None: context = {}
        ctx = context.copy()
        ctx['calledfrm'] = 'func'
        
        case = self.browse(cr, uid, id)
        inv_type = inv_type and inv_type or case.inv_type
         
        res = self.onchange_VISA_onTPtax(cr, uid, [case.id], inv_type
                                         , case.no_adult, case.a_basic, case.a_vfs, case.a_courier, case.a_dd, case.a_other, case.a_markup_perc, case.a_markup
                                         , case.a_tac_perc, case.a_tac, case.a_tds_perc, case.a_tds, case.a_tds1_perc, case.a_tds1, case.a_servicechrg_perc, case.a_servicechrg
                                         , case.a_tp_servicechrg, case.a_discount, case.a_cancel_markup, case.a_cancel_charges, case.a_cancel_service
                                         , case.no_child, case.c_basic, case.c_vfs, case.c_courier, case.c_dd, case.c_other, case.c_markup_perc, case.c_markup
                                         , case.c_tac_perc, case.c_tac, case.c_tds_perc, case.c_tds, case.c_tds1_perc, case.c_tds1, case.c_servicechrg_perc, case.c_servicechrg
                                         , case.c_tp_servicechrg, case.c_discount, case.c_cancel_markup, case.c_cancel_charges, case.c_cancel_service
                                         , case.no_infant, case.i_basic, case.i_vfs, case.i_courier, case.i_dd, case.i_other, case.i_markup_perc, case.i_markup
                                         , case.i_tac_perc, case.i_tac, case.i_tds_perc, case.i_tds, case.i_tds1_perc, case.i_tds1, case.i_servicechrg_perc, case.i_servicechrg
                                         , case.i_tp_servicechrg, case.i_discount, case.i_cancel_markup, case.i_cancel_charges, case.i_cancel_service
                                         , case.tptax_basic, case.tptax_courier, case.tptax_vfs, case.tptax_dd, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_tpservicechrg, case.tptax_ids, context=ctx)['value']
                        
        res['subtotal'] = res.get('a_rate',0) + res.get('c_rate',0) + res.get('i_rate',0)
        res['po_subtotal'] = res.get('a_po_rate',0) + res.get('c_po_rate',0) + res.get('i_po_rate',0)
        res['tac'] = (case.a_tac * case.no_adult) + (case.c_tac * case.no_child) + (case.i_tac * case.no_infant)
        res['tds'] = (case.a_tds * case.no_adult) + (case.c_tds * case.no_child) + (case.i_tds * case.no_infant)
        res['tds1'] = (case.a_tds1 * case.no_adult) + (case.c_tds1 * case.no_child) + (case.i_tds1 * case.no_infant)
        res['basic'] = (case.a_basic * case.no_adult) + (case.c_basic * case.no_child) + (case.i_basic * case.no_infant)
        res['discount'] = (case.a_discount * case.no_adult) + (case.c_discount * case.no_child) + (case.i_discount * case.no_infant)
        res['markup'] = ((case.a_markup * case.no_adult) + (case.c_markup * case.no_child) + (case.i_markup * case.no_infant))
        res['servicechrg'] = ((case.a_servicechrg + case.a_tp_servicechrg) * case.no_adult) \
                        + ((case.c_servicechrg + case.c_tp_servicechrg) * case.no_child) \
                        + ((case.i_servicechrg + case.i_tp_servicechrg) * case.no_infant)
                        
        res['other'] =  ((case.a_vfs + case.a_courier + case.a_dd + case.a_other + res.get('a_tptax',0)) * case.no_adult) \
                        + ((case.c_vfs + case.c_courier + case.c_dd + case.c_other + res.get('c_tptax',0)) * case.no_child) \
                        + ((case.i_vfs + case.i_courier + case.i_dd + case.i_other + res.get('i_tptax',0)) * case.no_infant)
        res['cancel_markup'] = ((case.a_cancel_markup * case.no_adult) + (case.c_cancel_markup * case.no_child) + (case.i_cancel_markup * case.no_infant))
        res['cancel_charges'] = ((case.a_cancel_charges * case.no_adult) + (case.c_cancel_charges * case.no_child) + (case.i_cancel_charges * case.no_infant))
        res['cancel_service'] = ((case.a_cancel_service * case.no_adult) + (case.c_cancel_service * case.no_child) + (case.i_cancel_service * case.no_infant))
        # TODO:
        # Bring TAX calculation & Optimize
        return res
    
    def _get_all_total(self, cr, uid, ids, field_name, arg, context):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        
        for case in self.browse(cr, uid, ids):
            
            getamt = self.calc_VISA_total(cr, uid, case.id, case.inv_type, context)
            res[case.id] = {
                            'a_tptax': getamt.get('a_tptax', 0), 'c_tptax': getamt.get('c_tptax', 0), 'i_tptax': getamt.get('i_tptax', 0),
                            'a_rate': getamt.get('a_rate', 0), 'c_rate': getamt.get('c_rate', 0), 'i_rate': getamt.get('i_rate', 0)
                            }
            res[case.id]['subtotal'] = getamt.get('subtotal',0)
            res[case.id]['po_subtotal'] = getamt.get('po_subtotal',0)
            res[case.id]['basicother'] = getamt.get('subtotal',0)
            
            def _calc_tax(case, basic, courier, vfs, dd, other, tac, tds, tds1, markup, tptax, servicechrg):
                amt4tax = tx = 0.00
                if case.tax_basic == True: amt4tax += basic
                if case.tax_vfs == True: amt4tax += vfs
                if case.tax_dd == True: amt4tax += dd
                if case.tax_courier == True: amt4tax += courier
                if case.tax_tac == True: amt4tax += tac
                if case.tax_tds == True: amt4tax += tds
                if case.tax_tds1 == True: amt4tax += tds1
                if case.tax_mark == True: amt4tax += markup
                if case.tax_other == True: amt4tax += other
                if case.tax_tptax == True: amt4tax += tptax
                if case.tax_servicechrg == True: amt4tax += servicechrg
             
                for t in case.tax_ids:
                    tx += round((amt4tax * t.amount), dp)
                return {'amt4tx':amt4tax, 'tax':tx}
            
            atx = _calc_tax(case, case.a_basic, case.a_courier, case.a_vfs, case.a_dd, case.a_other, case.a_tac, case.a_tds, case.a_tds1, case.a_markup, getamt.get('a_tptax', 0), case.a_servicechrg)
            ctx = _calc_tax(case, case.c_basic, case.c_courier, case.c_vfs, case.c_dd, case.c_other, case.c_tac, case.c_tds, case.c_tds1, case.c_markup, getamt.get('c_tptax', 0), case.c_servicechrg)
            itx = _calc_tax(case, case.i_basic, case.i_courier, case.i_vfs, case.i_dd, case.i_other, case.i_tac, case.i_tds, case.i_tds1, case.i_markup, getamt.get('i_tptax', 0), case.i_servicechrg)
             
            res[case.id].update({'a_tax': atx['tax'], 'c_tax': ctx['tax'], 'i_tax': itx['tax'] 
                            , 'taxes' : (atx['tax'] + ctx['tax'] + itx['tax'])
                            , 'tax_base' : (atx['amt4tx'] + ctx['amt4tx'] + itx['amt4tx'])
                            , 'tac'      : getamt.get('tac',0)
                            , 'markup'   : getamt.get('markup',0)
                            , 'servicechrg'  : getamt.get('servicechrg',0)
                            })
            res[case.id]['total'] = getamt.get('subtotal',0) + res[case.id]['taxes']
        return res
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(tr_invoice_visa, self).default_get(cr, uid, fields, context=context)
        if context == None: context = {}
        
        if context.get('travel_type','') == 'package':
            res.update({
                     'no_child' : 1,
                     'no_infant': 1})
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
                 
                'product_id'  : fields.many2one('product.product', 'Product', ondelete='restrict', domain=[('travel_type','=','visa')]), 
                'name'        : fields.char('Description', size=100, required=True),
                'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict'), 
                'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                    , help="The income or expense account related to the selected product."),
                'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
                'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
                'src_id'      : fields.many2one('tr.invoice.visa', 'Source Reference'),
                
                'valid_from' : fields.date('Valid From'),
                'valid_to'   : fields.date('Valid To') ,
                'pickup_date'  : fields.date('Visa Pick Up'),
                'delivery_date': fields.date('Visa Delivery'),
                'passenger'    : fields.char('Passenger', size=500),
                
                 # Adult
                'no_adult'    : fields.integer('No. of Adults'),
                'a_basic'     : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'a_vfs'       : fields.float('VFS', digits_compute=dp.get_precision('Account')), 
                'a_dd'        : fields.float('DD', digits_compute=dp.get_precision('Account')),
                'a_courier'   : fields.float('Courier', digits_compute=dp.get_precision('Account')),
                'a_other'     : fields.float('Other Charges', digits_compute=dp.get_precision('Account')),
                'a_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'a_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'a_tds_perc'  : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'a_tds'       : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'a_tds1_perc' : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'a_tds1'      : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'a_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'a_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'a_servicechrg'     : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'a_servicechrg_perc': fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'a_tp_servicechrg'  : fields.float('T.P. Service Charge', digits_compute=dp.get_precision('Account')),
                'a_discount'        : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'a_cancel_markup'   : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'a_cancel_charges'  : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'a_cancel_service'  : fields.float('Cancel Service Charges', digits_compute=dp.get_precision('Account')),
                'a_tptax'     : fields.function(_get_all_total, string='Adult T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_rate'      : fields.function(_get_all_total, string='Adult Rate', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_tax'       : fields.function(_get_all_total, string='Adult Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_total'     : fields.function(_get_all_total, string='Adult Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                
                 # Child
                'no_child' : fields.integer('No. of Children'),
                'c_basic'  : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'c_vfs'    : fields.float('VFS', digits_compute=dp.get_precision('Account')), 
                'c_dd'     : fields.float('DD', digits_compute=dp.get_precision('Account')),
                'c_courier'   : fields.float('Courier', digits_compute=dp.get_precision('Account')),
                'c_other'     : fields.float('Other Charges', digits_compute=dp.get_precision('Account')),
                'c_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'c_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'c_tds_perc'  : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'c_tds'       : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'c_tds1_perc' : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'c_tds1'      : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'c_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'c_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'c_servicechrg'     : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'c_servicechrg_perc': fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'c_tp_servicechrg'  : fields.float('T.P. Service Charge', digits_compute=dp.get_precision('Account')),
                'c_discount'        : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'c_cancel_markup'   : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'c_cancel_charges'  : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'c_cancel_service'  : fields.float('Cancel Service Charges', digits_compute=dp.get_precision('Account')),
                'c_tptax'   : fields.function(_get_all_total, string='Child T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_rate'    : fields.function(_get_all_total, string='Child Rate', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_tax'     : fields.function(_get_all_total, string='Child Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_total'   : fields.function(_get_all_total, string='Child Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                
                 # Infant
                'no_infant' : fields.integer('No. of Infants'),
                'i_basic'   : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'i_vfs'     : fields.float('VFS', digits_compute=dp.get_precision('Account')), 
                'i_dd'      : fields.float('DD', digits_compute=dp.get_precision('Account')),
                'i_courier'   : fields.float('Courier', digits_compute=dp.get_precision('Account')),
                'i_other'     : fields.float('Other Charges', digits_compute=dp.get_precision('Account')),
                'i_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'i_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'i_tds_perc'  : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'i_tds'       : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'i_tds1_perc' : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'i_tds1'      : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'i_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'i_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'i_servicechrg'     : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'i_servicechrg_perc': fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'i_tp_servicechrg'  : fields.float('T.P. Service Charge', digits_compute=dp.get_precision('Account')),
                'i_discount'        : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'i_cancel_markup'   : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'i_cancel_charges'  : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'i_cancel_service'  : fields.float('Cancel Service Charges', digits_compute=dp.get_precision('Account')),
                'i_tptax'   : fields.function(_get_all_total, string='Infant T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_rate'    : fields.function(_get_all_total, string='Infant Rate', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_tax'     : fields.function(_get_all_total, string='Infant Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_total'   : fields.function(_get_all_total, string='Infant Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                
                'tptax_basic'  : fields.boolean('On Basic'),
                'tptax_other'  : fields.boolean('On Other'),
                'tptax_vfs'    : fields.boolean('On VFS'),
                'tptax_dd'     : fields.boolean('On DD'),
                'tptax_tac'    : fields.boolean('On TAC'),
                'tptax_tds'    : fields.boolean('On TDS(T)'),
                'tptax_courier': fields.boolean('On Courier'),
                'tptax_tpservicechrg' : fields.boolean('On T.P. Service Charge'),
                'tptax_ids'    : fields.many2many('account.tax', 'visa_tptax_rel', 'visa_id', 'tax_id', 'T.P. Taxes'),
                
                'tax_basic'   : fields.boolean('On Basic'),
                'tax_vfs'     : fields.boolean('On VFS'),
                'tax_dd'      : fields.boolean('On DD'), 
                'tax_courier' : fields.boolean('On Courier'),
                'tax_tac'     : fields.boolean('On TAC'),
                'tax_tds'     : fields.boolean('On TDS(T)'),
                'tax_tds1'    : fields.boolean('On TDS(D)'),
                'tax_mark'    : fields.boolean('On Mark Up'),
                'tax_other'   : fields.boolean('On Other'),
                'tax_tptax'   : fields.boolean('On T.P. Tax'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                'tax_ids'   : fields.many2many('account.tax', 'visa_tax_rel', 'visa_id', 'tax_id', 'Taxes'),
                                
                'tax'          : fields.function(_get_all_total, string='TAX', store= True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'basicother'   : fields.function(_get_all_total, string='Basic+other', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'tac'          : fields.function(_get_all_total, string='TAC', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'markup'       : fields.function(_get_all_total, string='Markup', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'servicechrg'  : fields.function(_get_all_total, string='Service Charge', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'subtotal'     : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'taxes'        : fields.function(_get_all_total, string='Taxes', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'tax_base'     : fields.function(_get_all_total, string='Tax Base', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'total'        : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'po_subtotal'  : fields.function(_get_all_total, string='PO Subtotal', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                } 
    
    _defaults = {
                 'account_id'   : _default_account_id,
                 'inv_type' : lambda self,cr,uid,c: c.get('type', ''),
                 'no_adult' : 1,
                 'currency_id': _get_currency
                 }
                    
    def onchange_product(self, cr, uid, ids, product_id, inv_type, no_adult, no_child, no_infant, a_discount, a_cancel_markup, a_cancel_charges, c_discount, c_cancel_markup, c_cancel_charges, i_discount, i_cancel_markup, i_cancel_charges, context=None):
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
                
            # Fare Details
            res = { 'name' : prod.name_template,
                    'tax_ids': map(lambda x: x.id, prod.taxes_id),
                    'a_basic': prod.a_basic, 'a_courier' : prod.a_courier,'a_vfs' : prod.a_vfs,'a_tac_perc' : prod.a_tac_perc,'a_tac' : prod.a_tac, 'a_dd' : prod.a_dd, 'a_markup_perc': prod.a_markup_perc, 'a_markup' : prod.a_markup , 'a_other' : prod.a_other , 'a_servicechrg_perc' : prod.a_servicechrg_perc , 'a_servicechrg' : prod.a_servicechrg, 'a_tp_servicechrg' : prod.a_tp_servicechrg, 
                    'c_basic': prod.c_basic,'c_courier' : prod.c_courier, 'c_vfs' : prod.c_vfs,'c_tac_perc' : prod.c_tac_perc,'c_tac' : prod.c_tac, 'c_dd' : prod.c_dd, 'c_markup_perc': prod.c_markup_perc, 'c_markup' : prod.c_markup , 'c_other' : prod.c_other , 'c_servicechrg_perc' : prod.c_servicechrg_perc , 'c_servicechrg' : prod.c_servicechrg, 'c_tp_servicechrg' : prod.c_tp_servicechrg,
                    'i_basic': prod.i_basic,'i_courier' : prod.i_courier, 'i_vfs' : prod.i_vfs,'i_tac_perc' : prod.i_tac_perc,'i_tac' : prod.i_tac, 'i_dd' : prod.i_dd, 'i_markup_perc': prod.i_markup_perc, 'i_markup' : prod.i_markup , 'i_other' : prod.i_other , 'i_servicechrg_perc' : prod.i_servicechrg_perc , 'i_servicechrg' : prod.i_servicechrg, 'i_tp_servicechrg' : prod.i_tp_servicechrg,
                    'tptax_basic' : prod.tptax_basic, 'tptax_courier' : prod.tptax_courier, 'tptax_vfs' : prod.tptax_vfs, 'tptax_tac' : prod.tptax_tac, 'tptax_dd' : prod.tptax_dd, 'tptax_other' : prod.tptax_other, 'tptax_tpservicechrg' : prod.tptax_tpservicechrg, 
                    'tptax_ids' : map(lambda x: x.id, prod.tptax_ids),
                    'currency_id': prod.currency_id.id,
                   }
            res.update(taxon_vals)
            
#             res.update(self.onchange_VISA_onTPtax(cr, uid, ids, inv_type, no_adult, res['a_basic'], res['a_vfs'], res['a_courier'], res['a_dd'], res['a_other'], res['a_markup_perc'], res['a_markup']
#                                                   , res['a_tac_perc'], res['a_tac'], res['a_servicechrg_perc'], res['a_servicechrg'], res['a_tp_servicechrg'], a_discount, a_cancel_markup, a_cancel_charges
#                                                   , no_child,  res['c_basic'], res['c_vfs'], res['c_courier'], res['c_dd'], res['c_other'], res['c_markup_perc'], res['c_markup']
#                                                   , res['c_tac_perc'], res['c_tac'], res['c_servicechrg_perc'], res['c_servicechrg'], res['c_tp_servicechrg'], c_discount, c_cancel_markup, c_cancel_charges  
#                                                   , no_infant, res['i_basic'], res['i_vfs'], res['i_courier'], res['i_dd'], res['i_other'], res['i_markup_perc'], res['i_markup'] 
#                                                   , res['i_tac_perc'], res['i_tac'], res['i_servicechrg_perc'], res['i_servicechrg'], res['i_tp_servicechrg'], i_discount, i_cancel_markup, i_cancel_charges
#                                                   , res['tptax_basic'], res['tptax_courier'], res['tptax_vfs'], res['tptax_tac'], res['tptax_dd'], res['tptax_other'], res['tptax_ids'], context)['value'])
                            
         
        return {'value':res}
       
    def onchange_VISA_Total(self, cr, uid, ids, inv_type, chkwhich, calledby, no_pax, basic, vfs, courier, dd, other, markup_perc, markup
                            , tac_perc, tac, tds_perc, tds, tds1_perc, tds1, servicechrg_perc, servicechrg, tp_servicechrg, discount, cancel_markup, cancel_charges, cancel_service
                            , tptax_basic, tptax_courier, tptax_vfs, tptax_dd, tptax_other, tptax_tac, tptax_tds, tptax_tpservicechrg, tptax_ids, is_sc=False, context=None):   
        """ 
            Method  :: common for both Adult & Child
            Used    :: in Sales - Visa
            Returns :: Rate and/or Amount value for the given (%)
        """

        res = {}
        tptax = tpamt4tax = 0.00
        dp = get_dp_precision(cr, uid, 'Account')
        if calledby == 'all':
            if tac_perc:
                tac = round(((tac_perc * basic) / 100.00), dp)
                res['tac'] = tac 
            
            if tds_perc:
                tds = round(((tds_perc * tac) / 100.00), dp)
                res['tds'] = tds
                
            if tds1_perc:
                tds1 = round(((tds1_perc * discount) / 100.00), dp)
                res['tds1'] = tds1
                
            if markup_perc:
                markup = round(((markup_perc * basic) / 100.00), dp)
                res['markup'] = markup
        
        if tptax_basic == True   : tpamt4tax += basic
        if tptax_courier == True : tpamt4tax += courier
        if tptax_vfs == True     : tpamt4tax += vfs
        if tptax_tac == True     : tpamt4tax += tac
        if tptax_dd == True      : tpamt4tax += dd
        if tptax_other == True   : tpamt4tax += other
#         if tptax_tac == True     : tpamt4tax += tac
        if tptax_tds == True     : tpamt4tax += tds
        if tptax_tpservicechrg == True     : tpamt4tax += tp_servicechrg
        
        if context and context.get('calledfrm','') == 'func':
            for ttx in tptax_ids:
                tptax += round((tpamt4tax * ttx.amount), dp)
        else:
            for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
                tptax += round((tpamt4tax * ttx['amount']), dp)   

        if inv_type in ('out_invoice', 'out_refund'):        
            rate = (basic + vfs + courier + dd + other + markup + tptax - discount + tds1)
            if not is_sc and servicechrg_perc:
                servicechrg = round(((servicechrg_perc * rate) / 100.00), dp)
                res['servicechrg'] = servicechrg
                
            rate = (rate + servicechrg + tp_servicechrg - cancel_markup - cancel_charges - cancel_service) * no_pax
            res['po_rate'] = (basic + vfs + courier + dd + other + tptax + tds - tac - cancel_charges) * no_pax
        else:
            rate = (basic + vfs + courier + dd + other + tptax + tds - tac - cancel_charges) * no_pax
            
        res.update({'rate' : rate, 'tptax': tptax})
        
        result = {}
        pax_map = {'adult':'a_', 'child':'c_', 'infant':'i_'}
        for r in res.keys():
            result[pax_map[chkwhich]+r] = res[r]
             
        return {'value':result}
    
    def onchange_VISA_onTPtax(self, cr, uid, ids, inv_type
                              , no_adult, a_basic, a_vfs, a_courier, a_dd, a_other, a_markup_perc, a_markup, a_tac_perc, a_tac, a_tds_perc, a_tds, a_tds1_perc, a_tds1, a_servicechrg_perc, a_servicechrg, a_tp_servicechrg, a_discount, a_cancel_markup, a_cancel_charges, a_cancel_service
                              , no_child, c_basic, c_vfs, c_courier, c_dd, c_other, c_markup_perc, c_markup, c_tac_perc, c_tac, c_tds_perc, c_tds, c_tds1_perc, c_tds1, c_servicechrg_perc, c_servicechrg, c_tp_servicechrg, c_discount, c_cancel_markup, c_cancel_charges, c_cancel_service
                              , no_infant, i_basic, i_vfs, i_courier, i_dd, i_other, i_markup_perc, i_markup, i_tac_perc, i_tac, i_tds_perc, i_tds, i_tds1_perc, i_tds1, i_servicechrg_perc, i_servicechrg, i_tp_servicechrg, i_discount, i_cancel_markup, i_cancel_charges, i_cancel_service
                              , tptax_basic, tptax_courier, tptax_vfs, tptax_dd, tptax_other, tptax_tac, tptax_tds, tptax_tpservicechrg, tptax_ids, context=None):
        
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        res.update(self.onchange_VISA_Total(cr, uid, ids, inv_type, 'adult', 'all', no_adult, a_basic, a_vfs, a_courier, a_dd, a_other, a_markup_perc, a_markup
                            , a_tac_perc, a_tac, a_tds_perc, a_tds, a_tds1_perc, a_tds1, a_servicechrg_perc, a_servicechrg, a_tp_servicechrg, a_discount, a_cancel_markup, a_cancel_charges, a_cancel_service
                            , tptax_basic, tptax_courier, tptax_vfs, tptax_dd, tptax_other, tptax_tac, tptax_tds, tptax_tpservicechrg,tptax_ids, context=context)['value'])
         
        res.update(self.onchange_VISA_Total(cr, uid, ids, inv_type, 'child', 'all', no_child, c_basic, c_vfs, c_courier, c_dd, c_other, c_markup_perc, c_markup
                            , c_tac_perc, c_tac, c_tds_perc, c_tds, c_tds1_perc, c_tds1, c_servicechrg_perc, c_servicechrg, c_tp_servicechrg, c_discount, c_cancel_markup, c_cancel_charges, c_cancel_service
                            , tptax_basic, tptax_courier, tptax_vfs, tptax_dd, tptax_other, tptax_tac, tptax_tds, tptax_tpservicechrg, tptax_ids, context=context)['value'])

        res.update(self.onchange_VISA_Total(cr, uid, ids, inv_type, 'infant', 'all', no_infant, i_basic, i_vfs, i_courier, i_dd, i_other, i_markup_perc, i_markup
                            , i_tac_perc, i_tac, i_tds_perc, i_tds, i_tds1_perc, i_tds1, i_servicechrg_perc, i_servicechrg, i_tp_servicechrg, i_discount, i_cancel_markup, i_cancel_charges, i_cancel_service
                            , tptax_basic, tptax_courier, tptax_vfs, tptax_dd, tptax_other, tptax_tac, tptax_tds, tptax_tpservicechrg, tptax_ids, context=context)['value'])
                   
        return {'value':res}
    
    def onchange_validFrom(self, cr, uid, ids, valid_from):
        res = {}
        if valid_from:
            res['valid_to'] = valid_from 
        return {'value': res}
    
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
            nartn = 'Visa : ' + str(case.name) + ", " + str(case.passenger)
            getamt = self.calc_VISA_total(cr, uid, case.id, case.inv_type)
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
                'account_analytic_id' : case.invoice_id and case.invoice_id.account_analytic_id and case.invoice_id.account_analytic_id.id or False,
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
                             'visa_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('visa_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True

    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_visa, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
      
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_visa, self).write(cr, uid, ids, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: