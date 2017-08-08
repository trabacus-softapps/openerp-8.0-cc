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


class tr_invoice_car(osv.osv):
    _name = 'tr.invoice.car'
    _description = 'Invoice - Car'
    
    def calc_CAR_total(self, cr, uid, id, inv_type, context=None):
        res = {}
        if context == None: context = {}
        ctx = context.copy()
        ctx['calledfrm'] = 'func'
        case = self.browse(cr, uid, id)
        inv = case.opt_id and case.opt_id.invoice_id or False
        
        if inv : ctx.update({'ad_cnt'  : inv.adult + inv.twin + inv.triple ,
                             'ext_cnt' : inv.extra,
                             'ch_cnt'  : inv.cnb + inv.cwb,
                             'inf_cnt' : inv.infant})
        
        inv_type = inv_type and inv_type or case.inv_type
        res = self.onchange_CAR_total(cr, uid, [case.id], case.inv_type, 'amt', case.no_vehicle, case.basic, case.tac_perc, case.tac
                                         , case.markup_perc, case.markup, case.tds_perc, case.tds, case.other, case.driver_chrgs,  case.discount, case.tds1_perc
                                         , case.tds1, case.servicechrg_perc, case.servicechrg, case.cancel_markup, case.cancel_charges
                                         , case.cancel_service, case.tptax_basic, case.tptax_tac, case.tptax_tds, case.tptax_other, case.tptax_ids,case.cost_on
                                         , False, ctx)['value']
        
        res['subtotal'] = res.get('subtotal',0)
        res['tac'] = (case.tac * case.no_vehicle)
        res['tds'] = (case.tds * case.no_vehicle)
        res['tds1'] = (case.tds1 * case.no_vehicle)
        res['basic'] = (case.basic * case.no_vehicle)
        res['other'] = (res.get('tptax',0) * case.no_vehicle) + (case.driver_chrgs * case.no_vehicle)
        res['discount'] = (case.discount * case.no_vehicle)
        res['markup'] = (case.markup * case.no_vehicle)
        res['servicechrg'] = (case.servicechrg * case.no_vehicle)
        
        res['cancel_markup'] = (case.cancel_markup * case.no_vehicle)
        res['cancel_charges'] = (case.cancel_charges * case.no_vehicle)
        res['cancel_service'] = (case.cancel_service * case.no_vehicle)           
        
        return res
    
    def _get_AllTotal(self, cr, uid, ids, field_name, arg, context):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')

        for case in self.browse(cr, uid, ids):
              
            getamt = self.calc_CAR_total(cr, uid, case.id, case.inv_type)
            res[case.id] = {
                            'tptax': getamt.get('a_tptax', 0),
                            'subtotal': getamt.get('subtotal', 0),
                            'po_subtotal': getamt.get('po_subtotal', 0),
                            'a_rate': getamt.get('a_rate', 0),
                            'e_rate': getamt.get('e_rate', 0),
                            'c_rate': getamt.get('c_rate', 0),
                            'i_rate': getamt.get('i_rate', 0),
                            }
            
            amt4tax = tax = 0.00
            if case.tax_basic == True: amt4tax += case.basic   
            if case.tax_mark == True: amt4tax += case.markup   
            if case.tax_tac == True: amt4tax += case.tac   
            if case.tax_tds == True: amt4tax += case.tds   
            if case.tax_tds1 == True: amt4tax += case.tds1   
            if case.tax_tptax == True: amt4tax += case.tptax   
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
            
    _columns = {
                'invoice_id'  : fields.many2one('account.invoice', 'Invoice', ondelete='cascade'),
                'inv_type'    : fields.related('invoice_id', 'type', string='Invoice type', type='selection'
                                           , selection=[('out_invoice','Customer Invoice'),
                                            ('in_invoice','Supplier Invoice'),
                                            ('out_refund','Customer Refund'),
                                            ('in_refund','Supplier Refund')], store=True),
                'opt_id'  : fields.many2one('tr.invoice.option', 'Option', ondelete='cascade'),
                 
                'product_id'  : fields.many2one('product.product', 'Product', ondelete='restrict', domain=[('travel_type','=','car')]), 
                'name'        : fields.char('Description', size=100, required=True),
                'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict', track_visibility='onchange'), 
                'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                    , help="The income or expense account related to the selected product."),
                'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
                'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
                'src_id'      : fields.many2one('tr.invoice.car', 'Source Reference'),
                
                'vehicle_id'  : fields.many2one('tr.vehicle', 'Vehicle', ondelete='restrict'),
                
                'pax_id'   : fields.many2one('res.partner', 'Guest', domain=[('customer', '=', 1)], ondelete='restrict'), 
                'pax_name' : fields.char('Guest Name', size=30), 
                'pax_ph'   : fields.char('Contact No.', size=30), 
                'pax_email': fields.char('Email', size=30),
        
                'cost_type' : fields.selection([('ind_cost','Individual'),('cons_cost','Consolidated')], 'Calculation Type'),
                'start_dt'  : fields.date('Start Date'),  
                'end_dt'    : fields.date('End Date'),  
                'pick_up'   : fields.text('Pick Up from'),
                'drop_at'   : fields.text('Drop at'),
                'route'     : fields.text('Route'), 
                'incl'      : fields.text('Inclusive'), 
                'remarks'   : fields.text('Remarks'), 
                'details'   : fields.text('Cost Details'),
                
                'no_kms'   : fields.float('No. of Kms'),
                'no_days'  : fields.float('No. of Days'),
                'rate_km'  : fields.float('Rate per KM'),
                'mrkup_km' : fields.float('Markup per KM'),
                
                'usage_lmt'     : fields.float('Usage Limit'),
                'ext_rate_km'   : fields.float('Rate per Extra KM'), 
                'ext_rate_hour' : fields.float('Rate per Extra Hour'),
                'ext_mrkup_km'  : fields.float('Markup per Extra KM'),
                'ext_mrkup_hour': fields.float('Markup per Extra Hour'),
                'ext_km_trvld'  : fields.float('Extra KMs Travelled'),
                'ext_hr_trvld'  : fields.float('Extra Hours Travelled'),
                'driver_chrgs'  : fields.float('Driver Charges'),
                'driver'        : fields.char('Contact Person', size=100),
                'driver_ph'     : fields.char('Contact No.', size=50),
                'no_vehicle'    : fields.integer('No. of Vehicle', required=True),
                
                'basic'     : fields.float('Basic', digits_compute=dp.get_precision('Account')),
                'tac_perc'  : fields.float('TAC (%)', digits_compute=dp.get_precision('Account')),
                'tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
                'tds_perc'  : fields.float('TDS(T) (%)', digits_compute=dp.get_precision('Account')),
                'tds'       : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')),
                'tds1_perc' : fields.float('TDS(D) (%)', digits_compute=dp.get_precision('Account')),
                'tds1'      : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')),
                'markup_perc' : fields.float('Mark up (%)', digits_compute=dp.get_precision('Account')),
                'markup'      : fields.float('Mark up', digits_compute=dp.get_precision('Account')),
                'discount'    : fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
                'servicechrg'     : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'servicechrg_perc': fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'cancel_markup'   : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
                'cancel_charges'  : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
                'cancel_service'  : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')),
                
                'tax_basic' : fields.boolean('On Basic'),
                'tax_tac'   : fields.boolean('On TAC'),
                'tax_tds'   : fields.boolean('On TDS(T)'),
                'tax_tds1'  : fields.boolean('On TDS(D)'),
                'tax_tptax' : fields.boolean('On T.P.Tax'),
                'tax_mark'  : fields.boolean('On Mark Up'),
                'tax_other' : fields.boolean('On Other'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                
                'tax_ids'    : fields.many2many('account.tax', 'car_tax_rel', 'car_id', 'tax_id', 'Taxes'),
                'tptax_ids'  : fields.many2many('account.tax', 'car_tptax_rel', 'car_id', 'tax_id', 'T.P. Taxes'),
            
                'tptax_basic'  : fields.boolean('On Basic'),
                'tptax_other'  : fields.boolean('On Other'),
                'tptax_tac'    : fields.boolean('On TAC'),
                'tptax_tds'    : fields.boolean('On TDS(T)'),
                
                'tptax'     : fields.function(_get_AllTotal, type='float', string='T.P. Tax', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'subtotal'  : fields.function(_get_AllTotal, type='float', string='Subtotal', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'tax_base'  : fields.function(_get_AllTotal, type='float', string='Taxes Base', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'taxes'     : fields.function(_get_AllTotal, type='float', string='Taxes', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'total'     : fields.function(_get_AllTotal, type='float', string='Total', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'po_subtotal'  : fields.function(_get_AllTotal, type='float', string='PO Subtotal', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                'cost_on' : fields.selection([('only_adult','Adults Only')
                                              , ('with_extra','Adults With Extra Person')
                                              , ('with_child','Adults With Extra Person & Children')
                                              , ('all','All Passengers')], 'Split Cost Between'),
                
                'a_rate'  : fields.function(_get_AllTotal, type='float', string='Adults',  digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'e_rate'  : fields.function(_get_AllTotal, type='float', string='Extra',   digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'c_rate'  : fields.function(_get_AllTotal, type='float', string='Child',   digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'i_rate'  : fields.function(_get_AllTotal, type='float', string='Infants', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                }
   
    _defaults = {
                 'account_id' :  _default_account_id,
                 'inv_type'   :  lambda self,cr,uid,c: c.get('type', ''),
                 'no_vehicle' :  1,
                 'cost_type'  : 'ind_cost',
                 'cost_on'    : 'only_adult',
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
          
          res = {'name'   : prod.name_template,
                 'tax_ids': map(lambda x: x.id, prod.taxes_id),
                 'vehicle_id' : prod.vehicle_id and prod.vehicle_id.id or 0,
                 'cost_type': prod.cost_type, 'no_days': prod.no_days, 'usage_lmt': prod.usage_lmt, 'driver_chrgs':prod.driver_chrgs,
                 'rate_km': prod.rate_km, 'ext_rate_km': prod.ext_rate_km, 'ext_rate_hour': prod.ext_rate_hour,
                 'mrkup_km': prod.mrkup_km, 'ext_mrkup_km': prod.ext_mrkup_km, 'ext_mrkup_hour': prod.ext_mrkup_hour,
                 'basic'   : prod.a_basic, 'tac_perc': prod.a_tac_perc, 'tac' : prod.a_tac, 'markup_perc': prod.a_markup_perc,
                 'markup': prod.a_markup, 'tds_perc': prod.a_tds_perc, 'tds' : prod.a_tds,
                 'other': prod.a_other, 'servicechrg_perc': prod.a_servicechrg_perc, 'servicechrg': prod.a_servicechrg,
                 'tptax_basic': prod.tptax_basic, 'tptax_tac': prod.tptax_tac, 'tptax_tds': prod.tptax_tds,
                 'tptax_ids': map(lambda x: x.id, prod.tptax_ids),
                 'currency_id': prod.currency_id.id,
                }
          res.update(taxon_vals)
          print "basic", res['basic']
          print "res:",res
      return {'value':res}
  
    def onchange_start_dt(self, cr, uid, ids, start_dt):
        res = {}
        if start_dt:
            res['end_dt'] = start_dt 
        return {'value': res}
  
    def onchange_passenger(self, cr, uid, ids, pax_id):
        # TODO: 
        # fetch passenger address   
       name = contact = email = ''
       
       if pax_id:
           p = self.pool.get('res.partner').browse(cr, uid, pax_id)
           name = p.name
           contact = p.mobile
           email = p.email
           
       return {'value':{'pax_name': name, 'pax_contact': contact, 'pax_email': email,
                        }}
  
    def onchange_CAR_total(self, cr, uid, ids, inv_type, calledby, no_vehicle, basic, tac_perc, tac, markup_perc, markup
                          , tds_perc, tds, other, driver_chrgs,  discount, tds1_perc, tds1, servicechrg_perc, servicechrg, cancel_markup
                          , cancel_charges, cancel_service, tptax_basic, tptax_tac, tptax_tds, tptax_other, tptax_ids, cost_on
                          , is_sc=False, context=None):
       
        res = {}
        if context == None: context = {}
        dp = get_dp_precision(cr, uid, 'Account')
        
        tpamt4tax = tptax = a_rate = c_rate = e_rate = i_rate = 0.00
        
        iadult = context.get('ad_cnt', 0)
        ichild = context.get('ch_cnt', 0)
        iextra = context.get('ext_cnt', 0)
        iinfant = context.get('inf_cnt', 0)
        
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
        if tptax_other == True : tpamt4tax += other
        
        if context and context.get('calledfrm','') == 'func':
            for ttx in tptax_ids:
                tptax += round((tpamt4tax * ttx.amount), dp)
        else:
            for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
                tptax += round((tpamt4tax * ttx['amount']), dp)

        if inv_type in ('out_invoice', 'out_refund'):
            subtot = (basic + markup + tptax + tds1 + other + driver_chrgs - discount)
            if not is_sc and servicechrg_perc:
                servicechrg = round(((servicechrg_perc * subtot)/100.00), dp)
                res['servicechrg'] = servicechrg
            subtot = (subtot + servicechrg - cancel_markup - cancel_charges - cancel_service) * no_vehicle
            res['po_subtotal'] = (basic + tptax + tds + other + driver_chrgs - tac - cancel_charges) * no_vehicle
        else:
            subtot = (basic + tptax + tds + other + driver_chrgs - tac - cancel_charges) * no_vehicle
            
        
        if cost_on == 'only_adult':
            a_rate = subtot / (iadult or 1) 
            
        elif cost_on == 'with_extra':
            a_rate = subtot / ((iadult + iextra) or 1)
            e_rate = subtot / ((iadult + iextra) or 1)
            
        elif cost_on == 'with_child':
            a_rate = subtot / ((iadult + iextra + ichild) or 1)
            e_rate = subtot / ((iadult + iextra + ichild) or 1)
            c_rate = subtot / ((iadult + iextra + ichild) or 1)
            
        else:
            a_rate = subtot / ((iadult + iextra + ichild + iinfant) or 1)
            e_rate = subtot / ((iadult + iextra + ichild + iinfant) or 1)
            c_rate = subtot / ((iadult + iextra + ichild + iinfant) or 1)
            i_rate = subtot / ((iadult + iextra + ichild + iinfant) or 1)
             
        res.update({'subtotal' : subtot,
                    'tptax': tptax,
                    'a_rate':a_rate,'e_rate':e_rate,'c_rate':c_rate,'i_rate':i_rate,
                    })
        return {'value':res}
    
    def onchange_CAR_Basic(self, cr, uid, ids, cost_type, no_kms, no_days, usage_lmt, rate_km, ext_rate_km
                           , ext_hr_trvld, ext_rate_hour,  mrkup_km, ext_mrkup_km, ext_mrkup_hour, context=None):
        """ 
            Used: in Transfers
            Returns: Basic value
        """
        res = {}
        basic = 0
        ext_km_trvld = no_kms - usage_lmt
        
        if ext_km_trvld <= 0:
            ext_km_trvld = 0
        
        if cost_type == 'ind_cost':
            extamt = ext_km_trvld * (ext_rate_km + ext_mrkup_km)
            exthr = ext_hr_trvld * (ext_rate_hour + ext_mrkup_hour)
                             
            basic = (usage_lmt * (rate_km + mrkup_km)) + extamt + exthr  
            
        res.update({'ext_km_trvld' : ext_km_trvld,
                    'basic': basic
                    })
             
        return {'value': res}
  
    def print_voucher(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            data = {}
            data['ids'] = ids
            data['model'] = 'tr.invoice.car'
            data['output_type'] = 'pdf'
            data['variables'] = {'transfer_id':case.id,
                                 'invoice_id':case.invoice_id.id}
            return {'type': 'ir.actions.report.xml',
                    'report_name':'car_voucher',
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
            nartn = 'Transfers, Pax: ' + str(case.pax_name) + ", Vehicle: " + str(case.vehicle_id and case.vehicle_id.name or '')
            nartn += ', Route: ' + str(case.route) + ', Start Date: ' + str(case.start_dt) + ', End Date: ' + str(case.end_dt)
            
            getamt = self.calc_CAR_total(cr, uid, case.id, case.inv_type)
            subtot = getamt.get('subtotal',0)
            
            inv_currency = case.invoice_id.currency_id.id
            subtot = cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, subtot, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                
            vals = {
                'name'       : nartn,
                'passenger'  : case.pax_name,
                'tpartner_id': case.tpartner_id.id,
                'product_id' : case.product_id.id or False,
                'origin'     : case.invoice_id.name,
                'account_id' : case.account_id.id,
                'account_analytic_id' : case.invoice_id and case.invoice_id.account_analytic_id and case.invoice_id.account_analytic_id.id or False,                'currency_id': case.currency_id.id,
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
                             'car_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('car_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True

    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_car, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
      
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_car, self).write(cr, uid, ids, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result
    
#Inherited in Invoice.py file        
class tr_invoice_option(osv.osv):
    _name = "tr.invoice.option"
    _description = "Package Options"
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: