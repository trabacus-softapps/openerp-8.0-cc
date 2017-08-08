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

class tr_invoice_activity(osv.osv):
    _name = 'tr.invoice.activity'
    _description = 'Invoice - Activity'
    
    def calc_activity_total(self, cr, uid, id, inv_type, context=None):
        res = {}
        if context == None: context = {}
        ctx = context.copy()
        ctx['calledfrm'] = 'func'
        
        case = self.browse(cr, uid, id)
        inv_type = inv_type and inv_type or case.inv_type
        res = self.onchange_ACT_total(cr, uid, [case.id], inv_type, case.no_adult, case.a_basic, case.a_tac, case.a_markup, case.a_tds, case.a_discount, case.a_tds1
                                                        , case.a_servicechrg_perc, case.a_servicechrg, case.a_cancel_markup, case.a_cancel_charges, case.a_cancel_service
                                      
                                                        , case.no_child, case.c_basic, case.c_tac, case.c_markup, case.c_tds , case.c_discount
                                                        , case.c_tds1, case.c_servicechrg_perc, case.c_servicechrg, case.c_cancel_markup, case.c_cancel_charges
                                                        , case.c_cancel_service
                                                        
                                                        , case.no_infant, case.i_basic, case.i_tac,case.i_markup, case.i_tds, case.i_discount, case.i_tds1
                                                        , case.i_servicechrg_perc, case.i_servicechrg, case.i_cancel_markup, case.i_cancel_charges, case.i_cancel_service
                                                        , case.tptax_basic, case.tptax_tac, case.tptax_tds, case.tptax_ids, ctx)['value']
        
        res['subtotal'] = res.get('a_subtotal',0) + res.get('c_subtotal',0) + res.get('i_subtotal',0)
        res['po_subtotal'] = res.get('a_po_subtotal',0) + res.get('c_po_subtotal',0) + res.get('i_po_subtotal',0)
        res['tac'] = (case.a_tac * case.no_adult) + (case.c_tac * case.no_child) + (case.i_tac * case.no_infant)
        res['tds'] = (case.a_tds * case.no_adult) + (case.c_tds * case.no_child) + (case.i_tds * case.no_infant)
        res['tds1'] = (case.a_tds1 * case.no_adult) + (case.c_tds1 * case.no_child) + (case.i_tds1 * case.no_infant)
        res['basic'] = (case.a_basic * case.no_adult) + (case.c_basic * case.no_child) + (case.i_basic * case.no_infant)
        res['other'] = (res.get('a_tptax',0) * case.no_adult) + (res.get('c_tptax',0) * case.no_child) + (res.get('i_tptax',0) * case.no_infant)
        res['discount'] = (case.a_discount * case.no_adult) + (case.c_discount * case.no_child) + (case.i_discount * case.no_infant)
        res['markup'] = ((case.a_markup * case.no_adult) + (case.c_markup * case.no_child) + (case.i_markup * case.no_infant))
        res['servicechrg'] = (case.a_servicechrg * case.no_adult) + (case.c_servicechrg * case.no_child) + (case.i_servicechrg * case.no_infant)
        
        res['cancel_markup'] = ((case.a_cancel_markup * case.no_adult) + (case.c_cancel_markup * case.no_child) + (case.i_cancel_markup * case.no_infant))
        res['cancel_charges'] = ((case.a_cancel_charges * case.no_adult) + (case.c_cancel_charges * case.no_child) + (case.i_cancel_charges * case.no_infant))
        res['cancel_service'] = ((case.a_cancel_service * case.no_adult) + (case.c_cancel_service * case.no_child) + (case.i_cancel_service * case.no_infant))           
        
        return res
    
    def _get_all_total(self, cr, uid, ids, field_name, arg, context):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        cur_obj = self.pool.get('res.currency')

        for case in self.browse(cr, uid, ids):
              
            getamt = self.calc_activity_total(cr, uid, case.id, case.inv_type)
            res[case.id] = {
                            'a_tptax': getamt.get('a_tptax', 0), 'c_tptax': getamt.get('c_tptax', 0), 'i_tptax': getamt.get('i_tptax', 0),
                            'a_subtotal': getamt.get('a_subtotal', 0), 'c_subtotal': getamt.get('c_subtotal', 0), 'i_subtotal': getamt.get('i_subtotal', 0)
                            }
            res[case.id]['subtotal'] = getamt.get('subtotal',0)
            res[case.id]['po_subtotal'] = getamt.get('po_subtotal',0)
            res[case.id]['basicother'] = getamt.get('subtotal',0)

            def _calc_tax(case, no_pax, basic, markup, tac, tds, tds1, tptax, servicechrg):
                amt4tax = tx = 0.00
                if case.tax_basic == True: amt4tax += no_pax * basic   
                if case.tax_mark == True: amt4tax += no_pax * markup   
                if case.tax_tac == True: amt4tax += no_pax * tac   
                if case.tax_tds == True: amt4tax += no_pax * tds   
                if case.tax_tds1 == True: amt4tax += no_pax * tds1   
                if case.tax_tptax == True: amt4tax += no_pax * tptax   
                if case.tax_servicechrg == True: amt4tax += no_pax * servicechrg

                for t in case.tax_ids:
                    tx += round((amt4tax * t.amount), dp)
                return {'amt4tx':amt4tax, 'tax':tx}

            atx = _calc_tax(case, case.no_adult, case.a_basic, case.a_markup, case.a_tac, case.a_tds, case.a_tds1, case.a_servicechrg, getamt.get('a_tptax', 0))
            ctx = _calc_tax(case, case.no_child, case.c_basic, case.c_markup, case.c_tac, case.c_tds, case.c_tds1, case.c_servicechrg, getamt.get('c_tptax', 0))
            itx = _calc_tax(case, case.no_infant, case.i_basic, case.i_markup, case.i_tac, case.i_tds, case.i_tds1, case.i_servicechrg, getamt.get('i_tptax', 0))
             
            res[case.id].update({'a_tax': atx['tax'], 'c_tax': ctx['tax'], 'i_tax' : itx['tax'] 
                                , 'taxes' : (atx['tax'] + ctx['tax'] + itx['tax'])
                                , 'tax_base' : (atx['amt4tx'] + ctx['amt4tx'] + itx['amt4tx'])
                                , 'markup' : getamt.get('markup',0)
                                })
            res[case.id]['total'] = getamt.get('subtotal',0) + res[case.id]['taxes']
            
        return res
            
    def default_get(self, cr, uid, fields, context=None):
        res = super(tr_invoice_activity, self).default_get(cr, uid, fields, context=context)
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
                 
                'product_id'  : fields.many2one('product.product', 'Product', ondelete='restrict', domain=[('travel_type','=','activity')]), 
                'name'        : fields.char('Description', size=100, required=True),
                'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict'), 
                'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                    , help="The income or expense account related to the selected product."),
                'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
                'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
                'src_id'      : fields.many2one('tr.invoice.activity', 'Source Reference'),
                
                'details'     : fields.text('Details'),
                'act_date'    : fields.date('Date'),
                'pick_up'     : fields.char('Pick Up', size=500),
                'drop_at'     : fields.char('Drop At', size=500),
                
                # Adult
                'no_adult'      : fields.integer('No of Adult'),
                'a_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'a_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'a_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'a_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'a_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'a_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
                'a_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'a_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')), 
                'a_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'a_discount'    : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'a_cancel_markup'     : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'a_cancel_charges'    : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'a_servicechrg_perc'  : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
                'a_servicechrg'       : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'a_cancel_service': fields.float('Cancel Service Charge', digits_compute=dp.get_precision('Account')),
                'a_tptax'       : fields.function(_get_all_total, string='T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_subtotal'    : fields.function(_get_all_total, string='Subtotal', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_tax'         : fields.function(_get_all_total, string='Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_total'       : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                
                # Child
                'no_child'      : fields.integer('No of Children'),
                'c_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'c_tac_perc'    : fields.float('TAC (C) %', digits_compute=dp.get_precision('Account')),
                'c_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'c_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'c_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'c_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'c_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
                'c_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'c_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'c_discount'    : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'c_cancel_markup'     : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'c_cancel_charges'    : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'c_servicechrg_perc'  : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
                'c_servicechrg'       : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'c_cancel_service': fields.float('Cancel Service Charge', digits_compute=dp.get_precision('Account')),
                'c_tptax'       : fields.function(_get_all_total, string='T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_subtotal'    : fields.function(_get_all_total, string='Subtotal', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_tax'         : fields.function(_get_all_total, string='Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_total'       : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                
                
                 # Infant
                'no_infant'     : fields.integer('No of Infant'),
                'i_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'i_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'i_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'i_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'i_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'i_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
                'i_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'i_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')), 
                'i_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'i_discount'    : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'i_cancel_markup'      : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'i_cancel_charges'     : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'i_servicechrg_perc'   : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
                'i_servicechrg'        : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'i_cancel_service' : fields.float('Cancel Service Charge', digits_compute=dp.get_precision('Account')),
                'i_tptax'       : fields.function(_get_all_total, string='T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_subtotal'    : fields.function(_get_all_total, string='Subtotal', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_tax'         : fields.function(_get_all_total, string='Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_total'       : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
  
                'tax_basic'   : fields.boolean('On Basic'),
                'tax_tac'     : fields.boolean('On TAC'),
                'tax_tds'     : fields.boolean('On TDS(T)'),
                'tax_tds1'    : fields.boolean('On TDS(D)'),
                'tax_mark'    : fields.boolean('On Mark Up'),
                'tax_tptax'   : fields.boolean('On T.P. Tax'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                'tax_ids'     : fields.many2many('account.tax', 'activity_tax_rel', 'act_id', 'tax_id', 'Taxes'),
                
                'tptax_basic' : fields.boolean('On Basic'),
                'tptax_tac'   : fields.boolean('On TAC'),
                'tptax_tds'   : fields.boolean('On TDS(T)'),
                'tptax_ids'   : fields.many2many('account.tax', 'activity_tptax_rel', 'act_id', 'tax_id', 'T.P. Taxes'),
                
                'basicother'   : fields.function(_get_all_total, string='Basic + other', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'markup'       : fields.function(_get_all_total, string='Markup', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'subtotal'     : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'taxes'        : fields.function(_get_all_total, string='Taxes', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'tax_base'     : fields.function(_get_all_total, string='Tax Base', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'total'        : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'po_subtotal'  : fields.function(_get_all_total, string='PO Subtotal', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                
                }
    
    _defaults = {
                 'account_id' : _default_account_id,
                 'inv_type' : lambda self,cr,uid,c: c.get('type', ''),
                 'no_adult' : 1,
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
          
          res = {'name': prod.name_template, 'currency_id': prod.currency_id.id,
                 'tax_ids': map(lambda x: x.id, prod.taxes_id),
                 'a_basic': prod.a_basic,'a_tac_perc': prod.a_tac_perc, 'a_tac': prod.a_tac,'a_markup_perc': prod.a_markup_perc, 'a_markup': prod.a_markup,
                 'a_tds_perc': prod.a_tds_perc, 'a_tds': prod.a_tds, 'a_servicechrg_perc': prod.a_servicechrg_perc, 'a_servicechrg': prod.a_servicechrg,                   
                 'c_basic': prod.c_basic,'c_tac_perc': prod.c_tac_perc, 'c_tac': prod.c_tac,'c_markup_perc': prod.c_markup_perc, 'c_markup': prod.c_markup,
                 'c_tds_perc': prod.c_tds_perc, 'c_tds': prod.c_tds, 'c_servicechrg_perc': prod.c_servicechrg_perc, 'c_servicechrg': prod.c_servicechrg,
                 'i_basic': prod.i_basic,'i_tac_perc': prod.i_tac_perc, 'i_tac': prod.i_tac,'i_markup_perc': prod.i_markup_perc, 'i_markup': prod.i_markup,
                 'i_tds_perc': prod.i_tds_perc, 'i_tds': prod.i_tds, 'i_servicechrg_perc': prod.i_servicechrg_perc, 'i_servicechrg': prod.i_servicechrg,
                 'tptax_basic': prod.tptax_basic, 'tptax_tac': prod.tptax_tac, 'tptax_tds': prod.tptax_tds,
                 'tptax_ids': map(lambda x: x.id, prod.tptax_ids),
                 'currency_id': prod.currency_id.id,
                }
          res.update(taxon_vals)
      return {'value':res}
    
    
    def onchange_paxtotal(self, cr, uid, ids, inv_type, chkwhich, calledby, no_pax, basic, tac_perc, tac, markup_perc, markup
                          , tds_perc, tds,  discount, tds1_perc, tds1, servicechrg_perc, servicechrg, cancel_markup, cancel_charges, cancel_service
                           , tptax_basic, tptax_tac, tptax_tds, tptax_ids, is_sc=False, context=None):
        res = {}
        
        tpamt4tax = tptax = 0.0
        
        dp = get_dp_precision(cr, uid, 'Account') 
        
        if calledby == 'all':
            if tac_perc:
                tac = round(((tac_perc * basic)/100.00), dp)
                res['tac'] = tac
                
            if markup_perc:
                markup = round(((markup_perc * basic)/100.00), dp)
                res['markup'] = markup
            
            if tds_perc:
                tds = round(((tds_perc * tac)/100.00), dp)
                res['tds'] = tds
                
            if tds1_perc:
                tds1 = round(((tds1_perc * discount)/100.00), dp)
                res['tds1'] = tds1
                
        if tptax_basic == True : tpamt4tax += basic
        if tptax_tac == True   : tpamt4tax += tac
        if tptax_tds == True   : tpamt4tax += tds
        
        if context and context.get('calledfrm','') == 'func':
            for ttx in tptax_ids:
                tptax += round((tpamt4tax * ttx.amount), dp)
        else:
            for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
                tptax += round((tpamt4tax * ttx['amount']), dp)

        if inv_type in ('out_invoice', 'out_refund'):
            subtot = (basic + markup + tptax + tds1 - discount)
            if not is_sc and servicechrg_perc:
                servicechrg = round(((servicechrg_perc * subtot)/100.00), dp)
                res['servicechrg'] = servicechrg
            subtot = (subtot + servicechrg - cancel_markup - cancel_charges - cancel_service) * no_pax
            res['po_subtotal'] = (basic + tptax + tds - tac - cancel_charges) * no_pax
        else:
            subtot = (basic + tptax + tds - tac - cancel_charges) * no_pax 
            
            
        res.update({'subtotal' : subtot,
                    'tptax': tptax
                    })
        
        result = {}
        pax_map = {'adult':'a_', 'child':'c_', 'infant':'i_'}
        for r in res.keys():
            result[pax_map[chkwhich]+r] = res[r]
             
        return {'value':result}
        
    def onchange_ACT_total(self, cr, uid, ids, inv_type, no_adult, a_basic, a_tac, a_markup, a_tds,  a_discount, a_tds1
                               , a_servicechrg_perc, a_servicechrg, a_cancel_markup, a_cancel_charges, a_cancel_service
                             
                               , no_child, c_basic, c_tac, c_markup, c_tds,  c_discount, c_tds1
                               , c_servicechrg_perc, c_servicechrg, c_cancel_markup, c_cancel_charges, c_cancel_service
                             
                               , no_infant, i_basic, i_tac, i_markup, i_tds,  i_discount, i_tds1
                               , i_servicechrg_perc, i_servicechrg, i_cancel_markup, i_cancel_charges, i_cancel_service
                               
                               , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=None):
        """ 
            Method  :: common for both Adult & Child
            Used    :: in Sales - Activities
            Returns :: subtotal
        """
        
        res = {}
        dp = get_dp_precision(cr, uid, 'Account') 
        
        res.update(self.onchange_paxtotal(cr, uid, ids, inv_type, 'adult', 'amt', no_adult, a_basic, 0, a_tac
                                          , 0, a_markup, 0, a_tds,  a_discount, 0, a_tds1
                                          , a_servicechrg_perc, a_servicechrg, a_cancel_markup, a_cancel_charges, a_cancel_service
                                          , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        res.update(self.onchange_paxtotal(cr, uid, ids, inv_type, 'child', 'amt', no_child, c_basic, 0, c_tac
                                          , 0, c_markup, 0, c_tds,  c_discount, 0, c_tds1
                                          , c_servicechrg_perc, c_servicechrg, c_cancel_markup, c_cancel_charges, c_cancel_service
                                          , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        res.update(self.onchange_paxtotal(cr, uid, ids, inv_type, 'infant', 'amt', no_infant, i_basic, 0, i_tac
                                          , 0, i_markup, 0, i_tds,  i_discount, 0, i_tds1
                                          , i_servicechrg_perc, i_servicechrg, i_cancel_markup, i_cancel_charges, i_cancel_service
                                          , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        return {'value':res}
    
    
    def print_voucher(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = ids
            data['model'] = 'tr.invoice.car'
            data['output_type'] = 'pdf'
            data['variables'] = {'activity_id':case.id,
                                 'invoice_id':case.invoice_id.id}
            return {'type': 'ir.actions.report.xml',
                    'report_name':'act_voucher',
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
            nartn = 'Activity : ' + str(case.name)
            getamt = self.calc_activity_total(cr, uid, case.id, case.inv_type)
            subtot = getamt.get('subtotal',0)
            
            inv_currency = case.invoice_id.currency_id.id
            subtot = cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, subtot, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                
            vals = {
                'name'      : nartn,
                'passenger' : '',
                'product_id' : case.product_id.id or False,
                'tpartner_id': case.tpartner_id.id,
                'origin'    : case.invoice_id.name,
                'account_id': case.account_id.id,
                'account_analytic_id' : case.invoice_id and case.invoice_id.account_analytic_id and case.invoice_id.account_analytic_id.id or False,
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
                             'activity_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('activity_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True

    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_activity, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
      
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_activity, self).write(cr, uid, ids, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result
    
class tr_invoice_addon(osv.osv):
    _name = 'tr.invoice.addon'
    _description = 'Invoice - Add On'
    
    def calc_addon_total(self, cr, uid, id, inv_type, context=None):
        res = {}
        if context == None: context = {}
        ctx = context.copy()
        ctx['calledfrm'] = 'func'
        
        case = self.browse(cr, uid, id)
        inv_type = inv_type and inv_type or case.inv_type
        res = self.onchange_ADDON_total(cr, uid, [case.id], inv_type, case.no_adult, case.a_basic, case.a_tac, case.a_markup, case.a_tds
                                                        ,  case.a_discount, case.a_tds1, case.a_servicechrg_perc, case.a_servicechrg
                                                        , case.a_cancel_markup, case.a_cancel_charges, case.a_cancel_service
                                      
                                                        , case.no_child, case.c_basic, case.c_tac, case.c_markup, case.c_tds
                                                        ,  case.c_discount, case.c_tds1, case.c_servicechrg_perc, case.c_servicechrg
                                                        , case.c_cancel_markup, case.c_cancel_charges, case.c_cancel_service
                                                        
                                                        , case.no_infant, case.i_basic, case.i_tac, case.i_markup, case.i_tds
                                                        , case.i_discount, case.i_tds1, case.i_servicechrg_perc, case.i_servicechrg
                                                        , case.i_cancel_markup, case.i_cancel_charges, case.i_cancel_service
                                                        
                                                        , case.tptax_basic, case.tptax_tac, case.tptax_tds, case.tptax_ids, ctx)['value']

        res['subtotal'] = res.get('a_subtotal',0) + res.get('c_subtotal',0) + res.get('i_subtotal',0)
        res['po_subtotal'] = res.get('a_po_subtotal',0) + res.get('c_po_subtotal',0) + res.get('i_po_subtotal',0)
        res['tac'] = (case.a_tac * case.no_adult) + (case.c_tac * case.no_child) + (case.i_tac * case.no_infant)
        res['tds'] = (case.a_tds * case.no_adult) + (case.c_tds * case.no_child) + (case.i_tds * case.no_infant)
        res['tds1'] = (case.a_tds1 * case.no_adult) + (case.c_tds1 * case.no_child) + (case.i_tds1 * case.no_infant)
        res['basic'] = (case.a_basic * case.no_adult) + (case.c_basic * case.no_child) + (case.i_basic * case.no_infant)
        res['other'] = (res.get('a_tptax',0) * case.no_adult) + (res.get('c_tptax',0) * case.no_child) + (res.get('i_tptax',0) * case.no_infant)
        res['discount'] = (case.a_discount * case.no_adult) + (case.c_discount * case.no_child) + (case.i_discount * case.no_infant)
        res['markup'] = ((case.a_markup * case.no_adult) + (case.c_markup * case.no_child) + (case.i_markup * case.no_infant))
        res['servicechrg'] = (case.a_servicechrg * case.no_adult) + (case.c_servicechrg * case.no_child)  + (case.i_servicechrg * case.no_infant)
        
        res['cancel_markup'] = ((case.a_cancel_markup * case.no_adult) + (case.c_cancel_markup * case.no_child) + (case.i_cancel_markup * case.no_infant))
        res['cancel_charges'] = ((case.a_cancel_charges * case.no_adult) + (case.c_cancel_charges * case.no_child) + (case.i_cancel_charges * case.no_infant))
        res['cancel_service'] = ((case.a_cancel_service * case.no_adult) + (case.c_cancel_service * case.no_child) + (case.i_cancel_service * case.no_infant))           

        return res
    
    def _get_all_total(self, cr, uid, ids, field_name, arg, context):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')

        for case in self.browse(cr, uid, ids):
              
            getamt = self.calc_addon_total(cr, uid, case.id, context)
            res[case.id] = {
                            'a_tptax': getamt.get('a_tptax', 0), 'c_tptax': getamt.get('c_tptax', 0), 'i_tptax': getamt.get('i_tptax', 0),
                            'a_subtotal': getamt.get('a_subtotal', 0), 'c_subtotal': getamt.get('c_subtotal', 0), 'i_subtotal': getamt.get('i_subtotal', 0)
                            }
            res[case.id]['subtotal'] = getamt.get('subtotal',0)
            res[case.id]['po_subtotal'] = getamt.get('po_subtotal',0)
            res[case.id]['basicother'] = getamt.get('subtotal',0)

            def _calc_tax(case, no_pax, basic, markup, tac, tds, tds1, tptax, servicechrg):
                amt4tax = tx = 0.00
                if case.tax_basic == True: amt4tax += no_pax * basic   
                if case.tax_mark == True: amt4tax += no_pax * markup   
                if case.tax_tac == True: amt4tax += no_pax * tac   
                if case.tax_tds == True: amt4tax += no_pax * tds   
                if case.tax_tds1 == True: amt4tax += no_pax * tds1   
                if case.tax_tptax == True: amt4tax += no_pax * tptax   
                if case.tax_servicechrg == True: amt4tax += no_pax * servicechrg

                for t in case.tax_ids:
                    tx += round((amt4tax * t.amount), dp)
                return {'amt4tx':amt4tax, 'tax':tx}

            atx = _calc_tax(case, case.no_adult, case.a_basic, case.a_markup, case.a_tac, case.a_tds, case.a_tds1, case.a_servicechrg, getamt.get('a_tptax', 0))
            ctx = _calc_tax(case, case.no_child, case.c_basic, case.c_markup, case.c_tac, case.c_tds, case.c_tds1, case.c_servicechrg, getamt.get('c_tptax', 0))
            itx = _calc_tax(case, case.no_infant, case.i_basic, case.i_markup, case.i_tac, case.i_tds, case.i_tds1, case.i_servicechrg, getamt.get('i_tptax', 0))
             
            res[case.id].update({'a_tax': atx['tax'], 'c_tax': ctx['tax'], 'i_tax' : itx['tax'] 
                                , 'taxes' : (atx['tax'] + ctx['tax'] + itx['tax'])
                                , 'tax_base' : (atx['amt4tx'] + ctx['amt4tx'] + itx['amt4tx'])
                                , 'markup' : getamt.get('markup',0)
                                })
            res[case.id]['total'] = getamt.get('subtotal',0) + res[case.id]['taxes']
        return res
            
    def default_get(self, cr, uid, fields, context=None):
        res = super(tr_invoice_addon, self).default_get(cr, uid, fields, context=context)
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
                 
                'product_id'  : fields.many2one('product.product', 'Product', ondelete='restrict', domain=[('travel_type','=','add_on')]), 
                'name'        : fields.char('Description', size=100, required=True),
                'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict'), 
                'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                    , help="The income or expense account related to the selected product."),
                'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
                'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
                'src_id'      : fields.many2one('tr.invoice.addon', 'Source Reference'),
                
                'details'  : fields.text('Details'),
                'ao_date'  : fields.date('Date'),
                'pick_up'  : fields.char('Pick Up', size=500),
                'drop_at'  : fields.char('Drop At', size=500), 
                
                # Adult
                'no_adult'      : fields.integer('No of Adult'),
                'a_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'a_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'a_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'a_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'a_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'a_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
                'a_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'a_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')), 
                'a_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'a_discount'    : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'a_cancel_markup'     : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'a_cancel_charges'    : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'a_servicechrg_perc'  : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
                'a_servicechrg'       : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'a_cancel_service': fields.float('Cancel Service Charge', digits_compute=dp.get_precision('Account')),
                'a_tptax'       : fields.function(_get_all_total, string='T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_subtotal'    : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_tax'         : fields.function(_get_all_total, string='Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'a_total'       : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                
                # Child
                'no_child'      : fields.integer('No of Children'),
                'c_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'c_tac_perc'    : fields.float('TAC (C) %', digits_compute=dp.get_precision('Account')),
                'c_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'c_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'c_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'c_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'c_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
                'c_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'c_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'c_discount'    : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'c_cancel_markup'     : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'c_cancel_charges'    : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'c_servicechrg_perc'  : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
                'c_servicechrg'       : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'c_cancel_service': fields.float('Cancel Service Charge', digits_compute=dp.get_precision('Account')),
                'c_tptax'       : fields.function(_get_all_total, string='T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_subtotal'    : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_tax'         : fields.function(_get_all_total, string='Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'c_total'       : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                
                
                 # Infant
                'no_infant'     : fields.integer('No of Infant'),
                'i_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'i_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'i_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'i_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'i_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'i_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
                'i_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'i_tds1'        : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')), 
                'i_tds1_perc'   : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'i_discount'    : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'i_cancel_markup'      : fields.float('Cancel Markup', digits_compute=dp.get_precision('Account')),
                'i_cancel_charges'     : fields.float('Cancel Charges', digits_compute=dp.get_precision('Account')),
                'i_servicechrg_perc'   : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
                'i_servicechrg'        : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'i_cancel_service' : fields.float('Cancel Service Charge', digits_compute=dp.get_precision('Account')),
                'i_tptax'       : fields.function(_get_all_total, string='T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_subtotal'    : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_tax'         : fields.function(_get_all_total, string='Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'i_total'       : fields.function(_get_all_total, string='Total', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
  
                'tax_basic'   : fields.boolean('On Basic'),
                'tax_tac'     : fields.boolean('On TAC'),
                'tax_tds'     : fields.boolean('On TDS(T)'),
                'tax_tds1'    : fields.boolean('On TDS(D)'),
                'tax_mark'    : fields.boolean('On Mark Up'),
                'tax_tptax'   : fields.boolean('On T.P. Tax'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                'tax_ids'   : fields.many2many('account.tax', 'addon_tax_rel', 'act_id', 'tax_id', 'Taxes'),
                
                'tptax_basic' : fields.boolean('On Basic'),
                'tptax_tac'   : fields.boolean('On TAC'),
                'tptax_tds'   : fields.boolean('On TDS(T)'),
                'tptax_ids'   : fields.many2many('account.tax', 'addon_tptax_rel', 'act_id', 'tax_id', 'T.P. Taxes'),
                
                'basicother'   : fields.function(_get_all_total, string='Basic + other', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
                'markup'       : fields.function(_get_all_total, string='Markup', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
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
          
          res = {'name': prod.name_template,
                 'tax_ids': map(lambda x: x.id, prod.taxes_id),
                 'a_basic': prod.a_basic,'a_tac_perc': prod.a_tac_perc, 'a_tac': prod.a_tac,'a_markup_perc': prod.a_markup_perc, 'a_markup': prod.a_markup,
                 'a_tds_perc': prod.a_tds_perc, 'a_tds': prod.a_tds, 'a_servicechrg_perc': prod.a_servicechrg_perc, 'a_servicechrg': prod.a_servicechrg,                   
                 'c_basic': prod.c_basic,'c_tac_perc': prod.c_tac_perc, 'c_tac': prod.c_tac,'c_markup_perc': prod.c_markup_perc, 'c_markup': prod.c_markup,
                 'c_tds_perc': prod.c_tds_perc, 'c_tds': prod.c_tds, 'c_servicechrg_perc': prod.c_servicechrg_perc, 'c_servicechrg': prod.c_servicechrg,
                 'i_basic': prod.i_basic,'i_tac_perc': prod.i_tac_perc, 'i_tac': prod.i_tac,'i_markup_perc': prod.i_markup_perc, 'i_markup': prod.i_markup,
                 'i_tds_perc': prod.i_tds_perc, 'i_tds': prod.i_tds, 'i_servicechrg_perc': prod.i_servicechrg_perc, 'i_servicechrg': prod.i_servicechrg,
                 'tptax_basic': prod.tptax_basic, 'tptax_tac': prod.tptax_tac, 'tptax_tds': prod.tptax_tds,
                 'tptax_ids': map(lambda x: x.id, prod.tptax_ids),
                 'currency_id': prod.currency_id.id,
                }
          res.update(taxon_vals)
      return {'value':res}
    
    
    def onchange_paxtotal(self, cr, uid, ids, inv_type, chkwhich, calledby, no_pax, basic, tac_perc, tac, markup_perc, markup
                          , tds_perc, tds,  discount, tds1_perc, tds1, servicechrg_perc, servicechrg, cancel_markup, cancel_charges, cancel_service
                           , tptax_basic, tptax_tac, tptax_tds, tptax_ids, is_sc=False, context=None):
        res = {}
        
        tpamt4tax = tptax = 0.0
        
        dp = get_dp_precision(cr, uid, 'Account') 
        
        if calledby == 'all':
            if tac_perc:
                tac = round(((tac_perc * basic)/100.00), dp)
                res['tac'] = tac
                
            if markup_perc:
                markup = round(((markup_perc * basic)/100.00), dp)
                res['markup'] = markup
            
            if tds_perc:
                tds = round(((tds_perc * tac)/100.00), dp)
                res['tds'] = tds
                
            if tds1_perc:
                tds1 = round(((tds1_perc * discount)/100.00), dp)
                res['tds1'] = tds1
                
        if tptax_basic == True : tpamt4tax += basic
        if tptax_tac == True   : tpamt4tax += tac
        if tptax_tds == True   : tpamt4tax += tds
        
        if context and context.get('calledfrm','') == 'func':
            for ttx in tptax_ids:
                tptax += round((tpamt4tax * ttx.amount), dp)
        else:
            for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
                tptax += round((tpamt4tax * ttx['amount']), dp)

        if inv_type in ('out_invoice', 'out_refund'):
            subtot = (basic + markup + tptax + tds1 - discount)
            if not is_sc and servicechrg_perc:
                servicechrg = round(((servicechrg_perc * subtot)/100.00), dp)
                res['servicechrg'] = servicechrg
            subtot = (subtot + servicechrg - cancel_markup - cancel_charges - cancel_service) * no_pax
            res['po_subtotal'] = (basic + tptax + tds - tac - cancel_charges) * no_pax
        else:
            subtot = (basic + tptax + tds - tac - cancel_charges) * no_pax 
           
            
        res.update({'subtotal' : subtot,
                    'tptax': tptax
                    })
        
        result = {}
        pax_map = {'adult':'a_', 'child':'c_', 'infant':'i_'}
        for r in res.keys():
            result[pax_map[chkwhich]+r] = res[r]
             
        return {'value':result}
        
    def onchange_ADDON_total(self, cr, uid, ids, inv_type, no_adult, a_basic, a_tac, a_markup, a_tds,  a_discount, a_tds1
                               , a_servicechrg_perc, a_servicechrg, a_cancel_markup, a_cancel_charges, a_cancel_service
                             
                               , no_child, c_basic, c_tac, c_markup, c_tds,  c_discount, c_tds1
                               , c_servicechrg_perc, c_servicechrg, c_cancel_markup, c_cancel_charges, c_cancel_service
                             
                               , no_infant, i_basic, i_tac, i_markup, i_tds,  i_discount, i_tds1
                               , i_servicechrg_perc, i_servicechrg, i_cancel_markup, i_cancel_charges, i_cancel_service
                               
                               , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=None):
        """ 
            Method  :: common for both Adult & Child
            Used    :: in Sales - Add On
            Returns :: subtotal
        """
        
        res = {}
        dp = get_dp_precision(cr, uid, 'Account') 
        
        res.update(self.onchange_paxtotal(cr, uid, ids, inv_type, 'adult', 'amt', no_adult, a_basic, 0, a_tac
                                          , 0, a_markup, 0, a_tds,  a_discount, 0, a_tds1
                                          , a_servicechrg_perc, a_servicechrg, a_cancel_markup, a_cancel_charges, a_cancel_service
                                          , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        res.update(self.onchange_paxtotal(cr, uid, ids, inv_type, 'child', 'amt', no_child, c_basic, 0, c_tac
                                          , 0, c_markup, 0, c_tds,  c_discount, 0, c_tds1
                                          , c_servicechrg_perc, c_servicechrg, c_cancel_markup, c_cancel_charges, c_cancel_service
                                          , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        res.update(self.onchange_paxtotal(cr, uid, ids, inv_type, 'infant', 'amt', no_infant, i_basic, 0, i_tac
                                          , 0, i_markup, 0, i_tds,  i_discount, 0, i_tds1
                                          , i_servicechrg_perc, i_servicechrg, i_cancel_markup, i_cancel_charges, i_cancel_service
                                          , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=context)['value'])
        
        return {'value':res}
    
    
    def print_voucher(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = ids
            data['model'] = 'tr.invoice.car'
            data['output_type'] = 'pdf'
            data['variables'] = {'addon_id':case.id,
                                 'invoice_id':case.invoice_id.id}
            return {'type': 'ir.actions.report.xml',
                    'report_name':'ao_voucher',
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
            nartn = 'Add-on : ' + str(case.name)
            getamt = self.calc_addon_total(cr, uid, case.id, case.inv_type)
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
                'account_analytic_id' : case.invoice_id and case.invoice_id.account_analytic_id and case.invoice_id.account_analytic_id.id or False,
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
                             'addon_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('addon_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True

    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_addon, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
      
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_addon, self).write(cr, uid, ids, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: