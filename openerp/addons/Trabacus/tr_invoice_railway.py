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


class tr_invoice_railway(osv.osv):
    _name = 'tr.invoice.railway'
    _description = 'Invoice - Railway' 
    
    def calc_RAIL_total(self, cr, uid, id, inv_type, context=None):
         
         res = {}
         if context == None: context = {}
         ctx = context.copy()
         ctx['calledfrm'] = 'func'
         
         case = self.browse(cr, uid, id)
         inv_type = inv_type and inv_type or case.inv_type
         res = self.onchange_RAIL_total(cr, uid, [case.id], case.inv_type, 'amt', case.basic, case.irctc, case.gateway, case.tac_perc, case.tac 
                                          , case.markup_perc, case.markup, case.tds_perc, case.tds, case.tds1_perc, case.tds1, case.servicechrg_perc, case.servicechrg
                                          , case.discount, case.cancel_markup, case.cancel_charges, case.cancel_service
                                          , case.tptax_basic, case.tptax_irctc, case.tptax_tac, case.tptax_tds, case.tptax_gateway
                                          , case.tptax_ids, False, ctx)['value']
                                          
         res['subtotal'] = res.get('subtotal',0)
         res['tac'] = case.tac
         res['tds'] = case.tds 
         res['tds1'] = case.tds1
         res['basic'] = case.basic
         res['other'] = res.get('tptax',0)
         res['discount'] = case.discount
         res['markup'] = case.markup
         res['servicechrg'] = case.servicechrg
         
         res['cancel_markup'] = case.cancel_markup
         res['cancel_charges'] = case.cancel_charges
         res['cancel_service'] = case.cancel_service         
        
         return res
     
    def _get_AllTotal(self, cr, uid, ids, field_name, arg, context):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')

        for case in self.browse(cr, uid, ids):
              
            getamt = self.calc_RAIL_total(cr, uid, case.id, case.inv_type)
            res[case.id] = {
                            'tptax': getamt.get('tptax', 0),
                            'subtotal': getamt.get('subtotal', 0),
                            'po_subtotal': getamt.get('po_subtotal', 0)
                            }
            
            amt4tax = tax = 0.00
            if case.tax_basic == True: amt4tax += case.basic   
            if case.tax_mark == True: amt4tax += case.markup 
            if case.tax_irctc == True: amt4tax += case.irctc  
            if case.tax_gateway == True: amt4tax += case.gateway
            if case.tax_tac == True: amt4tax += case.tac
            if case.tax_tds == True: amt4tax += case.tds   
            if case.tax_tds1 == True: amt4tax += case.tds1   
            if case.tax_tptax == True: amt4tax += getamt.get('tptax', 0)
            if case.tax_servicechrg == True: amt4tax += case.servicechrg
            
            for t in case.tax_ids:
                tax += round((amt4tax * t.amount), dp)
        
        res[case.id].update({
                             'taxes' : tax
                            , 'tax_base' : amt4tax
                            , 'markup' : getamt.get('markup',0)
                            })
        res[case.id]['total'] = getamt.get('subtotal',0) + res[case.id]['taxes']
        
        return res
#     
    
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
                 
                'product_id'  : fields.many2one('product.product', 'Product', ondelete='restrict', domain=[('travel_type','=','railway')]), 
                'name'        : fields.char('Description', size=100, required=True),
                'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict'), 
                'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                    , help="The income or expense account related to the selected product."),
                'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
                'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
                'src_id'      : fields.many2one('tr.invoice.railway', 'Source Reference'),
                
                'ticket_no' : fields.char('Ticket No', size=30),
                'travel_dt' : fields.date('Travel Date'),
                'train_no'  : fields.char('Train No', size=10),
                'train_name': fields.char('Train Name', size=30),
                'source'    : fields.char('From', size=30),
                'dest'      : fields.char('To', size=30),
                'rl_class'  : fields.selection([('cc','Chair Car'),('sl','Sleeper Class'),('ac_1','1A Class'),('ac_2','2A Class'),('ac_3','3A Class')],'Class'),
                'dep'       : fields.datetime('Departure'),
                'arr'       : fields.datetime('Arrival'),
                
                'basic'     : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'irctc'     : fields.float('IRCTC', digits_compute=dp.get_precision('Account')),
                'gateway'   : fields.float('Gateway', digits_compute=dp.get_precision('Account')),
                'tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
                'tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'tds_perc'  : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
                'tds'       : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
                'tds1_perc' : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'tds1'      : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')), 
                'tds1_perc' : fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
                'servicechrg'     : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'servicechrg_perc': fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                
                'discount'           : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'cancel_markup'      : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'cancel_charges'     : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')),
                'cancel_service' : fields.float('Cancel Service Charge', digits_compute=dp.get_precision('Account')),
            
                'tptax_ids'    : fields.many2many('account.tax', 'rail_tptax_rel', 'rlline_id', 'tax_id', 'T.P. Taxes'),
                'tptax_basic'    : fields.boolean('On Basic'),
                'tptax_irctc'    : fields.boolean('On IRCTC'),
                'tptax_tac'      : fields.boolean('On TAC'),
                'tptax_tds'      : fields.boolean('On TDS(T)'),
                'tptax_gateway'  : fields.boolean('On Gateway'),
                
                'basicother'  : fields.function(_get_AllTotal, string='Basic + Others', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),            
                'tptax'       : fields.function(_get_AllTotal, string='T.P.Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                'subtotal'    : fields.function(_get_AllTotal, string='Subtotal', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                'tax_base'    : fields.function(_get_AllTotal, string='Taxes Base', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'taxes'       : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                'total'       : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                'po_subtotal' : fields.function(_get_AllTotal, string='Subtotal', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
                        
                'tax_basic'    : fields.boolean('On Basic'),
                'tax_irctc'    : fields.boolean('On IRCTC'),
                'tax_tac'      : fields.boolean('On TAC'),
                'tax_gateway'  : fields.boolean('On Gateway'),
                'tax_tds'      : fields.boolean('On TDS(T)'),
                'tax_tds1'     : fields.boolean('On TDS(D)'),
                'tax_mark'     : fields.boolean('On Markup'),
                'tax_tptax'    : fields.boolean('On T.P. Tax'),
                'tax_servicechrg' : fields.boolean('On Service Charge'), 
                
                'tax_ids'   : fields.many2many('account.tax', 'rail_tax_rel', 'rail_id', 'tax_id', 'Taxes'), 
                'rail_lines': fields.one2many('tr.invoice.railway.lines', 'railway_id', 'Railway Lines'),
            
                }
    
    _defaults = {
                 'account_id' : _default_account_id,
                 'inv_type'   : lambda self,cr,uid,c: c.get('type', ''),
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
                }
          res.update(taxon_vals)
      return {'value':res}
  
 
    def onchange_RAIL_total(self, cr, uid, ids, inv_type, calledby, basic, irctc, gateway, tac_perc, tac, markup_perc, markup
                                , tds_perc,tds, tds1_perc, tds1, servicechrg_perc, servicechrg, discount, cancel_markup, cancel_charges
                                , cancel_service, tptax_basic, tptax_irctc, tptax_tac, tptax_tds, tptax_gateway, tptax_ids
                                , is_sc=False, context=None):
        """     
            Used    :: in Invoice/SO - Railway
            Returns :: Subtotal
        """
        
        res = {}
        tpamt4tax = tptax = 0.00
        dp = get_dp_precision(cr, uid, 'Account') 
        
        # Calculate when percent/other field is called:
        if calledby == 'all':
            if tac_perc:
                tac = round(((tac_perc * basic) / 100.00), dp)
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
        if tptax_irctc == True : tpamt4tax += irctc
        if tptax_tac == True   : tpamt4tax += tac
        if tptax_tds == True   : tpamt4tax += tds
        if tptax_gateway == True  : tpamt4tax += gateway
        
        if context and context.get('calledfrm','') == 'func':
            for ttx in tptax_ids:
                tptax += round((tpamt4tax * ttx.amount), dp)
        else:
            for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
                tptax += round((tpamt4tax * ttx['amount']), dp)
            
            
        if inv_type in ('out_invoice', 'out_refund'):
            subtot = basic + irctc + gateway + markup + tptax + tds1 - discount
            if not is_sc and servicechrg_perc:
                servicechrg = round(((servicechrg_perc * subtot)/100.00), dp)
                res['servicechrg'] = servicechrg
            subtot += servicechrg - cancel_markup - cancel_charges - cancel_service
            res['po_subtotal'] = basic + irctc + gateway + tptax + tds - tac - cancel_charges
        else:
            subtot = basic + irctc + gateway + tptax + tds - tac - cancel_charges
            
        res.update({'subtotal' : subtot,
                    'tptax': tptax})
        return {'value' : res}
    
    def onchange_dep(self, cr, uid, ids, dep):
        res = {}
        if dep:
            res['arr'] = dep 
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
            nartn = "Railway: " + str(case.source or '') + ' - ' + str(case.dest or '') + ', ' + str(case.train_name or '') + ', ' + str(case.travel_dt or '')
            getamt = self.calc_RAIL_total(cr, uid, case.id, case.inv_type)
            subtot = getamt.get('subtotal',0)
            pax = ''
            first_sec = case.rail_lines and case.rail_lines[0]
            if first_sec: pax = first_sec.pax_name or ''
            
            inv_currency = case.invoice_id.currency_id.id
            subtot = cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, subtot, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                
            vals = {
                'name'       : nartn,
                'passenger'  : pax,
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
                             'rail_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('rail_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True

    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_railway, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
      
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_railway, self).write(cr, uid, ids, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result
       
class tr_invoice_railway_lines(osv.osv):
    _name = 'tr.invoice.railway.lines'
    _description = 'Invoice - Railway Lines'
    
    _columns = {
                'railway_id'  : fields.many2one('tr.invoice.railway', 'Railway', ondelete='cascade'), 
                'src_id'      : fields.many2one('tr.invoice.railway.lines', 'Source Reference'),
                
                'pax_id'   : fields.many2one('res.partner', 'Passenger', domain=[('customer', '=', 1)], ondelete='restrict'), 
                'pax_name' : fields.char('Passenger Name', size=30), 
                'pax_age'  : fields.char('Age', size=30), 
                'coach_no' : fields.char('Coach No.', size=30),
                'seat_no'  : fields.char('Seat No.', size=30),
                }
    
    def onchange_passenger(self, cr, uid, ids, pax_id):
       name = ''
       
       if pax_id:
           p = self.pool.get('res.partner').browse(cr, uid, pax_id)
           name = p.name
           
       return {'value':{'pax_name': name,
                        }}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: