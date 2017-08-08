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
import re
from datetime import datetime 
import time

def get_dp_precision(cr, uid, application):
    cr.execute('select digits from decimal_precision where name=%s', (application,))
    res = cr.fetchone()
    return res[0] if res else 2


class tr_invoice_hotel(osv.osv):
    _name = 'tr.invoice.hotel'
    _description = 'Invoice - Hotel' 
    
    def calc_Hotel_total(self, cr, uid, id, inv_type, context=None):   
        res = {}
        if context == None: context = {}
        ctx = context.copy()
        ctx['calledfrm'] = 'func'
        case = self.browse(cr, uid, id)
        inv_type = inv_type and inv_type or case.inv_type
        
        res = self.onchange_Hotel_onTPtax(cr, uid, [case.id], inv_type, 'allpax', 'all', case.no_adult, case.a_basic, case.a_other, case.a_tac, case.a_tds, case.a_tds1, case.a_markup, case. a_servicechrg_perc, case.a_servicechrg, case.a_discount, case.a_cancel_markup, case.a_cancel_charges, case.a_cancel_service
                             , case.no_twin, case.tn_basic, case.tn_other, case.tn_tac, case.tn_tds, case.tn_tds1, case.tn_markup, case.tn_servicechrg_perc, case.tn_servicechrg, case.tn_discount, case.tn_cancel_markup, case.tn_cancel_charges, case.tn_cancel_service
                             , case.no_triple, case.t3_basic, case. t3_other, case.t3_tac, case.t3_tds, case.t3_tds1, case.t3_markup, case.t3_servicechrg_perc, case.t3_servicechrg, case.t3_discount, case.t3_cancel_markup, case.t3_cancel_charges, case.t3_cancel_service
                             , case.no_cwb, case.c_basic, case.c_other, case.c_tac, case.c_tds, case.c_tds1, case.c_markup, case.c_servicechrg_perc, case.c_servicechrg, case.c_discount, case.c_cancel_markup, case.c_cancel_charges, case.c_cancel_service
                             , case.no_cnb, case.cn_basic, case.cn_other, case.cn_tac, case.cn_tds, case.cn_tds1, case.cn_markup, case.cn_servicechrg_perc, case.cn_servicechrg, case.cn_discount, case.cn_cancel_markup, case.cn_cancel_charges, case.cn_cancel_service
                             , case.no_infant, case.i_basic, case.i_other, case.i_tac, case.i_tds, case.i_tds1, case.i_markup, case.i_servicechrg_perc, case.i_servicechrg, case.i_discount, case.i_cancel_markup, case.i_cancel_charges, case.i_cancel_service
                             , case.no_extra, case.e_basic, case.e_other, case.e_tac, case.e_tds, case.e_tds1, case.e_markup, case.e_servicechrg_perc, case.e_servicechrg, case.e_discount, case.e_cancel_markup, case.e_cancel_charges, case.e_cancel_service
                             , case.early_chkin, case.late_chkout, case.no_meal, case.meal_rate, case.meal_tax, case.tptax_basic, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_ids, context=ctx)['value']
        
        
        res['basic'] = (case.a_basic * case.no_adult) + (case.tn_basic * case.no_twin) + (case.t3_basic * case.no_triple) + (case.c_basic * case.no_cwb) + (case.cn_basic * case.no_cnb) + (case.i_basic * case.no_infant) + (case.e_basic * case.no_extra)
        res['tac'] = (case.a_tac * case.no_adult) + (case.tn_tac * case.no_twin) + (case.t3_tac * case.no_triple) + (case.c_tac * case.no_cwb) + (case.cn_tac * case.no_cnb) + (case.i_tac * case.no_infant) + (case.e_tac * case.no_extra)
        res['tds'] = (case.a_tds * case.no_adult) + (case.tn_tds * case.no_twin) + (case.t3_tds * case.no_triple) + (case.c_tds * case.no_cwb) + (case.cn_tds * case.no_cnb) + (case.i_tds * case.no_infant) + (case.e_tds * case.no_extra)
        res['tds1'] = (case.a_tds1 * case.no_adult) + (case.tn_tds1 * case.no_twin) + (case.t3_tds1 * case.no_triple) + (case.c_tds1 * case.no_cwb) + (case.cn_tds1 * case.no_cnb) + (case.i_tds1 * case.no_infant) + (case.e_tds1 * case.no_extra)
        res['discount'] = (case.a_discount * case.no_adult) + (case.tn_discount * case.no_twin) + (case.t3_discount * case.no_triple) + (case.c_discount * case.no_cwb) + (case.cn_discount * case.no_cnb) + (case.i_discount * case.no_infant) + (case.e_discount * case.no_extra)
        res['markup'] = (case.a_markup * case.no_adult) + (case.tn_markup * case.no_twin) + (case.t3_markup * case.no_triple) + (case.c_markup * case.no_cwb) + (case.cn_markup * case.no_cnb) + (case.i_markup * case.no_infant) + (case.e_markup * case.no_extra)
        res['servicechrg'] = (case.a_servicechrg * case.no_adult) + (case.tn_servicechrg * case.no_twin) + (case.t3_servicechrg * case.no_triple) + (case.c_servicechrg * case.no_cwb) + (case.cn_servicechrg * case.no_cnb) + (case.i_servicechrg * case.no_infant) + (case.e_servicechrg * case.no_extra)
                        
        res['other'] = ((res.get('a_tptax',0) + case.a_other) * case.no_adult) + ((res.get('tn_tptax',0) + case.tn_other) * case.no_twin) \
                        + ((res.get('t3_tptax',0) + case.t3_other) * case.no_triple) \
                        + ((res.get('c_tptax',0) + case.c_other) * case.no_cwb) + ((res.get('cn_tptax',0) + case.cn_other) * case.no_cnb) \
                        + ((res.get('i_tptax',0) + case.i_other) * case.no_infant) + ((res.get('e_tptax',0) + case.e_other) * case.no_extra)
        
        res['cancel_markup'] = (case.a_cancel_markup * case.no_adult) + (case.tn_cancel_markup * case.no_twin) + (case.t3_cancel_markup * case.no_triple) + (case.c_cancel_markup * case.no_cwb) + (case.cn_cancel_markup * case.no_cnb) + (case.i_cancel_markup * case.no_infant) + (case.e_cancel_markup * case.no_extra)
        res['cancel_charges'] = (case.a_cancel_charges * case.no_adult) + (case.tn_cancel_charges * case.no_twin) + (case.t3_cancel_charges * case.no_triple) + (case.c_cancel_charges * case.no_cwb) + (case.cn_cancel_charges * case.no_cnb) + (case.i_cancel_charges * case.no_infant) + (case.e_cancel_charges * case.no_extra)
        res['cancel_service'] = (case.a_cancel_service * case.no_adult) + (case.tn_cancel_service * case.no_twin) + (case.t3_cancel_service * case.no_triple) + (case.c_cancel_service * case.no_cwb) + (case.cn_cancel_service * case.no_cnb) + (case.i_cancel_service * case.no_infant) + (case.e_cancel_service * case.no_extra)
        return res
    
    def _get_AllTotal(self, cr, uid, ids, field_name, arg, context):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        
        for case in self.browse(cr, uid, ids):
            
            getamt = self.calc_Hotel_total(cr, uid, case.id, case.inv_type, context)
            res[case.id] = {
                            'a_tptax': getamt.get('a_tptax', 0), 'tn_tptax': getamt.get('tn_tptax', 0), 't3_tptax': getamt.get('t3_tptax', 0), 'c_tptax': getamt.get('c_tptax', 0), 'cn_tptax': getamt.get('cn_tptax', 0), 'i_tptax': getamt.get('i_tptax', 0), 'e_tptax': getamt.get('e_tptax', 0),
                            'a_rate': getamt.get('a_rate', 0), 'tn_rate': getamt.get('tn_rate', 0), 't3_rate': getamt.get('t3_rate', 0), 'c_rate': getamt.get('c_rate', 0), 'cn_rate': getamt.get('cn_rate', 0), 'i_rate': getamt.get('i_rate', 0), 'e_rate': getamt.get('e_rate', 0)
                            }
            res[case.id]['subtotal'] = getamt.get('subtotal',0)
            res[case.id]['po_subtotal'] = getamt.get('po_subtotal',0)
            res[case.id]['basicother'] = getamt.get('subtotal',0) - getamt.get('servicechrg',0)
            
            def _calc_tax(case, no_pax, basic, other, tac, tds, tds1, markup, servicechrg, tptax):
                amt4tax = tx = 0.00
                if case.tax_basic == True: amt4tax += (basic * no_pax)
                if case.tax_other == True: amt4tax += (other * no_pax)
                if case.tax_tac == True: amt4tax += (tac * no_pax)
                if case.tax_tds == True: amt4tax += (tds * no_pax)
                if case.tax_tds1 == True: amt4tax += (tds1 * no_pax)
                if case.tax_mark == True: amt4tax += (markup * no_pax)
                if case.tax_tptax == True: amt4tax += (tptax * no_pax)
                if case.tax_servicechrg == True: amt4tax += (servicechrg * no_pax)
             
                for t in case.tax_ids:
                    tx += round((amt4tax * t.amount), dp)
                return {'amt4tx':amt4tax, 'tax':tx}
            
            atx  = _calc_tax(case, case.no_adult, case.a_basic, case.a_other, case.a_tac, case.a_tds, case.a_tds1, case.a_markup, case.a_servicechrg, getamt.get('a_tptax', 0))
            tntx = _calc_tax(case, case.no_twin, case.tn_basic, case.tn_other, case.tn_tac, case.tn_tds, case.tn_tds1, case.tn_markup, case.tn_servicechrg, getamt.get('tn_tptax', 0))
            t3tx = _calc_tax(case, case.no_triple, case.t3_basic, case.t3_other, case.t3_tac, case.t3_tds, case.t3_tds1, case.t3_markup, case.t3_servicechrg, getamt.get('t3_tptax', 0))
            ctx  = _calc_tax(case, case.no_cwb, case.c_basic, case.c_other, case.c_tac, case.c_tds, case.c_tds1, case.c_markup, case.c_servicechrg, getamt.get('c_tptax', 0))
            cntx = _calc_tax(case, case.no_cnb, case.cn_basic, case.cn_other, case.cn_tac, case.cn_tds, case.cn_tds1, case.cn_markup, case.cn_servicechrg, getamt.get('cn_tptax', 0))
            etx  = _calc_tax(case, case.no_extra, case.e_basic, case.e_other, case.e_tac, case.e_tds, case.e_tds1, case.e_markup, case.e_servicechrg, getamt.get('e_tptax', 0))
            itx  = _calc_tax(case, case.no_infant, case.i_basic, case.i_other, case.i_tac, case.i_tds, case.i_tds1, case.i_markup, case.i_servicechrg, getamt.get('i_tptax', 0))
          
            res[case.id].update({'a_tax': atx['tax'], 'tn_tax': tntx['tax'], 't3_tax': t3tx['tax'], 'c_tax': ctx['tax'], 'cn_tax': cntx['tax'], 'i_tax': itx['tax'], 'e_tax': etx['tax'] 
                            , 'taxes' : (atx['tax'] + tntx['tax'] + t3tx['tax'] + ctx['tax'] + cntx['tax'] + itx['tax'] + etx['tax'])
                            , 'tax_base' : (atx['amt4tx'] + tntx['amt4tx'] + t3tx['amt4tx'] + ctx['amt4tx'] + cntx['amt4tx'] + itx['amt4tx'] + etx['amt4tx'])
                            , 'tac'    : getamt.get('tac', 0)
                            , 'servicechrg': getamt.get('servicechrg', 0)
                            })
            res[case.id]['total'] = getamt.get('subtotal',0) + res[case.id]['taxes']
        return res
    
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(tr_invoice_hotel, self).default_get(cr, uid, fields, context=context)
        if context == None: context = {}
        print "ctx", context
        if context.get('travel_type','') == 'package':
            res.update({
                     'no_twin'  : 1,
                     'no_triple': 1,
                     'no_cwb'   : 1,
                     'no_cnb'   : 1,
                     'no_infant': 1,
                     'no_extra' : 1 })
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
                
                'product_id'  : fields.many2one('product.product', 'Product', ondelete='restrict'), 
                'name'        : fields.char('Description', size=100, required=True),
                'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict'), 
                'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                    , help="The income or expense account related to the selected product."),
                'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
                'currency_id' : fields.many2one('res.currency', 'Currency'),
                'src_id'      : fields.many2one('tr.invoice.hotel', 'Source Reference'),
                                               
                'paxpartner_id' : fields.many2one('res.partner', 'Passenger', ondelete='restrict'),
                'pax_name'      : fields.char('Passenger Name', size=30),
                'pax_contact'   : fields.char('Contact No.', size=30),
                'pax_email'     : fields.char('Email', size=30),
                
                'h_contact' : fields.char('Hotel Contact', size=30),
                'h_phone'   : fields.char('Hotel Phone', size=30),
                'h_email'   : fields.char('Hotel Email', size=30),
                'check_in'  : fields.datetime('Check In'), 
                'check_out' : fields.datetime('Check Out'),
                'no_nts'    : fields.integer('No of Nights'),
                
                'meal_id'    : fields.many2one('tr.meal.plan','Meal Plan', ondelete='restrict'),
                'rmcateg_id' : fields.many2one('tr.room.categ','Room Category', ondelete='restrict'),
                
                'confrmd_by' : fields.char('Confirmed By'),
                'reference'  : fields.char('Reference'),
                'inclusive'  : fields.text('Inclusive'),
                'remarks'    : fields.text('Remarks'),
                'dep'   : fields.text('Departure Details'),
                'arr'   : fields.text('Arrival Details'),
                
                 # Adult
                'no_adult'      : fields.integer('No of Adult'),
                'adult_type'    : fields.selection([('room','Per Room'), ('person','Per Person')], string='Type'),
                'no_type'       : fields.integer('No of Person/Room'),
                'a_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'a_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'a_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'a_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'a_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'a_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'a_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'a_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'a_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'a_other_perc'  : fields.float('Other %', digits_compute=dp.get_precision('Account')),
                'a_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
                'a_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'a_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'a_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'a_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'a_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                'a_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')), 
                'a_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'a_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'a_tax'         : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'a_total'       : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                 # Twin Sharing
                'no_twin'        : fields.integer('No of Twin'),
                'tn_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'tn_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'tn_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'tn_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'tn_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'tn_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'tn_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'tn_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'tn_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'tn_other_perc'  : fields.float('Other %', digits_compute=dp.get_precision('Account')),
                'tn_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
                'tn_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'tn_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'tn_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'tn_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'tn_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                'tn_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')), 
                'tn_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'tn_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'tn_tax'         : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'tn_total'       : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                 # Triple Sharing
                'no_triple'      : fields.integer('No of Triple'),
                't3_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                't3_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                't3_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                't3_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                't3_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                't3_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                't3_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                't3_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                't3_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                't3_other_perc'  : fields.float('Other %', digits_compute=dp.get_precision('Account')),
                't3_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
                't3_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                't3_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                't3_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                't3_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                't3_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                't3_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                't3_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                't3_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                't3_tax'         : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                't3_total'       : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                 # Child with Bed
                'no_cwb'        : fields.integer('No of CWB'),
                'c_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'c_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'c_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'c_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'c_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'c_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'c_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'c_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'c_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'c_other_perc'  : fields.float('Other %', digits_compute=dp.get_precision('Account')),
                'c_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
                'c_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'c_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'c_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'c_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'c_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                'c_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                'c_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'c_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'c_tax'         : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'c_total'       : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                 # Child without Bed
                'no_cnb'         : fields.integer('No of CNB'),
                'cn_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'cn_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'cn_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'cn_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'cn_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'cn_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'cn_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'cn_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'cn_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'cn_other_perc'  : fields.float('Other %', digits_compute=dp.get_precision('Account')),
                'cn_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
                'cn_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'cn_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'cn_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'cn_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'cn_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                'cn_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                'cn_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'cn_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'cn_tax'         : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'cn_total'       : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                 # Infant
                'no_infant'     : fields.integer('No of Infant'),
                'i_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'i_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'i_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'i_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'i_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'i_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'i_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'i_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'i_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'i_other_perc'  : fields.float('Other %', digits_compute=dp.get_precision('Account')),
                'i_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
                'i_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'i_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'i_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'i_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'i_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                'i_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                'i_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'i_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'i_tax'         : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'i_total'       : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                 # Extra Person
                'no_extra'      : fields.integer('No of Extra Person'),
                'e_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'e_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'e_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'e_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'e_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'e_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'e_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'e_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'e_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'e_other_perc'  : fields.float('Other %', digits_compute=dp.get_precision('Account')),
                'e_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
                'e_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'e_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'e_discount'       : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'e_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'e_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                'e_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                'e_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'e_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'e_tax'         : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'e_total'       : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                'early_chkin'     : fields.float('Early Check-In', digits_compute=dp.get_precision('Account')),
                'late_chkout'     : fields.float('Late Check-Out', digits_compute=dp.get_precision('Account')),
                
                'no_meal'    : fields.float('No of Meals', digits_compute=dp.get_precision('Account')),
                'meal_rate'  : fields.float('Meal Rate', digits_compute=dp.get_precision('Account')),
                'meal_tax'   : fields.float('Meal Tax', digits_compute=dp.get_precision('Account')),
                'meal_cost'  : fields.function(_get_AllTotal, string='Total Meal Cost', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                'tptax_basic'  : fields.boolean('On Basic'),
                'tptax_other'  : fields.boolean('On Other'),
                'tptax_tac'    : fields.boolean('On TAC'),
                'tptax_tds'    : fields.boolean('On TDS(T)'),
                'tptax_ids'    : fields.many2many('account.tax', 'hotel_tptax_rel', 'hotel_id', 'tax_id', 'T.P. Taxes'),
                
                'tax_basic'    : fields.boolean('On Basic'),
                'tax_other'    : fields.boolean('On Other'),
                'tax_tac'      : fields.boolean('On TAC'),
                'tax_tds'      : fields.boolean('On TDS(T)'),
                'tax_tds1'     : fields.boolean('On TDS(D)'),
                'tax_mark'     : fields.boolean('On Mark Up'),
                'tax_tptax'    : fields.boolean('On T.P. Tax'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                'tax_ids' : fields.many2many('account.tax', 'hotel_tax_rel', 'hotel_id', 'tax_id', 'Taxes'),
                
                'basicother' : fields.function(_get_AllTotal, string='Basic + Others', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'tac'        : fields.function(_get_AllTotal, string='TAC', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'servicechrg': fields.function(_get_AllTotal, string='Service Charge', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'subtotal'   : fields.function(_get_AllTotal, string='Subtotal', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'taxes'      : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'tax_base'   : fields.function(_get_AllTotal, string='Tax Base', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'total'      : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'po_subtotal' : fields.function(_get_AllTotal, string='PO Subtotal', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                }
                
    _defaults = {
                 'account_id' : _default_account_id,
                 'inv_type'   : lambda self,cr,uid,c: c.get('type', ''),
                 'adult_type' : 'person',
                 'no_adult' : 1,
                 'currency_id': _get_currency
                 }
    
    def onchange_product(self, cr, uid, ids, product_id, meal_id, rmcateg_id, checkin, checkout
                         , no_adult, no_twin, no_triple, no_cwb, no_cnb, no_infant, no_extra 
                         , a_tds1, a_discount, a_cancel_markup, a_cancel_charges, a_cancel_service
                         , tn_tds1, tn_discount, tn_cancel_markup, tn_cancel_charges, tn_cancel_service
                         , t3_tds1, t3_discount, t3_cancel_markup, t3_cancel_charges, t3_cancel_service
                         , c_tds1, c_discount, c_cancel_markup, c_cancel_charges, c_cancel_service
                         , cn_tds1, cn_discount, cn_cancel_markup, cn_cancel_charges, cn_cancel_service
                         , e_tds1, e_discount, e_cancel_markup, e_cancel_charges, e_cancel_service
                         , i_tds1, i_discount, i_cancel_markup, i_cancel_charges, i_cancel_service
                         , no_meal, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=None):
        res = {}
        hprice_obj = self.pool.get('tr.service.hotelpricing')
        servc_obj = self.pool.get('tr.product.services')

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
          
            res = {'name'  :  prod.name,           
                   'currency_id': prod.currency_id.id,             
                   }
            res.update(taxon_vals)
            
            if meal_id and rmcateg_id and checkin and checkout:
                checkin  = (parser.parse(''.join((re.compile('\d')).findall(checkin)))).strftime('%Y-%m-%d')
                checkout = (parser.parse(''.join((re.compile('\d')).findall(checkout)))).strftime('%Y-%m-%d')
                             
                cr.execute(" select * \
                             from tr_service_hotelpricing where service_id = %d and rmcateg_id = %d \
                             and meal_id = %d \
                             and ('%s'::date between valid_from and valid_to \
                             or '%s'::date between valid_from and valid_to) \
                             order by valid_to"%(prod.service_id.id, rmcateg_id, meal_id, checkin, checkout))
                hpvals = cr.dictfetchall()
                
                ci = checkin
                co = checkout
                nof_days = 1
                a = datetime.strptime(ci,"%Y-%m-%d")
                b = datetime.strptime(co, "%Y-%m-%d")
                d_delta = b - a
                if d_delta.days > 0: nof_days = d_delta.days
            
                if len(hpvals) == 1:
                    hpvals = hpvals[0]
                    del hpvals['id']
                    return {'value': hpvals}
                
                else:
                    a_basic = a_markup = a_tac = a_tds = a_servicechrg = a_other = a_tptax = 0.00
                    tn_basic = tn_markup = tn_tac = tn_tds = tn_servicechrg = tn_other = tn_tptax = 0.00
                    t3_basic = t3_markup = t3_tac = t3_tds = t3_servicechrg = t3_other = t3_tptax = 0.00
                    c_basic = c_markup = c_tac = c_tds = c_servicechrg = c_other = c_tptax = 0.00
                    cn_basic = cn_markup = cn_tac = cn_tds = cn_servicechrg = cn_other = cn_tptax = 0.00
                    e_basic = e_markup = e_tac = e_tds = e_servicechrg = e_other = e_tptax = 0.00
                    i_basic = i_markup = i_tac = i_tds = i_servicechrg = i_other = i_tptax = 0.00
                    early_chkin = late_chkout = meal_rate = meal_tax = 0.00
                         
                    for pr in hpvals:
                        if co > pr['valid_to']:
                           a = datetime.strptime(ci,"%Y-%m-%d")
                           b = datetime.strptime(pr['valid_to'], "%Y-%m-%d")
                           delta = b - a
                           
                        elif co < pr['valid_to']:
                           a = datetime.strptime(ci,"%Y-%m-%d")
                           b = datetime.strptime(co, "%Y-%m-%d")
                           delta = b - a
                           
                        if delta:
                            a_basic   += pr['a_basic'] * delta.days or 0
                            a_markup  += pr['a_markup'] * delta.days or 0
                            a_tac     += pr['a_tac'] * delta.days or 0
                            a_tds     += pr['a_tds'] * delta.days or 0
                            a_servicechrg += pr['a_servicechrg'] * delta.days or 0
                            a_other   += pr['a_other'] * delta.days or 0 
                            a_tptax   += pr['a_tptax'] * delta.days or 0
                            
                            tn_basic   += pr['tn_basic'] * delta.days or 0
                            tn_markup  += pr['tn_markup'] * delta.days or 0
                            tn_tac     += pr['tn_tac'] * delta.days or 0
                            tn_tds     += pr['tn_tds'] * delta.days or 0
                            tn_servicechrg += pr['tn_servicechrg'] * delta.days or 0
                            tn_other   += pr['tn_other'] * delta.days or 0 
                            tn_tptax   += pr['tn_tptax'] * delta.days or 0
                            
                            t3_basic   += pr['t3_basic'] * delta.days or 0
                            t3_markup  += pr['t3_markup'] * delta.days or 0
                            t3_tac     += pr['t3_tac'] * delta.days or 0
                            t3_tds     += pr['t3_tds'] * delta.days or 0
                            t3_servicechrg += pr['t3_servicechrg'] * delta.days or 0
                            t3_other   += pr['t3_other'] * delta.days or 0 
                            t3_tptax   += pr['t3_tptax'] * delta.days or 0
                            
                            c_basic   += pr['c_basic'] * delta.days or 0
                            c_markup  += pr['c_markup'] * delta.days or 0
                            c_tac     += pr['c_tac'] * delta.days or 0
                            c_tds     += pr['c_tds'] * delta.days or 0
                            c_servicechrg += pr['c_servicechrg'] * delta.days or 0
                            c_other   += pr['c_other'] * delta.days or 0 
                            c_tptax   += pr['c_tptax'] * delta.days or 0
                            
                            cn_basic   += pr['cn_basic'] * delta.days or 0
                            cn_markup  += pr['cn_markup'] * delta.days or 0
                            cn_tac     += pr['cn_tac'] * delta.days or 0
                            cn_tds     += pr['cn_tds'] * delta.days or 0
                            cn_servicechrg += pr['cn_servicechrg'] * delta.days or 0
                            cn_other   += pr['cn_other'] * delta.days or 0 
                            cn_tptax   += pr['cn_tptax'] * delta.days or 0
                            
                            e_basic   += pr['e_basic'] * delta.days or 0
                            e_markup  += pr['e_markup'] * delta.days or 0
                            e_tac     += pr['e_tac'] * delta.days or 0
                            e_tds     += pr['e_tds'] * delta.days or 0
                            e_servicechrg += pr['e_servicechrg'] * delta.days or 0
                            e_other   += pr['e_other'] * delta.days or 0 
                            e_tptax   += pr['e_tptax'] * delta.days or 0
                            
                            i_basic   += pr['i_basic'] * delta.days or 0
                            i_markup  += pr['i_markup'] * delta.days or 0
                            i_tac     += pr['i_tac'] * delta.days or 0
                            i_tds     += pr['i_tds'] * delta.days or 0
                            i_servicechrg += pr['i_servicechrg'] * delta.days or 0
                            i_other   += pr['i_other'] * delta.days or 0 
                            i_tptax   += pr['i_tptax'] * delta.days or 0
                            
                            early_chkin += pr['early_chkin']
                            late_chkout += pr['late_chkout']
                            meal_rate   += pr['meal_rate']
                            meal_tax    += pr['meal_tax']

                        ci = pr['valid_to']
                    
                    pvals = {'a_basic'   : (a_basic / nof_days),
                                    'a_markup'  : (a_markup / nof_days),
                                    'a_tac'     : (a_tac / nof_days),
                                    'a_tds'     : (a_tds / nof_days),
                                    'a_servicechrg' : (a_servicechrg / nof_days),
                                    'a_other'       : (a_other / nof_days),
                                    'a_tptax'       : (a_tptax / nof_days),
                                    
                                    'tn_basic'   : (tn_basic / nof_days),
                                    'tn_markup'  : (tn_markup / nof_days),
                                    'tn_tac'     : (tn_tac / nof_days),
                                    'tn_tds'     : (tn_tds / nof_days),
                                    'tn_servicechrg' : (tn_servicechrg / nof_days),
                                    'tn_other'       : (tn_other / nof_days),
                                    'tn_tptax'       : (tn_tptax / nof_days),
                                    
                                    't3_basic'   : (t3_basic / nof_days),
                                    't3_markup'  : (t3_markup / nof_days),
                                    't3_tac'     : (t3_tac / nof_days),
                                    't3_tds'     : (t3_tds / nof_days),
                                    't3_servicechrg' : (t3_servicechrg / nof_days),
                                    't3_other'       : (t3_other / nof_days),
                                    't3_tptax'       : (t3_tptax / nof_days),
                                    
                                    'c_basic'   : (c_basic / nof_days),
                                    'c_markup'  : (c_markup / nof_days),
                                    'c_tac'     : (c_tac / nof_days),
                                    'c_tds'     : (c_tds / nof_days),
                                    'c_servicechrg' : (c_servicechrg / nof_days),
                                    'c_other'       : (c_other / nof_days),
                                    'c_tptax'       : (c_tptax / nof_days),
                                    
                                    'cn_basic'   : (cn_basic / nof_days),
                                    'cn_markup'  : (cn_markup / nof_days),
                                    'cn_tac'     : (cn_tac / nof_days),
                                    'cn_tds'     : (cn_tds / nof_days),
                                    'cn_servicechrg' : (cn_servicechrg / nof_days),
                                    'cn_other'       : (cn_other / nof_days),
                                    'cn_tptax'       : (cn_tptax / nof_days),
                                    
                                    'e_basic'   : (e_basic / nof_days),
                                    'e_markup'  : (e_markup / nof_days),
                                    'e_tac'     : (e_tac / nof_days),
                                    'e_tds'     : (e_tds / nof_days),
                                    'e_servicechrg' : (e_servicechrg / nof_days),
                                    'e_other'       : (e_other / nof_days),
                                    'e_tptax'       : (e_tptax / nof_days),
                                    
                                    'i_basic'   : (i_basic / nof_days),
                                    'i_markup'  : (i_markup / nof_days),
                                    'i_tac'     : (i_tac / nof_days),
                                    'i_tds'     : (i_tds / nof_days),
                                    'i_servicechrg' : (i_servicechrg / nof_days),
                                    'i_other'       : (i_other / nof_days),
                                    'i_tptax'       : (i_tptax / nof_days),
                                    
                                    'early_chkin' : (early_chkin / nof_days),
                                    'late_chkout' : (late_chkout / nof_days),
                                    'meal_rate'   : (meal_rate / nof_days),
                                    'meal_tax'    : (meal_tax / nof_days),
                                    }
                    pvals.update(self.onchange_Hotel_onTPtax(cr, uid, ids, 'out_invoice', 'allpax', 'amt'
                                                , no_adult, pvals['a_basic'], pvals['a_other'], pvals['a_tac'], pvals['a_tds'], a_tds1, pvals['a_markup'], 0, pvals['a_servicechrg'], a_discount, a_cancel_markup, a_cancel_charges, a_cancel_service
                                                , no_twin, pvals['tn_basic'], pvals['tn_other'], pvals['tn_tac'], pvals['tn_tds'], tn_tds1, pvals['tn_markup'], 0, pvals['tn_servicechrg'], tn_discount, tn_cancel_markup, tn_cancel_charges, tn_cancel_service
                                                , no_triple, pvals['t3_basic'], pvals['t3_other'], pvals['t3_tac'], pvals['t3_tds'], t3_tds1, pvals['t3_markup'], 0, pvals['t3_servicechrg'], t3_discount, t3_cancel_markup, t3_cancel_charges, t3_cancel_service
                                                , no_cwb, pvals['c_basic'], pvals['c_other'], pvals['c_tac'], pvals['c_tds'], c_tds1, pvals['c_markup'], 0, pvals['c_servicechrg'], c_discount, c_cancel_markup, c_cancel_charges, c_cancel_service
                                                , no_cnb, pvals['cn_basic'], pvals['cn_other'], pvals['cn_tac'], pvals['cn_tds'], cn_tds1, pvals['cn_markup'], 0, pvals['cn_servicechrg'], cn_discount, cn_cancel_markup, cn_cancel_charges, cn_cancel_service
                                                , no_infant, pvals['i_basic'], pvals['i_other'], pvals['i_tac'], pvals['i_tds'], i_tds1, pvals['i_markup'], 0, pvals['i_servicechrg'], i_discount, i_cancel_markup, i_cancel_charges, i_cancel_service
                                                , no_extra, pvals['e_basic'], pvals['e_other'], pvals['e_tac'], pvals['e_tds'], e_tds1, pvals['e_markup'], 0, pvals['e_servicechrg'], e_discount, e_cancel_markup, e_cancel_charges, e_cancel_service
                                                , pvals['early_chkin'], pvals['late_chkout'], no_meal, pvals['meal_rate'], pvals['meal_tax'], tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context)['value'])
                    return {'value': pvals}
                    
        return {'value':res}
    
    def onchange_passenger(self, cr, uid, ids, paxpartner_id):
        # TODO: 
        # fetch passenger address   
       name = contact = email = ''
       
       if paxpartner_id:
           p = self.pool.get('res.partner').browse(cr, uid, paxpartner_id)
           name = p.name
           contact = p.mobile
           email = p.email
           
       return {'value':{'pax_name': name, 'pax_contact': contact, 'pax_email': email,
                        }}
    
    
    def onchange_Hotel_total(self, cr, uid, ids, inv_type, chkwhich, calledby, no_pax, basic, other, tac_perc, tac, tds_perc, tds, tds1_perc, tds1, markup_perc, markup
                           , servicechrg_perc, servicechrg, discount, cancel_markup, cancel_charges, cancel_service, tptax_basic
                           , tptax_other, tptax_tac, tptax_tds, tptax_ids, is_sc=False, context=None):
        
        """ 
            Method  :: common for both Adult,Extra,Child & Infant
            Used    :: in Product- Hotel
            Returns :: Total 
        """
        
        dp = get_dp_precision(cr, uid, 'Account')
        res = {}
        tptax = tpamt4tax = 0.00
        
        # Calculate when percent/other fields are called:
        if calledby == 'all':
            if tac_perc:
                tac = round(((tac_perc * basic) / 100.00), 2)
                res['tac'] = tac
                
            if tds_perc:
                tds = round(((tds_perc * tac) / 100.00), 2)
                res['tds'] = tds
                
            if tds1_perc:
                tds1 = round(((tds1_perc * discount) / 100.00), dp)
                res['tds1'] = tds1     
                
            if markup_perc:
                markup = round(((markup_perc * basic) / 100.00), 2)
                res['markup'] = markup
                 
        if tptax_basic == True : tpamt4tax += basic
        if tptax_other == True : tpamt4tax += other
        if tptax_tac == True : tpamt4tax += tac
        if tptax_tds == True : tpamt4tax += tds
               
        if context and context.get('calledfrm','') == 'func':
            for ttx in tptax_ids:
                tptax += round((tpamt4tax * ttx.amount), dp)
        else:
            for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
                tptax += round((tpamt4tax * ttx['amount']), dp)   

        res['tptax'] = tptax
        
        subrate = basic  + other + markup + tptax 
        
        if inv_type in ('out_invoice', 'out_refund'):
            subrate = basic + markup + other + tptax + tds1 - discount
            if not is_sc and servicechrg_perc:
                servicechrg = round(((servicechrg_perc * subrate)/100.00), dp)
                res['servicechrg'] = servicechrg
            subrate = (subrate + servicechrg - cancel_markup - cancel_charges - cancel_service) * no_pax
            res['po_rate'] = (basic + other + tptax + tds - tac - cancel_charges) * no_pax 
        else:
            subrate = (basic + other + tptax + tds - tac - cancel_charges) * no_pax 

        res['rate'] = subrate
        
        result = {}
        pax_map = {'adult':'a_', 'twin':'tn_' , 'triple':'t3_' , 'cwb':'c_' , 'cnb':'cn_' , 'extra': 'e_', 'infant':'i_'}
        for r in res.keys():
            result[pax_map[chkwhich]+r] = res[r]
        return {'value': result}
    
    
    def onchange_Hotel_onTPtax(self, cr, uid, ids, inv_type, chkpax, chkwhich, no_adult, a_basic, a_other, a_tac, a_tds, a_tds1, a_markup, a_servicechrg_perc, a_servicechrg, a_discount, a_cancel_markup, a_cancel_charges, a_cancel_service
                             , no_twin, tn_basic, tn_other, tn_tac, tn_tds, tn_tds1, tn_markup, tn_servicechrg_perc, tn_servicechrg, tn_discount, tn_cancel_markup, tn_cancel_charges, tn_cancel_service
                             , no_triple, t3_basic,  t3_other, t3_tac, t3_tds, t3_tds1, t3_markup, t3_servicechrg_perc, t3_servicechrg, t3_discount, t3_cancel_markup, t3_cancel_charges, t3_cancel_service
                             , no_cwb, c_basic, c_other, c_tac, c_tds, c_tds1, c_markup, c_servicechrg_perc, c_servicechrg, c_discount, c_cancel_markup, c_cancel_charges, c_cancel_service
                             , no_cnb, cn_basic, cn_other, cn_tac, cn_tds, cn_tds1, cn_markup, cn_servicechrg_perc, cn_servicechrg, cn_discount, cn_cancel_markup, cn_cancel_charges, cn_cancel_service
                             , no_infant, i_basic, i_other, i_tac, i_tds, i_tds1, i_markup, i_servicechrg_perc, i_servicechrg, i_discount, i_cancel_markup, i_cancel_charges, i_cancel_service
                             , no_extra, e_basic, e_other, e_tac, e_tds, e_tds1, e_markup, e_servicechrg_perc, e_servicechrg, e_discount, e_cancel_markup, e_cancel_charges, e_cancel_service
                             , early_chkin, late_chkout, no_meal, meal_rate, meal_tax, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=None):
        
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        
        if chkpax in ('adult', 'allpax'):
            res.update(self.onchange_Hotel_total(cr, uid, ids, inv_type, 'adult', 'all', no_adult, a_basic, a_other, 0, a_tac,  0, a_tds, 0, a_tds1, 0, a_markup 
                               , a_servicechrg_perc, a_servicechrg, a_discount, a_cancel_markup, a_cancel_charges, a_cancel_service, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        if chkpax in ('twin', 'allpax'):
            res.update(self.onchange_Hotel_total(cr, uid, ids, inv_type, 'twin', 'all', no_twin, tn_basic, tn_other, 0, tn_tac, 0, tn_tds, 0, tn_tds1, 0, tn_markup
                               , tn_servicechrg_perc, tn_servicechrg, tn_discount, tn_cancel_markup, tn_cancel_charges, tn_cancel_service, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        if chkpax in ('triple', 'allpax'):
            res.update(self.onchange_Hotel_total(cr, uid, ids, inv_type, 'triple', 'all', no_triple, t3_basic, t3_other, 0, t3_tac, 0, t3_tds, 0, t3_tds1, 0, t3_markup 
                               , t3_servicechrg_perc, t3_servicechrg, t3_discount, t3_cancel_markup, t3_cancel_charges, t3_cancel_service, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
           
        if chkpax in ('cwb', 'allpax'):
            res.update(self.onchange_Hotel_total(cr, uid, ids, inv_type, 'cwb', 'all', no_cwb, c_basic, c_other, 0, c_tac, 0, c_tds, 0, c_tds1, 0, c_markup 
                               , c_servicechrg_perc, c_servicechrg, c_discount, c_cancel_markup, c_cancel_charges, c_cancel_service, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        if chkpax in ('cnb', 'allpax'):
            res.update(self.onchange_Hotel_total(cr, uid, ids, inv_type, 'cnb', 'all', no_cnb, cn_basic, cn_other, 0, cn_tac, 0, cn_tds, 0, cn_tds1, 0, cn_markup 
                               , cn_servicechrg_perc, cn_servicechrg, cn_discount, cn_cancel_markup, cn_cancel_charges, cn_cancel_service, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        if chkpax in ('infant', 'allpax'):
            res.update(self.onchange_Hotel_total(cr, uid, ids, inv_type, 'infant', 'all', no_infant, i_basic, i_other, 0, i_tac, 0,  i_tds, 0, i_tds1, 0,  i_markup 
                               ,  i_servicechrg_perc, i_servicechrg, i_discount, i_cancel_markup, i_cancel_charges, i_cancel_service, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        if chkpax in ('extra', 'allpax'):
            res.update(self.onchange_Hotel_total(cr, uid, ids, inv_type, 'extra', 'all', no_extra, e_basic, e_other, 0, e_tac, 0, e_tds, 0, e_tds1, 0, e_markup 
                               , e_servicechrg_perc, e_servicechrg, e_discount, e_cancel_markup, e_cancel_charges, e_cancel_service, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        tmc = no_meal * (meal_rate + meal_tax)
        res['meal_cost'] = tmc
        res['subtotal'] = res.get('a_rate', 0) + res.get('tn_rate', 0) + res.get('t3_rate', 0) + res.get('c_rate', 0) + res.get('cn_rate', 0) + res.get('i_rate', 0) + res.get('e_rate', 0) + tmc + early_chkin + late_chkout
        res['po_subtotal'] = res.get('a_po_rate', 0) + res.get('tn_po_rate', 0) + res.get('t3_po_rate', 0) + res.get('c_po_rate', 0) + res.get('cn_po_rate', 0) + res.get('i_po_rate', 0) + res.get('e_po_rate', 0) + tmc + early_chkin + late_chkout
        
        return {'value' : res}

    def print_voucher(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = ids
            data['model'] = 'tr.invoice.hotel'
            data['output_type'] = 'pdf'
            data['variables'] = {'hotel_id':case.id,    
                                 'invoice_id':case.invoice_id.id,
                                 'uid' : uid
                                 }
            return {'type': 'ir.actions.report.xml',
                    'report_name':'ht_voucher',
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
            nartn = case.invoice_id.travel_type == 'dom_hotel' and'Domestic Hotel' or 'International Hotel'
            nartn += ', Pax: ' + str(case.pax_name) + ", Hotel: " + str(case.name) 
            nartn += ", Check-in: " + str(case.check_in) + ", Check-out: " + str(case.check_out) 
            getamt = self.calc_Hotel_total(cr, uid, case.id, case.inv_type)
            subtot = getamt.get('subtotal',0)

            inv_currency = case.invoice_id.currency_id.id
            subtot = cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, subtot, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                
            vals = {
                'name'        : nartn,
                'passenger'   : case.pax_name,
                'tpartner_id' : case.tpartner_id.id,
                'product_id'  : case.product_id.id or False,
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
                             'hotel_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('hotel_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True

    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_hotel, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
      
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_hotel, self).write(cr, uid, ids, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: