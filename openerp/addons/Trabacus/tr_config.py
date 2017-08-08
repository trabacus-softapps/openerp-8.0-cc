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
from lxml import etree

import openerp.addons.decimal_precision as dp
import time

TRAVEL_TYPES = [
        ('package', 'Holiday Package'),
        ('dom_flight', 'Domestic Flight'),
        ('int_flight', 'International Flight'),
        ('dom_hotel', 'Domestic Hotel'),
        ('int_hotel', 'International Hotel'),
        ('car','Transfers'),
        ('activity', 'Activities'),
        ('add_on', 'Add On'),
        ('visa','Visa'),
        ('insurance','Insurance'),
        ('railway','Railway'),
        ('cruise','Cruise'),
        ('direct','Miscellaneous'),
    ]

class tr_travel_type(osv.osv):
    _name = 'tr.travel.type' 
    _description = "Travel/Service Type"
    _columns = {
                'name' : fields.char('Name', size=100, required=True),
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'Travel Type already exists !'),
                       ]

class crm_case_stage(osv.osv):
    _inherit = 'crm.case.stage'
    _defaults = {'type': 'opportunity'
                 }
    
class tr_city(osv.osv):
    _name = 'tr.city' 
    _description = "City"
    _columns = {
                'name': fields.char('City', size=100, required=True),
                'state_id': fields.many2one("res.country.state", 'State', ondelete='restrict', required=True)
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'City already exists !'),
                       ]
    _order = "name"
        
class tr_room_categ(osv.osv):
    _name = 'tr.room.categ' 
    _description = "Room Category"
    _columns = {
                'name': fields.char('Room Category', size=100, required=True),
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Category already exists !'),
                       ]
    _order = "name"

class tr_visa_categ(osv.osv):
    _name = 'tr.visa.categ' 
    _description = "Visa Category"
    _columns = {
                'name': fields.char('Visa Category', size=100,required=True),
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Category already exists !'),
                       ]
    _order = "name"

class tr_meal_plan(osv.osv):
    _name = 'tr.meal.plan' 
    _description = "Meal Plan"
    _columns = {
            'name'    : fields.char('Meal Plan', size=30, required=True),
            'sequence': fields.integer('Sequence', help="Gives the sequence order"),
               }
    _defaults = {
                 'sequence': 1
                 }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Meal Plan already exists !'),
                       ]
    _order = "sequence,name"

class tr_vehicle(osv.osv):
    _name = 'tr.vehicle' 
    _description = "Vehicle"
    _columns = {
        'name':fields.char('Vehicle', size=100, required=True),
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Vehicle already exists !'),
                       ]
    _order = "name"

class tr_flight_psr(osv.osv):

    def _get_values(self, cr, uid, context=None):
        a = 1
        day = [(str((a+r)), str((a+r))) for r in range(31)]
        day.append(('32','End Of Month'))
        return day

    _name = 'tr.flight.psr' 
    _description = "Flight PSR Date Configuration"
    _columns = {
            'from'  : fields.selection(_get_values,'From'),
            'to'    : fields.selection(_get_values,'TO'),
               }

class tr_flight_class(osv.osv):
    _name = 'tr.flight.class' 
    _description = "Flight Class"
    _columns = {
                'name' : fields.char('Flight Class', size=64, required=True),
                'type' : fields.selection([('economy','Economy'), ('business','Business')], 'Type')
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Class already exists !'),
                       ]
    _order = "name"

class tr_flight_faretype(osv.osv):
    _name = 'tr.flight.faretype' 
    _description = "Flight Fare Type"
    _columns = {
                'code' : fields.char("Code", size=54, required=True),
                'name' : fields.char('Description', size=100, required=True),
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Fare Type already exists !'),
                       ]
    _order = "name"
    
class tr_flight_category(osv.osv):
    _name = 'tr.flight.category' 
    _description = "Flight Category"
    _columns = {
                'name' : fields.char('Flight Category', size=100, required=True),
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Category already exists !'),
                       ]
    _order = "name" 
    
class tr_airlines_taxcomp(osv.osv):
    _name = 'tr.airlines.taxcomp'
    _description = "Airline Tax Component"
    _columns = {
                  'name' : fields.char('Name', size=64, required=True),
                  }
    _order='name'
    _sql_constraints = [
        ('data_uniq', 'unique(name)', 'This Component already exists !')]
    
    
class tr_ticket_stock(osv.osv):
    _name = 'tr.ticket.stock'
    _description = 'Ticket Stock'
    _columns = {
                 'company_id' : fields.many2one('res.company',' Company'),
                 'partner_id' : fields.many2one('res.partner',' Travel Partner'),
                 'date' : fields.date('Date'),
                 'from_tckt_no' : fields.char('From Ticket No',size = 25),
                 'to_tckt_no' : fields.char('To Ticket No',size = 25)
                }
    _defaults = {
                  'date'   :  lambda *a: time.strftime('%Y-%m-%d'),
                  }
                  
    
class tr_airlines(osv.osv):
    _name = 'tr.airlines' 
    _description = "Airlines"
    _columns = {
                'code'      : fields.char("Code", size=54, required=True),
                'name'      : fields.char('Airlines', size=100, required=True),
                'number'    : fields.char('Airline Number',size=5),
                'lcc'       : fields.boolean('Low Cost Carrier'),
                'tax_lines' : fields.one2many('tr.airlines.taxes', 'airline_id', 'Taxes'),
               }
    _sql_constraints = [
                        ('code_uniq', 'unique(code)', 'Code for this Airline already exists !'),
                         ('number_uniq', 'unique(number)', 'Airline Number already exists !'),
                       ]
    _order = "name"
    
    # Child line
    def _cleanup_lines(self, cr, uid, lines, context=None):
        """
            Convert records to dict of values suitable for one2many line creation
            :param list(browse_record) lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
            
        """
        clean_lines = []
        for line in lines:
            clean_line = {}
            
            for field in line._all_columns.keys():
                if line._all_columns[field].column._type == 'many2one':
                    clean_line[field] = line[field].id
                
                    
                elif line._all_columns[field].column._type not in ['many2many','one2many']:
                    clean_line[field] = line[field]
                    
            clean_lines.append(clean_line)
        return map(lambda x: (0,0,x), clean_lines)
    

class tr_airlines_taxes(osv.osv):
    _name = 'tr.airlines.taxes'
    _description = "Airlines Taxes"
    
class tr_feedback_rating(osv.osv):
    _name = 'tr.feedback.rating' 
    _description = "Feedback Rating"
    _columns = {
        'name':fields.char('Feedback Rating', size=30, required=True),
               }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Rating already exists !'),
                       ] 


class tr_theme(osv.osv):
    _name = 'tr.theme' 
    _description = "Theme "
    _columns = {  
        'name' : fields.char('Theme', size=300, required=True),
        }  
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Theme already exists !'),
                       ]
    _order = "name"

class tr_itinerary_meal(osv.osv):
    _name = 'tr.itinerary.meal' 
    _description = "Itinerary Meal"
    _columns = {
        'code':fields.char('Code',size=30, required=True),
        'name':fields.char('Description', size=30,required=True),
        }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Itinerary Meal already exists !'),
                       ]
    _order = "name"
    
  
class tr_duration(osv.osv):
    _name = 'tr.duration' 
    _description = "Duration Details"
    _columns = {
        'name':fields.char('Description', size=30,required=True),
        'no_nights':fields.integer('No. of Nights  ')
        }
    
class tr_chklist_particulars(osv.osv):
    _name = "tr.chklist.particulars"
    _description = "Check List Questions"
    _columns ={
               'name' : fields.char('Description', size=500, required=True),
               'travel_type' : fields.selection(TRAVEL_TYPES,'Service Type', required=True),
               }
    _order = "travel_type"
    _sql_constraints = [
                        ('name_uniq', 'unique(travel_type, name)', 'This Particular for this type already exists !'),
                       ]
    
class tr_destination(osv.osv):
    _name = 'tr.destination' 
    _description = "Destination"
    _columns = {
        'code'  : fields.char('Code', size=12, required=True),
        'name'  : fields.char('Destination', size=30, required=True),
        'country_id': fields.many2one('res.country', 'Country', required=True, ondelete="restrict"),
        'state_id'  : fields.many2one('res.country.state', 'State', ondelete="restrict"),
        
               } 
    _order='country_id,code'
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'code must be unique !'),
        ('data_uniq', 'unique(name,country_id)', 'Destination for this Country already exists !')]

class tr_flyer_details(osv.osv):
    _name = 'tr.flyer.details' 
    _description = "Frequent Flyer"
    _columns = {
        'name'        : fields.char('Frequent Flyer Number', size=30, required=True),
        'partner_id'  : fields.many2one('res.partner','Partner', ondelete="cascade"),
        'airline_id'  : fields.many2one('tr.airlines','Airline', ondelete="restrict"),
               }
    
class tr_hotel_type(osv.osv):
    _name = 'tr.hotel.type' 
    _description = "Hotel Type"
    _columns = {
        'name'  : fields.char('Destination', size=30, required=True),
               } 
    _order='name'
    _sql_constraints = [
        ('data_uniq', 'unique(name)', 'This Hotel Type already exists !')]

class tr_visa_req_type(osv.osv):
    _name = "tr.visa.req.type"
    _description = "Visa - Requirement Type"
    _columns = {
                'name' : fields.char("Type", size=200, required=True),                
                }
    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'This Type already exists !'),
                       ]
    _order = "name"

class tr_visa_requirement(osv.osv):
    _name = 'tr.visa.requirement'
    _description = "Visa Requirement"
    _columns = {
                  'type_id' :fields.many2one('tr.visa.req.type','Type', ondelete='restrict'),
                  'name' : fields.text('Requirement'),
                  'service_id' : fields.many2one('tr.product.services','Service', ondelete='cascade')
                }
                
class tr_commission(osv.osv):
    _name = 'tr.commission' 
    _description = "Partner Commission"
    
    # to display supplier or customer in view(kanchan)
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):

        mod_obj = self.pool.get('ir.model.data')
        users_obj = self.pool.get('res.users')
        groups_obj = self.pool.get('res.groups')
        grp = ""

        res = super(tr_commission, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

        if view_type == 'form':
            if context is None: context = {}
            if context.get('supplier','') == True:
               doc = etree.XML(res['arch'])
               node = doc.xpath("//field[@name='partner_id']")[0]
               node.set('string', 'Supplier')
               res['arch'] = etree.tostring(doc)
            elif context.get('customer','')== True:
                doc = etree.XML(res['arch'])
                node = doc.xpath("//field[@name='partner_id']")[0]
                node.set('string', 'Customer')
                res['arch'] = etree.tostring(doc)                
        return res

    
    _columns = {
                'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade', required=True),
                'name'      : fields.char('Name', size=30),
                'supplier'  : fields.boolean('Supplier'),
                'customer'  : fields.boolean('Customer'),
                'ft_lines'  : fields.one2many('tr.commission.lines', 'commission_id', 'Flight'),                
               }
    _sql_constraints = [
        ('data_uniq', 'unique(partner_id)', 'Commission for this Partner already exists !')]
    
    def _check_default(self, cr, uid, ids, context=None):
        """
            Check: Unique default commission structure for Airline/Partner 
        """
        comlin_obj = self.pool.get('tr.commission.lines')
        
        for case in self.browse(cr, uid, ids, context):
            for com in case.ft_lines:
                if com.by_default == True:
                    comlin_ids = []
                    if case.supplier:                        
                        comlin_ids = comlin_obj.search(cr,uid,[('commission_id','=',case.id),('airline_id','=',com.airline_id.id),('by_default','=',True),('id','!=',com.id)])
                    if case.customer:
                        comlin_ids = comlin_obj.search(cr,uid,[('commission_id','=',case.id),('airline_id','=',com.airline_id.id),('tpartner_id','=',com.tpartner_id.id),('by_default','=',True),('id','!=',com.id)])
                    if comlin_ids:
                       return False 

        return True
    
    _constraints = [
                     (_check_default, 'Default Commission for this Airline Already Exists.', ['ft_lines']),
                    ]

    
    def write(self, cr, uid, ids, vals, context=None):
        
        # Updating: partner in lines 
        if 'partner_id' in vals:
            for case in self.browse(cr, uid, ids):
                cr.execute("update tr_commission_lines set partner_id = %d where commission_id = %d"%(vals['partner_id'], case.id))
               
        return super(tr_commission, self).write(cr, uid, ids, vals, context)
    
    
class tr_commission_lines(osv.osv):
    _name = 'tr.commission.lines' 
    _description = "Partner Commission lines"
    _columns = {
                'commission_id': fields.many2one('tr.commission', 'Commission', ondelete='cascade'),
                'airline_id'   : fields.many2one('tr.airlines', 'Airline', ondelete='cascade', required=True),
                'partner_id'   : fields.related('commission_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', store=True),
                'tpartner_id'  : fields.many2one('res.partner', 'Supplier', ondelete='cascade', domain=[('supplier', '=', True)]),
                
                'by_default'   : fields.boolean('Use by default'),
                'start_date'   : fields.date('Start Date'),
                'end_date'     : fields.date('End Date'),
                'tac_basic'    : fields.boolean('Basic (A)'),
                'tac_basic1'   : fields.boolean('Basic (B)'),
                'tac_basic2'   : fields.boolean('Basic (C)'),
                
                'tac_other'    : fields.boolean('Other (A)'),
                'tac_other1'   : fields.boolean('Other (B)'),
                'tac_other2'   : fields.boolean('Other (C)'),
                
                'tac_select' : fields.selection([('onlyA','Only A'), ('AplusB','A + B'), ('AB100','(A+B) on (100-A)'), ('ABC', 'A, B, C')], 'Tac Calculation'),
                'tac_perc'   : fields.float('TAC (A) %', digits_compute=dp.get_precision('Account')),
                'tac_perc1'  : fields.float('TAC (B) %', digits_compute=dp.get_precision('Account')),
                'tac_perc2'  : fields.float('TAC (C) %', digits_compute=dp.get_precision('Account')),
                'tax_lines'  : fields.one2many('tr.commissionln.taxes', 'commissionln_id', 'Taxes'),
                
                'tptax_ids'  : fields.many2many('account.tax',
                                                      'commission_supplier_taxes_rel', 'commissionln_id', 'tax_id',
                                                      'Supplier Taxes', domain=[('parent_id', '=', False),('type_tax_use','in',['purchase','all'])]),
                'tptax_basic'  : fields.boolean('On Basic'),
                'tptax_other'  : fields.boolean('On Other'),
                'tptax_airtax' : fields.boolean('On AirLine Tax'),
                'tptax_tac'    : fields.boolean('On TAC'),
                'tptax_tds'    : fields.boolean('On TDS'),
                
                'markup_perc' : fields.float('MarkUp (%)', digits_compute=dp.get_precision('Account')),
                'markup'      : fields.float('MarkUp', digits_compute=dp.get_precision('Account')),
                'servicechrg_perc' : fields.float('Service Charge(%)', digits_compute=dp.get_precision('Account')),
                'servicechrg' : fields.float('Service Charge', digits_compute=dp.get_precision('Account')), 
                
                'ftclass_ids' : fields.many2many('tr.flight.class', 'commissionln_ftclass_rel', 'commln_id', 'ftclass_id', 'Flight Class'),
                'ftfare_ids'  : fields.many2many('tr.flight.faretype', 'commissionln_faretype_rel', 'commln_id', 'faretype_id', 'FareType'),
                'ftfrom_ids'  : fields.many2many('tr.airport', 'commissionln_ftfrom_rel', 'commln_id', 'from_id', 'From'),
                'ftto_ids'    : fields.many2many('tr.airport', 'commissionln_ftto_rel', 'commln_id', 'to_id', 'To'),
                
             'cancel_markup' : fields.float('Cancellation Markup'), 
            'cancel_charges' : fields.float('Cancellation Charges'), 
            'cancel_service' : fields.float('Cancellation Service Charges'), 

               }
    
    def onchange_airline(self, cr, uid, ids, airline_id, tpartner_id, start_date, end_date, context={}):
        """
            Onchange is common for both Supplier Commission & Customer Discount
        """
        res = {}
        airln_obj = self.pool.get('tr.airlines')
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # only Airline: [Gets Taxes from Airline Master]
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if airline_id:
            airline = airln_obj.browse(cr, uid, airline_id)
            res['tax_lines'] = airln_obj._cleanup_lines(cr, uid, airline.tax_lines)
            
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # In Customer: for given supplier, if commission is available
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if airline_id and context.get('customer', False):
            if tpartner_id and start_date and end_date:
                suppln_ids = self.search(cr, uid, [('airline_id','=',airline_id), ('partner_id','=', tpartner_id), ('start_date', '<=',start_date), ('end_date','>=',end_date)], limit=1)
                supplnid = suppln_ids and suppln_ids[0] or False
                if not supplnid:
                    return {'value': res}
                
                res = self.copy_data(cr, uid, supplnid, None, context)
                del res['commission_id']
                del res['start_date']
                del res['end_date']
                del res['tpartner_id']
                
        return {'value': res}
 
class tr_commissionln_taxes(osv.osv):
    _name = 'tr.commissionln.taxes'
    _description = "Commission lines Taxes"
    _columns = {
                'commissionln_id' : fields.many2one('tr.commission.lines', 'Lines', ondelete='cascade'),
                'component_id'    : fields.many2one('tr.airlines.taxcomp', 'Tax Name', ondelete='restrict', required=True),
                'tac_a'  : fields.boolean('TAC on A'),
                'tac_b'  : fields.boolean('TAC on B'),
                'tac_c'  : fields.boolean('TAC on C'),
                'disc_a'  : fields.boolean('Discount on A'),
                'disc_b'  : fields.boolean('Discount on B'),
                'disc_c'  : fields.boolean('Discount on C'),
               }
    
class tr_supplier_systems_inherited(osv.osv):
    _inherit = "tr.supplier.systems"
    _columns = {
                'code' : fields.char("Code", size=54, required=True),
                'name' : fields.char("Name", size=200, required=True),
                'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade', required=True, domain=[('supplier', '=', True)]),
                'traveltype_ids': fields.many2many('tr.travel.type', 'supplier_traveltype_rel', 'supplier_id', 'traveltyp_id','Travel Type'),
                }
    _sql_constraints = [
                        ('code_uniq', 'unique(code)', 'Code should be unique !'),
                       ]
        
    
class tr_airport(osv.osv):
    _name = "tr.airport"
    _columns = {
                'code' : fields.char("Code", size=54, required=True),
                'name' : fields.char("Name", size=200, required=True),
                'type' : fields.selection([('domestic','Domestic'), ('international', 'International')], 'Type', required=True),
                'destination_id': fields.many2one('tr.destination', 'Destination', ondelete='cascade'),
                
                }
    _sql_constraints = [
                        ('code_uniq', 'unique(code)', 'Code should be unique !'),
                       ]
    
    def name_get(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        res = []
        if not ids: return res

        for record in self.read(cr, uid, ids, ['code', 'name'], context):
            name = record['name'] + ' ['+ record['code'] + ']'
            res.append((record['id'], name))
        return res
            
class tr_lost_remarks(osv.osv):
    _name = 'tr.lost.remarks' 
    _description = "Lead Lost Remarks"
    _columns = {
                'name' : fields.char('Name', size=100, required=True),
               }
 
class tr_services_account(osv.osv):
    _name = 'tr.services.account' 
    _description = "Service Accounts"
    _columns = {
                'name' : fields.selection(TRAVEL_TYPES,'Service Type', required=True),
                'company_id'  : fields.many2one('res.company', 'Company', required=True),
                
                'discount_id'  : fields.many2one('account.account', 'Discount'),
                'tac_id'       : fields.many2one('account.account', 'TAC'),
                'tds_payable_id'      : fields.many2one('account.account', 'TDS Payable'),
                'tds_receivable_id'   : fields.many2one('account.account', 'TDS Receivable'),
                
                'markup_id'       : fields.many2one('account.account', 'Markup'),
                'servicechrg_id'  : fields.many2one('account.account', 'Service Charge'),
                'cancel_service_id': fields.many2one('account.account', 'Cancel Service'),
                'cancel_markup_id' : fields.many2one('account.account', 'Cancel Markup'),
               }
    _defaults = {
                 'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
                 }
    _sql_constraints = [
                        ('name_uniq', 'unique(name,company_id)', 'Accounts for this Service and Company already exists !'),
                       ]
  
class tr_voucher_terms(osv.osv):
    _name = 'tr.voucher.terms' 
    _description = "Voucher Terms & Condition"
    _columns = {
                    'name'  : fields.selection(TRAVEL_TYPES,'Service Type', required=True),
                    'company_id'  : fields.many2one('res.company', 'Company', required=True),
                    'desc' : fields.text('Terms and Condition')
                    
                }
                    

class task(osv.osv):
    _inherit = "project.task"
    _columns = {
            'kanban_state': fields.selection([('normal', 'Normal'),('blocked', 'Blocked'),('done', 'Ready for next stage')], 'Kanban State',
                                         help="A task's kanban state indicates special situations affecting it:\n"
                                              " * Normal is the default situation\n"
                                              " * Blocked indicates something is preventing the progress of this task\n"
                                              " * Ready for next stage indicates the task is ready to be pulled to the next stage",
                                         readonly=True, required=False),
                }
task()

class tr_vessele(osv.osv):
    _name = "tr.vessele"
    _columns = {
                'name': fields.char('Name', size=100, required=True),
                }
    
class tr_cabin_category(osv.osv):
    _name = "tr.cabin.category"
    _columns = {
                'name': fields.char('Name', size=100, required=True),
                }

  
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: