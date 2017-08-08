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


def get_dp_precision(cr, uid, application):
    cr.execute('select digits from decimal_precision where name=%s', (application,))
    res = cr.fetchone()
    return res[0] if res else 2

class tr_invoice_flight(osv.osv):
    _name = 'tr.invoice.flight' 
    _description = "Invoice - Flight"

    def calc_Flight_total(self, cr, uid, id, inv_type, context=None):
         
        # TODO:
        # Need to include code for calculating child & Infant w.r.t package
        #
        
        airtax = tpamt4tax = tptax = ad_POsubtot = ad_other = 0.00
        
        case = self.browse(cr, uid, id)
        
        for atx in case.airtax_ids:
            airtax += atx.amount
            
        if case.tptax_basic == True : tpamt4tax += case.a_basic
        if case.tptax_airtax == True: tpamt4tax += airtax
        if case.tptax_tac == True   : tpamt4tax += case.a_tac
        if case.tptax_tds == True   : tpamt4tax += case.a_tds
        if case.tptax_other == True : tpamt4tax += case.a_other

        for ttx in case.tptax_ids:
            tptax += round((tpamt4tax * ttx.amount),2)
            
        inv_type = inv_type and inv_type or case.inv_type
        
        if inv_type in ('out_invoice', 'out_refund'):
            ad_basic = (case.a_basic + case.a_raf + case.a_other + case.a_reissue + case.a_markup + tptax + airtax - case.a_discount + case.a_tds1)
            ad_subtot =  ad_basic + case.a_servicechrg - (case.a_cancel_markup + case.a_cancel_service + case.a_cancel_charges)
            ad_other = (case.a_raf + case.a_other + case.a_reissue + tptax + airtax)
            ad_POsubtot = (case.a_basic + case.a_raf + case.a_other + case.a_reissue + airtax + tptax + case.a_vendor + case.a_tds - case.a_tac
                           - case.a_cancel_charges)
            
        else: # Purchase
            ad_basic = (case.a_basic + case.a_raf + case.a_other + case.a_reissue + airtax + tptax + case.a_vendor + case.a_tds - case.a_tac) 
            ad_subtot =  ad_basic - case.a_cancel_charges
         
        return {'adult_basic': ad_basic, 'adult_subtotal' : ad_subtot, 'other': ad_other, 'tptax':tptax, 'airtax':airtax,
                'subtot': ad_subtot, 'po_subtot': ad_POsubtot}
         
    def _get_AllTotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        # TODO:
        # Need to include code for calculating child & Infant w.r.t package
        #
        dp = get_dp_precision(cr, uid, 'Account')
        for case in self.browse(cr, uid, ids):
            amt4tax = tax = 0.00
            getamt = self.calc_Flight_total(cr, uid, case.id, case.inv_type)
            
            if case.tax_basic == True: amt4tax += case.a_basic
            if case.tax_other == True: amt4tax += case.a_other
            if case.tax_raf == True: amt4tax += case.a_raf
            if case.tax_tac == True: amt4tax += case.a_tac
            if case.tax_tds == True: amt4tax += case.a_tds
            if case.tax_tds1 == True: amt4tax += case.a_tds1
            if case.tax_mark == True: amt4tax += case.a_markup
            if case.tax_tptax == True: amt4tax += case.a_tptax
            if case.tax_vendor == True: amt4tax += case.a_vendor
            if case.tax_reissue == True: amt4tax += case.a_reissue
            if case.tax_airlntax == True: amt4tax += case.a_airtax
            if case.tax_servicechrg == True: amt4tax += case.a_servicechrg
                
            # TODO: need to configure it
#             amt4tax -= case.a_discount
#             amt4tax -= (case.cancel_markup + case.cancel_charges + case.cancel_service)
              
            for t in case.tax_ids:
                tax += round((amt4tax * t.amount),dp)           
                
            res[case.id] = {'a_total': getamt.get('adult_subtotal',0),
                            'a_tax': getamt.get('airtax',0),
                            'a_tptax': getamt.get('tptax',0), 
#                             'c_total': 0, 
#                             'i_total': 0, 
                            'basicother' : getamt.get('adult_basic',0),
                            'taxes'      : tax, 
                            'tax_base'   : amt4tax,
                            'po_subtotal' : getamt.get('po_subtot',0),
                            'total'       : getamt.get('adult_subtotal',0) + tax,
                            }
        return res
    
    def _get_InvoiceState(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = case.invoice_id and case.invoice_id.state or ''
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
    

    def default_get(self, cr, uid, fields, context=None):
        if not context: context = {}
        res = super(tr_invoice_flight, self).default_get(cr, uid, fields, context=context) or {}

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Fetch: Show All Data
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        param_obj = self.pool.get("ir.config_parameter")
        showall_details = param_obj.get_param(cr, uid, "showdetails")
        
        if showall_details: res['is_showdetails'] = True
        return res
    
    _columns = {
                
            'invoice_id'  : fields.many2one('account.invoice', 'Invoice', ondelete='cascade'), 
            'inv_type'    : fields.related('invoice_id', 'type', string='Invoice type', type='selection'
                                           , selection=[('out_invoice','Customer Invoice'),
                                            ('in_invoice','Supplier Invoice'),
                                            ('out_refund','Customer Refund'),
                                            ('in_refund','Supplier Refund')], store=True),
            'opt_id'  : fields.many2one('tr.invoice.option', 'Option', ondelete='cascade'),
                
            'state'       : fields.function(_get_InvoiceState, type='selection', string='Status'), 
            'product_id'  : fields.many2one('product.product', 'Product', ondelete='restrict'), 
            'name'        : fields.char('Description', size=100, required=True), 
            'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', required=True, domain=[('supplier', '=', 1)], ondelete='restrict'), 
            'account_id'  : fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], ondelete='restrict'
                                                , help="The income or expense account related to the selected product."),
            'company_id'  : fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
            'currency_id' : fields.many2one("res.currency", "Currency", ondelete='restrict'),
            'src_id'      : fields.many2one('tr.invoice.flight', 'Source Reference'),
            
            'pnr'        : fields.char('PNR', size=20),
            'airline_pnr': fields.char('Airline PNR', size=20),
            'ticket_no'  : fields.char('Ticket No', size=30), 
            
            'paxpartner_id' : fields.many2one('res.partner', 'Passenger', ondelete='restrict'),
            'pax_name'      : fields.char('Passenger Name', size=30),
            'pax_contact'   : fields.char('Contact No.', size=30),
            'pax_email'     : fields.char('Email', size=30),
            'pax_type'      : fields.selection([('adult','Adult'),('child','Child'), ('infant','Infant')],'Type'),
            
            'passport_no' : fields.char('Passport No', size=10),
            'nation'      : fields.char('Nationality', size=10),
            'issue_place' : fields.char('Place of Issue', size=10),
            'valid_from'  : fields.date('Valid From'),
            'valid_to'    : fields.date('Valid Upto'),   
            'address'     : fields.char('Address', size=50),  
            
            'is_reconciled'    : fields.boolean('Reconciled'),
            'reconcile_date'   : fields.date('Reconcile Date'),
            'reconcile_amount' : fields.float('Reconcile Amount', digits_compute=dp.get_precision('Account')),
            'reconcile_remarks' : fields.text('Reconcile Remarks'),
            
            'adult'       : fields.integer('No. of Adults'),  
            'a_tac_perc'  : fields.float('TAC (A) %', digits_compute=dp.get_precision('Account')),
            'a_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
            'a_tac_basic' : fields.boolean('On Basic'),
            'a_tac_other' : fields.boolean('On Other'),
            'a_tac_tptax' : fields.boolean('On T.P.Tax'), 
            
            'a_tac_perc1'   : fields.float('TAC (B) %', digits_compute=dp.get_precision('Account')),
            'a_tac_basic1'  : fields.boolean('On Basic'),
            'a_tac_other1'  : fields.boolean('On Other'),
            'a_tac_tptax1'  : fields.boolean('On T.P.Tax'),
            
            'a_tac_perc2'   : fields.float('TAC (C) %', digits_compute=dp.get_precision('Account')),        
            'a_tac_basic2'  : fields.boolean('On Basic'),
            'a_tac_other2'  : fields.boolean('On Other'),
            'a_tac_tptax2'  : fields.boolean('On T.P. Tax'),    
            
            'a_basic'    : fields.float('Basic', digits_compute=dp.get_precision('Account')), 
            'a_tds'      : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
            'a_tds_perc' : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
            'a_tds1'     : fields.float('TDS(D)', digits_compute=dp.get_precision('Account')), 
            'a_tds1_perc': fields.float('TDS(D) %', digits_compute=dp.get_precision('Account')),
            'a_raf'      : fields.float('RAF', digits_compute=dp.get_precision('Account')), 
            'a_markup_perc'  : fields.float('MarkUp %', digits_compute=dp.get_precision('Account')),
            'a_markup'       : fields.float('MarkUp', digits_compute=dp.get_precision('Account')),
            'a_servicechrg_perc' : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
            'a_servicechrg'      : fields.float('Service Charge', digits_compute=dp.get_precision('Account')), 
            'a_other'    : fields.float('Other Charges', digits_compute=dp.get_precision('Account')),
            'a_vendor'   : fields.float('Vendor Charge', digits_compute=dp.get_precision('Account')), 
            'a_reissue'  : fields.float('Reissue Charges', digits_compute=dp.get_precision('Account')),  
               
            'a_disc_perc'  : fields.float('TAC (A) %', digits_compute=dp.get_precision('Account')),
            'a_disc'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
            'a_disc_basic' : fields.boolean('On Basic'),
            'a_disc_other' : fields.boolean('On Other'),
            'a_disc_tptax' : fields.boolean('On T.P.Tax'), 
            
            'a_disc_perc1'  : fields.float('TAC (B) %', digits_compute=dp.get_precision('Account')),
            'a_disc_basic1' : fields.boolean('On Basic'),
            'a_disc_other1' : fields.boolean('On Other'),
            'a_disc_tptax1' : fields.boolean('On T.P.Tax'),
            
            'a_disc_perc2'   : fields.float('TAC (C) %', digits_compute=dp.get_precision('Account')),        
            'a_disc_basic2'  : fields.boolean('On Basic'),
            'a_disc_other2'  : fields.boolean('On Other'),
            'a_disc_tptax2'  : fields.boolean('On T.P. Tax'),
            'a_disc_select'  : fields.selection([('onlyA','Only A'), ('AplusB','A + B'), ('AB100','(A+B) on (100-A)'), ('ABC', 'A, B, C')], 'Discount Calculation'),
            'a_discount'     : fields.float('Discount', digits_compute=dp.get_precision('Account')), 
            
            'a_tptax'    : fields.function(_get_AllTotal, string='T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
            'a_tax'      : fields.function(_get_AllTotal, string='Airline Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
            'a_total'    : fields.function(_get_AllTotal, string='Adult Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
            'a_tac_select' : fields.selection([('onlyA','Only A'), ('AplusB','A + B'), ('AB100','(A+B) on (100-A)'), ('ABC', 'A, B, C')], 'Tac Calculation'),
            
            'airtax_ids' : fields.one2many('tr.airlines.taxes', 'flight_id', 'Airline Taxes'),
            'tptax_ids'  : fields.many2many('account.tax', 'flight_tptax_rel', 'flight_id', 'tax_id', 'T.P. Taxes'),
            
            'tptax_basic'  : fields.boolean('On Basic'),
            'tptax_other'  : fields.boolean('On Other'),
            'tptax_airtax' : fields.boolean('On AirLine Tax'),
            'tptax_tac'    : fields.boolean('On TAC'),
            'tptax_tds'    : fields.boolean('On TDS'), 
            
            
            # TODO: remove if these fields are not used in package               
#             'child'     : fields.integer('No. of Children'), 
#             'c_basic'   : fields.function(_get_AllTotal, string='Basic', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'c_wopsf'   : fields.function(_get_AllTotal, string='WO/PSF', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'c_tac'     : fields.function(_get_AllTotal, string='TAC', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'c_tds'     : fields.function(_get_AllTotal, string='TDS', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'c_tax'     : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),  
#             'c_in'      : fields.function(_get_AllTotal, string='IN', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'c_yq'      : fields.function(_get_AllTotal, string='YQ', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'c_tptax'   : fields.function(_get_AllTotal, string='T.P.Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'c_markup'  : fields.function(_get_AllTotal, string='MarkUp', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'c_servicechrg' : fields.function(_get_AllTotal, string='Service Charge', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'c_other'  : fields.function(_get_AllTotal, string='Other Charges', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'c_total'  : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),  
             
            # TODO: remove if these fields are not used in package 
#             'infant'    : fields.integer('No. of Infants'), 
#             'i_basic'   : fields.function(_get_AllTotal, string='Basic', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'i_wopsf'   : fields.function(_get_AllTotal, string='WO/PSF', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'i_tac'     : fields.function(_get_AllTotal, string='TAC', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'i_tds'     : fields.function(_get_AllTotal, string='TDS', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'i_tax'     : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),  
#             'i_in'      : fields.function(_get_AllTotal, string='IN', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'i_yq'      : fields.function(_get_AllTotal, string='YQ', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'i_tptax'   : fields.function(_get_AllTotal, string='T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'i_markup'  : fields.function(_get_AllTotal, string='MarkUp', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'i_servicechrg' : fields.function(_get_AllTotal, string='Service Charge', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'i_other'  : fields.function(_get_AllTotal, string='Other Charges', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'), 
#             'i_total'  : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),  

            # TODO:
            # Fields which are not required: delete it
#             'ft_basicother': fields.function(_get_AllTotal, string='Basic + Others', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),            
#             'ft_tptax'     : fields.function(_get_AllTotal, string='T.P.Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"), 
#             'ft_markup'    : fields.function(_get_AllTotal, string='Mark Up', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
#             'tax_base'     : fields.function(_get_AllTotal, type='float', string='Taxes Base', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#             'taxes'        : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
#             'ft_airlntax'  : fields.function(_get_AllTotal, string='Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"), 
#             'ft_tac'       : fields.function(_get_AllTotal, string='TAC', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
#             'ft_tds'       : fields.function(_get_AllTotal, string='TDS(T)', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
#             'ft_tds1'      : fields.function(_get_AllTotal, string='TDS(D)', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
#             'ft_raf'       : fields.function(_get_AllTotal, string='RAF', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
#             'ft_servicechrg' : fields.function(_get_AllTotal, string='Service Charges', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
            
            'basicother' : fields.function(_get_AllTotal, string='Basic + Others', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
            'subtotal'   : fields.function(_get_AllTotal, string='Subtotal', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
            'taxes'      : fields.function(_get_AllTotal, string='Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
            'tax_base'   : fields.function(_get_AllTotal, type='float', string='Taxes Base', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
            'total'      : fields.function(_get_AllTotal, string='Total', type='float', digits_compute=dp.get_precision('Account'), store=True, multi="tot"),
            'po_subtotal': fields.function(_get_AllTotal, string='PO Subtotal', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                    
            'tax_basic'    : fields.boolean('On Basic'),
            'tax_other'    : fields.boolean('On Other'),
            'tax_tac'      : fields.boolean('On TAC'),
            'tax_tds'      : fields.boolean('On TDS(T)'),
            'tax_tds1'     : fields.boolean('On TDS(D)'),
            'tax_mark'     : fields.boolean('On Mark Up'),
            'tax_raf'      : fields.boolean('On RAF'),
            'tax_tptax'    : fields.boolean('On T.P.Tax'),
            'tax_vendor'   : fields.boolean('On Vendor'),
            'tax_airlntax' : fields.boolean('On AirLine Tax'),
            'tax_reissue'  : fields.boolean('On Reissue Charges'),
            'tax_servicechrg' : fields.boolean('On Service Charge'), 
            
            'ft_traveltype' : fields.selection([('dom_flight','Domestic'),('int_flight','International Flight'), ('package','Holiday Package')], 'Flight Type'),
            'tax_ids' : fields.many2many('account.tax', 'flight_tax_rel', 'flight_id', 'tax_id', 'Taxes'), 
            'flight_lines': fields.one2many('tr.invoice.flight.lines', 'flight_id', 'Flight Lines'),
            
            'a_cancel_markup'  : fields.float('Cancellation Markup', digits_compute=dp.get_precision('Account')), 
            'a_cancel_charges' : fields.float('Cancellation Charges', digits_compute=dp.get_precision('Account')), 
            'a_cancel_service' : fields.float('Cancellation Service Charges', digits_compute=dp.get_precision('Account')), 
            
            # TODO: include child & infant cancellation chrg w.r.t packages
            
             'is_refunded'    : fields.boolean('Refunded'),
             'is_showdetails' : fields.boolean('Show Extended/All Details'),
        }
    
    _defaults = {
                 'adult': 1,
                 'account_id'   : _default_account_id,
                 'ft_traveltype': lambda self,cr,uid,c: c.get('travel_type', ''),
                 'pax_type' : 'adult',
                 'inv_type' : lambda self,cr,uid,c: c.get('type', ''),
                 'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
                 'currency_id': _get_currency
                 } 
    
    
    def onchange_validfrom(self, cr, uid, ids, valid_from):
        res = {}
        if valid_from :
            res['valid_to'] = valid_from
        return {'value' : res}
    
    def _check_uniq_tikno(self,cr,uid,ids,context=None):
        for case in self.browse(cr,uid,ids):
            if case.invoice_id.type == 'out_invoice':
                if case.ticket_no:
                    cr.execute("select id from tr_invoice_flight where ticket_no ='"+str(case.ticket_no)+"' AND id !=" + str(case.id) + "  AND (src_id !=" + str(case.id) + " OR src_id is Null) AND inv_type in ('out_invoice')"  )
                    tik_ids = cr.fetchall()
                    if tik_ids:
                        return False
        return True
        
    _constraints = [
                     (_check_uniq_tikno, "Ticket Number Should Be Unique", ['ticket_no']),
                    ]
    
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
  
    def onchange_passenger(self, cr, uid, ids, paxpartner_id):
        # TODO: 
        # fetch passenger address   
       name = contact = email = passport = nation = issue_place = ''
       valid_from = valid_to = False
       
       if paxpartner_id:
           p = self.pool.get('res.partner').browse(cr, uid, paxpartner_id)
           name = p.name
           contact = p.mobile
           email = p.email
           passport = p.passport_no
           nation = p.nation
           issue_place = p.place_issue
           valid_from = p.valid_from
           valid_to = p.valid_till
           
       return {'value':{'pax_name': name, 'pax_contact': contact, 'pax_email': email,
                        'passport_no': passport, 'nation': nation, 'issue_place': issue_place,
                        'valid_from': valid_from, 'valid_to': valid_to
                        }}
        
    
    def onchange_FT_airline(self, cr, uid, ids, tpartner_id, flight_lines, context={}):
        res = {}
         
        comm_obj = self.pool.get('tr.commission')
        commln_obj = self.pool.get('tr.commission.lines')
        airln_obj = self.pool.get('tr.airlines')
        FTln_obj = self.pool.get('tr.invoice.flight.lines')
         
        customer_id = context.get('partner_id', False)
        
        # stopping the ONchange for credit note 
        if context.get('type') == 'out_refund':
            return {'value': res}
        res = {
               'airtax_ids': [], 'tptax_ids': [],
               'a_tac_basic' : False, 'a_tac_basic1': False, 'a_tac_basic2': False,
               'a_tac_other' : False, 'a_tac_other1': False, 'a_tac_other2': False,
               'a_tac_select': False, 'a_tac_perc' : 0.00, 'a_tac_perc1' : 0.00, 'a_tac_perc2' : 0.00,
               'a_markup_perc': 0.00, 'a_markup': 0.00, 'a_servicechrg_perc': 0.00,
               'a_servicechrg': 0.00, 'a_discount': 0.00,
               'tptax_basic': False, 'tptax_other': False, 'tptax_airtax': False,
               'tptax_tac': False,  'tptax_tds': False,
               'a_disc_basic' : False, 'a_disc_basic1': False, 'a_disc_basic2': False,
               'a_disc_other' : False, 'a_disc_other1': False, 'a_disc_other2': False,
               'a_disc_select': False, 'a_disc_perc' : 0.00, 'a_disc_perc1' : 0.00, 'a_disc_perc2' : 0.00,
               }
         
        airline_id = dep = arr = faretype_id = ftclass_id = False
        
        rec = idrec = 1
        savedSector = []
        newSector = []
        if context and context.get('calledfrm','') == 'func':
            sectln = flight_lines and flight_lines[0]
            if sectln:
               savedSector =  [FTln_obj.read(cr, uid, sectln.id, ["airline_id", "dep", "arr", "faretype_id", "ftclass_id", "from_id", "to_id"])]
        else:
            # Fetching: First Sector Line
            for ln in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'flight_lines', flight_lines, ["airline_id", "dep", "arr", "faretype_id", "ftclass_id", "from_id", "to_id"]):
                if ln.get('id', False) and idrec == 1: # First saved sector line 
                    savedSector = [ln]
                if rec == 1: # First new sector line
                    newSector = [ln]
                rec += 1
                if ln.get('id', False): idrec += 1
            
        sectorln = savedSector and savedSector or newSector
        for ln in sectorln:
            # saved records, m2o value will come in tuples:
            airline_id  = isinstance(ln['airline_id'], tuple)  and ln['airline_id'][0]  or ln['airline_id']
            faretype_id = isinstance(ln['faretype_id'], tuple) and ln['faretype_id'][0] or ln['faretype_id']
            ftclass_id  = isinstance(ln['ftclass_id'], tuple)  and ln['ftclass_id'][0]  or ln['faretype_id']
            from_id     = isinstance(ln['from_id'], tuple)     and ln['from_id'][0]     or ln['from_id']
            to_id       = isinstance(ln['to_id'], tuple)       and ln['to_id'][0]       or ln['to_id'] 
            dep = ln['dep']
            arr = ln['arr']
            
        if not airline_id: return {'value': res}
         
        search_date = []
         
        if dep and arr:
            dep_date = (parser.parse(dep)).strftime('%Y-%m-%d')
            arr_date = (parser.parse(arr)).strftime('%Y-%m-%d')
            search_date = [('start_date', '<=',dep_date), ('end_date','>=',arr_date)]
            
        airline = airln_obj.browse(cr, uid, airline_id)
        res['airtax_ids'] = airln_obj._cleanup_lines(cr, uid, airline.tax_lines)
        supp_airtaxes = []
         
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Supplier configured data :
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if tpartner_id:
            exception = suppairline = False
            search_criteria = search_date + [('airline_id','=',airline_id), ('partner_id','=',tpartner_id), ('by_default','=',False)]

            # ...............................................
            # Fetch: Commission exists for given criteria
            suppairln_ids = commln_obj.search(cr, uid, search_criteria)
            suppairln_id = suppairln_ids and suppairln_ids[0] or False
            if suppairln_id:
                suppairline = commln_obj.browse(cr, uid, suppairln_id)
                
                # Checking For Exceptions
                if faretype_id and faretype_id in map(lambda x: x.id, suppairline.ftfare_ids): exception = True
                if ftclass_id and ftclass_id in map(lambda x: x.id, suppairline.ftclass_ids) : exception = True
                if from_id and to_id:
                    if (from_id in map(lambda x: x.id, suppairline.ftfrom_ids)) and (to_id in map(lambda x: x.id, suppairline.ftto_ids)): 
                        exception = True
             
            # ....................................................... 
            # Fetch: Default Commission when exception is arised:
            if exception or not suppairln_id:
                search_criteria = [('airline_id','=',airline_id), ('partner_id','=',tpartner_id), ('by_default','=',True)]
                
                suppairln_ids = commln_obj.search(cr, uid, search_criteria)
                suppairln_id = suppairln_ids and suppairln_ids[0] or False
                if suppairln_id: 
                    suppairline = commln_obj.browse(cr, uid, suppairln_id)
                    
            if suppairline:
                supp_airtaxes = airln_obj._cleanup_lines(cr, uid, suppairline.tax_lines)
                res.update({
                            'airtax_ids'  : supp_airtaxes,
                            'a_tac_basic' : suppairline.tac_basic,
                            'a_tac_basic1': suppairline.tac_basic1,
                            'a_tac_basic2': suppairline.tac_basic2,
                            'a_tac_other' : suppairline.tac_other,
                            'a_tac_other1': suppairline.tac_other1,
                            'a_tac_other2': suppairline.tac_other2,
                            'a_tac_select': suppairline.tac_select,
                            'a_tac_perc'  : suppairline.tac_perc,
                            'a_tac_perc1' : suppairline.tac_perc1,
                            'a_tac_perc2' : suppairline.tac_perc2,
                            'tptax_basic' : suppairline.tptax_basic, 
                            'tptax_other' : suppairline.tptax_other, 
                            'tptax_airtax': suppairline.tptax_airtax,
                            'tptax_tac'   : suppairline.tptax_tac,
                            'tptax_tds'   : suppairline.tptax_tds,
                            'tptax_ids'   : map(lambda x: x.id, suppairline.tptax_ids),
                            })
             
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Customer configured data:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if customer_id and tpartner_id:
            exception = custairline = False
            search_criteria = search_date + [('airline_id','=',airline_id), ('partner_id','=',customer_id), ('tpartner_id','=',tpartner_id), ('by_default','=',False)]
             
            # ...............................................
            # Fetch: Charges exists for given criteria 
            custairln_ids = commln_obj.search(cr, uid, search_criteria)
            custairln_id = custairln_ids and custairln_ids[0] or False
            if custairln_id: 
                custairline = commln_obj.browse(cr, uid, custairln_id)
                 
                # Checking For Exceptions
                if faretype_id and faretype_id in map(lambda x: x.id, custairline.ftfare_ids): exception = True
                if ftclass_id and ftclass_id in map(lambda x: x.id, custairline.ftclass_ids) : exception = True
                if from_id and to_id:
                    if (from_id in map(lambda x: x.id, custairline.ftfrom_ids)) and (to_id in map(lambda x: x.id, custairline.ftto_ids)): 
                        exception = True
            
            # ....................................................... 
            # Fetch: Default Charges when exception is arised: 
            if exception or not custairln_id:
                search_criteria = [('airline_id','=',airline_id), ('partner_id','=',customer_id), ('tpartner_id','=',tpartner_id), ('by_default','=',True)]
                custairln_ids = commln_obj.search(cr, uid, search_criteria)
                custairln_id = custairln_ids and custairln_ids[0] or False
                if custairln_id: 
                    custairline = commln_obj.browse(cr, uid, custairln_id)
             
            if custairline:
                cust_airtaxes = airln_obj._cleanup_lines(cr, uid, custairline.tax_lines)
                combined_airtaxes = []
                 
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # [Adding / Merging]: Supplier TAC & Customer Discount for Airline Tax
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                if not supp_airtaxes:
                    combined_airtaxes = cust_airtaxes
                     
                else:
                    stxDict = dict([(x[2]['component_id'], x[2]) for x in supp_airtaxes])
                    ctxDict = dict([(x[2]['component_id'], x[2]) for x in cust_airtaxes])
                     
                    for s in stxDict:
                        # If TP Airline Tax is NOT discounted for Customer 
                        if s not in ctxDict.keys():
                            combined_airtaxes.append(stxDict[s])
                         
                        else: # Else merging discount:
                            newlist = stxDict[s]
                            newlist['disc_a'] = ctxDict[s]['disc_a']
                            newlist['disc_b'] = ctxDict[s]['disc_b']
                            newlist['disc_c'] = ctxDict[s]['disc_c']
                            combined_airtaxes.append(newlist)
                     
                    diff_ctxDict = [x for x in ctxDict.keys() if x not in stxDict.keys()]
                    # Appending remaining Customer Airline Taxes
                    for c in diff_ctxDict:
                        combined_airtaxes.append(ctxDict[c])
                         
                    combined_airtaxes = map(lambda x:(0,0,x), combined_airtaxes)
                 
                res.update({
                            'airtax_ids'   : combined_airtaxes,
                            'a_disc_basic' : custairline.tac_basic,
                            'a_disc_basic1': custairline.tac_basic1,
                            'a_disc_basic2': custairline.tac_basic2,
                            'a_disc_other' : custairline.tac_other,
                            'a_disc_other1': custairline.tac_other1,
                            'a_disc_other2': custairline.tac_other2,
                            'a_disc_select': custairline.tac_select,
                            'a_disc_perc'  : custairline.tac_perc,
                            'a_disc_perc1' : custairline.tac_perc1,
                            'a_disc_perc2' : custairline.tac_perc2,
                            'a_markup_perc': custairline.markup_perc,
                            'a_markup'     : custairline.markup,
                            'a_servicechrg_perc': custairline.servicechrg_perc,
                            'a_servicechrg'     : custairline.servicechrg,
                            })
        return {'value': res}
    
    def calculate_TACamt(self, cr, uid, ids, a_basic, a_other, a_tptax, tac_select, a_tac_perc, a_tac_basic, a_tac_other, a_tac_tptax, a_tac_perc1, a_tac_basic1, a_tac_other1
                                             , a_tac_tptax1, a_tac_perc2, a_tac_basic2, a_tac_other2, a_tac_tptax2, airtxtac_a, airtxtac_b, airtxtac_c, airtxtac_a4b, airtxtac_a4c, airtxtac_b4c, context=None):
        
        """
            Method calculates TAC amount based on Components selected..
            Note: 
                Same logic is used to calculate for DISCOUNT
        """
        
        TAC_amount = 0.00
        dp = get_dp_precision(cr, uid, 'Account')
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #    Componentwise TAC amt Calculation
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Atacbasic = a_tac_basic and round(((a_tac_perc * a_basic) / 100.00), dp) or 0
        Atactax   = round(((a_tac_perc * airtxtac_a) / 100.00), dp) or 0
        Atactax_4b = round(((a_tac_perc * airtxtac_a4b) / 100.00), dp) or 0
        Atactax_4c = round(((a_tac_perc * airtxtac_a4c) / 100.00), dp) or 0
        
        Atacothr  = a_tac_other and round(((a_tac_perc * a_other) / 100.00), dp) or 0
        Atactptax = a_tac_tptax and round(((a_tac_perc * a_tptax) / 100.00), dp) or 0
        
        Btactax  = round(((a_tac_perc1 * (airtxtac_b - Atactax_4b)) / 100.00), dp) or 0
        Btactax_4c  = round(((a_tac_perc1 * (airtxtac_b4c - Atactax_4c)) / 100.00), dp) or 0
        Btacbasic = a_tac_basic1 and round(((a_tac_perc1 * (a_basic - Atacbasic)) / 100.00), dp) or 0
        Btacothr  = a_tac_other1 and round(((a_tac_perc1 * (a_other - Atacothr))  / 100.00), dp) or 0
        Btactptax = a_tac_tptax1 and round(((a_tac_perc1 * (a_tptax - Atactptax)) / 100.00), dp) or 0

        Ctactax   = round(((a_tac_perc2 * (airtxtac_c - Atactax_4c - Btactax_4c)) / 100.00), dp) or 0
        Ctacbasic = a_tac_basic2 and round(((a_tac_perc2 * (a_basic - Atacbasic - Btacbasic)) / 100.00), dp) or 0
        Ctacothr  = a_tac_other2 and round(((a_tac_perc2 * (a_other - Atacothr - Btacothr))   / 100.00), dp) or 0
        Ctactptax = a_tac_tptax2 and round(((a_tac_perc2 * (a_tptax - Atactptax - Btactptax)) / 100.00), dp) or 0

        if tac_select ==  'onlyA':
            TAC_amount =  (Atacbasic + Atactax + Atacothr + Atactptax)
            
        elif tac_select ==  'AB100':
            TAC_amount = (  (Atacbasic + Atactax + Atacothr + Atactptax)
                          + (Btacbasic + Btactax + Btacothr + Btactptax))
            
        elif tac_select == 'ABC':
                         
            TAC_amount = (  (Atacbasic + Atactax + Atacothr + Atactptax)
                          + (Btacbasic + Btactax + Btacothr + Btactptax)
                          + (Ctacbasic + Ctactax + Ctacothr + Ctactptax))
        else:
             # without deduction
             Btacbasic = a_tac_basic1 and ((a_tac_perc1 * (a_basic)) / 100.00) or 0
             Btactax   = ((a_tac_perc1 * (airtxtac_b))   / 100.00) or 0
             Btacothr  = a_tac_other1 and ((a_tac_perc1 * (a_other)) / 100.00) or 0
             Btactptax   = a_tac_tptax1   and ((a_tac_perc1 * (a_tptax))   / 100.00) or 0
             
             TAC_amount = ( (Atacbasic + Atactax + Atacothr + Atactptax)
                          + (Btacbasic + Btactax + Btacothr + Btactptax))
            
        return TAC_amount
    
    def onchange_FT_subTotal(self, cr, uid, ids, inv_type, calledby, a_basic, a_other, a_servicechrg_perc, a_servicechrg
                              , a_markup_perc, a_markup, a_raf, a_tds_perc, a_tds, a_tds1_perc, a_tds1, a_vendor, a_reissue
                              , a_tac_perc, a_tac, tac_select, a_tac_basic, a_tac_other, a_tac_tptax
                              , a_tac_perc1, a_tac_basic1, a_tac_other1, a_tac_tptax1 
                              , a_tac_perc2, a_tac_basic2, a_tac_other2, a_tac_tptax2 
                              , tptax_basic, tptax_airtax, tptax_tac, tptax_tds, tptax_other
                              , airtax_ids, tptax_ids
                              , a_discount, disc_select, a_disc_perc, a_disc_basic, a_disc_other, a_disc_tptax
                              , a_disc_perc1, a_disc_basic1, a_disc_other1, a_disc_tptax1
                              , a_disc_perc2, a_disc_basic2, a_disc_other2, a_disc_tptax2
                              , a_cancel_markup, a_cancel_charges, a_cancel_service
                              , context=None):
        """ 
            Method  :: common for both Domestic & International Flight
            Used    :: in Invoice/SO - Flight (Dom/Int)
            Returns :: Subtotal
        """
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        
        tptax = tpamt4tax = 0.00
        airtax = airtxtac_a = airtxtac_b = airtxtac_c = airtxtac_a4b = airtxtac_b4c = airtxtac_a4c = 0.00
        airtxdisc_a = airtxdisc_b = airtxdisc_c = airtxdisc_a4b = airtxdisc_b4c = airtxdisc_a4c = 0.00

        
        for atx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'airtax_ids', airtax_ids, ['amount', 'tac_a', 'tac_b', 'tac_c', 'disc_a', 'disc_b', 'disc_c']):
            airtax += atx.get('amount',0)
            # Checked amount for TAC / Discount
            airtxtac_a += atx.get('tac_a') and atx.get('amount',0) or 0.00
            airtxtac_b += atx.get('tac_b') and atx.get('amount',0) or 0.00
            airtxtac_c += atx.get('tac_c') and atx.get('amount',0) or 0.00
            airtxdisc_a += atx.get('disc_a') and atx.get('amount',0) or 0.00
            airtxdisc_b += atx.get('disc_b') and atx.get('amount',0) or 0.00
            airtxdisc_c += atx.get('disc_c') and atx.get('amount',0) or 0.00
            
            # Checked amount for TAC / Discount B & C 
            airtxtac_a4b += atx.get('tac_a') and (atx.get('tac_b') and atx.get('amount',0)) or 0.00
            airtxtac_a4c += atx.get('tac_a') and (atx.get('tac_c') and atx.get('amount',0)) or 0.00
            airtxtac_b4c += atx.get('tac_b') and (atx.get('tac_c') and atx.get('amount',0)) or 0.00
            airtxdisc_a4b += atx.get('disc_a') and (atx.get('disc_b') and atx.get('amount',0)) or 0.00
            airtxdisc_a4c += atx.get('disc_a') and (atx.get('disc_c') and atx.get('amount',0)) or 0.00
            airtxdisc_b4c += atx.get('disc_b') and (atx.get('disc_c') and atx.get('amount',0)) or 0.00
            
        if tptax_basic == True : tpamt4tax += a_basic
        if tptax_airtax == True: tpamt4tax += airtax
        if tptax_tac == True   : tpamt4tax += a_tac
        if tptax_tds == True   : tpamt4tax += a_tds
        if tptax_other == True : tpamt4tax += a_other

        for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
            tptax += round((tpamt4tax * ttx['amount']),2)

        # .......................................................            
        # Percent Calculation:
        if calledby == 'all':
            # TAC Calculation
            if tac_select and (a_tac_perc or a_tac_perc1 or a_tac_perc2):
                a_tac = self.calculate_TACamt(cr, uid, ids, a_basic, a_other, tptax, tac_select, a_tac_perc, a_tac_basic, a_tac_other, a_tac_tptax
                                                 , a_tac_perc1, a_tac_basic1, a_tac_other1, a_tac_tptax1, a_tac_perc2, a_tac_basic2, a_tac_other2
                                                 , a_tac_tptax2, airtxtac_a, airtxtac_b, airtxtac_c, airtxtac_a4b, airtxtac_a4c, airtxtac_b4c)
                res['a_tac'] = a_tac
            
            # Discount Calculation same like TAC
            if disc_select and (a_disc_perc or a_disc_perc1 or a_disc_perc2):
                a_discount = self.calculate_TACamt(cr, uid, ids, a_basic, a_other, tptax, disc_select, a_disc_perc, a_disc_basic, a_disc_other
                                                   , a_disc_tptax, a_disc_perc1, a_disc_basic1, a_disc_other1, a_disc_tptax1, a_disc_perc2
                                                   , a_disc_basic2, a_disc_other2, a_disc_tptax2, airtxdisc_a, airtxdisc_b, airtxdisc_c
                                                   , airtxdisc_a4b, airtxdisc_a4c, airtxdisc_b4c)
                res['a_discount'] = a_discount
            
            # TDS on TAC...
            if a_tds_perc:
                a_tds = round(((a_tds_perc * a_tac) / 100.00), dp)
                res['a_tds'] = a_tds
                    
            # TDS on Discount...
            if a_tds1_perc:
                a_tds1 = round(((a_tds1_perc * a_discount) / 100.00), dp)
                res['a_tds1'] = a_tds1
         
            if a_markup_perc:
                a_markup = round(((a_markup_perc * a_basic) / 100.00), dp)
                res['a_markup'] = a_markup
        # .......................................................
                
        if inv_type in ('out_invoice', 'out_refund'):    
            tot = a_basic + a_other + a_markup + a_raf + airtax + a_reissue + tptax - a_discount + a_tds1
            if a_servicechrg_perc:
                a_servicechrg = round(((a_servicechrg_perc * tot) / 100.00), dp)
                res['a_servicechrg'] = a_servicechrg
            tot += a_servicechrg - a_cancel_markup - a_cancel_charges - a_cancel_service
        else: # Purchase
            tot = a_basic + a_other + a_raf + airtax + tptax + a_reissue + a_vendor + a_tds - a_tac - a_cancel_charges
        
        
        res.update({
               'a_total' : tot,
               'a_tptax' : tptax,
               'a_tax': airtax,
               })
        return {'value':res}
    
    # To Compute the Refund (total amount - refunded amount)
    def compute_refund_amount (self, cr, uid, ref_invlines, refund_id, context = None):
        FT_obj = self.pool.get('tr.invoice.flight')
        ftln_obj = self.pool.get('tr.invoice.flight.lines')
        # Deleting The Airline Taxes
        cr.execute("""delete from tr_airlines_taxes where flight_id in 
            (select id from tr_invoice_flight where invoice_id =  """+ str(refund_id[0])+""")""")
        # Deleting The Sector Line Which is already refunde
        for case in ref_invlines:
#             cr.execute("""delete from tr_invoice_flight_lines where src_id in 
#                         (select id from tr_invoice_flight_lines where is_refunded = True and flight_id =  """+ str(case.id)+""")""")
            sctr_ids = ftln_obj.search(cr,uid,[('is_refunded','=',True),('flight_id','=',case.src_id.id)])
            if sctr_ids: 
                ref_sctr_ids = ftln_obj.search(cr,uid,[('src_id','in',sctr_ids),('flight_id','=',(case.id))])
                ftln_obj.unlink(cr,uid,ref_sctr_ids)
            cr.execute(""" select      
                             ((case when inv.inv_a_tac > 0 then inv.inv_a_tac else 0 end) 
                                     - (case when cn.c_a_tac > 0 then cn.c_a_tac else 0 end )) as a_tac,
                             ((case when inv.inv_a_basic > 0 then inv.inv_a_basic else 0 end)
                                     - (case when cn.c_a_basic > 0 then cn.c_a_basic else 0 end)) as a_basic,
                             ((case when inv.inv_a_tds  > 0 then inv.inv_a_tds else 0 end)
                                     - (case when cn.c_a_tds  > 0 then cn.c_a_tds else 0 end)) as a_tds,
                             ((case when inv.inv_a_tds1 > 0 then inv.inv_a_tds1 else 0 end)
                                     - (case when cn.c_a_tds1 > 0 then cn.c_a_tds1 else 0 end)) as a_tds1,
                             ((case when inv.inv_a_raf > 0 then inv.inv_a_raf  else 0 end)
                                     - (case when cn.c_a_raf > 0 then cn.c_a_raf else 0 end)) as a_raf,
                             ((case when inv.inv_a_markup > 0 then inv.inv_a_markup else 0 end)  
                                     - (case when cn.c_a_markup > 0 then cn.c_a_markup else 0 end)) as a_markup,
                             ((case when inv.inv_a_servicechrg > 0 then inv.inv_a_servicechrg else 0 end)
                                     - (case when cn.c_a_servicechrg > 0 then cn.c_a_servicechrg else 0 end)) as a_servicechrg,
                             ((case when inv.inv_a_other > 0 then inv.inv_a_other else 0 end)
                                     - (case when cn.c_a_other > 0 then cn.c_a_other else 0 end)) as a_other,
                             ((case when inv.inv_a_vendor > 0 then inv.inv_a_vendor else 0 end)
                                     - (case when cn.c_a_vendor > 0 then cn.c_a_vendor else 0 end)) as a_vendor,
                             ((case when inv.inv_a_reissue > 0 then inv.inv_a_reissue  else 0 end)
                                     - (case when cn.c_a_reissue > 0 then cn.c_a_reissue else 0 end)) as a_reissue,
                             ((case when inv.inv_a_disc > 0 then inv.inv_a_disc else 0 end)
                                     - (case when cn.c_a_disc > 0 then cn.c_a_disc else 0 end)) as a_disc,
                             ((case when inv.inv_a_discount > 0 then inv.inv_a_discount else 0 end)
                                     - (case when cn.c_a_discount > 0 then cn.c_a_discount else 0 end)) as a_discount
 
                        from
                             
                            (select id as id,
                                    a_tac as inv_a_tac,
                                    a_basic as inv_a_basic,
                                    a_tds as inv_a_tds ,
                                    a_tds1 as inv_a_tds1,
                                    a_raf as inv_a_raf,
                                    a_markup as inv_a_markup,
                                    a_servicechrg as inv_a_servicechrg,
                                    a_other as inv_a_other,
                                    a_vendor as inv_a_vendor,
                                    a_reissue as inv_a_reissue,
                                    a_disc as inv_a_disc,
                                    a_discount as inv_a_discount
                         
                                 from tr_invoice_flight where id = """ + str(case.src_id.id) + """ )inv
                                 left outer join
                                    (select 
                                    f.src_id as id,
                                    sum(f.a_tac) as c_a_tac,
                                    sum(f.a_basic)as c_a_basic,
                                    sum(f.a_tds) as c_a_tds ,
                                    sum(f.a_tds1) as c_a_tds1,
                                    sum(f.a_raf) as c_a_raf,
                                    sum(f.a_markup) as c_a_markup,
                                    sum(f.a_servicechrg) as c_a_servicechrg,
                                    sum(f.a_other) as c_a_other,
                                    sum(f.a_vendor) as c_a_vendor,
                                    sum(f.a_reissue) as c_a_reissue,
                                    sum(f.a_disc) as c_a_disc,
                                    sum(f.a_discount) as c_a_discount
                                        
                                     
                              from tr_invoice_flight f inner join account_invoice i  
                              on f.invoice_id = i.id 
                              where f.src_id = """ + str(case.src_id.id) + """  and f.invoice_id !=  """+ str(refund_id[0])+"""
                              and i.state not in ('cancel')
                              group by f.src_id)cn
                              on inv.id  = cn.id""")
            invvals = cr.dictfetchone()
            
            cr.execute("""  select 
                                    inv.component_id,
                                    ((case when inv.inv_amount > 0 then inv.inv_amount else 0 end) 
                                        -(case when  cn.cn_amount > 0 then  cn.cn_amount else 0 end)) as amount 
                                from
                                    (select component_id,amount as inv_amount 
                                from tr_airlines_taxes where flight_id =""" + str(case.src_id.id) + """ )inv
                                left outer join 
                                    (select component_id,sum(amount) as cn_amount 
                                from tr_airlines_taxes where flight_id 
                                in (select f.id from tr_invoice_flight f inner join account_invoice i on f.invoice_id = i.id 
                                    where f.src_id = """ + str(case.src_id.id) +""" 
                                    and f.invoice_id !=  """+ str(refund_id[0])+""" and i.state not in ('cancel'))
                                group by component_id )cn 
                                on cn.component_id = inv.component_id
                            """)
            airtaxes = cr.fetchall()
            airtaxvals = []
            
            for tax in airtaxes:
                cmpvals = {'component_id':tax[0],'amount':tax[1]}
                airtaxvals.append((0,0,cmpvals))
                
            vals = {
                    'a_tac' : invvals['a_tac'],'a_basic' : invvals['a_basic'],'a_tds' : invvals['a_tds'],'a_tds1' : invvals['a_tds1'],'a_tac' : invvals['a_tac'],
                    'a_raf' : invvals['a_raf'],'a_markup' : invvals['a_markup'],
                    'a_servicechrg' : invvals['a_servicechrg'],'a_other' : invvals['a_other'],'a_vendor' : invvals['a_vendor'],
                    'a_reissue' : invvals['a_reissue' ],'a_disc' : invvals['a_disc' ],'a_discount' : invvals['a_discount'],
                    'airtax_ids' : airtaxvals,
                    }
            FT_obj.write(cr,uid,[case.id],vals)
            
        return True
    
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
            nartn = case.ft_traveltype == 'dom_flight' and 'Domestic Flight,' or 'International Flight,' 
            nartn += ' Pax: ' +  str(case.pax_name or '')
            nartn += ' Tkt: ' + str(case.ticket_no or '')
            nartn += ' PNR: ' + str(case.airline_pnr or '')
                            
            first_sect = case.flight_lines and case.flight_lines[0]
            last_sect = case.flight_lines and case.flight_lines[-1]
            if first_sect: # First Sector
              nartn += ' SEC: ' + str(first_sect.from_id and first_sect.from_id.code or '')
              
            if last_sect: # Last Sector
                nartn += ' - ' + str(last_sect.to_id and last_sect.to_id.code or '')
         
            getamt = self.calc_Flight_total(cr, uid, case.id, case.inv_type)
            subtot = getamt.get('subtot',0) 
                    
            inv_currency = case.invoice_id.currency_id.id
            subtot = cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, subtot, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                
            vals = {
                'name'       : nartn,
                'passenger'  : case.pax_name,
                'product_id' : case.product_id.id or False,
                'tpartner_id': case.tpartner_id.id or False,
                'origin'    : case.invoice_id.name,
                'account_id': case.account_id.id,
                'account_analytic_id' : case.invoice_id and case.invoice_id.account_analytic_id and case.invoice_id.account_analytic_id.id or False,
                'currency_id': case.currency_id.id,
                'price_unit': subtot,
                'quantity'  : 1,
                'price_subtotal': subtot,
                'basic'   : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_basic, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'other'   : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('other',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'tac'     : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_tac, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'tds'     : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_tds, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'tds1'    : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_tds1, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'markup'  : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_markup, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'discount'      : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_discount, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'servicechrg'   : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_servicechrg, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'a_cancel_markup' : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_cancel_markup, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'a_cancel_charges': cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_cancel_charges, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'a_cancel_service': cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, case.a_cancel_service, context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                'purchase_amt'  : cur_obj.compute(cr, uid, case.currency_id.id, inv_currency, getamt.get('po_subtot',0), context={'date': case.invoice_id.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                    }
            print "valsflight",vals
            if chkwhich == 'to_create':
                vals.update({
                             'flight_id': case.id,
                             'invoice_id': case.invoice_id.id,
                             })
                invln_obj.create(cr, uid, vals, context=context)
            else:
                ilids = invln_obj.search(cr, uid, [('flight_id','=', case.id), ('invoice_id','=', case.invoice_id.id)])
                invln_obj.write(cr, uid, ilids, vals, context=context)
                
            inv_obj.write(cr, uid, [case.invoice_id.id], context)
            
        return True
    
    def create(self, cr, uid, vals, context=None):
        result = super(tr_invoice_flight, self).create(cr, uid, vals, context)
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, [result], 'to_create', context)
        return result
       
    def write(self, cr, uid, ids, vals, context=None):
        result = super(tr_invoice_flight, self).write(cr, uid, ids, vals, context) 
        if context and context.get('travel_type','') != 'package':
            self.invoice_line_create(cr, uid, ids, 'to_write', context)
        return result

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for case in self.browse(cr,uid,ids):
            if case.inv_type == 'out_refund' and case.src_id:
                for ft in self.browse(cr,uid,[case.src_id]):
                    if ft.src_id.is_refunded and ft.inv_type == 'out_refund':
                        self.write(cr, uid, [ft.id],{'is_refunded':False}, context)
        return super(tr_invoice_flight, self).unlink(cr, uid, ids, context) 
    
tr_invoice_flight()

class tr_invoice_flight_lines(osv.osv):
    _name = 'tr.invoice.flight.lines' 
    _description = "Flight Lines"
             
    _columns = {     
            'flight_id' : fields.many2one('tr.invoice.flight', 'Flight', ondelete='cascade'),
            'src_id'    : fields.many2one('tr.invoice.flight.lines', 'Source Reference'),
            
            'airline_id' : fields.many2one('tr.airlines', 'Airline', ondelete='restrict'),
            'from_id'    : fields.many2one('tr.airport', 'From', ondelete='restrict'),
            'to_id'      : fields.many2one('tr.airport', 'To', ondelete='restrict'),
            'ftclass_id' : fields.many2one('tr.flight.class', 'Class', ondelete='restrict'),
            'faretype_id': fields.many2one('tr.flight.faretype', 'Fare Type', ondelete='restrict'),
            'ft_num'     : fields.char('Flight No', size=10),
            'dep'        : fields.datetime('Departure'),
            'arr'        : fields.datetime('Arrival'),
           
           'is_refunded' : fields.boolean('Refunded'),
               }
    def onchange_dep(self, cr, uid, ids, dep):
        res = {}
        if dep :
            res['arr'] = dep
        return {'value' : res}


class tr_airlines_taxes_inherited(osv.osv):
    _inherit = 'tr.airlines.taxes'
    _columns = {
                'flight_id' : fields.many2one('tr.invoice.flight', 'Flight Line', ondelete='cascade'),
                
                'airline_id'   : fields.many2one('tr.airlines', 'Airlines', ondelete='cascade'),
                'component_id' : fields.many2one('tr.airlines.taxcomp', 'Tax Name', ondelete='restrict', required=True),
                'tac_a'        : fields.boolean('TAC on A'),
                'tac_b'        : fields.boolean('TAC on B'),
                'tac_c'        : fields.boolean('TAC on C'),
                'disc_a'       : fields.boolean('Discount on A'),
                'disc_b'       : fields.boolean('Discount on B'),
                'disc_c'       : fields.boolean('Discount on C'),
                'amount'       : fields.float('Amount', digits_compute=dp.get_precision('Account')),
               }
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: