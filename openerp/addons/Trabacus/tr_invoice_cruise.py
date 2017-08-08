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

class tr_invoice_cruise(osv.osv):
    _name = 'tr.invoice.cruise'
    _description = 'Invoice - Cruise' 
    
    
    def calc_CRS_total(self, cr, uid, id, inv_type, context=None):
        res = {}
        if context == None: context = {}
        ctx = context.copy()
        ctx['calledfrm'] = 'func'
        
        case = self.browse(cr, uid, id)
        res = self.onchange_CRS_onTPtax(cr, uid, [case.id], case.inv_type, case.no_adult, case.a_basic, case.a_paxhandle, case.a_crshandle, case.a_holiday, case.a_fuel, case.a_promo
                                  , case.a_tac_perc, case.a_tac, case.a_tds_perc, case.a_tds, case.a_tds1_perc, case.a_tds1, case.a_markup_perc, case.a_markup, case.a_servicechrg_perc, case.a_servicechrg, case.a_discount, case.a_cancel_charges, case.a_cancel_service
                                  , case.a_cancel_markup, case.no_extra, case.e_basic, case.e_paxhandle, case.e_crshandle, case.e_holiday, case.e_fuel, case.e_promo
                                  , case.e_tac_perc, case.e_tac, case.e_tds_perc, case.e_tds, case.e_tds1_perc, case.e_tds1, case.e_markup_perc, case.e_markup, case.e_servicechrg_perc, case.e_servicechrg, case.e_discount, case.e_cancel_charges, case.e_cancel_service
                                  , case.e_cancel_markup, case.no_child, case.c_basic, case.c_paxhandle, case.c_crshandle, case.c_holiday, case.c_fuel, case.c_promo
                                  , case.c_tac_perc, case.c_tac, case.c_tds_perc, case.c_tds, case.c_tds1_perc, case.c_tds1, case.c_markup_perc, case.c_markup, case.c_servicechrg_perc, case.c_servicechrg, case.c_discount, case.c_cancel_charges, case.c_cancel_service
                                  , case.c_cancel_markup, case.no_infant, case.i_basic, case.i_paxhandle, case.i_crshandle, case.i_holiday, case.i_fuel, case.i_promo
                                  , case.i_tac_perc, case.i_tac, case.i_tds_perc, case.i_tds, case.i_tds1_perc, case.i_tds1, case.i_markup_perc, case.i_markup, case.i_servicechrg_perc, case.i_servicechrg, case.i_discount, case.i_cancel_charges, case.i_cancel_service
                                  , case.i_cancel_markup, case.tptax_basic, case.tptax_paxhandle, case.tptax_crshandle, case.tptax_holiday, case.tptax_fuel, case.tptax_promo
                                  , case.tptax_tac, case.tptax_tds, case.tptax_ids, context=ctx)['value']
            
        res['subtotal'] = res.get('a_subtotal',0) +  res.get('e_subtotal',0) + res.get('c_subtotal',0) + res.get('i_subtotal',0)
        res['po_subtotal'] = res.get('a_po_subtotal',0) +  res.get('e_po_subtotal',0) + res.get('c_po_subtotal',0) + res.get('i_po_subtotal',0)
        res['tac'] = (case.a_tac * case.no_adult) + (case.e_tac * case.no_extra) + (case.c_tac * case.no_child) + (case.i_tac * case.no_infant)
        res['tds'] = (case.a_tds * case.no_adult) + (case.e_tds * case.no_extra) + (case.c_tds * case.no_child) + (case.i_tds * case.no_infant)
        res['tds1'] = (case.a_tds1 * case.no_adult) + (case.e_tds1 * case.no_extra) + (case.c_tds1 * case.no_child) + (case.i_tds1 * case.no_infant)
        res['basic'] = (case.a_basic * case.no_adult) + (case.e_basic * case.no_extra) + (case.c_basic * case.no_child) + (case.i_basic * case.no_infant)
        res['discount'] = (case.a_discount * case.no_adult) + (case.e_discount * case.no_extra) + (case.c_discount * case.no_child) + (case.i_discount * case.no_infant)
        res['markup'] = ((case.a_markup * case.no_adult) + (case.e_markup * case.no_extra) + (case.c_markup * case.no_child) + (case.i_markup * case.no_infant))
        res['servicechrg'] = (case.a_servicechrg * case.no_adult) + (case.e_servicechrg * case.no_extra) + (case.c_servicechrg * case.no_child) + (case.i_servicechrg * case.no_infant)
                        
        res['other'] =  ((case.a_paxhandle + case.a_crshandle + case.a_holiday + case.a_fuel - case.a_promo + res.get('a_tptax',0)) * case.no_adult) \
                        + ((case.e_paxhandle + case.e_crshandle + case.e_holiday + case.e_fuel - case.e_promo + res.get('e_tptax',0)) * case.no_extra) \
                        + ((case.c_paxhandle + case.c_crshandle + case.c_holiday + case.c_fuel - case.c_promo + res.get('c_tptax',0)) * case.no_child) \
                        + ((case.i_paxhandle + case.i_crshandle + case.i_holiday + case.i_fuel - case.i_promo + res.get('i_tptax',0)) * case.no_infant)
        res['cancel_markup'] = (case.a_cancel_markup * case.no_adult) + (case.e_cancel_markup * case.no_extra) + (case.c_cancel_markup * case.no_child) + (case.i_cancel_markup * case.no_infant)
        res['cancel_charges'] = (case.a_cancel_charges * case.no_adult) + (case.e_cancel_charges * case.no_extra) + (case.c_cancel_charges * case.no_child) + (case.i_cancel_charges * case.no_infant)
        res['cancel_service'] = (case.a_cancel_service * case.no_adult) + (case.e_cancel_service * case.no_extra) + (case.c_cancel_service * case.no_child) + (case.i_cancel_service * case.no_infant)
         
        return res 

    def _get_Alltotal(self, cr, uid, ids, field_name, arg, context):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        
        for case in self.browse(cr, uid, ids):
            tax = 0.00 
            getamt = self.calc_CRS_total(cr, uid, case.id, case.inv_type, context)
            res[case.id] = {
                            'a_tptax': getamt.get('a_tptax', 0), 'e_tptax': getamt.get('e_tptax', 0), 'c_tptax': getamt.get('c_tptax', 0), 'i_tptax': getamt.get('i_tptax', 0),
                            'a_subtotal': getamt.get('a_subtotal', 0), 'e_subtotal': getamt.get('e_subtotal', 0), 'c_subtotal': getamt.get('c_subtotal', 0), 'i_subtotal': getamt.get('i_subtotal', 0)
                            }
            res[case.id]['basicother'] = getamt.get('subtotal',0)
            res[case.id]['subtotal'] = getamt.get('subtotal',0)
            res[case.id]['po_subtotal'] = getamt.get('po_subtotal',0)
            res[case.id]['tac'] = case.a_tac + case.e_tac + case.c_tac + case.i_tac
             
            def _calc_tax(case, no_pax, basic, paxhandle, crshandle, holiday, fuel, promo, tac, tds, tds1, markup, servicechrg, tptax):
                amt4tax = tx = 0.00
                if case.tax_basic == True: amt4tax += (basic * no_pax)
                if case.tax_paxhandle == True: amt4tax += (paxhandle * no_pax)
                if case.tax_crshandle == True: amt4tax += (crshandle * no_pax)
                if case.tax_holiday == True: amt4tax += (holiday * no_pax)
                if case.tax_fuel == True: amt4tax += (fuel * no_pax)
                if case.tax_promo == True: amt4tax += (promo * no_pax)
                if case.tax_tac == True: amt4tax += (tac * no_pax)
                if case.tax_tds == True: amt4tax += (tds * no_pax)
                if case.tax_tds1 == True: amt4tax += (tds1 * no_pax)
                if case.tax_mark == True: amt4tax += (markup * no_pax)
                if case.tax_servicechrg == True: amt4tax += (servicechrg * no_pax)
                if case.tax_tptax == True: amt4tax += (tptax * no_pax)
             
                for t in case.tax_ids:
                    tx += round((amt4tax * t.amount), dp)
                return {'amt4tx':amt4tax, 'tax':tx}
                
            atx = _calc_tax(case, case.no_adult, case.a_basic, case.a_paxhandle, case.a_crshandle, case.a_holiday, case.a_fuel, case.a_promo, case.a_tac, case.a_tds, case.a_tds1, case.a_markup, case.a_servicechrg, getamt.get('a_tptax',0))
            etx = _calc_tax(case, case.no_extra, case.e_basic, case.e_paxhandle, case.e_crshandle, case.e_holiday, case.e_fuel, case.e_promo, case.e_tac, case.e_tds, case.e_tds1, case.e_markup, case.e_servicechrg, getamt.get('e_tptax',0))
            ctx = _calc_tax(case, case.no_child, case.c_basic, case.c_paxhandle, case.c_crshandle, case.c_holiday, case.c_fuel, case.c_promo, case.c_tac, case.c_tds, case.c_tds1, case.c_markup, case.c_servicechrg, getamt.get('c_tptax',0))
            itx = _calc_tax(case, case.no_infant, case.i_basic, case.i_paxhandle, case.i_crshandle, case.i_holiday, case.i_fuel, case.i_promo, case.i_tac, case.i_tds, case.i_tds1, case.i_markup, case.i_servicechrg, getamt.get('i_tptax',0))
            
            res[case.id].update({'a_tax': atx['tax'], 'e_tax': etx['tax'], 'c_tax': ctx['tax'], 'i_tax': itx['tax'], 
                                 'taxes' : (atx['tax'] + etx['tax'] + ctx['tax'] + itx['tax']),
                                 'tax_base' : (atx['amt4tx'] + etx['amt4tx'] + ctx['amt4tx'] + itx['amt4tx'])
                                })
            res[case.id]['total'] = getamt.get('subtotal',0) + res[case.id]['taxes']
        return res
    
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(tr_invoice_cruise, self).default_get(cr, uid, fields, context=context)
        if context == None: context = {}
        
        if context.get('travel_type','') == 'package':
            res.update({
                     'no_extra' : 1,
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
                 
                'product_id'  : fields.many2one('product.product', 'Product', ondelete='restrict', domain=[('travel_type','=','cruise')]), 
                'name'        : fields.char('Description', size=100, required=True),
                'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict'), 
                'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                    , help="The income or expense account related to the selected product."),
                'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
                'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
                'src_id'      : fields.many2one('tr.invoice.cruise', 'Source Reference'),
                
                'no_nts'  : fields.integer('No. of Nights'),  
                'sail_dt' : fields.date('Sailing Date'),
                'rate'    : fields.char('Rate', size=100),
                'vessele_id'     : fields.many2one('tr.vessele', 'Vessele', required=True, ondelete='restrict' ),  
                'cabincateg_id'  : fields.many2one('tr.cabin.category', 'Cabin Category', required=True, ondelete='restrict'),
                'inclusive'  : fields.text('Inclusive'),
                'remarks'    : fields.text('Remarks'),
                'passenger'  : fields.char('Passenger', size=500),
                
                # Adult
                'no_adult'    : fields.integer('No. of Adults'),
                'a_basic'     : fields.float('Cabin Fare', digits_compute=dp.get_precision('Account')),
                'a_paxhandle' : fields.float('Passenger Handling Charges', digits_compute=dp.get_precision('Account')),
                'a_crshandle' : fields.float('Handling Charges', digits_compute=dp.get_precision('Account')), 
                'a_holiday'   : fields.float('Holiday Surcharges', digits_compute=dp.get_precision('Account')), 
                'a_fuel'      : fields.float('Fuel Surcharges', digits_compute=dp.get_precision('Account')), 
                'a_promo'     : fields.float('Promo Discount', digits_compute=dp.get_precision('Account')),
                'a_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'a_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'a_tds_perc'  : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
                'a_tds'       : fields.float('TDS', digits_compute=dp.get_precision('Account')),
                'a_tds1_perc'    : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'a_tds1'         : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'a_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'a_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'a_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'a_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'a_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'a_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')),
                'a_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')),
                'a_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                'a_tptax'    : fields.function(_get_Alltotal, string='Adult T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'a_subtotal' : fields.function(_get_Alltotal, string='Adult Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'a_tax'      : fields.function(_get_Alltotal, string='Adult Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'a_total'    : fields.function(_get_Alltotal, string='Adult Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                  
                # Extra
                'no_extra'    : fields.integer('No. of Extra Person'),
                'e_basic'     : fields.float('Cabin Fare', digits_compute=dp.get_precision('Account')),
                'e_paxhandle' : fields.float('Passenger Handling Charges', digits_compute=dp.get_precision('Account')),
                'e_crshandle' : fields.float('Handling Charges', digits_compute=dp.get_precision('Account')), 
                'e_holiday'   : fields.float('Holiday Surcharges', digits_compute=dp.get_precision('Account')), 
                'e_fuel'      : fields.float('Fuel Surcharges', digits_compute=dp.get_precision('Account')), 
                'e_promo'     : fields.float('Promo Discount', digits_compute=dp.get_precision('Account')),
                'e_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'e_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'e_tds_perc'  : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
                'e_tds'       : fields.float('TDS', digits_compute=dp.get_precision('Account')),
                'e_tds1'      : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'e_tds1_perc'    : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'e_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'e_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'e_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'e_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'e_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'e_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')),
                'e_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')),
                'e_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                'e_tptax'     : fields.function(_get_Alltotal, string='Extra T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'e_subtotal'  : fields.function(_get_Alltotal, string='Extra Person Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'e_tax'       : fields.function(_get_Alltotal, string='Extra Person Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'e_total'     : fields.function(_get_Alltotal, string='Extra Person Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                # Child
                'no_child'    : fields.integer('No. of Children'),
                'c_basic'     : fields.float('Cabin Fare', digits_compute=dp.get_precision('Account')),
                'c_paxhandle' : fields.float('Passenger Handling Charges', digits_compute=dp.get_precision('Account')),
                'c_crshandle' : fields.float('Handling Charges', digits_compute=dp.get_precision('Account')), 
                'c_holiday'   : fields.float('Holiday Surcharges', digits_compute=dp.get_precision('Account')), 
                'c_fuel'      : fields.float('Fuel Surcharges', digits_compute=dp.get_precision('Account')), 
                'c_promo'     : fields.float('Promo Discount', digits_compute=dp.get_precision('Account')),
                'c_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'c_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'c_tds_perc'  : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
                'c_tds'       : fields.float('TDS', digits_compute=dp.get_precision('Account')),
                'c_tds1'      : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'c_tds1_perc'    : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'c_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'c_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'c_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'c_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'c_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'c_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')),
                'c_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')),
                'c_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                'c_tptax'    : fields.function(_get_Alltotal, string='Child T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'c_subtotal' : fields.function(_get_Alltotal, string='Child Total', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                'c_tax'      : fields.function(_get_Alltotal, string='Child Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'c_total'    : fields.function(_get_Alltotal, string='Child Total', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                
                # Infant
                'no_infant'   : fields.integer('No. of Infant'),
                'i_basic'     : fields.float('Cabin Fare', digits_compute=dp.get_precision('Account')),
                'i_paxhandle' : fields.float('Passenger Handling Charges', digits_compute=dp.get_precision('Account')),
                'i_crshandle' : fields.float('Handling Charges', digits_compute=dp.get_precision('Account')), 
                'i_holiday'   : fields.float('Holiday Surcharges', digits_compute=dp.get_precision('Account')), 
                'i_fuel'      : fields.float('Fuel Surcharges', digits_compute=dp.get_precision('Account')), 
                'i_promo'     : fields.float('Promo Discount', digits_compute=dp.get_precision('Account')),
                'i_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'i_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'i_tds_perc'  : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
                'i_tds'       : fields.float('TDS', digits_compute=dp.get_precision('Account')),
                'i_tds1'      : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'i_tds1_perc'    : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'i_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'i_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'i_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'i_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'i_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'i_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')),
                'i_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')),
                'i_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                'i_tptax'    : fields.function(_get_Alltotal, string='Infant T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'i_subtotal' : fields.function(_get_Alltotal, string='Infant Total', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                'i_tax'      : fields.function(_get_Alltotal, string='Infant Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'i_total'    : fields.function(_get_Alltotal, string='Infant Total', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
        
                'tptax_basic'     : fields.boolean('On Cabin'),
                'tptax_paxhandle' : fields.boolean('On Passenger Handling Charges'),
                'tptax_crshandle' : fields.boolean('On Handling Charges'), 
                'tptax_holiday'   : fields.boolean('On Holiday Surcharges'),
                'tptax_fuel'    : fields.boolean('On Fuel Surcharges'),
                'tptax_promo'   : fields.boolean('On Promo Discount'),
                'tptax_tac'     : fields.boolean('On TAC'),
                'tptax_tds'     : fields.boolean('On TDS(T)'),
                'tptax_ids'     : fields.many2many('account.tax', 'cruise_tptax_rel', 'cruise_id', 'tax_id', 'T.P. Taxes'),
                
                'tax_basic'      : fields.boolean('On Cabin'),
                'tax_paxhandle'  : fields.boolean('On Passenger Handling Charges'),
                'tax_crshandle'  : fields.boolean('On Handling Charges'), 
                'tax_holiday'    : fields.boolean('On Holiday Surcharges'),
                'tax_fuel'    : fields.boolean('On Fuel Surcharges'),
                'tax_promo'   : fields.boolean('On Promo Discount'),
                'tax_tac'     : fields.boolean('On TAC'),
                'tax_tds'     : fields.boolean('On TDS(T)'),
                'tax_tds1'    : fields.boolean('On TDS(D)'),
                'tax_mark'    : fields.boolean('On Mark Up'),
                'tax_tptax'   : fields.boolean('On T.P. Tax'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                'tax_ids'    : fields.many2many('account.tax', 'cruise_tax_rel', 'cruise_id', 'tax_id', 'Taxes'),
            
                'basicother'  : fields.function(_get_Alltotal, string='Basic + Others', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'tac'         : fields.function(_get_Alltotal, string='TAC', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'subtotal'    : fields.function(_get_Alltotal, string='Subtotal', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                'tax_base'    : fields.function(_get_Alltotal, string='Tax Base', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'taxes'       : fields.function(_get_Alltotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                'total'       : fields.function(_get_Alltotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                'po_subtotal'    : fields.function(_get_Alltotal, string='PO Subtotal', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                
                
                }
    _defaults = {
                 'account_id'   : _default_account_id,
                 'inv_type' : lambda self,cr,uid,c: c.get('type', ''),
                 'no_adult': 1,
                 'currency_id': _get_currency
                 }
    
    
    def onchange_product(self, cr, uid, ids, product_id
                        , vessele_id, cabincateg_id, sail_dt, context=None):
        res = {}  
        crprice_obj = self.pool.get('tr.service.cruisepricing')
        servc_obj = self.pool.get('tr.product.services')
        
        if context == None: context = {} 
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
          
            res = {
                   'name'    : prod.name, 
                   'no_nts'  : prod.no_nts,
                   'rate'    : prod.desc,
                   'tptax_ids': map(lambda x: x.id, prod.tptax_ids),
                   'tax_ids': map(lambda x: x.id, prod.taxes_id),
                   'currency_id': prod.currency_id.id,
                }
            
            res.update(taxon_vals)
            
            if vessele_id and cabincateg_id and sail_dt:
                cr.execute(" select * \
                             from tr_service_cruisepricing where service_id = %d and vessele_id = %d \
                             and cabincateg_id = %d \
                             and '%s'::date between valid_from and valid_to \
                             order by valid_to"%(prod.service_id.id, vessele_id, cabincateg_id, sail_dt))
                crpvals = cr.dictfetchall()   
                
                print "crpvals", crpvals
                
                if len(crpvals) == 1:
                    crpvals = crpvals[0]
                    del crpvals['id']
                    crpvals['sail_dt'] = sail_dt
                    return {'value': crpvals}
                
        return {'value':res}
     
    def onchange_CRS_total(self, cr, uid, ids, inv_type, chkwhich, calledby, no_pax, basic, paxhandle, crshandle, holiday
                           , fuel, promo, tac_perc, tac, tds_perc, tds, tds1_perc, tds1, markup_perc, markup
                           , servicechrg_perc, servicechrg, discount, cancel_charges, cancel_markup, cancel_service
                           , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds
                           , tptax_ids, is_sc=False, context=None):
        
        """ 
            Method  :: common for both Adult,Extra,Child & Infant
            Used    :: in Invoice - Cruise
            Returns :: Subtotal 
        """
        
        dp = get_dp_precision(cr, uid, 'Account')
        res = {}
        tptax = tpamt4tax = 0.00
        
        # Calculate when percent/other fields are called:
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
                 
        if tptax_basic == True : tpamt4tax += basic
        if tptax_paxhandle == True : tpamt4tax += paxhandle
        if tptax_crshandle == True : tpamt4tax += crshandle
        if tptax_holiday == True   : tpamt4tax += holiday
        if tptax_fuel == True  : tpamt4tax += fuel
        if tptax_promo == True : tpamt4tax += promo
        if tptax_tac == True : tpamt4tax += tac
        if tptax_tds == True : tpamt4tax += tds
               
        if context and context.get('calledfrm','') == 'func':
            for ttx in tptax_ids:
                tptax += round((tpamt4tax * ttx.amount), dp)
        else:
            for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
                tptax += round((tpamt4tax * ttx['amount']), dp)   

        res['tptax'] = tptax
         
        subtot = (basic + paxhandle + crshandle + holiday + fuel + tptax - promo)    
        if inv_type in ('out_invoice', 'out_refund'):
            subtot += (markup + tds1 - discount)
            if not is_sc and servicechrg_perc:
                servicechrg = round(((servicechrg_perc * subtot) / 100.00), dp)
                res['servicechrg'] = servicechrg
            subtot = (subtot + servicechrg - (cancel_charges + cancel_markup + cancel_service)) * no_pax
            res['po_subtotal'] = (basic + paxhandle + crshandle + holiday + fuel + tptax - promo + tds - tac - cancel_charges) * no_pax
                
        else: 
            subtot = ((subtot + tds - tac - cancel_charges) * no_pax)
            
        res.update({'subtotal' : subtot})
          
        result = {}
        pax_map = {'adult':'a_', 'extra': 'e_', 'child':'c_', 'infant':'i_'}
        for r in res.keys():
            result[pax_map[chkwhich]+r] = res[r]
                
        return {'value': result}
    
    
    def onchange_CRS_onTPtax(self, cr, uid, ids, inv_type, no_adult, a_basic, a_paxhandle, a_crshandle, a_holiday, a_fuel, a_promo, a_tac_perc, a_tac, a_tds_perc, a_tds, a_tds1_perc, a_tds1, a_markup_perc, a_markup, a_servicechrg_perc, a_servicechrg, a_discount, a_cancel_charges, a_cancel_markup, a_cancel_service
                             , no_extra, e_basic, e_paxhandle, e_crshandle, e_holiday, e_fuel, e_promo, e_tac_perc, e_tac, e_tds_perc, e_tds, e_tds1_perc, e_tds1, e_markup_perc, e_markup, e_servicechrg_perc, e_servicechrg, e_discount, e_cancel_charges, e_cancel_markup, e_cancel_service
                             , no_child, c_basic, c_paxhandle, c_crshandle, c_holiday, c_fuel, c_promo, c_tac_perc, c_tac, c_tds_perc, c_tds, c_tds1_perc, c_tds1, c_markup_perc, c_markup, c_servicechrg_perc, c_servicechrg, c_discount, c_cancel_charges, c_cancel_markup, c_cancel_service
                             , no_infant, i_basic, i_paxhandle, i_crshandle, i_holiday, i_fuel, i_promo, i_tac_perc, i_tac, i_tds_perc, i_tds, i_tds1_perc, i_tds1, i_markup_perc, i_markup, i_servicechrg_perc, i_servicechrg, i_discount, i_cancel_charges, i_cancel_markup, i_cancel_service
                             , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds, tptax_ids, context=None):
        res = {}
        
        res.update(self.onchange_CRS_total(cr, uid, ids, inv_type, 'adult', 'all', no_adult, a_basic, a_paxhandle, a_crshandle, a_holiday
                           , a_fuel, a_promo, a_tac_perc, a_tac, a_tds_perc, a_tds, a_tds1_perc, a_tds1, a_markup_perc, a_markup, a_servicechrg_perc, a_servicechrg, a_discount, a_cancel_charges, a_cancel_markup, a_cancel_service
                           , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        res.update(self.onchange_CRS_total(cr, uid, ids, inv_type, 'extra', 'all', no_extra, e_basic, e_paxhandle, e_crshandle, e_holiday
                           , e_fuel, e_promo, e_tac_perc, e_tac, e_tds_perc, e_tds, e_tds1_perc, e_tds1, e_markup_perc, e_markup, e_servicechrg_perc, e_servicechrg, e_discount, e_cancel_charges, e_cancel_markup, e_cancel_service
                           , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        res.update(self.onchange_CRS_total(cr, uid, ids, inv_type, 'child', 'all', no_child, c_basic, c_paxhandle, c_crshandle, c_holiday
                           , c_fuel, c_promo, c_tac_perc, c_tac, c_tds_perc, c_tds, c_tds1_perc, c_tds1, c_markup_perc, c_markup, c_servicechrg_perc, c_servicechrg, c_discount, c_cancel_charges, c_cancel_markup, c_cancel_service
                           , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        res.update(self.onchange_CRS_total(cr, uid, ids, inv_type, 'infant', 'all', no_infant, i_basic, i_paxhandle, i_crshandle, i_holiday
                           , i_fuel, i_promo, i_tac_perc, i_tac, i_tds_perc, i_tds, i_tds1_perc, i_tds1, i_markup_perc, i_markup, i_servicechrg_perc, i_servicechrg, i_discount, i_cancel_charges, i_cancel_markup, i_cancel_service
                           , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        return {'value': res}
    
    
    def print_voucher(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = ids
            data['model'] = 'tr.invoice.cruise'
            data['output_type'] = 'pdf'
            data['variables'] = {'cruise_id':case.id,    
                                 'invoice_id':case.invoice_id.id,
                                 'uid' : uid
                                 }
            return {'type': 'ir.actions.report.xml',
                    'report_name':'cs_voucher',
                    'datas':data,
                    }
    
    
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
            nartn = 'Cruise, ' + str(case.name) + ", " + str(case.vessele_id.name) + ", " + str(case.sail_dt)
            getamt = self.calc_CRS_total(cr, uid, case.id, case.inv_type)
            subtot = getamt.get('subtotal',0)
            
            inv_currency = case.invoice_id.currency_id.id
            subtot = cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, subtot, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                
            vals = {
                'name'       : nartn,
                'passenger'  : '',
                'product_id' : case.product_id.id or False,
                'tpartner_id': case.tpartner_id.id, 
                'origin'    : case.invoice_id.name,
                'account_id': case.account_id.id,
                'account_analytic_id' : case.invoice_id and case.invoice_id.account_analytic_id and case.invoice_id.account_analytic_id.id or False,                'currency_id': case.currency_id.id,
                'currency_id': case.currency_id.id,
                'price_unit': subtot,
                'quantity'  : 1,
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
                             'cruise_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('cruise_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True

    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_cruise, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
      
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_cruise, self).write(cr, uid, ids, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: