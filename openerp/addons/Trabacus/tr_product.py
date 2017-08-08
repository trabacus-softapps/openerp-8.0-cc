#-*- coding: utf-8 -*-
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

import tr_config

def get_dp_precision(cr, uid, application):
    cr.execute('select digits from decimal_precision where name=%s', (application,))
    res = cr.fetchone()
    return res[0] if res else 2


# TODO: delete this object is not required
class tr_prod_opt_flight(osv.osv):
    _name = 'tr.prod.opt.flight' 
    _description = "Product Option - Flight"
    _columns = {
        'parent_id' : fields.many2one('product.product', 'Parent', ondelete='cascade'),
        'name'      : fields.char('Option', size=200),
        'image'     : fields.binary('Image'),
        'ref_id'    : fields.integer('Sale Flight Option Reference'),
            
        'sumry'      : fields.text('Summary'),
        'smry_adult' : fields.float('Adult Charges', digits_compute=dp.get_precision('Account')),
        'smry_child' : fields.float('Child Charges', digits_compute=dp.get_precision('Account')),
        'smry_infnt' : fields.float('Infant Charges', digits_compute=dp.get_precision('Account')),
        'notes'      : fields.text('Internal Note'),
        'type'       : fields.selection([('ft_detail','Flight Details'), ('ft_smry','Flight Summary')], 'Costing Type'),
        'sector_ids' : fields.one2many('tr.prod.flight.lines', 'ftopt_id', 'Sector Lines' ),
        'product_ids': fields.many2many('product.product', 'flopt_prod_rel', 'opt_id', 'prod_id', 'Product', domain="[('travel_type','in',('dom_flight','int_flight'))]"),
        
        #TODO: delete
        'members': fields.many2many('res.users', 'opt_user_rel', 'opt_id', 'uid', 'Project Members',),
               }
    
    def populate_sectorlines(self, cr, uid, ids, context=None):
        # Note:
        # Product Flight tpricing is removed:
        #
        # TODO:
        # delete this method
        #
        
#         ftpricing_obj = self.pool.get('tr.service.flightpricing')
#         ftln_obj = self.pool.get('tr.prod.flight.lines')
#         
#         for case in self.browse(cr, uid, ids):
#             for prod in case.product_ids:
#                 for ln in prod.service_id.ftline_ids:
# #                     lnvals = {
# #                               'airline_id': ln.airline_id and ln.airline_id.id or False,
# #                               'source': ln.source,
# #                               'dest': ln.dest,
# #                               'ft_class': ln.ft_class,
# #                               'ft_num': ln.ft_num,
# #                               'ftopt_id': case.id
# #                               }
#                     lnvals = ftpricing_obj.read(cr, uid, ln.id, []) or {}
#                     del lnvals['service_id']
#                     del lnvals['airline_id']
#                     lnvals['airline_id'] = ln.airline_id and ln.airline_id.id or False
#                     lnvals['ftopt_id'] = case.id
#                     
#                     ftln_obj.create(cr, uid, lnvals)
        return True
    
tr_prod_opt_flight()

    
class tr_product_services(osv.osv):
    _name = 'tr.product.services' 
    _description = "Product Services"
    
    def _get_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')

        def _calc_tptax(case, basic, courier, vfs, tac, tds, dd, other, tp_servicechrg):
                tpamt4tax = tptx = 0.00
                if case.tptax_basic == True   : tpamt4tax += basic
                if case.tptax_courier == True : tpamt4tax += courier
                if case.tptax_vfs == True     : tpamt4tax += vfs
                if case.tptax_tac == True     : tpamt4tax += tac
                if case.tptax_tds == True     : tpamt4tax += tds
                if case.tptax_dd == True      : tpamt4tax += dd
                if case.tptax_other == True   : tpamt4tax += other
                if case.tptax_tpservicechrg == True   : tpamt4tax += tp_servicechrg
                for ttx in case.tptax_ids:
                    tptx += round((tpamt4tax * ttx.amount),dp)
                return tptx
 
        for case in self.browse(cr, uid, ids):
            tpamt4tax = ctpamt4tax = itpamt4tax = tptax = ctptax = itptax = 0.00
             
            res[case.id] = {'a_rate': 0.00, 'c_rate': 0.00, 'i_rate':0.00
                            , 'a_tptax':0.00, 'c_tptax':0.00, 'i_tptax':0.00
                            , 'total': 0.00
                            }
           
            a_tptax = _calc_tptax(case, case.a_basic, case.a_courier, case.a_vfs, case.a_tac, case.a_tds, case.a_dd, case.a_other, case.a_tp_servicechrg)
            c_tptax = _calc_tptax(case, case.c_basic, case.c_courier, case.c_vfs, case.c_tac, case.c_tds, case.c_dd, case.c_other, case.c_tp_servicechrg)
            i_tptax = _calc_tptax(case, case.i_basic, case.i_courier, case.i_vfs, case.i_tac, case.i_tds, case.i_dd, case.i_other, case.i_tp_servicechrg)

            if case.travel_type == 'car':
                res[case.id]['a_rate'] = case.a_basic + a_tptax + case.a_markup + case.a_other + case.driver_chrgs + case.a_servicechrg
                res[case.id]['a_tptax'] = case.a_tptax
                 
            if case.travel_type == 'visa':
                res[case.id]['a_rate'] = (case.a_basic + case.a_vfs + case.a_courier + case.a_dd + case.a_other + case.a_servicechrg + a_tptax + case.a_markup + case.a_tp_servicechrg) 
                res[case.id]['c_rate'] = (case.c_basic + case.c_vfs + case.c_courier + case.c_dd + case.c_other + case.c_servicechrg + c_tptax + case.c_markup + case.c_tp_servicechrg) 
                res[case.id]['i_rate'] = (case.i_basic + case.i_vfs + case.i_courier + case.i_dd + case.i_other + case.i_servicechrg + i_tptax + case.i_markup + case.i_tp_servicechrg)
                res[case.id]['a_tptax'] = a_tptax
                res[case.id]['c_tptax'] = c_tptax
                res[case.id]['i_tptax'] = i_tptax

            elif case.travel_type in ('activity', 'add_on'):
                res[case.id]['a_rate'] = (case.a_basic + case.a_servicechrg + a_tptax + case.a_markup) 
                res[case.id]['c_rate'] = (case.c_basic + case.c_servicechrg + c_tptax + case.c_markup) 
                res[case.id]['i_rate'] = (case.i_basic + case.i_servicechrg + i_tptax + case.i_markup)
                res[case.id]['a_tptax'] = a_tptax
                res[case.id]['c_tptax'] = c_tptax
                res[case.id]['i_tptax'] = i_tptax
                  
                
        return res
    
    def _get_currency(self, cr, uid, ctx):
        comp = self.pool.get('res.users').browse(cr, uid, uid).company_id
        if not comp:
            comp_id = self.pool.get('res.company').search(cr, uid, [])[0]
            comp = self.pool.get('res.company').browse(cr, uid, comp_id)
        return comp.currency_id.id
    
    _columns = { 
        'travel_type' : fields.selection(tr_config.TRAVEL_TYPES,'Service Type'),
        'desc'        : fields.char('Description', size=128),
        
        'country_id' : fields.many2one('res.country', 'Country', ondelete='restrict'), 
        'currency_id': fields.many2one("res.currency", "Currency", ondelete='restrict'),
        'rate_till'  : fields.date('Rate Valid Till'),
        
        'contact_name'   : fields.char('Name', size=150),
        'contact_phone'  : fields.char('Contact No.', size=100),
        'contact_email'  : fields.char('Email', size=100),
        'contact_address': fields.char('Address', size=500),
        'h_contact' : fields.char('Hotel Contact', size=30),
        'h_phone'   : fields.char('Hotel Phone', size=30),
        'h_email'   : fields.char('Hotel Email', size=30),
        'no_nts'  : fields.integer('No. of Nights'),  
        
        'httype_id'    : fields.many2one('tr.hotel.type','Hotel Type', ondelete='restrict'),
#         'tp_name'      : fields.char('Name', size=150),
        'tp_phone'     : fields.char('Contact No.', size=100),  
        'tp_email'     : fields.char('Email', size=100),
        'tp_street'    : fields.char('Street', size=128),
        'tp_street2'   : fields.char('Street2', size=128),
        'tp_zip'       : fields.char('Zip', size=24),
        'tp_city'      : fields.char('City', size=128),
        'tp_country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
        'tp_state_id'  : fields.many2one("res.country.state", 'State', domain="[('country_id','=',tp_country_id)]", ondelete='restrict'),
        
        'visa_categ_id' : fields.many2one('tr.visa.categ', 'Visa Category', ondelete='restrict'),
        'visa_req_ids'  : fields.one2many('tr.visa.requirement', 'service_id', 'Visa Requirement'),
         
        'tr_type'    : fields.char('Type', size=30),
        'info'       : fields.char('Information', size=30),
        'cost_type'  : fields.selection([('ind_cost','Individual'),('cons_cost','Consolidated')], 'Calculation Type'),
        'pick_up'    : fields.text('From'),
        'drop_at'    : fields.text('To'),
        
        'no_days'   : fields.float('No. of Days'),  
        'rate_km'   : fields.float('Rate per KM'),
        'mrkup_km'  : fields.float('Markup per KM'), 
                
        'subtotal'  : fields.function(_get_amount, string='Total', type='float', digits_compute=dp.get_precision('Account'), multi="amt"),
        'total'     : fields.function(_get_amount, string='Total', type='float', digits_compute=dp.get_precision('Account'), multi="amt"),

        'no_seats'    : fields.integer('No. of Seats'),
        'vehicle_id'  : fields.many2one('tr.vehicle', 'Vehicle', ondelete='restrict'),
        'tpartner_id' : fields.many2one('res.partner', 'Travel Partner', domain=[('supplier', '=', 1)], ondelete='restrict'), 
            
        'usage_lmt'     : fields.float('Usage Limit'),
        'ext_rate_km'   : fields.float('Rate per Extra KM'), 
        'ext_rate_hour' : fields.float('Rate per Extra Hour'),
        'ext_mrkup_km'  : fields.float('Markup per Extra KM'),
        'ext_mrkup_hour': fields.float('Markup per Extra Hour'),
        'driver_chrgs'  : fields.float('Driver Charges'),
        
        'a_basic'   : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'a_vfs'     : fields.float('VFS', digits_compute=dp.get_precision('Account')),
        'a_dd'      : fields.float('DD', digits_compute=dp.get_precision('Account')),
        'a_courier' : fields.float('Courier', digits_compute=dp.get_precision('Account')),
        'a_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'a_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'a_markup_perc' : fields.float('Mark Up %', digits_compute=dp.get_precision('Account')),
        'a_markup'      : fields.float('Mark UP', digits_compute=dp.get_precision('Account')),
        'a_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
        'a_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
        'a_other'       : fields.float('Other Charges', digits_compute=dp.get_precision('Account')),
        'a_servicechrg_perc'  : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
        'a_servicechrg'       : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'a_tp_servicechrg'  : fields.float('T.P. Service Charge', digits_compute=dp.get_precision('Account')),
        'a_tptax'    : fields.function(_get_amount, string='Adult T.P.Tax', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
        'a_rate'     : fields.function(_get_amount, string='Adult Charges', store=True, type='float', digits_compute=dp.get_precision('Account'), multi='tot'),
               
        'c_basic'   : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'c_vfs'     : fields.float('VFS', digits_compute=dp.get_precision('Account')),
        'c_dd'      : fields.float('DD', digits_compute=dp.get_precision('Account')),
        'c_courier' : fields.float('Courier', digits_compute=dp.get_precision('Account')),
        'c_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'c_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'c_markup_perc' : fields.float('Mark Up %', digits_compute=dp.get_precision('Account')),
        'c_markup'      : fields.float('Mark Up', digits_compute=dp.get_precision('Account')),
        'c_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
        'c_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
        'c_other'       : fields.float('Other Charges', digits_compute=dp.get_precision('Account')),
        'c_servicechrg_perc': fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        'c_servicechrg'     : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'c_tp_servicechrg'  : fields.float('T.P. Service Charge', digits_compute=dp.get_precision('Account')),
        'c_tptax'      : fields.function(_get_amount, string='Child T.P Tax', type='float', digits_compute=dp.get_precision('Account'), multi="amt"),
        'c_rate'       : fields.function(_get_amount, string='Child Fees', type='float', digits_compute=dp.get_precision('Account'), multi="amt"),
        
        'i_basic'   : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'i_vfs'     : fields.float('VFS', digits_compute=dp.get_precision('Account')),
        'i_dd'      : fields.float('DD', digits_compute=dp.get_precision('Account')),
        'i_courier' : fields.float('Courier', digits_compute=dp.get_precision('Account')),
        'i_tac_perc'  : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'i_tac'       : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'i_markup_perc' : fields.float('Mark Up %', digits_compute=dp.get_precision('Account')),
        'i_markup'      : fields.float('Mark Up', digits_compute=dp.get_precision('Account')),
        'i_tds_perc'    : fields.float('TDS(T) %', digits_compute=dp.get_precision('Account')),
        'i_tds'         : fields.float('TDS(T)', digits_compute=dp.get_precision('Account')), 
        'i_other'       : fields.float('Other Charges', digits_compute=dp.get_precision('Account')),
        'i_servicechrg'     : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'i_servicechrg_perc': fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        'i_tp_servicechrg'  : fields.float('T.P. Service Charge', digits_compute=dp.get_precision('Account')),
        'i_tptax'    : fields.function(_get_amount, string=' Infant T.P Tax', type='float', digits_compute=dp.get_precision('Account'), multi="amt"),
        'i_rate'     : fields.function(_get_amount, string='Infant Fees', type='float', digits_compute=dp.get_precision('Account'), multi="amt"),

        'tptax_basic'   : fields.boolean('On Basic'),
        'tptax_other'   : fields.boolean('On Other'),
        'tptax_vfs'     : fields.boolean('On VFS'),
        'tptax_dd'      : fields.boolean('On DD'),
        'tptax_tac'     : fields.boolean('On TAC'),
        'tptax_tds'     : fields.boolean('On TDS(T)'),        
        'tptax_courier' : fields.boolean('On Courier'),
        'tptax_tpservicechrg'   : fields.boolean('On T.P. Service Charge'),  
        'tptax_ids'  : fields.many2many('account.tax', 'prod_tptax_rel', 'product_id', 'tax_id', 'T.P. Taxes'),
        
        'htline_ids'  : fields.one2many('tr.service.hotelpricing', 'service_id', 'Hotel Pricing', ondelete='cascade'), 
        'crsline_ids' : fields.one2many('tr.service.cruisepricing', 'service_id', 'Cruise Pricing', ondelete='cascade'),
         
               }
    
    _defaults = { 
               'currency_id': _get_currency
               }
    
tr_product_services()
    
class product_product(osv.osv): 
    _inherit = 'product.product'
    _table = "product_product"
    _inherits = {
                  'tr.product.services': 'service_id' 
                  }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        travel_typ = context.get('default_travel_type', False)
#       hol_trtyp = context.get('hol_trtyp', False)
        #TO do : For Holiday Package
        if travel_typ:            
            tree_name = search_name = form_name = ''
            
            if travel_typ == 'dom_package':
                tree_name = "product_tree_view_trprodDompack"
                form_name = 'product_form_view_trprod_Dompack'
            if travel_typ == 'dom_flight':
                tree_name = 'product_tree_view_trprodFlight'
                form_name = "product_form_view_trprod_Flight"
            if travel_typ == 'int_flight':
                tree_name = "product_tree_view_trprodFlight"
                form_name = 'product_form_view_trprod_Flight'
            if travel_typ == 'dom_hotel':
                tree_name = 'product_tree_view_trprodHT'
                form_name = "product_form_view_trprod_Hotel"
            if travel_typ == 'int_hotel':
                tree_name = 'product_tree_view_trprodHT'
                form_name = "product_form_view_trprod_Hotel"
            if travel_typ == 'car':
                tree_name = "product_tree_view_trprodCar"
                form_name = "product_form_view_trprod_Car"
            if travel_typ == 'activity':
                tree_name = "product_tree_view_trprodActivity"
                form_name = "product_form_view_trprod_Activity"
            if travel_typ == 'add_on':
                tree_name = "product_tree_view_trprodAddon"
                form_name = "product_form_view_trprod_Addon"
            if travel_typ == 'visa':
                tree_name = "product_tree_view_trprodVisa"
                form_name = "product_form_view_trprod_Visa"
            if travel_typ == 'insurance':
                tree_name = "product_tree_view_trprodINS"
                form_name = "product_form_view_trprod_Ins"
            if travel_typ == 'cruise':
                tree_name = "product_tree_view_trprodCrus"
                form_name = "product_form_view_trprod_Cruise"
            if travel_typ == 'railway':
                tree_name = "product_tree_view_trprodOthr"
                form_name = "product_form_view_trprod_Other"
               
            if not view_type:
                view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', '=', tree_name)])
                view_type = 'tree'
               
            if view_type == 'tree':
                view_id = self.pool.get('ir.ui.view').search(cr,uid,[('name', '=', tree_name)])   
               
            if view_type == 'form':
                view_id = self.pool.get('ir.ui.view').search(cr,uid,[('name', '=', form_name)])
               
            if view_id and isinstance(view_id, (list, tuple)):
                view_id = view_id[0]
        
        return super(product_product,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

    
    _columns = {
        # Standard fields
        'default_code' : fields.char('Code', size=10),
        'name_template': fields.related('product_tmpl_id', 'name', string="Name", type='char', size=500, store=True),
        'create_date'  : fields.date('Creation Date', readonly=True, select=False, help="Date on which Product is created."),
         
        # Extra
        'service_id'   : fields.many2one('tr.product.services', 'Services', required=True, ondelete="cascade"),
        'travel_type1' : fields.related('service_id', 'travel_type', type='selection', string='Service Type', store=True),
        'othr_trtype'  : fields.selection([('railway','Railway')], "Service Type"),
        
        'create_tp'     : fields.boolean('Create Travel Partner'),
        'blacklist_ok'  : fields.boolean('Black List'),
        'destination_id': fields.many2one('tr.destination', 'Destination', ondelete='restrict'),
        
        'terms_conditions': fields.text('Terms & conditions'),
        'requirements'  : fields.text('Requirements'),
        'requirements1' : fields.text('Requirements1'),
        'inclusions'    : fields.text('Inclusions'),
        'remarks'       : fields.text('Remarks'),

        'flight_opt_ids' : fields.one2many('tr.prod.opt.flight', 'parent_id', 'Flight Option' ),
        
        'taxon_ids' : fields.one2many('tr.prod.taxon', 'product_id', 'Tax on', ondelete='cascade'),
        }
    
    
    
#     Product: Others
    def onchange_TravelType(self, cr, uid, ids, othr_trtype):
        return {'value':{'travel_type' : othr_trtype}}
    
# #    Visa:    
#     def onchange_pVISA_onAmt(self, cr, uid, ids, chkif, chkwhich, basic, vfs, tac, courier, dd, other_chrg, servicechrg_perc, servicechrg, tp_servicechrg, tptax, markup):
#         """ 
#             Method  :: common for both Adult & Child
#             Used    :: in Product - Visa
#             Returns :: (%) value for the given Amount
#         """
#         res = {}
#         
#         if chkwhich == 'tac':
#            res['tac_perc'] = round(((tac / float(basic or 1)) * 100), 2)
#            
#         if chkwhich == 'tptax':
#            res['tptax_perc'] = round(((tptax / float(basic or 1)) * 100), 2) 
# 
#         amt = (basic + vfs + courier + dd + other_chrg + markup + tptax)
#         if chkwhich == 'servc':
#             res['servicechrg_perc'] = round(((servicechrg / float(amt or 1)) * 100), 2)
#         else:
#             servicechrg = round(((servicechrg_perc * amt) / 100.00), 2)
#             res['servicechrg'] = servicechrg
#                 
#         res['rate'] = (amt + servicechrg + tp_servicechrg)
#             
#         result = {}
#         if chkif == 'adult':
#            result = res.copy() 
#            
#         elif chkif == 'child':
#             for r in res.keys():
#                 result['c_'+r] = res[r]
#                 
#         return {'value': result}
# 
# #    Visa:
#     def onchange_pVISA_Total(self, cr, uid, ids, chkif, chkwhich, basic, vfs, courier, dd, other_chrg, servicechrg_perc, servicechrg, markup, tac_perc, tptax_perc, tptax, tp_servicechrg):  
#         """ 
#             Method  :: common for both Adult & Child
#             Used    :: in Product - Visa
#             Returns :: Subtotal and/or Amount value for the given (%)
#         """
# 
#         res = {}
#         if chkwhich == 'tac':
#             res['tac'] = round(((tac_perc * basic) / 100.00), 2) 
#            
#         if chkwhich == 'tptax':
#             tptax = round(((tptax_perc * basic) / 100.00), 2)
#             res['tptax'] = tptax 
#            
#         amt = (basic + vfs + courier + dd + other_chrg + markup + tptax)
#         
#         servicechrg = round(((servicechrg_perc * amt) / 100.00), 2)
#         
#         res.update({'rate' : (amt + servicechrg + tp_servicechrg),
#                     'servicechrg': servicechrg,
#                })
# 
#         result = {}
#         if chkif == 'adult':
#            result = res.copy() 
#            
#         elif chkif == 'child':
#             for r in res.keys():
#                 result['c_'+r] = res[r]
#                 
#         return {'value':result}


#    Visa:
                              
    def onchange_pVISA_Total(self, cr, uid, ids, chkif, calledby, basic, vfs, courier, dd, other_chrg, markup_perc, markup
                            , tac_perc, tac, servicechrg_perc, servicechrg, tp_servicechrg
                            , tptax_basic, tptax_courier, tptax_vfs, tptax_tac, tptax_dd, tptax_other_chrg, tptax_tpservicechrg, tptax_ids, is_sc=False, context=None):  
        """ 
            Method  :: common for both Adult & Child
            Returns :: Subtotal and/or Amount value for the given (%)
        """

        res = {}
        tptax = tpamt4tax = 0.00
        dp = get_dp_precision(cr, uid, 'Account') 
        if calledby == 'all':
            if tac_perc:
                res['tac'] = round(((tac_perc * basic) / 100.00), dp) 
            
            if markup_perc:
                res['markup'] = round(((markup_perc * basic) / 100.00), dp)
                
        if tptax_basic == True   : tpamt4tax += basic
        if tptax_courier == True : tpamt4tax += courier
        if tptax_vfs == True     : tpamt4tax += vfs
        if tptax_tac == True     : tpamt4tax += tac
        if tptax_dd == True      : tpamt4tax += dd
        if tptax_other_chrg == True   : tpamt4tax += other_chrg
        if tptax_tpservicechrg == True   : tpamt4tax += tp_servicechrg
        

        for ttx in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'tptax_ids', tptax_ids, ["amount"]):
            tptax += round((tpamt4tax * ttx['amount']),dp)  
           
        amt = (basic + vfs + courier + dd + other_chrg + markup + tptax)
        
        if not is_sc and servicechrg_perc:
            servicechrg = round(((servicechrg_perc * amt) / 100.00), dp)
        
        res.update({'rate' : (amt + servicechrg + tp_servicechrg),
                    'servicechrg': servicechrg,
                    'tptax': tptax
               })

        result = {}
        pax_map = {'adult':'a_', 'child':'c_', 'infant':'i_'}
        for r in res.keys():
            result[pax_map[chkif]+r] = res[r]
            
        return {'value':result}
    
    
    def onchange_pVISA_onTPtax(self, cr, uid, ids, basic, vfs, courier, dd, other_chrg, markup_perc, markup, tac_perc, tac, servicechrg_perc, servicechrg, tp_servicechrg
                              , c_basic, c_vfs, c_courier, c_dd, c_other, c_markup_perc, c_markup, c_tac_perc, c_tac, c_servicechrg_perc, c_servicechrg, c_tp_servicechrg
                              , i_basic, i_vfs, i_courier, i_dd, i_other, i_markup_perc, i_markup, i_tac_perc, i_tac, i_servicechrg_perc, i_servicechrg, i_tp_servicechrg
                             , tptax_basic, tptax_courier, tptax_vfs, tptax_tac, tptax_dd, tptax_other_chrg, tptax_tpservicechrg, tptax_ids, context=None):
        
        res = {}
        res.update(self.onchange_pVISA_Total(cr, uid, ids, 'adult', 'all', basic, vfs, courier, dd, other_chrg, markup_perc, markup
                                            , tac_perc, tac, servicechrg_perc, servicechrg, tp_servicechrg
                                            , tptax_basic, tptax_courier, tptax_vfs, tptax_tac, tptax_dd, tptax_other_chrg, tptax_tpservicechrg, tptax_ids, False, context)['value'])
         
        res.update(self.onchange_pVISA_Total(cr, uid, ids, 'child', 'all', c_basic, c_vfs, c_courier, c_dd, c_other, c_markup_perc, c_markup
                                            , c_tac_perc, c_tac, c_servicechrg_perc, c_servicechrg, c_tp_servicechrg
                                            , tptax_basic, tptax_courier, tptax_vfs, tptax_tac, tptax_dd, tptax_other_chrg, tptax_tpservicechrg, tptax_ids, False, context)['value'])

        res.update(self.onchange_pVISA_Total(cr, uid, ids, 'infant', 'all', i_basic, i_vfs, i_courier, i_dd, i_other, i_markup_perc, i_markup
                                            , i_tac_perc, i_tac, i_servicechrg_perc, i_servicechrg, i_tp_servicechrg
                                            , tptax_basic, tptax_courier, tptax_vfs, tptax_tac, tptax_dd, tptax_other_chrg, tptax_tpservicechrg, tptax_ids, False, context)['value'])
                   
        return {'value':res}
    
#    Visa:    
#     def onchange_pVISA_onAmt(self, cr, uid, ids, chkif, basic, vfs, tac, courier, dd, other_chrg, servicechrg_perc, servicechrg, tp_servicechrg, tptax, markup):
#         """ 
#             Method  :: common for both Adult & Child
#             Used    :: in Product - Visa
#             Returns :: adds Amount to Subtotal
#         """
#         res = {}
# 
#         amt = (basic + vfs + courier + dd + other_chrg + markup + tptax)
# 
#         if servicechrg_perc:
#             servicechrg = round(((servicechrg_perc * amt) / 100.00), 2)
#             res['servicechrg'] = servicechrg
#                 
#         res['rate'] = (amt + servicechrg + tp_servicechrg)
#             
#         result = {}
#         if chkif == 'adult':
#            result = res.copy() 
#            
#         elif chkif == 'child':
#             for r in res.keys():
#                 result['c_'+r] = res[r]
#                 
#         return {'value': result}
     
#     Product: Activities
    def onchange_pACTIVITY_paxTotal(self, cr, uid, ids, chkwhich, calledby, basic
                                    , tac_perc, tac, markup_perc, markup, tds_perc, tds, servicechrg_perc, servicechrg                                    
                                    , tptax_basic, tptax_tac, tptax_tds, tptax_ids, is_sc=False, context=None):
        
        act_obj = self.pool.get('tr.invoice.activity')
        
        res = act_obj.onchange_paxtotal(cr, uid, ids, 'out_invoice', chkwhich, calledby, 1, basic, tac_perc, tac
                                             , markup_perc, markup, tds_perc, tds,  0, 0, 0
                                             , servicechrg_perc, servicechrg, 0, 0, 0
                                             , tptax_basic, tptax_tac, tptax_tds, tptax_ids, is_sc, context)['value']
       
        if chkwhich== 'adult':
            res['a_rate'] = res['a_subtotal']
        if chkwhich== 'child':
            res['c_rate'] = res['c_subtotal']
        if chkwhich== 'infant':
            res['i_rate'] = res['i_subtotal']
            
        return {'value':res}
    
    
      
    
    def onchange_pACTIVITY_onTPtax(self, cr, uid, ids
                                   , a_basic, a_tac, a_markup, a_tds, a_servicechrg_perc, a_servicechrg
                                   , c_basic, c_tac, c_markup, c_tds, c_servicechrg_perc, c_servicechrg                             
                                   , i_basic, i_tac, i_markup, i_tds, i_servicechrg_perc, i_servicechrg                                
                                   , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=None):  
        act_obj = self.pool.get('tr.invoice.activity')
        
        res = act_obj.onchange_ACT_total(cr, uid, ids, 'out_invoice', 1, a_basic, a_tac, a_markup, a_tds
                                               ,  0, 0, a_servicechrg_perc, a_servicechrg, 0, 0, 0                             
                                               , 1, c_basic, c_tac, c_markup, c_tds,  0
                                               , 0, c_servicechrg_perc, c_servicechrg, 0, 0, 0                             
                                               , 1, i_basic, i_tac, i_markup, i_tds,  0
                                               , 0, i_servicechrg_perc, i_servicechrg, 0, 0, 0
                                               , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context)['value']
                                               
        res['a_rate'] = res['a_subtotal']
        res['c_rate'] = res['c_subtotal']
        res['i_rate'] = res['i_subtotal']
        return {'value':res}
        
#     Product: ADD On
    
    def onchange_pADDON_paxTotal(self, cr, uid, ids, chkwhich, calledby, basic
                                    , tac_perc, tac, markup_perc, markup, tds_perc, tds, servicechrg_perc, servicechrg                                    
                                    , tptax_basic, tptax_tac, tptax_tds, tptax_ids, is_sc=False, context=None):
        
        addon_obj = self.pool.get('tr.invoice.addon')
        
        res = addon_obj.onchange_paxtotal(cr, uid, ids, 'out_invoice', chkwhich, calledby, 1, basic, tac_perc, tac
                                             , markup_perc, markup, tds_perc, tds,  0, 0, 0
                                             , servicechrg_perc, servicechrg, 0, 0, 0
                                             , tptax_basic, tptax_tac, tptax_tds, tptax_ids, is_sc, context)['value']
        if chkwhich== 'adult':
            res['a_rate'] = res['a_subtotal']
        if chkwhich== 'child':
            res['c_rate'] = res['c_subtotal']
        if chkwhich== 'infant':
            res['i_rate'] = res['i_subtotal']
            
        return {'value':res}
        
        
    def onchange_pADDON_onTPtax(self, cr, uid, ids
                                , a_basic, a_tac, a_markup, a_tds, a_servicechrg_perc, a_servicechrg                             
                                , c_basic, c_tac, c_markup, c_tds, c_servicechrg_perc, c_servicechrg                             
                                , i_basic, i_tac, i_markup, i_tds, i_servicechrg_perc, i_servicechrg                                
                                , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context=None):        
                
        addon_obj = self.pool.get('tr.invoice.addon')
        
        res = addon_obj.onchange_ADDON_total(cr, uid, ids, 'out_invoice', 1, a_basic, a_tac, a_markup, a_tds
                                               ,  0, 0, a_servicechrg_perc, a_servicechrg, 0, 0, 0
                                               , 1, c_basic, c_tac, c_markup, c_tds,  0
                                               , 0, c_servicechrg_perc, c_servicechrg, 0, 0, 0
                                               , 1, i_basic, i_tac, i_markup, i_tds,  0
                                               , 0, i_servicechrg_perc, i_servicechrg, 0, 0, 0
                                               , tptax_basic, tptax_tac, tptax_tds, tptax_ids, context)['value']
                                                         
        res['a_rate'] = res['a_subtotal']
        res['c_rate'] = res['c_subtotal']
        res['i_rate'] = res['i_subtotal']
        return {'value':res}
    
#     Product: Transfers(Car)
    def onchange_pCAR_Basic(self, cr, uid, ids, cost_type, no_days, usage_lmt, rate_km, ext_rate_km
                           , ext_rate_hour,  mrkup_km, ext_mrkup_km, ext_mrkup_hour, context=None):
        """ 
            Used: in Transfers
            Returns: Basic value
        """
        car_obj = self.pool.get('tr.invoice.car')
        res = car_obj.onchange_CAR_Basic(cr, uid, ids, cost_type, usage_lmt, 1, usage_lmt, rate_km, ext_rate_km
                           , 0, ext_rate_hour,  mrkup_km, ext_mrkup_km, ext_mrkup_hour, context)['value']
        res['a_basic'] = res['basic']
        return {'value': res}
    
#     Product: Transfers(Car)
    def onchange_pCAR_Total(self, cr, uid, ids, calledby, basic, tac_perc, tac, markup_perc, markup, tds_perc, tds
                            , other_chrg, driver_chrgs,  servicechrg_perc, servicechrg, tptax_basic, tptax_tac
                            , tptax_tds, tptax_other_chrg, tptax_ids, is_sc=False, context=None):
        """
            Used: in Transfers
            Returns: Total value
        """   
        car_obj = self.pool.get('tr.invoice.car')
        res = car_obj.onchange_CAR_total(cr, uid, ids, 'out_invoice', calledby, 1, basic, tac_perc, tac, markup_perc, markup
                                            , tds_perc, tds, other_chrg, driver_chrgs,  0, 0, 0, servicechrg_perc, servicechrg, 0
                                            , 0, 0, tptax_basic, tptax_tac, tptax_tds, tptax_other_chrg, tptax_ids, 'only_adult',

                                             False, context)['value']

        res['rate'] = res['subtotal']
        res['tptax'] = res['tptax']
        result = {}
        for r in res:
            result['a_'+r] = res[r]
        return {'value': result}
    
    def button_dummy(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {}, context)

    def _to_create_HotelTP(self, cr, uid, id, chkwhich, vals, context=None):
        """  To create Travel Partner for Hotel Products """
        tpid = False
        partner_obj = self.pool.get('res.partner')
        tpvals = {
               'name'     : vals.get('name',''),
               'supplier' : 1, 
               'customer' : 0,
               'hotel_id' : id, 
               'tpartner_type' : 'tp_hotel',  
               'street'  : vals.get('tp_street',''),
               'street2' : vals.get('tp_street2',''),
               'city'    : vals.get('tp_city',''),
               'zip'     : vals.get('tp_zip',''),
               'country_id': vals.get('tp_country_id',False),
               'state_id'  : vals.get('tp_state_id',False),
               'phone'     : vals.get('tp_phone',''),
               'email'     : vals.get('tp_email',''),
               }
        return {'tpartner_id' : tpid}
    
    def create(self, cr, uid, vals, context=None):
        print 'cruise vals', vals
        result = super(product_product, self).create(cr, uid, vals, context=context)
        
        # TODO: need to check thoroughly
        # To create Travel Partner for Hotel Products
        if (vals.get('travel_type','') in ('dom_hotel', 'int_hotel') and vals.get('create_tp',False)):
             newvals = self._to_create_HotelTP(cr, uid, result, vals, context)
             newvals['create_tp'] = False
     
        return result
            
    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        unlink_service_ids = []
        
        for product in self.browse(cr, uid, ids, context=context):
            servc_id = product.service_id.id
            
            # Check if the product is last product of this service
            other_product_ids = self.search(cr, uid, [('service_id', '=', servc_id), ('id', '!=', product.id)], context=context)
            
            if not other_product_ids:
                unlink_service_ids.append(servc_id)
            unlink_ids.append(product.id)
            
        res = super(product_product, self).unlink(cr, uid, unlink_ids, context=context)
        # delete templates after calling super, as deleting template could lead to deleting
        # products due to ondelete='cascade'
        self.pool.get('tr.product.services').unlink(cr, uid, unlink_service_ids, context=context)
        return res
    
product_product()


class tr_service_hotelpricing(osv.osv):
    _name = 'tr.service.hotelpricing' 
    _description = "Hotel Pricing"
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(tr_service_hotelpricing, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        traveltype = context.get('travel_type', '')
       #  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
       #  DOM / Int Hotel:  [to hide irrelevant fields]
#      #  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         if view_type == 'tree':
#             if traveltype == 'int_hotel':
#                 view = """<?xml version="1.0" encoding="utf-8"?>
#                              <tree string="Pricing Details">
#                             </tree>
#                        """
#             else:
#                 view = """<?xml version="1.0" encoding="utf-8"?>
#                              <tree string="Pricing Details">
#                             </tree>
#                        """
#                     
#             view = etree.fromstring(view.encode('utf8'))
#             xarch, xfields = self._view_look_dom_arch(cr, uid, view, view_id, context=context)
#             view = xarch
#             res.update({
#                 'arch': view
#             })
             
        if view_type == 'form':
            for f in res['fields']:
                if traveltype == 'int_hotel':
                    if f == 'ex_rate':
                        res['fields'][f]['invisible'] = True
                else:
                    if f in ('twin_rate', 'triple_rate', 'infant_rate'):
                        res['fields'][f]['invisible'] = True
        return res
    
    def _get_AllTotal(self, cr, uid, ids, field_name, arg, context):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'a_tptax':0.00, 'tn_tptax':0.00, 't3_tptax':0.00, 'c_tptax':0.00, 'cn_tptax':0.00, 'i_tptax':0.00, 'e_tptax':0.00,
                            'a_rate':0.00, 'tn_rate':0.00, 't3_rate':0.00, 'c_rate':0.00, 'cn_rate':0.00, 'i_rate':0.00, 'e_tptax':0.00,
                            'subtotal':0.00, 'meal_cost': 0.00
                            }
            
            def _calc_tptax(basic, other, tac, tds, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids):
                tpamt4tax = tptax = 0.00
                if tptax_basic == True : tpamt4tax += basic
                if tptax_other == True : tpamt4tax += other
                if tptax_tac == True : tpamt4tax += tac
                if tptax_tds == True : tpamt4tax += tds
                for ttx in tptax_ids:
                    tptax += round((tpamt4tax * ttx.amount), dp)
                return tptax
            
            res[case.id]['a_tptax']  = _calc_tptax(case.a_basic, case.a_other, case.a_tac, case.a_tds, case.tptax_basic, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['tn_tptax'] = _calc_tptax(case.tn_basic, case.tn_other, case.tn_tac, case.tn_tds, case.tptax_basic, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['t3_tptax'] = _calc_tptax(case.t3_basic, case.t3_other, case.t3_tac, case.t3_tds, case.tptax_basic, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['c_tptax']  = _calc_tptax(case.c_basic, case.c_other, case.c_tac, case.c_tds, case.tptax_basic, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['cn_tptax'] = _calc_tptax(case.cn_basic, case.cn_other, case.cn_tac, case.cn_tds, case.tptax_basic, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['i_tptax']  = _calc_tptax(case.i_basic, case.i_other, case.i_tac, case.i_tds, case.tptax_basic, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['e_tptax']  = _calc_tptax(case.e_basic, case.e_other, case.e_tac, case.e_tds, case.tptax_basic, case.tptax_other, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            
            res[case.id]['a_rate']  = case.a_basic  + case.a_markup  + case.a_other  + case.a_servicechrg  + res[case.id]['a_tptax']
            res[case.id]['tn_rate'] = case.tn_basic + case.tn_markup + case.tn_other + case.tn_servicechrg + res[case.id]['tn_tptax']
            res[case.id]['t3_rate'] = case.t3_basic + case.t3_markup + case.t3_other + case.t3_servicechrg + res[case.id]['t3_tptax']
            res[case.id]['c_rate']  = case.c_basic  + case.c_markup  + case.c_other  + case.c_servicechrg  + res[case.id]['c_tptax']
            res[case.id]['cn_rate'] = case.cn_basic + case.cn_markup + case.cn_other + case.cn_servicechrg + res[case.id]['cn_tptax']
            res[case.id]['i_rate']  = case.i_basic  + case.i_markup  + case.i_other  + case.i_servicechrg  + res[case.id]['i_tptax']
            res[case.id]['e_rate']  = case.e_basic  + case.e_markup  + case.e_other  + case.e_servicechrg  + res[case.id]['e_tptax']
            
            res[case.id]['meal_cost'] = (case.no_meal * (case.meal_rate + case.meal_tax))
            res[case.id]['subtotal'] = res[case.id]['a_rate'] + res[case.id]['tn_rate'] + res[case.id]['t3_rate'] + res[case.id]['c_rate'] \
                                        + res[case.id]['cn_rate'] + res[case.id]['i_rate'] + res[case.id]['e_rate'] \
                                        + res[case.id]['meal_cost']
        return res
     
    _columns = { 
        'service_id' : fields.many2one('tr.product.services', 'Service', ondelete='cascade'),
        'meal_id'    : fields.many2one('tr.meal.plan','Meal Plan', ondelete='restrict', required=True),
        'rmcateg_id' : fields.many2one('tr.room.categ', 'Room Category', ondelete='restrict', required=True),
        
        'valid_from' : fields.date('Valid From', required=True),
        'valid_to'   : fields.date('Valid To', required=True) ,
        'inclusions' : fields.text('Inclusions'),
        'remarks'    : fields.text('Remarks'),
        
        # Adult
        'adult_type'    : fields.selection([('room','Per Room'), ('person','Per Person')], string='Type'),
        'a_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'a_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
        'a_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
        'a_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'a_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'a_tds_perc'    : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
        'a_tds'         : fields.float('TDS', digits_compute=dp.get_precision('Account')),
        'a_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        'a_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'a_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
        'a_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        'a_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        
        # Twin Sharing
        'tn_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'tn_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
        'tn_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
        'tn_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'tn_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'tn_tds_perc'    : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
        'tn_tds'         : fields.float('TDS', digits_compute=dp.get_precision('Account')),
        'tn_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        'tn_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'tn_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
        'tn_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        'tn_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),

        # Triple Sharing
        't3_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        't3_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
        't3_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
        't3_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        't3_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        't3_tds_perc'    : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
        't3_tds'         : fields.float('TDS', digits_compute=dp.get_precision('Account')),
        't3_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        't3_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        't3_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
        't3_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        't3_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
#         
        # Child with Bed
        'c_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'c_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
        'c_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
        'c_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'c_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'c_tds_perc'    : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
        'c_tds'         : fields.float('TDS', digits_compute=dp.get_precision('Account')),
        'c_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        'c_servicechrg'       : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'c_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
        'c_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        'c_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        
         # Child without Bed
        'cn_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'cn_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
        'cn_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
        'cn_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'cn_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'cn_tds_perc'    : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
        'cn_tds'         : fields.float('TDS', digits_compute=dp.get_precision('Account')),
        'cn_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        'cn_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'cn_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
        'cn_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        'cn_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
         
         # Infant
        'i_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'i_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
        'i_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
        'i_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'i_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'i_tds_perc'    : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
        'i_tds'         : fields.float('TDS', digits_compute=dp.get_precision('Account')),
        'i_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        'i_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'i_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
        'i_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        'i_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        
         # Extra Person
        'e_basic'       : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'e_markup_perc' : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
        'e_markup'      : fields.float('Markup', digits_compute=dp.get_precision('Account')),
        'e_tac_perc'    : fields.float('TAC %', digits_compute=dp.get_precision('Account')),
        'e_tac'         : fields.float('TAC', digits_compute=dp.get_precision('Account')),
        'e_tds_perc'    : fields.float('TDS %', digits_compute=dp.get_precision('Account')),
        'e_tds'         : fields.float('TDS', digits_compute=dp.get_precision('Account')),
        'e_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
        'e_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
        'e_other'       : fields.float('Other', digits_compute=dp.get_precision('Account')),
        'e_tptax'       : fields.function(_get_AllTotal, string='T.P. Taxes', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        'e_rate'        : fields.function(_get_AllTotal, string='Rate', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        
        'early_chkin'   : fields.float('Early Check-In', digits_compute=dp.get_precision('Account')),
        'late_chkout'   : fields.float('Late Check-Out', digits_compute=dp.get_precision('Account')),
                
        'no_meal'    : fields.float('No of Meals', digits_compute=dp.get_precision('Account')),
        'meal_rate'  : fields.float('Meal Rate', digits_compute=dp.get_precision('Account')),
        'meal_tax'   : fields.float('Meal Tax', digits_compute=dp.get_precision('Account')),
        'meal_cost'  : fields.function(_get_AllTotal, string='Total Meal Cost', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
        'tptax_basic'  : fields.boolean('On Basic'),
        'tptax_other'  : fields.boolean('On Other'),
        'tptax_tac'    : fields.boolean('On TAC'),
        'tptax_tds'    : fields.boolean('On TDS'),
        'tptax_ids'    : fields.many2many('account.tax', 'photel_tptax_rel', 'hotel_id', 'tax_id', 'T.P. Taxes'),
        
        'subtotal'   : fields.function(_get_AllTotal, string='Subtotal', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
         
               }
    _defaults = {
                 'adult_type': 'person', 
                 }
    
    def _check_validdate(self, cr, uid, ids, context=None):
        cases = self.browse(cr, uid, ids, context=context)
        for c in cases:
            if c.valid_from > c.valid_to:
                return False
        return True

    _constraints = [
                (_check_validdate, 'Please Check the Valid Dates..!!', ['valid_from']),
            ]

    def onchange_validfrom(self, cr, uid, ids, valid_from):  
        res = {}
        if valid_from:
            res['valid_to'] = valid_from
        return {'value':res}

    def onchange_Hotel_total(self, cr, uid, ids, chkwhich, calledby, basic, other, tac_perc, tac, tds_perc, tds, markup_perc, markup
                           , servicechrg_perc, servicechrg, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, is_sc=False, context=None):
        
        HT_obj = self.pool.get('tr.invoice.hotel')
        return HT_obj.onchange_Hotel_total(cr, uid, ids, 'out_invoice', chkwhich, calledby, 1, basic, other, tac_perc, tac, tds_perc, tds, 0, 0, markup_perc, markup
                           , servicechrg_perc, servicechrg, 0, 0, 0, 0, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, is_sc, context)
        
    def onchange_Hotel_onTPtax(self, cr, uid, ids, chkpax, chkwhich, a_basic, a_other, a_tac, a_tds, a_markup, a_servicechrg_perc, a_servicechrg 
                             , tn_basic, tn_other, tn_tac, tn_tds, tn_markup, tn_servicechrg_perc, tn_servicechrg  
                             , t3_basic,  t3_other, t3_tac, t3_tds, t3_markup, t3_servicechrg_perc, t3_servicechrg
                             , c_basic, c_other, c_tac, c_tds, c_markup, c_servicechrg_perc, c_servicechrg
                             , cn_basic, cn_other, cn_tac, cn_tds, cn_markup, cn_servicechrg_perc, cn_servicechrg
                             , i_basic, i_other, i_tac, i_tds, i_markup, i_servicechrg_perc, i_servicechrg
                             , e_basic, e_other, e_tac, e_tds, e_markup, e_servicechrg_perc, e_servicechrg
                             , early_chkin, late_chkout, no_meal, meal_rate, meal_tax, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context=None):
        
        HT_obj = self.pool.get('tr.invoice.hotel')
        return HT_obj.onchange_Hotel_onTPtax(cr, uid, ids, 'out_invoice', chkpax, chkwhich, 1, a_basic, a_other, a_tac, a_tds, 0, a_markup, a_servicechrg_perc, a_servicechrg, 0, 0, 0, 0
                             , 1, tn_basic, tn_other, tn_tac, tn_tds, 0, tn_markup, tn_servicechrg_perc, tn_servicechrg, 0, 0, 0, 0
                             , 1, t3_basic,  t3_other, t3_tac, t3_tds, 0, t3_markup, t3_servicechrg_perc, t3_servicechrg, 0, 0, 0, 0
                             , 1, c_basic, c_other, c_tac, c_tds, 0, c_markup, c_servicechrg_perc, c_servicechrg, 0, 0, 0, 0
                             , 1, cn_basic, cn_other, cn_tac, cn_tds, 0, cn_markup, cn_servicechrg_perc, cn_servicechrg, 0, 0, 0, 0
                             , 1, i_basic, i_other, i_tac, i_tds, 0, i_markup, i_servicechrg_perc, i_servicechrg, 0, 0, 0, 0
                             , 1, e_basic, e_other, e_tac, e_tds, 0, e_markup, e_servicechrg_perc, e_servicechrg, 0, 0, 0, 0
                             , early_chkin, late_chkout, no_meal, meal_rate, meal_tax, tptax_basic, tptax_other, tptax_tac, tptax_tds, tptax_ids, context)
    
tr_service_hotelpricing()

class tr_service_cruisepricing(osv.osv):
    _name = 'tr.service.cruisepricing' 
    _description = "Cruise Pricing"
         
    def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        dp = get_dp_precision(cr, uid, 'Account')
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'a_tptax':0.00, 'e_tptax':0.00, 'c_tptax':0.00, 'i_tptax':0.00, 'a_rate':0.00, 'e_rate':0.00, 'c_rate':0.00, 'i_rate':0.00
                            }
            def _calc_tptax(basic, paxhandle, crshandle, holiday, fuel, promo, tac, tds 
                            , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday
                            , tptax_fuel, tptax_promo, tptax_tac, tptax_tds, tptax_ids):
                tpamt4tax = tptax = 0.00
                if tptax_basic == True : tpamt4tax += basic
                if tptax_paxhandle == True : tpamt4tax += paxhandle
                if tptax_crshandle == True : tpamt4tax += crshandle
                if tptax_holiday == True : tpamt4tax += holiday
                if tptax_fuel == True : tpamt4tax += fuel
                if tptax_promo == True : tpamt4tax += promo
                if tptax_tac == True : tpamt4tax += tac
                if tptax_tds == True : tpamt4tax += tds
                for ttx in tptax_ids:
                    tptax += round((tpamt4tax * ttx.amount), dp)
                return tptax
            
            res[case.id]['a_tptax'] =  _calc_tptax(case.a_basic, case.a_paxhandle, case.a_crshandle, case.a_holiday, case.a_fuel, case.a_promo, case.a_tac, case.a_tds, case.tptax_basic, case.tptax_paxhandle, case.tptax_crshandle, case.tptax_holiday, case.tptax_fuel, case.tptax_promo, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['e_tptax'] =  _calc_tptax(case.e_basic, case.e_paxhandle, case.e_crshandle, case.e_holiday, case.e_fuel, case.e_promo, case.e_tac, case.e_tds, case.tptax_basic, case.tptax_paxhandle, case.tptax_crshandle, case.tptax_holiday, case.tptax_fuel, case.tptax_promo, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['c_tptax'] =  _calc_tptax(case.c_basic, case.c_paxhandle, case.c_crshandle, case.c_holiday, case.c_fuel, case.c_promo, case.c_tac, case.c_tds, case.tptax_basic, case.tptax_paxhandle, case.tptax_crshandle, case.tptax_holiday, case.tptax_fuel, case.tptax_promo, case.tptax_tac, case.tptax_tds, case.tptax_ids)
            res[case.id]['i_tptax'] =  _calc_tptax(case.i_basic, case.i_paxhandle, case.i_crshandle, case.i_holiday, case.i_fuel, case.i_promo, case.i_tac, case.i_tds, case.tptax_basic, case.tptax_paxhandle, case.tptax_crshandle, case.tptax_holiday, case.tptax_fuel, case.tptax_promo, case.tptax_tac, case.tptax_tds, case.tptax_ids)
           
            res[case.id]['a_rate']  = case.a_basic  + case.a_paxhandle  - case.a_crshandle  + case.a_holiday + case.a_fuel - case.a_promo  + res[case.id]['a_tptax']
            res[case.id]['e_rate'] =  case.e_basic + case.e_paxhandle  - case.e_crshandle  + case.e_holiday + case.e_fuel - case.e_promo  + res[case.id]['e_tptax']
            res[case.id]['c_rate'] =  case.c_basic + case.c_paxhandle  - case.c_crshandle  + case.c_holiday + case.c_fuel - case.c_promo  + res[case.id]['c_tptax']
            res[case.id]['i_rate']  = case.i_basic  + case.i_paxhandle  - case.i_crshandle  + case.i_holiday + case.i_fuel - case.i_promo   + res[case.id]['i_tptax']
            
        return res
        
    _columns = {
                'service_id' : fields.many2one('tr.product.services', 'Service', ondelete='cascade'),
                
                'vessele_id'     : fields.many2one('tr.vessele', 'Vessele', required=True),  
                'cabincateg_id'  : fields.many2one('tr.cabin.category', 'Cabin Category', required=True),
                'no_nts'  : fields.integer('No. of Nights'), 
                'valid_from': fields.date('Valid From'),
                'valid_to'  : fields.date('Valid To'),
                'rate'    : fields.char('Rate', size=100),
      
#                 adult                
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
                'a_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'a_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'a_servicechrg_perc' : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'a_servicechrg'      : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'a_tptax': fields.function(_get_subtotal, string='Adult T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'a_rate' : fields.function(_get_subtotal, string='Adult Charges', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
        
                # Extra
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
                'e_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'e_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'e_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'e_servicechrg'       : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'e_tptax' : fields.function(_get_subtotal, string='Extra T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'e_rate'  : fields.function(_get_subtotal, string='Extra Person Charges', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                
                # Child
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
                'c_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'c_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'c_servicechrg_perc' : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'c_servicechrg'      : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'c_tptax': fields.function(_get_subtotal, string='Child T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'c_rate' : fields.function(_get_subtotal, string='Child charges', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                
                # Infant
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
                'i_markup_perc'  : fields.float('Markup %', digits_compute=dp.get_precision('Account')),
                'i_markup'       : fields.float('Markup', digits_compute=dp.get_precision('Account')),
                'i_servicechrg_perc'  : fields.float('Service Charge %', digits_compute=dp.get_precision('Account')),
                'i_servicechrg'    : fields.float('Service Charge', digits_compute=dp.get_precision('Account')),
                'i_tptax': fields.function(_get_subtotal, string='Infant T.P. Tax', type='float', digits_compute=dp.get_precision('Account'), store=True, multi='tot'),
                'i_rate' : fields.function(_get_subtotal, string='Infant Charges', type='float', digits_compute=dp.get_precision('Account'), store= True, multi='tot'),
                
                'tptax_basic'     : fields.boolean('On Cabin'),
                'tptax_paxhandle' : fields.boolean('On Passenger Handling Charges'),
                'tptax_crshandle' : fields.boolean('On Handling Charges'), 
                'tptax_holiday'   : fields.boolean('On Holiday Surcharges'),
                'tptax_fuel'    : fields.boolean('On Fuel Surcharges'),
                'tptax_promo'   : fields.boolean('On Promo Discount'),
                'tptax_tac'     : fields.boolean('On TAC'),
                'tptax_tds'     : fields.boolean('On TDS(T)'),
                'tptax_ids'     : fields.many2many('account.tax', 'pcruise_tptax_rel', 'cruise_id', 'tax_id', 'T.P. Taxes'),
                
                }
    
    def onchange_validFrom(self, cr, uid, ids, valid_from):
        res = {}
        if valid_from:
            res['valid_to'] = valid_from 
        return {'value': res}
    
    def onchange_CRS_Subtotal(self, cr, uid, ids, chkwhich, calledby, basic, paxhandle, crshandle, holiday
                           , fuel, promo, tac_perc, tac, tds_perc, tds, markup_perc, markup, servicechrg_perc, servicechrg
                           , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds
                           , tptax_ids, is_sc=False, context=None):
        """
            Returns: Subtotal
        """
        cruise_obj = self.pool.get('tr.invoice.cruise')
        
        res = cruise_obj.onchange_CRS_total(cr, uid, ids, 'out_invoice', chkwhich, calledby, 1, basic, paxhandle, crshandle, holiday
                                                , fuel, promo, tac_perc, tac, tds_perc, tds, 0, 0, markup_perc, markup, servicechrg_perc, servicechrg
                                                , 0, 0, 0, 0, tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo
                                                , tptax_tac, tptax_tds, tptax_ids, is_sc, context)['value']
        if chkwhich== 'adult':
            res['a_rate'] = res['a_subtotal']
        if chkwhich== 'extra':
            res['e_rate'] = res['e_subtotal']
        if chkwhich== 'child':
            res['c_rate'] = res['c_subtotal']
        if chkwhich== 'infant':
            res['i_rate'] = res['i_subtotal']
            
        return {'value': res}
    
    def onchange_CRS_onTPTAX(self, cr, uid, ids
                             , a_basic, a_paxhandle, a_crshandle, a_holiday, a_fuel, a_promo, a_tac, a_tds, a_markup, a_servicechrg_perc, a_servicechrg
                             , e_basic, e_paxhandle, e_crshandle, e_holiday, e_fuel, e_promo, e_tac, e_tds, e_markup, e_servicechrg_perc, e_servicechrg
                             , c_basic, c_paxhandle, c_crshandle, c_holiday, c_fuel, c_promo, c_tac, c_tds, c_markup, c_servicechrg_perc, c_servicechrg
                             , i_basic, i_paxhandle, i_crshandle, i_holiday, i_fuel, i_promo, i_tac, i_tds, i_markup, i_servicechrg_perc, i_servicechrg
                             , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds, tptax_ids, context=None):
        
       cruise_obj = self.pool.get('tr.invoice.cruise')
       
       res = cruise_obj.onchange_CRS_onTPtax(cr, uid, ids, 'out_invoice'
                             , 1, a_basic, a_paxhandle, a_crshandle, a_holiday, a_fuel, a_promo, 0, a_tac, 0, a_tds, 0, 0, 0, a_markup, a_servicechrg_perc, a_servicechrg, 0, 0, 0, 0
                             , 1, e_basic, e_paxhandle, e_crshandle, e_holiday, e_fuel, e_promo, 0, e_tac, 0, e_tds, 0, 0, 0, e_markup, e_servicechrg_perc, e_servicechrg, 0, 0, 0, 0
                             , 1, c_basic, c_paxhandle, c_crshandle, c_holiday, c_fuel, c_promo, 0, c_tac, 0, c_tds, 0, 0, 0, c_markup, c_servicechrg_perc, c_servicechrg, 0, 0, 0, 0
                             , 1, i_basic, i_paxhandle, i_crshandle, i_holiday, i_fuel, i_promo, 0, i_tac, 0, i_tds, 0, 0, 0, i_markup, i_servicechrg_perc, i_servicechrg, 0, 0, 0, 0
                             , tptax_basic, tptax_paxhandle, tptax_crshandle, tptax_holiday, tptax_fuel, tptax_promo, tptax_tac, tptax_tds, tptax_ids, context)['value'] 
        
       res['a_rate'] = res['a_subtotal']
       res['e_rate'] = res['e_subtotal']
       res['c_rate'] = res['c_subtotal']
       res['i_rate'] = res['i_subtotal']
       
       return {'value': res} 
    
class tr_prod_taxon(osv.osv):
    _name = 'tr.prod.taxon' 
    _description = "Product Tax on Component"
    _columns = {
                'company_id' : fields.many2one('res.company', 'Company'),
                'product_id' : fields.many2one('product.product', 'Product', ondelete='cascade'),
                
                'tax_basic'    : fields.boolean('On Basic'),
                'tax_irctc'    : fields.boolean('On IRCTC'),
                'tax_gateway'  : fields.boolean('On Gateway'),
                'tax_vfs'      : fields.boolean('On VFS'),
                'tax_dd'       : fields.boolean('On DD'),
                'tax_tax'      : fields.boolean('On Hotel Tax'),
                'tax_other'    : fields.boolean('On Other'),
                'tax_tac'      : fields.boolean('On TAC'),
                'tax_tds'      : fields.boolean('On TDS(T)'),
                'tax_tds1'     : fields.boolean('On TDS(D)'),
                'tax_mark'     : fields.boolean('On Mark Up'),
                'tax_courier'  : fields.boolean('On Courier'),
                'tax_raf'      : fields.boolean('On RAF'),
                'tax_tptax'    : fields.boolean('On T.P.Tax'),
                'tax_vendor'   : fields.boolean('On Vendor'),
                'tax_airlntax' : fields.boolean('On AirLine Tax'),
                'tax_reissue'  : fields.boolean('On Reissue Charges'),
                'tax_servicechrg' : fields.boolean('On Service Charge'),
                'tax_paxhandle'  : fields.boolean('On Passenger Handling Charges'),
                'tax_crshandle'  : fields.boolean('On Handling Charges'), 
                'tax_holiday'    : fields.boolean('On Holiday Surcharges'),
                'tax_fuel'  : fields.boolean('On Fuel Surcharges'),
                'tax_promo' : fields.boolean('On Promo Discount'), 
                }
    _defaults = {
#                  'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
                'company_id' : False
                 }
    
    _sql_constraints = [
                        ('uniq_cmpid','unique(product_id,company_id)','Company and Product are already exists!!!')
                        ]
    
    

# TODO: delete this object is not required
class tr_prod_flight_lines(osv.osv):
    _name = 'tr.prod.flight.lines' 
    _description = "Product Flight Lines"
     
    def _get_Alltotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'a_total':0, 'c_total':0, 'i_total':0, 'total':0}
        return res
     
    _columns = {
        'ftopt_id' : fields.many2one('tr.prod.opt.flight', 'Opt Flight', ondelete='cascade'),
                 
        'airline_id' : fields.many2one('tr.airlines', 'Airline', ondelete='restrict'),
        'source'     : fields.char('From', size=30),
        'dest'       : fields.char('To', size=30),
        'ft_class'   : fields.char('Class', size=20),
        'ft_num'     : fields.char('Flight No', size=10),
         
        'a_tac'        : fields.float('TAC', digits_compute=dp.get_precision('Account')), 
        'a_tac_perc'   : fields.float('TAC (A) %', digits_compute=dp.get_precision('Account')), 
        'a_tac_basic'  : fields.boolean('On Basic'),
        'a_tac_wopsf'  : fields.boolean('On WO/PSF'),
        'a_tac_yq'     : fields.boolean('On YQ'),
        'a_tac_in'     : fields.boolean('On IN'),
        'a_tac_other'  : fields.boolean('On Other'),
        'a_tac_tax'    : fields.boolean('On Tax'),   
        'a_tac_tptax'  : fields.boolean('On T.P. Tax'),   
 
        'a_tac_perc1'   : fields.float('TAC (B) %', digits_compute=dp.get_precision('Account')),
        'a_tac_basic1'  : fields.boolean('On Basic'),
        'a_tac_yq1'     : fields.boolean('On YQ'),
        'a_tac_other1'  : fields.boolean('On Other'),
        'a_tac_tax1'    : fields.boolean('On Tax'), 
        'a_tac_tptax1'  : fields.boolean('On T.P. Tax'),
 
        'a_tac_perc2'   : fields.float('TAC (C) %', digits_compute=dp.get_precision('Account')),
        'a_tac_basic2'  : fields.boolean('On Basic'),
        'a_tac_yq2'     : fields.boolean('On YQ'), 
        'a_tac_other2'  : fields.boolean('On Other'),
        'a_tac_tax2'    : fields.boolean('On Tax'), 
        'a_tac_tptax2'  : fields.boolean('On T.P. Tax'),
         
        'a_basic'   : fields.float('Basic', digits_compute=dp.get_precision('Account')), 
        'a_tds'     : fields.float('TDS', digits_compute=dp.get_precision('Account')), 
        'a_tds_perc': fields.float('TDS (%)', digits_compute=dp.get_precision('Account')),
        'a_wopsf'   : fields.float('WO/PSF', digits_compute=dp.get_precision('Account')), 
        'a_tax'     : fields.float('Taxes', digits_compute=dp.get_precision('Account')),
        'a_in'      : fields.float('IN', digits_compute=dp.get_precision('Account')), 
        'a_yq'      : fields.float('YQ', digits_compute=dp.get_precision('Account')), 
        'a_tptax'     : fields.float('T.P. Tax', digits_compute=dp.get_precision('Account')),
        'a_tptax_perc': fields.float('T.P. Tax (%)', digits_compute=dp.get_precision('Account')),
        'a_markup'    : fields.float('MarkUp', digits_compute=dp.get_precision('Account')),
        'a_servicechrg'  : fields.float('Service Charge', digits_compute=dp.get_precision('Account')), 
        'a_other'   : fields.float('Other Charges', digits_compute=dp.get_precision('Account')), 
         
        'c_tac'        : fields.float('TAC', digits_compute=dp.get_precision('Account')), 
        'c_tac_perc'   : fields.float('TAC (A) %', digits_compute=dp.get_precision('Account')), 
        'c_tac_basic'  : fields.boolean('On Basic'),
        'c_tac_wopsf'  : fields.boolean('On WO/PSF'),
        'c_tac_yq'     : fields.boolean('On YQ'),
        'c_tac_in'     : fields.boolean('On IN'),
        'c_tac_other'  : fields.boolean('On Other'),
        'c_tac_tax'    : fields.boolean('On Tax'),
        'c_tac_tptax'  : fields.boolean('On T.P. Tax'),
 
        'c_tac_perc1'   : fields.float('TAC (B) %', digits_compute=dp.get_precision('Account')),
        'c_tac_basic1'  : fields.boolean('On Basic'),
        'c_tac_yq1'     : fields.boolean('On YQ'),
        'c_tac_other1'  : fields.boolean('On Other'),
        'c_tac_tax1'    : fields.boolean('On Tax'), 
        'c_tac_tptax1'    : fields.boolean('On T.P. Tax'),      
 
        'c_tac_perc2'   : fields.float('TAC (C) %', digits_compute=dp.get_precision('Account')),
        'c_tac_basic2'  : fields.boolean('On Basic'),
        'c_tac_yq2'     : fields.boolean('On YQ'), 
        'c_tac_other2'  : fields.boolean('On Other'),
        'c_tac_tax2'    : fields.boolean('On Tax'), 
        'c_tac_tptax2'    : fields.boolean('On T.P. Tax'),
         
        'c_basic'   : fields.float('Basic', digits_compute=dp.get_precision('Account')),
        'c_tds'     : fields.float('TDS', digits_compute=dp.get_precision('Account')),
        'c_tds_perc': fields.float('TDS (%)', digits_compute=dp.get_precision('Account')),
        'c_wopsf'   : fields.float('WO/PSF', digits_compute=dp.get_precision('Account')),
        'c_tax'     : fields.float('Taxes', digits_compute=dp.get_precision('Account')),
        'c_in'      : fields.float('IN', digits_compute=dp.get_precision('Account')), 
        'c_yq'      : fields.float('YQ', digits_compute=dp.get_precision('Account')), 
        'c_tptax'     : fields.float('T.P. Tax', digits_compute=dp.get_precision('Account')),
        'c_tptax_perc': fields.float('T.P. Tax (%)', digits_compute=dp.get_precision('Account')),
        'c_markup'  : fields.float('MarkUp', digits_compute=dp.get_precision('Account')),
        'c_servicechrg'  : fields.float('Service Charge', digits_compute=dp.get_precision('Account')), 
        'c_other'   : fields.float('Other Charges', digits_compute=dp.get_precision('Account')), 
         
        'i_tac'        : fields.float('TAC', digits_compute=dp.get_precision('Account')), 
        'i_tac_perc'   : fields.float('TAC (A) %', digits_compute=dp.get_precision('Account')), 
        'i_tac_basic'  : fields.boolean('On Basic'),
        'i_tac_wopsf'  : fields.boolean('On WO/PSF'),
        'i_tac_yq'     : fields.boolean('On YQ'),
        'i_tac_in'     : fields.boolean('On IN'),
        'i_tac_other'  : fields.boolean('On Other'),
        'i_tac_tax'    : fields.boolean('On Tax'),   
        'i_tac_tptax'  : fields.boolean('On T.P. Tax'),   
 
        'i_tac_perc1'   : fields.float('TAC (B) %', digits_compute=dp.get_precision('Account')),
        'i_tac_basic1'  : fields.boolean('On Basic'),
        'i_tac_yq1'     : fields.boolean('On YQ'),
        'i_tac_other1'  : fields.boolean('On Other'),
        'i_tac_tax1'    : fields.boolean('On Tax'), 
        'i_tac_tptax1'  : fields.boolean('On T.P. Tax'),
 
        'i_tac_perc2'   : fields.float('TAC (C) %', digits_compute=dp.get_precision('Account')),
        'i_tac_basic2'  : fields.boolean('On Basic'),
        'i_tac_yq2'     : fields.boolean('On YQ'), 
        'i_tac_other2'  : fields.boolean('On Other'),
        'i_tac_tax2'    : fields.boolean('On Tax'), 
        'i_tac_tptax2'  : fields.boolean('On T.P. Tax'),
         
        'i_basic'   : fields.float('Basic', digits_compute=dp.get_precision('Account')), 
        'i_tds'     : fields.float('TDS', digits_compute=dp.get_precision('Account')), 
        'i_tds_perc': fields.float('TDS (%)', digits_compute=dp.get_precision('Account')),
        'i_wopsf'   : fields.float('WO/PSF', digits_compute=dp.get_precision('Account')), 
        'i_tax'     : fields.float('Taxes', digits_compute=dp.get_precision('Account')),  
        'i_in'      : fields.float('IN', digits_compute=dp.get_precision('Account')), 
        'i_yq'      : fields.float('YQ', digits_compute=dp.get_precision('Account')), 
        'i_tptax'     : fields.float('T.P. Tax', digits_compute=dp.get_precision('Account')),
        'i_tptax_perc': fields.float('T.P. Tax (%)', digits_compute=dp.get_precision('Account')),
        'i_markup'  : fields.float('MarkUp', digits_compute=dp.get_precision('Account')),
        'i_servicechrg'  : fields.float('Service Charge', digits_compute=dp.get_precision('Account')), 
        'i_other'   : fields.float('Other Charges', digits_compute=dp.get_precision('Account')),
         
        'a_tac_select' : fields.selection([('onlyA','Only A'), ('AplusB','A + B'), ('AB100','(A+B) on (100-A)')], 'Tac Calculation'),
        'c_tac_select' : fields.selection([('onlyA','Only A'), ('AplusB','A + B'), ('AB100','(A+B) on (100-A)')], 'Tac Calculation'),
        'i_tac_select' : fields.selection([('onlyA','Only A'), ('AplusB','A + B'), ('AB100','(A+B) on (100-A)')], 'Tac Calculation'),
         
        'a_total'  : fields.function(_get_Alltotal, method=True, type='float', digits=(16,2), string='Adult Total', multi='tot'),
        'c_total'  : fields.function(_get_Alltotal, method=True, type='float', digits=(16,2), string='Child Total', multi='tot'),
        'i_total'  : fields.function(_get_Alltotal, method=True, type='float', digits=(16,2), string='Infant Total', multi='tot'),
        'total'    : fields.function(_get_Alltotal, method=True, type='float', digits=(16,2), string='Total', multi='tot'), 
                }
     
    _defaults = {
         'a_tac_select' : 'onlyA',
         'c_tac_select' : 'onlyA',
         'i_tac_select' : 'onlyA',
          }
    
    
class tr_prod_itinerary(osv.osv):
    _name = 'tr.prod.itinerary' 
    _description = "Itinerary Details"
    _columns = {
                'name' : fields.text('Name'),
                'destination_id': fields.many2one('tr.destination','Destination', ondelete='restrict'),
                'image'  : fields.binary('Image'),
                'no_day' : fields.integer('Day'),
                'heading': fields.char('Heading',size=200),
                'overnight_id': fields.many2one('tr.destination','Over Night Stay', ondelete='restrict'),
                'meal_id': fields.many2one('tr.itinerary.meal','Meals', ondelete='restrict')
               } 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: