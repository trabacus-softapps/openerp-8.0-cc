from openerp.osv import fields, osv
from openerp import netsvc
import logging
from openerp import SUPERUSER_ID
from openerp import tools
import base64
import re
from openerp.addons.base.ir.ir_mail_server import MailDeliveryException
from openerp.tools.translate import _
from datetime import datetime
from openerp.http import request
import openerp

_logger = logging.getLogger(__name__)


class cc_time(osv.osv):
    _name='cc.time'
    _columns={'name':fields.char('Time',size=10), 
              }
cc_time() 

class cc_city(osv.osv):
    _name='cc.city'
    _columns={'name':fields.char('City',size=125),
              'code':fields.char('Code',size=10),
              'state_id':fields.many2one('res.country.state','State'),
              'sequence':fields.integer('Sequence'),
              }
    _defaults = {'sequence' : 9999}
cc_city()

class cc_location(osv.osv):
    _name='cc.location'
    _columns={'name':fields.char('Loacation',size=125),
              'code':fields.char('Pincode',size=10),
              'city_id':fields.many2one('cc.city','city'),
              }
cc_location()

class cc_cuisine(osv.osv):
    _name='cc.cuisine'
    _columns={'name':fields.char('Cuisine',size=125)
              }
cc_cuisine()

class cc_dining_style(osv.osv):
    _name='cc.dining.style'
    _columns={'name':fields.char('Dining Style',size=125)
              }
cc_dining_style()

#  Table For Web
class cc_menus_table(osv.osv):
    _name='cc.menus.table'
    _columns = {
                  'food_type'   : fields.char('Type',size=20),
                  'name'        : fields.char('Name',size=75),
                  'description' : fields.text('Description',digits=(16, 2)),
                  'ffp_mu'      : fields.float('FFP Markup',digits=(16, 2)),
                  'to_mu'       : fields.float('TO Markup',digits=(16, 2)),
                  'ffp_co'      : fields.float('FFP Commission',digits=(16, 2)), 
                  'price'       : fields.float('Menu Total with To Markup',digits=(16, 2)),
                  'pp_person'   : fields.float('Price Per Person',digits=(16, 2)), 
                  'guest'       : fields.integer('Guest'),
                  'venue_id'    : fields.many2one('res.partner','Restaurant'),
                  'operator_id' : fields.many2one('res.partner','Operator'),
                  'menu_id'     : fields.many2one('cc.menus','Menus'),
                  'service_charge':fields.float('Service Charge',digits=(16, 2)),
                  'vat'         : fields.float('Vat',digits=(16, 2)),
                  'total_price' : fields.float('Total Price',digits=(16, 2)),
                  'booking_date':fields.date('Booking Date'),
                  'price_type'  :fields.selection([('bf_non_premium','B/F Non Premium'),
                                                   ('bf_standard','B/F Standard'),
                                                   ('bf_premium','B/F Premium'),
                                                   ('l_non_premium','Lunch Non Premium'),
                                                   ('l_standard','Lunch Standard'),
                                                   ('l_premium','Lunch Premium'),
                                                   ('at_non_premium','AT Non Premium'),
                                                   ('at_standard','AT Standard'),
                                                   ('at_premium','AT Premium'),
                                                   ('d_non_premium','Dinner Non Premium'),
                                                   ('d_standard','Dinner Standard'),
                                                   ('d_premium','Dinner Premium')],
                                                   'Type'), 
                'website_session_id': fields.char('Session UUID4'),      
               } 
    
    _defaults = {
                  'guest'   : 0.00,
               }
cc_menus_table()
    
class cc_menus(osv.osv):
    _name='cc.menus'
    
#     def _get_total(self, cr, uid, ids, field_name, arg, context): 
#         res={}
#         if context is None: context={}
#         
#         for case in self.browse(cr,uid,ids):
#             if case.food_type == 'meal' and context.get('cc_group'):
#                sc = 0
#                if not case.partner_id.sc_included and case.cc_group:
#                   sc_perc = case.partner_id.menu_sc > 0 and case.partner_id.menu_sc or case.partner_id.cc_company_id and case.partner_id.cc_company_id.menu_sc or 0
#                   sc = (case.rest_price + case.markup) * (sc_perc/100)
#                res[case.id] = case.rest_price + case.markup + sc  
#             else:
#                res[case.id] = self.get_tourop_price(cr, uid, ids, case.food_type, case.rest_price, case.markup, case.service_charge, case.sc_included, case.sc_disc, context)['value']['to_price'] 
#         return res

    
    
    def _get_total(self, cr, uid, ids, field_name, arg, context):
         
        res={}
        if context is None: context={}        
        for case in self.browse(cr,uid,ids): 
            sc_perc = case.service_charge
            sc_included = case.sc_included
            sc_disc = case.sc_disc
            if case.food_type == 'meal' and case.cc_group:
               sc = 0
               sc_included = case.partner_id.sc_included or case.partner_id.parent_id and case.partner_id.parent_id.sc_included or False
               if not sc_included and case.cc_group:
                  sc_perc = case.partner_id.menu_sc > 0 and case.partner_id.menu_sc or case.partner_id.parent_id and not case.partner_id.parent_id.sc_included and case.partner_id.parent_id.menu_sc or 0
                  sc_disc = True
                   
            res[case.id] = self.get_tourop_price(cr, uid, ids, case.food_type, case.rest_price, case.markup, sc_perc, sc_included, sc_disc, context)['value']['to_price'] 
        return res

    def _get_total1(self, cr, uid, ids, field_name, arg, context): 
        res1={}
        for case in self.browse(cr,uid,ids):            
            sc = 0
            if not case.partner_id.sc_included and case.cc_group:
               sc_perc = case.partner_id.menu_sc > 0 and case.partner_id.menu_sc or case.partner_id.cc_company_id and case.partner_id.cc_company_id.menu_sc or 0
               sc = (case.rest_price + case.markup) * (sc_perc/100)
            res1[case.id] = case.rest_price1 + case.markup1 + sc  

            
        return res1
        
    _columns={'cc_fit'      : fields.boolean('Fit'),
              'cc_group'    : fields.boolean('Group'),
              'food_type'   : fields.selection([('meal','Meal'),('drink','Drink'),('events','Events')],'Type'),
              'include_srvchrg'   : fields.selection([('yes','Yes'),('no','No')],'Service Charge Included'),
              'active'      : fields.boolean('Active'),    
              'partner_id'  : fields.many2one('res.partner','Partner'),
              'name'        : fields.char('Name',size=75),
              'description' : fields.text('Description'),
              'rest_price'  : fields.float('Restaurant Price',digits=(16, 2)), 
              'markup'      : fields.float('Markup',digits=(16, 2)),
              'commission'  : fields.float('Commission',digits=(16, 2)),
              'service_charge' : fields.float('Service Charge',digits=(16, 2)),
              'sc_included' : fields.boolean('Service Charge(Included)'), 
#Added By Shubhra
              'min_covers' : fields.integer('Min. Covers'),
              'sc_disc'      : fields.boolean('Service Charge Discretionary'), 
              'to_price'    : fields.function(_get_total, type='float', store=True, string='Tour Operator Price'),
              'heading'     : fields.char('Heading',size=50),
# fields to add in option-2 tab in menu 
              'description1' : fields.text('Description'),
              'rest_price1'  : fields.float('Restaurant Price',digits=(16, 2)), 
              'markup1'      : fields.float('Markup',digits=(16, 2)),
              'commission1'  : fields.float('Commission',digits=(16, 2)),
              'service_charge1' : fields.float('Service Charge',digits=(16, 2)),
              'sc_included1' : fields.boolean('Service Charge(Included)'), 
              'to_price1'    : fields.function(_get_total1, type='float', store=True, string='Tour Operator Price'),
              'heading1'     : fields.char('Heading',size=50),
              'image': fields.binary("Image",
                                     help="This field holds the image used as avatar for this contact, limited to 1024x1024px"),
              'break_fast'   : fields.boolean('Break-Fast'),
              'lunch'        : fields.boolean('Lunch'),
              'afternoon_tea': fields.boolean('AT'),
              'dinner'       : fields.boolean('Dinner'),
              'kids_menu'    : fields.boolean('Kids Menu'),
              'meal_type':fields.selection([('bf_non_premium','B/F Non Premium'),
                                            ('bf_standard','B/F Standard'),
                                            ('bf_premium','B/F Premium'),
                                            ('l_non_premium','Lunch Non Premium'),
                                            ('l_standard','Lunch Standard'),
                                            ('l_premium','Lunch Premium'),
                                            ('at_non_premium','AT Non Premium'),
                                            ('at_standard','AT Standard'),
                                            ('at_premium','AT Premium'),
                                            ('d_non_premium','Dinner Non Premium'),
                                            ('d_standard','Dinner Standard'),
                                            ('d_premium','Dinner Premium')],
                                            'Type'),
              'course'       : fields.selection([('c1','1'),('c2','2'),('c3','3'),('c4','4'),('c5','5'),('c6','6')],'Course'),
              'pricing_ids'  : fields.one2many('cc.menu.pricing','menu_id','Menu Pricing'),  
              'field_type'   : fields.selection([('markup','Markup'),('commission','commission')],'Select Field'),
              'drink_size'   : fields.char('Size',size=20),
              'remove_htls_to'  : fields.many2many('res.partner','menu_top_hide_rel','menu_id','top_id','Hide this menu from'),
              'show_htls_to'    : fields.many2many('res.partner','menu_top_show_rel','menu_id','top_id','Show this menu only to'),
              'start_date'      : fields.date('Start Date'),
              'end_date'      : fields.date('End Date'),
              'is_sun'   : fields.boolean('Sun'),
              'is_mon'   : fields.boolean('Mon'),
              'is_tue'   : fields.boolean('Tue'),
              'is_wed'   : fields.boolean('Wed'),
              'is_thu'   : fields.boolean('Thu'),
              'is_fri'   : fields.boolean('Fri'),
              'is_sat'   : fields.boolean('Sat'),

              }
    _defaults={'sc_included': True,
              'sc_included1': True,
              'active'      : True,
              'kids_menu'   : False,
              'is_sun'   : True,
              'is_mon'   : True,
              'is_tue'   : True,
              'is_wed'   : True,
              'is_thu'   : True,
              'is_fri'   : True,
              'is_sat'   : True,
              #Added By Shubhra
              'sc_disc'     : False,
              'min_covers': 1,
              } 
    
    def get_tourop_price(self, cr, uid, ids, food_type,rest_price, markup, service_charge, sc_included, sc_disc, context=None):
        
        res={}
        if context is None: context = {}            
        pricing_obj = self.pool.get('cc.menu.pricing')        
        
        if food_type in ('drink','events','meal'):
           if food_type == 'meal' and context.get('partner_id'):
              partner = self.pool.get('res.partner').browse(cr, uid, context.get('partner_id'))
              if not partner.sc_included:
                  service_charge = partner.menu_sc > 0 and partner.menu_sc or partner.parent_id and not partner.parent_id.sc_included and partner.parent_id.menu_sc or 0
                  sc_included = partner.sc_included or partner.parent_id and partner.parent_id.sc_included or False
                    
           context.update({'food_type':food_type})
           res = pricing_obj.onchange_pricing(cr, uid, ids, 'mon', rest_price, markup, service_charge, sc_included, sc_disc,context)['value']
           return {'value':{'to_price':res['mon_total'],'markup':res['mon_ffp_mu']}} 
        else:     
            res['to_price'] = rest_price + markup + service_charge
            
        return{'value':res}
        
    def price_changes(self,cr,uid,ids,context=None):
        
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', 'Inform Changes in Price')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        ctx.update({
            'default_model': 'cc.menus',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment'
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        } 
        
    def markup_apply_to_all(self, cr, uid, ids, context=None):
        pricing_obj = self.pool.get('cc.menu.pricing')
        
        for case in self.browse(cr, uid, ids):
            values={}
            pricing_ids = pricing_obj.search(cr, uid, [('meal_type','=',case.meal_type),('menu_id','=',case.id)])
            if case.field_type == 'markup':
               values={'mon_ffp_mu':case.markup1,
                       'tue_ffp_mu':case.markup1,
                       'wed_ffp_mu':case.markup1,
                       'thu_ffp_mu':case.markup1,
                       'fri_ffp_mu':case.markup1,
                       'sat_ffp_mu':case.markup1,
                       'sun_ffp_mu':case.markup1}
            else:
               values={'mon_to_mu':case.commission1,
                       'tue_to_mu':case.commission1,
                       'wed_to_mu':case.commission1,
                       'thu_to_mu':case.commission1,
                       'fri_to_mu':case.commission1,
                       'sat_to_mu':case.commission1,
                       'sun_to_mu':case.commission1} 
            pricing_obj.write(cr, uid, pricing_ids,values,context=None)
            
        return self.write(cr, uid, ids, {'markup':0.00,'meal_type':'','commission':0.00}, context)
    
    def update_pricing(self, cr, uid, ids, context=None):
        if context is None:
           context = {}        
        context.update({'mu_update':True}) 
        pricing_obj = self.pool.get('cc.menu.pricing')           
        for case in self.browse(cr,uid,ids):
            for pr in case.pricing_ids:
                vals={}
                sc_inc = case.sc_included
                sc = case.service_charge or 0.00
                sc_disc = case.sc_disc
                for day in ['mon','tue','wed','thu','fri','sat','sun']:
                    vals.update(pricing_obj.onchange_pricing(cr, uid, ids, day, pr[day+'_price'], pr[day+'_ffp_mu'], sc, sc_inc, sc_disc, context)['value'])
                pricing_obj.write(cr,uid,[pr.id],vals,{})
#                 vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'tue', pr.tue_price, pr.tue_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
#                 vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'wed', pr.wed_price, pr.wed_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
#                 vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'thu', pr.thu_price, pr.thu_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
#                 vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'fri', pr.fri_price, pr.fri_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
#                 vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'sat', pr.sat_price, pr.sat_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
#                 vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'sun', pr.sun_price, pr.sun_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
                
        return True
                
   
    def create(self, cr, uid, vals, context=None):
        res = super(cc_menus,self).create(cr,uid,vals,context)
        pricing_obj = self.pool.get('cc.menu.pricing')
        #Creating pricing lines
        if res:
           if vals['food_type'] == 'meal':
              for type in ['bf_non_premium','bf_standard','bf_premium','l_non_premium','l_standard','l_premium','at_non_premium','at_standard','at_premium','d_non_premium','d_standard','d_premium']:
                  active = False
                  if type in ('bf_non_premium','bf_standard','bf_premium'):
                     active=vals['break_fast']
                  elif type in ('l_non_premium','l_standard','l_premium'):
                     active=vals['lunch']
                  elif type in ('at_non_premium','at_standard','at_premium'):
                     active='afternoon_tea' in vals and vals['afternoon_tea'] or False  
                  elif type in ('d_non_premium','d_standard','d_premium'):
                     active=vals['dinner']   
                  pricing_obj.create(cr,uid,{'meal_type':type,'menu_id':res,'active':active})
        return res
    
    def write(self, cr ,uid, ids, vals,context = None):
        res= super(cc_menus,self).write(cr ,uid, ids, vals,context)     
        pricing_obj = self.pool.get('cc.menu.pricing')
        for case in self.browse(cr,uid,ids):
            #To update pricing records to active
            if case.food_type == 'meal':
                cr.execute("""update cc_menu_pricing set active = true where id in (
                              select a.id
                              from 
                                (
                                  select mp.id
                                        ,(case when """ + str(case.break_fast) + """ = 'True' and mp.meal_type in ('bf_non_premium','bf_standard','bf_premium') then true 
                                          else case when """ + str(case.lunch) + """ = 'True' and mp.meal_type in ('l_non_premium','l_standard','l_premium') then true
                                          else case when """ + str(case.afternoon_tea) + """ = 'True' and mp.meal_type in ('at_non_premium','at_standard','at_premium') then true
                                          else case when """ + str(case.dinner) + """ = 'True' and mp.meal_type in ('d_non_premium','d_standard','d_premium') then true
                                          else false
                                          end end end end) as active
                                        , mp.meal_type
                                  from cc_menu_pricing mp 
                                  INNER JOIN cc_menus m on m.id = mp.menu_id 
                                  where menu_id = """+ str(case.id)+ """ 
                                ) a
                                where a.active = true)""")
                
                #To update pricing records to inactive
                cr.execute("""update cc_menu_pricing set active = false where id in (
                              select a.id
                              from 
                                (
                                  select mp.id
                                        ,(case when """ + str(case.break_fast) + """ = 'False' and mp.meal_type in ('bf_non_premium','bf_standard','bf_premium') then true 
                                          else case when """ + str(case.lunch) + """ = 'False' and mp.meal_type in ('l_non_premium','l_standard','l_premium') then true
                                          else case when """ + str(case.afternoon_tea) + """ = 'False' and mp.meal_type in ('at_non_premium','at_standard','at_premium') then true
                                          else case when """ + str(case.dinner) + """ = 'False' and mp.meal_type in ('d_non_premium','d_standard','d_premium') then true
                                          else false
                                          end end end end) as active
                                        , mp.meal_type
                                  from cc_menu_pricing mp 
                                  INNER JOIN cc_menus m on m.id = mp.menu_id 
                                  where menu_id = """+ str(case.id)+ """
                                ) a
                                where a.active = true)""")
                
        return res 
    
    # On Change of Minimum Covers 
    def onchange_min_covers(self, cr, uid, ids, min_covers):                
        print min_covers
        warning = {}
        if min_covers < 1:
            warning = {'title':'Warning!','message':'Please Enter Min. Covers as numbers greater than 0'}
        
        return {'warning':warning}
        
cc_menus()

class cc_events(osv.osv):
    _name = 'cc.events'
    _columns = {'active':fields.boolean('Active'),
                'name':fields.char('Events Name',size=250),
                'description': fields.text('Description'),
                'date_from'  : fields.date('Date From'),
                'date_to'    : fields.date('Date To'),
                'bt_from'    : fields.many2one('cc.time','BF Time From'),
                'bt_to'      : fields.many2one('cc.time','BF Time To'),
                'lt_from'    : fields.many2one('cc.time','L Time From'),
                'lt_to'      : fields.many2one('cc.time','L Time To'),
                'att_from'   : fields.many2one('cc.time','AT Time From'),
                'att_to'     : fields.many2one('cc.time','AT Time To'),
                'dt_from'    : fields.many2one('cc.time','D Time From'),
                'dt_to'      : fields.many2one('cc.time','D Time To'),
                'menu_ids'   : fields.many2many('cc.menus','events_menu_rel','events_id','menu_id','Menus'),
                'covers'     : fields.integer('Max. Covers'),
                'partner_id' : fields.many2one('res.partner','Partner'),
                'remove_htls_to'  : fields.many2many('res.partner','event_top_hide_rel','event_id','top_id','Hide this event from'),
                'show_htls_to'    : fields.many2many('res.partner','event_top_show_rel','event_id','top_id','Show this event only to'),

                }
    
    def default_get(self, cr, uid, fields, context=None):
        print context
        return super(cc_events, self).default_get(cr, uid, fields, context=context)
    
    def _check_duration(self, cr, uid, ids, context=None):
        obj_fy = self.browse(cr, uid, ids[0], context=context)
        if obj_fy.date_to < obj_fy.date_from:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe start date of a fiscal year must precede its end date.', ['date_from','date_to'])
    ]
    
cc_events()

class cc_black_out_day(osv.osv):
    _name='cc.black.out.day'
    _columns={'date':fields.date('Date'),
              'date_to':fields.date('Date'),
              'name':fields.char('Description',size=100),  
              'from_time_id' : fields.many2one('cc.time','From Time'),
              'to_time_id' : fields.many2one('cc.time','To Time'),
              'partner_id':fields.many2one('res.partner','Partner'),            
              }
cc_black_out_day()

class cc_menu_pricing(osv.osv):
    _name='cc.menu.pricing'
    
    def _get_total(self, cr, uid, ids, fieldnames, args, context=None):
        result = {}        
        for case in self.browse(cr, uid, ids, context=context):
            sc = mon_sc = tue_sc = wed_sc = thu_sc = fri_sc = sat_sc = sun_sc = 0.00
            sc_inc = case.menu_id.sc_included
            sc = case.menu_id.service_charge or 0.00
            sc_disc = case.menu_id.sc_disc
            result[case.id] = {
                                'mon_total' : self.onchange_pricing(cr, uid, ids, 'mon', case.mon_price, case.mon_ffp_mu, sc, sc_inc, sc_disc, context)['value']['mon_total'],
                                'tue_total' : self.onchange_pricing(cr, uid, ids, 'tue', case.tue_price, case.tue_ffp_mu, sc, sc_inc, sc_disc, context)['value']['tue_total'],
                                'wed_total' : self.onchange_pricing(cr, uid, ids, 'wed', case.wed_price, case.wed_ffp_mu, sc, sc_inc, sc_disc, context)['value']['wed_total'],
                                'thu_total' : self.onchange_pricing(cr, uid, ids, 'thu', case.thu_price, case.thu_ffp_mu, sc, sc_inc, sc_disc, context)['value']['thu_total'],
                                'fri_total' : self.onchange_pricing(cr, uid, ids, 'fri', case.fri_price, case.fri_ffp_mu, sc, sc_inc, sc_disc, context)['value']['fri_total'],
                                'sat_total' : self.onchange_pricing(cr, uid, ids, 'sat', case.sat_price, case.sat_ffp_mu, sc, sc_inc, sc_disc, context)['value']['sat_total'],
                                'sun_total' : self.onchange_pricing(cr, uid, ids, 'sun', case.sun_price, case.sun_ffp_mu, sc, sc_inc, sc_disc, context)['value']['sun_total'],
                              }
        return result

    _columns={'meal_type':fields.selection([('bf_non_premium','B/F Non Premium'),
                                       ('bf_standard','B/F Standard'),
                                       ('bf_premium','B/F Premium'),
                                       ('l_non_premium','Lunch Non Premium'),
                                       ('l_standard','Lunch Standard'),
                                       ('l_premium','Lunch Premium'),
                                       ('at_non_premium','AT Non Premium'),
                                       ('at_standard','AT Standard'),
                                       ('at_premium','AT Premium'),
                                       ('d_non_premium','Dinner Non Premium'),
                                       ('d_standard','Dinner Standard'),
                                       ('d_premium','Dinner Premium')],
                                      'Type'),
              'mon_price':fields.float('Mon',digits=(16, 2)),
              'mon_ffp_mu':fields.float('Mon FFP MU',digits=(16, 2)), 
              'mon_to_mu':fields.float('Mon Com.',digits=(16, 2)), 
              'mon_total': fields.function(_get_total, type='float',string='Total'),
              'tue_price':fields.float('Tue',digits=(16, 2)),
              'tue_ffp_mu':fields.float('Tue FFP MU',digits=(16, 2)),
              'tue_to_mu':fields.float('Tue Com.',digits=(16, 2)),
              'wed_price':fields.float('Wed',digits=(16, 2)),
              'wed_ffp_mu':fields.float('Wed FFP MU',digits=(16, 2)),
              'wed_to_mu':fields.float('Wed Com.',digits=(16, 2)),
              'thu_price':fields.float('Thu',digits=(16, 2)),
              'thu_ffp_mu':fields.float('Thu FFP MU',digits=(16, 2)),
              'thu_to_mu':fields.float('Thu Com.',digits=(16, 2)),
              'fri_price':fields.float('Fri',digits=(16, 2)),
              'fri_ffp_mu':fields.float('Fri FFP MU',digits=(16, 2)),
              'fri_to_mu':fields.float('Fri Com.',digits=(16, 2)),
              'sat_price':fields.float('Sat',digits=(16, 2)),
              'sat_ffp_mu':fields.float('Sat FFP MU',digits=(16, 2)),
              'sat_to_mu':fields.float('Sat Com.',digits=(16, 2)),
              'sun_price':fields.float('Sun',digits=(16, 2)),
              'sun_ffp_mu':fields.float('Sun FFP MU',digits=(16, 2)),
              'sun_to_mu':fields.float('Sun Com.',digits=(16, 2)),
              'menu_id':fields.many2one('cc.menus','Menus'),
              'active':fields.boolean('Active'),
              'mon_total': fields.function(_get_total, type='float',string='Total',multi='total', store=True),
              'tue_total': fields.function(_get_total, type='float',string='Total',multi='total', store=True),
              'wed_total': fields.function(_get_total, type='float',string='Total',multi='total', store=True),
              'thu_total': fields.function(_get_total, type='float',string='Total',multi='total', store=True),
              'fri_total': fields.function(_get_total, type='float',string='Total',multi='total', store=True),
              'sat_total': fields.function(_get_total, type='float',string='Total',multi='total', store=True),
              'sun_total': fields.function(_get_total, type='float',string='Total',multi='total', store=True),
#               'op_markup_id' :fields.many2one('cc.operator.markup','Markup')                            
             }
    _defaults = {  'mon_price':0.00,
                   'mon_ffp_mu' : 0.00,
                   'mon_to_mu':0.00,
                   'tue_price':0.00,
                   'tue_ffp_mu' : 0.00,
                   'tue_to_mu':0.00,
                   'wed_price':0.00,
                   'wed_ffp_mu' : 0.00,
                   'wed_to_mu':0.00,
                   'thu_price':0.00,
                   'thu_ffp_mu' : 0.00,
                   'thu_to_mu':0.00,
                   'fri_price':0.00,
                   'fri_ffp_mu' : 0.00,
                   'fri_to_mu':0.00,
                   'sat_price':0.00,
                   'sat_ffp_mu' : 0.00,
                   'sat_to_mu':0.00,
                   'sun_price':0.00,
                   'sun_ffp_mu' : 0.00,
                   'sun_to_mu':0.00,
                   }
    
    def onchange_pricing(self, cr, uid, ids, day, price, markup, service_charge, sc_included, sc_disrtnry,context=None):
        res={}
        sc = 0.00 
        if context is None:
           context = {} 
        total = mark_up = 0.00
        if price > 0 :
            if not context.get('mu_update',True):
                if price and price > 0 and price <= 25:
                    markup = 0.20 * price
                elif price > 25:
                    markup = 0.15 * price            
                if context.get('food_type') == 'drink':
                    markup = 0.10 * price
                
                    
            mark_up = round(markup,2)         
               
            total = (price + mark_up) or 0.00
            if not context.get('mu_update',True):
               mark_up = round(mark_up + (round(total,1) - total),2)
               total = price + mark_up        
            
            if not sc_included:
               sc = (price * (service_charge/100.00))
               if not sc_disrtnry:
                  sc = round((price * (service_charge/100.00)),1)  
               if sc_disrtnry:
                  sc = round(((price + mark_up) * (service_charge/100.00)),1)
                   
            total += sc      
        
        if day == 'mon':
           res['mon_total'] = total
           res['mon_ffp_mu'] = mark_up
        elif day == 'tue':
           res['tue_total'] = total
           res['tue_ffp_mu'] = mark_up
        elif day == 'wed':
           res['wed_total'] = total
           res['wed_ffp_mu'] = mark_up
        elif day == 'thu':
           res['thu_total'] = total
           res['thu_ffp_mu'] = mark_up
        elif day == 'fri':
           res['fri_total'] = total
           res['fri_ffp_mu'] = mark_up
        elif day == 'sat':
           res['sat_total'] = total
           res['sat_ffp_mu'] = mark_up
        elif day == 'sun':
           res['sun_total'] = total
           res['sun_ffp_mu'] = mark_up
        return {'value':res} 
        
    
cc_menu_pricing()

class cc_opening_hrs(osv.osv):
    
    _name='cc.opening.hrs'
    _columns={'partner_id'  : fields.many2one('res.partner','Partner'),
              'name'        : fields.selection([('monday','Monday'),('tuesday','Tuesday'),('wednesday','Wednesday'),('thursday','Thursday'),('friday','Friday'),('saturday','Saturday'),('sunday','Sunday')],'Day'),
              'bf_from'     : fields.many2one('cc.time','B/F From'),
              'bf_to'       : fields.many2one('cc.time','B/F To'),
              'lunch_from'  : fields.many2one('cc.time','Lunch From'),
              'lunch_to'    : fields.many2one('cc.time','Lunch To'),
              'dinner_from' : fields.many2one('cc.time','Dinner From'),
              'dinner_to'   : fields.many2one('cc.time','Dinner To'),              
              }
    
    def onchange_time(self, cr, uid, ids, bf_from,bf_to,lunch_from,lunch_to,dinner_from,dinner_to):                
        
        time_invalid = False
        warning = res = {}
        
        if bf_from > 23.59:       time_invalid = True; res['bf_from']     = 0
        elif bf_to > 23.59:       time_invalid = True; res['bf_to']       = 0
        elif lunch_from > 23.59:  time_invalid = True; res['lunch_from']  = 0
        elif lunch_to > 23.59:    time_invalid = True; res['lunch_to']    = 0
        elif dinner_from > 23.59: time_invalid = True; res['dinner_from'] = 0
        elif dinner_to > 23.59:   time_invalid = True; res['dinner_to']   = 0
        
        if time_invalid:
           warning = {'title':'Warning!','message':'Time should be less than 23:59.'}
        return {'value':res,'warning':warning}
        
cc_opening_hrs()


class cc_time_allocations(osv.osv):
    _name='cc.time.allocations' 
    _columns={'name'    : fields.selection([('monday','Monday'),('tuesday','Tuesday'),('wednesday','Wednesday'),('thursday','Thursday'),('friday','Friday'),('saturday','Saturday'),('sunday','Sunday')],'Day'),
              'type'    : fields.selection([('break_fast','Break Fast'),('lunch','Lunch'),('at','Afternoon Tea'),('dinner','Dinner')],'Type'),
              'non_frm_id' : fields.many2one('cc.time','Non Premium From'),
              'non_to_id' : fields.many2one('cc.time','Non Premium To'),
              'std_frm_id' : fields.many2one('cc.time','Standard From'),
              'std_to_id' : fields.many2one('cc.time','Standard To'),
              'pre_frm_id' : fields.many2one('cc.time','Premium From'),
              'pre_to_id' : fields.many2one('cc.time','Premium To-'),              
              'covers'  : fields.integer('Covers'),
              'cap'     : fields.integer('Maximum Covers/Shift'),
              'partner_id':fields.many2one('res.partner','Partner'),
              }
    _default={'covers':0}
cc_time_allocations()

class cc_private_rooms(osv.osv):
    _name='cc.private.rooms'
    _columns={'partner_id'     : fields.many2one('res.partner','Partner'),
              'name'           : fields.char('Name',size=75),
              'no_of_seated'   : fields.integer('No.of Covers Seated'),
              'no_of_standing' : fields.integer('No.of Covers Standing'),
              'max_nos'        : fields.integer('Max. No. on one table'),
              'av_screen'      : fields.selection([('yes','Yes'),('no','No')],'AV Screen'),
              'projector'      : fields.selection([('yes','Yes'),('no','No')],'Projector'),
              'others'         : fields.char('Others',size=100), 
              }
    _defaults={'av_screen':'no',
               'projector' :'no'}
    
cc_private_rooms()

class cc_reminder_time(osv.osv): 
    _name='cc.reminder.time'
    _columns = {'company_id':fields.many2one('res.company','Company'),
                'template_id':fields.many2one('email.template','Template'),
                'reminder_date':fields.datetime('Date'),
                'reminded':fields.boolean('Reminded'),
                'lead_id' : fields.many2one('crm.lead','Lead'),
               }
    _order = 'template_id'
    
cc_reminder_time()     

class account_config_settings(osv.osv_memory):
    _inherit='account.config.settings'
    
    def confirm_all_invoices(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        invoice_obj = self.pool.get('account.invoice')
        #invoice_ids = invoice_obj.search(cr,uid,[('state','=','draft')])
        invoice_ids = []
        

        for inv in invoice_obj.browse(cr,uid,invoice_ids):
            _logger.info('Invoice %d', inv.id)
            wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_open', cr)
        return True
    
    def confirm_Afternoontea_leads(self, cr, uid, ids, context=None):
        info_obj = self.pool.get('cc.send.rest.info')
        #info_ids = info_obj.search(cr,uid,[('lead_id.state','=','open'),('lead_id.service_type','=','noontea')])
        info_ids = [] 
        for info in info_obj.browse(cr,uid,info_ids):
            _logger.info('lead %d', info.lead_id.id)
            info_obj.cc_create_invoices(cr, uid, [info.id], context)
        return True
    
    def add_followers(self, cr, uid, ids, context=None):
        lead_obj = self.pool.get('crm.lead')
        inv_obj = self.pool.get('account.invoice')
        user_obj = self.pool.get('res.users')
        Mail_obj = self.pool.get('mail.followers')
        user = user_obj.browse(cr,uid,uid)
        subtype_ids = self.pool.get('mail.message.subtype').search(cr,uid,[('name','=','Discussions')])
        user_ids = user_obj.search(cr,uid,[('role','in',('admin','bo'))])
        lead_ids = lead_obj.search(cr,uid,[('state','=','draft')])
        inv_ids = inv_obj.search(cr,uid,[('state','=','draft')])
        # for ld in lead_obj.browse(cr,uid,lead_ids): Commented adding of followers is not required
        #     _logger.info('Lead %d', ld.id)
        #     userids = user_ids
        #     userids.remove(ld.user_id.id)
        #     for u in user_obj.browse(cr,uid,userids):
        #         Mail_obj.create(cr,uid,{'res_model':'crm.lead',
        #                                 'res_id': ld.id,
        #                                 'partner_id' : u.partner_id.id,
        #                                 'subtype_ids': [(6, 0, subtype_ids)]
        #                                 })
        # for inv in inv_obj.browse(cr,uid,inv_ids):
        #     _logger.info('Invoice %d', inv.id)
        #     userids = user_ids
        #     userids.remove(inv.user_id.id)
        #     for u in user_obj.browse(cr,uid,userids):
        #         Mail_obj.create(cr,uid,{'res_model':'account.invoice',
        #                                 'res_id': inv.id,
        #                                 'partner_id' : u.partner_id.id,
        #                                 'subtype_ids': [(6, 0, subtype_ids)]
        #                                 })
        return True
    
account_config_settings() 

class base_config_settings(osv.osv_memory):
    _inherit='base.config.settings'
    
    def add_followers(self, cr, uid, ids, context=None):
        lead_obj = self.pool.get('crm.lead')
        inv_obj = self.pool.get('account.invoice')
        user_obj = self.pool.get('res.users')
        Mail_obj = self.pool.get('mail.followers')
        user = user_obj.browse(cr,uid,uid)
        subtype_ids = self.pool.get('mail.message.subtype').search(cr,uid,[('name','=','Discussions')])
        user_ids = user_obj.search(cr,uid,[('role','in',('admin','bo'))])
        lead_ids = lead_obj.search(cr,uid,[('user_id','>',0)])
        inv_ids = inv_obj.search(cr,uid,[('user_id','>',0)])
        # for ld in lead_obj.browse(cr,uid,lead_ids): Commented adding of followers is not required
        #     _logger.info('Lead %d', ld.id)
        #     userids = user_ids
        #     userids.remove(ld.user_id.id)
        #     for u in user_obj.browse(cr,uid,userids):
        #         Mail_obj.create(cr,uid,{'res_model':'crm.lead',
        #                                 'res_id': ld.id,
        #                                 'partner_id' : u.partner_id.id,
        #                                 'subtype_ids': [(6, 0, subtype_ids)]
        #                                 })
        # for inv in inv_obj.browse(cr,uid,inv_ids):
        #     _logger.info('Invoice %d', inv.id)
        #     userids = user_ids
        #     userids.remove(inv.user_id.id)
        #     for u in user_obj.browse(cr,uid,userids):
        #         Mail_obj.create(cr,uid,{'res_model':'account.invoice',
        #                                 'res_id': inv.id,
        #                                 'partner_id' : u.partner_id.id,
        #                                 'subtype_ids': [(6, 0, subtype_ids)]
        #                                 })
        return True
    
    def create_vouchers(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        inv_obj = self.pool.get('account.invoice')
        vch_obj = self.pool.get('account.voucher')
        inv_ids = inv_obj.search(cr,uid,[('state','=','paid')])
        inv_ids = []
       
        vch_ids = vch_obj.search(cr,uid,[])
        vch_obj.cancel_voucher(cr, uid, vch_ids)
        vch_obj.unlink(cr, uid, vch_ids)
        
        for inv in inv_obj.browse(cr,uid,inv_ids):
            _logger.info('Invoice - %d', inv.id)
#             wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
#             inv_obj.action_cancel_draft(cr, uid, [inv.id])
#             wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_open', cr)
            res = {}
            res = vch_obj.onchange_partner_id(cr, uid, [], inv.partner_id.id, 8, inv.amount_total, inv.currency_id.id, inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment', inv.date_invoice, context=context)['value']
 
            line_cr_ids = []
            print "name", inv.number
            if 'line_cr_ids' in res:
                for ln in res['line_cr_ids']:
                    if inv.number == ln['name']:
                        line_cr_ids.append((0,0, ln))   
                del res['line_cr_ids']
                   
            line_dr_ids = []
            if 'line_dr_ids' in res:
                for ln in res['line_dr_ids']:
                    if inv.number == ln['name']:
                        line_dr_ids.append((0,0, ln))
                del res['line_dr_ids']
                   
            res.update({'partner_id':inv.partner_id.id,
                                   'amount':inv.amount_total,
                                   'reference':inv.name,
                                   'journal_id':8,
                                   'date':inv.date_invoice,
                                   'account_id':140,
                                   'type':inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                                   'line_cr_ids': line_cr_ids,
                                   'line_dr_ids': line_dr_ids,
                                   })
            vid = vch_obj.create(cr,uid,res)
              
            wf_service.trg_validate(uid, 'account.voucher', vid, 'proforma_voucher', cr)
        return True


base_config_settings()

class mail_mail(osv.Model):
    _inherit='mail.mail'
    
    #Overriden
    def send_get_email_dict(self, cr, uid, mail, partner=None, context=None):
        """ Return a dictionary for specific email values, depending on a
            partner, or generic to the whole recipients given by mail.email_to.

            :param browse_record mail: mail.mail browse_record
            :param browse_record partner: specific recipient partner
        """
        body = self.send_get_mail_body(cr, uid, mail, partner=partner and partner[0], context=context)
        subject = self.send_get_mail_subject(cr, uid, mail, partner=partner and partner[0], context=context)
        body_alternative = tools.html2plaintext(body)

        # generate email_to, heuristic:
        # 1. if 'partner' is specified and there is a related document: Followers of 'Doc' <email>
        # 2. if 'partner' is specified, but no related document: Partner Name <email>
        # 3; fallback on mail.email_to that we split to have an email addresses list
        
        email_to = []
        if partner:
            for cc_partner in partner:
                if cc_partner and mail.record_name:
                    email_to.append(('"%s" <%s>') % (cc_partner.name, cc_partner.email))
                elif cc_partner:
                    email_to.append('%s <%s>' % (cc_partner.name, cc_partner.email))
        else:
            email_to = tools.email_split(mail.email_to)

        return {
            'body': body,
            'body_alternative': body_alternative,
            'subject': subject,
            'email_to': email_to,
        }

#     #Overriden:Version:7.0
#     def send(self, cr, uid, ids, auto_commit=False, recipient_ids=None, context=None):
#         """ Sends the selected emails immediately, ignoring their current
#             state (mails that have already been sent should not be passed
#             unless they should actually be re-sent).
#             Emails successfully delivered are marked as 'sent', and those
#             that fail to be deliver are marked as 'exception', and the
#             corresponding error mail is output in the server logs.
#      
#             :param bool auto_commit: whether to force a commit of the mail status
#                 after sending each mail (meant only for scheduler processing);
#                 should never be True during normal transactions (default: False)
#             :param list recipient_ids: specific list of res.partner recipients.
#                 If set, one email is sent to each partner. Its is possible to
#                 tune the sent email through ``send_get_mail_body`` and ``send_get_mail_subject``.
#                 If not specified, one email is sent to mail_mail.email_to.
#             :return: True
#         """
#         tmp_server_id = False
#         tmp_email_from = False
#         tmp_reply_to   = False 
#         if 'mail_server_id' in context:
#             tmp_server_id = context.get('mail_server_id',False)
#         if 'email_from' in context:
#             tmp_email_from = context.get('email_from',False)
#         if 'reply_to' in context:
#             tmp_reply_to = context.get('reply_to',False)      
#             
#         ir_mail_server = self.pool.get('ir.mail_server')
#         for mail in self.browse(cr, uid, ids, context=context):
#             try:
#                 # handle attachments
#                 attachments = []
#                 for attach in mail.attachment_ids:
#                     attachments.append((attach.datas_fname, base64.b64decode(attach.datas)))
#                 # specific behavior to customize the send email for notified partners
#                 email_list = []
#                 cc_partner = []
#                 if recipient_ids:
#                     for partner in self.pool.get('res.partner').browse(cr, SUPERUSER_ID, recipient_ids, context=context):
#                         cc_partner.append(partner)
#                     email_list.append(self.send_get_email_dict(cr, uid, mail, partner=cc_partner, context=context))
#                 else:
#                     email_list.append(self.send_get_email_dict(cr, uid, mail, context=context))
#      
#                 # build an RFC2822 email.message.Message object and send it without queuing
#                 res = None
#                 for email in email_list:
#                     msg = ir_mail_server.build_email(
#                         email_from = tmp_email_from or mail.email_from,
#                         email_to = email.get('email_to'),
#                         subject = email.get('subject'),
#                         body = email.get('body'),
#                         body_alternative = email.get('body_alternative'),
#                         email_cc = tools.email_split(mail.email_cc),
#                         reply_to = tmp_reply_to or email.get('reply_to'),
#                         attachments = attachments,
#                         message_id = mail.message_id,
#                         references = mail.references,
#                         object_id = mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
#                         subtype = 'html',
#                         subtype_alternative = 'plain')
#                     res = ir_mail_server.send_email(cr, uid, msg,
#                         mail_server_id=mail.mail_server_id.id or tmp_server_id, context=context)
#                 if res:
#                     mail.write({'state': 'sent', 'message_id': res})
#                     mail_sent = True
#                 else:
#                     mail.write({'state': 'exception'})
#                     mail_sent = False
#      
#                 # /!\ can't use mail.state here, as mail.refresh() will cause an error
#                 # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
#                 if mail_sent:
#                     self._postprocess_sent_message(cr, uid, mail, context=context)
#             except Exception:
#                 _logger.exception('failed sending mail.mail %s', mail.id)
#                 mail.write({'state': 'exception'})
#      
#             if auto_commit == True:
#                 cr.commit()
#         return True
    
    def send(self, cr, uid, ids, auto_commit=False, raise_exception=False, context=None):
        """ Sends the selected emails immediately, ignoring their current
            state (mails that have already been sent should not be passed
            unless they should actually be re-sent).
            Emails successfully delivered are marked as 'sent', and those
            that fail to be deliver are marked as 'exception', and the
            corresponding error mail is output in the server logs.

            :param bool auto_commit: whether to force a commit of the mail status
                after sending each mail (meant only for scheduler processing);
                should never be True during normal transactions (default: False)
            :param bool raise_exception: whether to raise an exception if the
                email sending process has failed
            :return: True
        """ 
        if context is None:
            context = {}
        tmp_server_id = False
        tmp_email_from = False
        tmp_reply_to   = False 
        if 'mail_server_id' in context:
            tmp_server_id = context.get('mail_server_id',False)
        if 'email_from' in context:
            tmp_email_from = context.get('email_from',False)
        #if mail is sent form white labeling site then below code is to change from address    
        user = self.pool.get('res.users').browse(cr, uid, uid)
        operator = user.partner_id
        if user.is_wlabeling and user.role and user.role not in ('admin','bo'):
           if user.role in ('client','venue'):
              tmp_email_from = user.partner_id.email
           else:
              operator = user.partner_id.parent_id
              tmp_email_from = user.partner_id and user.partner_id.parent_id and user.partner_id.parent_id.email or ''
                 
        if 'reply_to' in context:
            tmp_reply_to = context.get('reply_to',False)    
        
        ir_mail_server = self.pool.get('ir.mail_server')
        for mail in self.browse(cr, SUPERUSER_ID, ids, context=context):
            try:
                # handle attachments
                attachments = []
                for attach in mail.attachment_ids:
                    attachments.append((attach.datas_fname, base64.b64decode(attach.datas)))
                # specific behavior to customize the send email for notified partners
                email_list = []
                cc_partner = []
                if mail.email_to:
                    email_list.append(self.send_get_email_dict(cr, uid, mail, context=context))
                                        
                elif mail.recipient_ids:
                    for partner in mail.recipient_ids: 
                        cc_partner.append(partner)
                    email_list.append(self.send_get_email_dict(cr, uid, mail, partner=cc_partner, context=context))
                # headers
                headers = {}
                bounce_alias = self.pool['ir.config_parameter'].get_param(cr, uid, "mail.bounce.alias", context=context)
                catchall_domain = self.pool['ir.config_parameter'].get_param(cr, uid, "mail.catchall.domain", context=context)
                if bounce_alias and catchall_domain:
                    if mail.model and mail.res_id:
                        headers['Return-Path'] = '%s-%d-%s-%d@%s' % (bounce_alias, mail.id, mail.model, mail.res_id, catchall_domain)
                    else:
                        headers['Return-Path'] = '%s-%d@%s' % (bounce_alias, mail.id, catchall_domain)
                
                cr.execute("select id from ir_mail_server where smtp_user = (select email from res_partner where id = " + str(operator.id) + ")")
                mail_server = cr.fetchone()                
                if not mail_server:
                   mail_server = mail.mail_server_id.id
                else:
                    mail_server = mail_server[0] 
                    
                if context and context.get('tmp_name') in ('Enquiry - Booking Confirmation To Venue1','Enquiry - Amendment Confirmation To Venue'):
                   mail_server = mail.mail_server_id.id
                   tmp_email_from = context.get('email_from',False)
                    
                # build an RFC2822 email.message.Message object and send it without queuing
                res = None
                for email in email_list:
                    msg = ir_mail_server.build_email(
                        email_from = tmp_email_from or mail.email_from,
                        email_to=email.get('email_to'),
                        subject=email.get('subject'),
                        body=email.get('body'),
                        body_alternative=email.get('body_alternative'),
                        email_cc=tools.email_split(mail.email_cc),
                        reply_to=mail.reply_to,
                        attachments=attachments,
                        message_id=mail.message_id,
                        references=mail.references,
                        object_id=mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
                        subtype='html',
                        subtype_alternative='plain',
                        headers=headers)
                    res = ir_mail_server.send_email(cr, uid, msg,
                                                    mail_server_id=mail_server,
                                                    context=context)
                if res:
                    mail.write({'state': 'sent', 'message_id': res})
                    mail_sent = True
                else:
                    mail.write({'state': 'exception'})
                    mail_sent = False

                # /!\ can't use mail.state here, as mail.refresh() will cause an error
                # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
                if mail_sent:
                    self._postprocess_sent_message(cr, uid, mail, context=context)
            except Exception as e:
                _logger.exception('failed sending mail.mail %s', mail.id)
                mail.write({'state': 'exception'})
                if raise_exception:
                    if isinstance(e, AssertionError):
                        # get the args of the original error, wrap into a value and throw a MailDeliveryException
                        # that is an except_orm, with name and value as arguments
                        value = '. '.join(e.args)
                        raise MailDeliveryException(_("Mail Delivery Failed"), value)
                    raise

            if auto_commit == True:
                cr.commit()
        return True
         
mail_mail()

class account_partner_ledger(osv.osv_memory):
    _inherit='account.partner.ledger'
    _columns={'partner_id':fields.many2one('res.partner','Partner',domain="[('parent_id','=',False)]"),
              }
    _defaults={'filter':'filter_date',
                'result_selection': 'customer_supplier',}
    
    def onchange_filter(self, cr, uid, ids, filter='filter_date', fiscalyear_id=False, context=None):
        res = super(account_partner_ledger, self).onchange_filter(cr, uid, ids, filter=filter, fiscalyear_id=fiscalyear_id, context=context)
        if filter in ['filter_date']:
            fiscal_obj = self.pool.get('account.fiscalyear')
            fiscalyear=False
            if fiscalyear_id:
                fiscalyear = fiscal_obj.browse(cr,uid,fiscalyear_id)                
            res['value'].update({'period_from': False, 'period_to': False, 'date_from':fiscalyear and fiscalyear.date_start or False  ,'date_to': fiscalyear and fiscalyear.date_stop or False})
        return res
        
    def pre_print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data['form'].update(self.read(cr, uid, ids, ['result_selection'], context=context)[0])
        data['form'].update(self.read(cr, uid, ids, ['partner_id'], context=context)[0])
        return data

account_partner_ledger()

class mail_message(osv.Model):
    _inherit='mail.message'
    _columns={'ccaction_id':fields.integer('Action'),}
    _message_read_fields = ['id', 'parent_id', 'model', 'res_id', 'body', 'subject', 'date', 'to_read', 'email_from',
                            'type', 'vote_user_ids', 'attachment_ids', 'author_id', 'partner_ids', 'record_name','ccaction_id']
    
    def _message_read_dict(self, cr, uid, message, parent_id=False, context=None):
        res = super(mail_message,self)._message_read_dict(cr, uid, message, parent_id, context)
        if res:
           res.update({'ccaction_id':message.ccaction_id,
                       'attachment_ids':message.attachment_ids})
        return res 
    
mail_message()   

class work_detail(osv.osv):
    _name='work.detail'
    _columns = {'name':fields.char('Work Detail',size=125),
              }
work_detail()

class cc_operator_markup(osv.osv):
    _name='cc.operator.markup'
    _columns={'partner_id':fields.many2one('res.partner','Partner'),
              'restaurant_id':fields.many2one('res.partner','Restaurant',domain=[('type','=','default'),('partner_type','=','venue'),('active','=',True)]),
              'menu_id':fields.many2one('cc.menus','Menus',domain="[('partner_id','=',restaurant_id)]"),
              'menu_ids':fields.many2many('cc.menus','rel_om_menu','omarkup_id','menu_id','Menus',domain="[('partner_id','=',restaurant_id)]"),
              'markup_perc' : fields.float('Markup (%)',digits=(16, 2)),
              'markup_ids':fields.one2many('cc.markup','op_markup_id','Markup'),
              'is_populated':fields.boolean('Pricing Populated?'),
              'mrkup_lvl' : fields.selection([('rest_lvl','Restaurant Level'),('menu_lvl','Menu Level')],'Markup Level')
              }
    _defaults={'is_populated':False,
               'markup_perc' :0.00}
    _sql_constraints = [
        ('menu_uniq', 'unique(menu_id,partner_id)', 'You cannot select same menu twice.'),
    ]
    
    def populate_pricing(self, cr, uid, ids,context=None):      
        pricing_obj = self.pool.get('cc.menu.pricing')
        markup_obj = self.pool.get('cc.markup')
        for case in self.browse(cr,uid,ids):
           pricing_ids = pricing_obj.search(cr, uid, ['|',('active','=',True),('active','=',False),('menu_id','=',case.menu_id.id)])
           read_data = pricing_obj.read(cr, uid, pricing_ids,['id'])
           for d in read_data:
               markup_obj.create(cr,uid,{'pricing_id':d['id'],'op_markup_id':case.id})
           if len(read_data) >0:    
              self.write(cr,uid,ids,{'is_populated':True})    
        return True
            
cc_operator_markup()

class cc_markup(osv.osv):
    _name='cc.markup'
    
    def _get_total(self, cr, uid, ids, fieldnames, args, context=None):
        result = {} 
        pricing_obj = self.pool.get('cc.menu.pricing')       
        for case in self.browse(cr, uid, ids, context=context):
            sc = mon_sc = tue_sc = wed_sc = thu_sc = fri_sc = sat_sc = sun_sc = 0.00
            sc_inc = case.pricing_id.menu_id.sc_included
            sc = case.pricing_id.menu_id.service_charge or 0.00
            sc_disc = case.pricing_id.menu_id.sc_disc
            result[case.id] = {
                                'mon_total' : pricing_obj.onchange_pricing(cr, uid, ids, 'mon', case.mon_price, case.mon_ffp_mu, sc, sc_inc, sc_disc, context)['value']['mon_total'],
                                'tue_total' : pricing_obj.onchange_pricing(cr, uid, ids, 'tue', case.tue_price, case.tue_ffp_mu, sc, sc_inc, sc_disc, context)['value']['tue_total'],
                                'wed_total' : pricing_obj.onchange_pricing(cr, uid, ids, 'wed', case.wed_price, case.wed_ffp_mu, sc, sc_inc, sc_disc, context)['value']['wed_total'],
                                'thu_total' : pricing_obj.onchange_pricing(cr, uid, ids, 'thu', case.thu_price, case.thu_ffp_mu, sc, sc_inc, sc_disc, context)['value']['thu_total'],
                                'fri_total' : pricing_obj.onchange_pricing(cr, uid, ids, 'fri', case.fri_price, case.fri_ffp_mu, sc, sc_inc, sc_disc, context)['value']['fri_total'],
                                'sat_total' : pricing_obj.onchange_pricing(cr, uid, ids, 'sat', case.sat_price, case.sat_ffp_mu, sc, sc_inc, sc_disc, context)['value']['sat_total'],
                                'sun_total' : pricing_obj.onchange_pricing(cr, uid, ids, 'sun', case.sun_price, case.sun_ffp_mu, sc, sc_inc, sc_disc, context)['value']['sun_total'],
                              }
        return result

    
    _columns={'meal_type':fields.related('pricing_id','meal_type',type='selection', selection=[('bf_non_premium','B/F Non Premium'),
                                   ('bf_standard','B/F Standard'),
                                   ('bf_premium','B/F Premium'),
                                   ('l_non_premium','Lunch Non Premium'),
                                   ('l_standard','Lunch Standard'),
                                   ('l_premium','Lunch Premium'),
                                   ('at_non_premium','AT Non Premium'),
                                   ('at_standard','AT Standard'),
                                   ('at_premium','AT Premium'),
                                   ('d_non_premium','Dinner Non Premium'),
                                   ('d_standard','Dinner Standard'),
                                   ('d_premium','Dinner Premium')],
                                  string='Type' ,readonly=True),
           
            'mon_price':fields.related('pricing_id','mon_price',string='Mon',type='float',digits=(16, 2)),
            'mon_ffp_mu':fields.related('pricing_id','mon_ffp_mu',string='Mon FFP MU',type='float', digits=(16, 2)), 
            'mon_to_mu':fields.float('Mon Com.',digits=(16, 2)), 
            'tue_price':fields.related('pricing_id','tue_price',string='Tue',type='float',digits=(16, 2)),
            'tue_ffp_mu':fields.related('pricing_id','tue_ffp_mu',string='Tue FFP MU',type='float', digits=(16, 2)),
            'tue_to_mu':fields.float('Tue Com.',digits=(16, 2)),
            'wed_price':fields.related('pricing_id','wed_price',string='Wed',type='float',digits=(16, 2)),
            'wed_ffp_mu':fields.related('pricing_id','wed_ffp_mu',string='Wed FFP MU',type='float', digits=(16, 2)),
            'wed_to_mu':fields.float('Wed Com.',digits=(16, 2)),
            'thu_price':fields.related('pricing_id','thu_price',string='Thu',type='float',digits=(16, 2)),
            'thu_ffp_mu':fields.related('pricing_id','thu_ffp_mu',string='Thu FFP MU',type='float', digits=(16, 2)), 
            'thu_to_mu':fields.float('Thu Com.',digits=(16, 2)),
            'fri_price':fields.related('pricing_id','fri_price',string='Fri',type='float',digits=(16, 2)),
            'fri_ffp_mu':fields.related('pricing_id','fri_ffp_mu',string='Fri FFP MU',type='float', digits=(16, 2)), 
            'fri_to_mu':fields.float('Fri Com.',digits=(16, 2)),
            'sat_price':fields.related('pricing_id','sat_price',string='Sat',type='float',digits=(16, 2)),
            'sat_ffp_mu':fields.related('pricing_id','sat_ffp_mu',string='Sat FFP MU',type='float', digits=(16, 2)), 
            'sat_to_mu':fields.float('Sat Com.',digits=(16, 2)),
            'sun_price':fields.related('pricing_id','sun_price',string='Sun',type='float',digits=(16, 2)),
            'sun_ffp_mu':fields.related('pricing_id','sun_ffp_mu',string='Sun FFP MU',type='float', digits=(16, 2)), 
            'sun_to_mu':fields.float('Sun Com.',digits=(16, 2)),
            'active':fields.related('pricing_id','active',string='Active',type='boolean'),
            'pricing_id':fields.many2one('cc.menu.pricing','pricing'),
            'op_markup_id':fields.many2one('cc.operator.markup','Markup'),
            'mon_total': fields.function(_get_total, type='float',string='Total',multi='total'),
            'tue_total': fields.function(_get_total, type='float',string='Total',multi='total'),
            'wed_total': fields.function(_get_total, type='float',string='Total',multi='total'),
            'thu_total': fields.function(_get_total, type='float',string='Total',multi='total'),
            'fri_total': fields.function(_get_total, type='float',string='Total',multi='total'),
            'sat_total': fields.function(_get_total, type='float',string='Total',multi='total'),
            'sun_total': fields.function(_get_total, type='float',string='Total',multi='total'),
         }
    
cc_markup()

class cc_tube_station(osv.osv):    
    _name='cc.tube.station'
    _columns={'name':fields.char('Tube Station',size=128,required=True)}        
cc_tube_station() 

class login_time_tracking(osv.osv):
    _name='login.time.tracking'
    
    def _get_time(self, cr, uid, ids, fieldnames, args, context=None):
        result = {}
        lead_obj = self.pool.get('crm.lead')        
        for case in self.browse(cr, uid, ids, context=context):
            delta = ''
            if case.login and case.logout:
               a = datetime.strptime(case.login,"%Y-%m-%d %H:%M:%S")
               b = datetime.strptime(case.logout,"%Y-%m-%d %H:%M:%S")
               delta = b - a

            #To Get the previous record logout
            cr.execute("""select logout from login_time_tracking
                          where name = %s
                          and logout <= %s
                          order by logout desc limit 1""",(case.name.id, case.login))
            logout = cr.fetchone()
            if logout:
               lead_ids = lead_obj.search(cr, uid, [('sales_person','=',case.name.id),('create_date','>=',logout[0] or case.login),('create_date','<=',case.logout),('state','in',['open','done'])])
            else:
               lead_ids = lead_obj.search(cr, uid, [('sales_person','=',case.name.id),('create_date','<=',case.logout),('state','in',['open','done'])])
            result[case.id] = {'duration':str(delta),
                               'enquiries' : len(lead_ids)}
        return result

    _columns={'name':fields.many2one('res.users','Users'),
              'login' : fields.datetime('Login'),
              'logout' : fields.datetime('Logout'),
              'duration':fields.function(_get_time, type='char', size=128,string='Session Time',multi='total'),
              'enquiries':fields.function(_get_time, type='integer',string='Bookings',multi='total'),
              'partner_name': fields.related('name', 'partner_id', 'display_name', type="char", size=250, string="Partner", store=True),
              }
    
    _order = "id desc"
login_time_tracking()

class email_template(osv.osv):
    _inherit='email.template'
    
    def send_mail(self, cr, uid, template_id, res_id, force_send=False, raise_exception=False, context=None):
        """Generates a new mail message for the given template and record,
           and schedules it for delivery through the ``mail`` module's scheduler.

           :param int template_id: id of the template to render
           :param int res_id: id of the record to render the template with
                              (model is taken from the template)
           :param bool force_send: if True, the generated mail.message is
                immediately sent after being created, as if the scheduler
                was executed for this message only.
           :returns: id of the mail.message that was created
        """
        if context is None:
            context = {}
        mail_mail = self.pool.get('mail.mail')
        ir_attachment = self.pool.get('ir.attachment')

        # create a mail_mail based on values, without attachments
        values = self.generate_email(cr, uid, template_id, res_id, context=context)
        h = False
        
        try:
            h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
        except:
               pass 
        
        if h != 'www.choicedining.co.uk' and 'create_user' in context:
           values['attachment_ids'] = [] 
        if not values.get('email_from'):
            raise osv.except_osv(_('Warning!'),_("Sender email is missing or empty after template rendering. Specify one to deliver your message"))
        # process partner_to field that is a comma separated list of partner_ids -> recipient_ids
        # NOTE: only usable if force_send is True, because otherwise the value is
        # not stored on the mail_mail, and therefore lost -> fixed in v8
        values['recipient_ids'] = []
        partner_to = values.pop('partner_to', '')
        print 'partner_to',partner_to
        if partner_to:
            # placeholders could generate '', 3, 2 due to some empty field values
            tpl_partner_ids = [pid for pid in partner_to.split(',') if pid]
            values['recipient_ids'] += [(4, pid) for pid in self.pool['res.partner'].exists(cr, SUPERUSER_ID, tpl_partner_ids, context=context)]
        print 'recipient_ids',values
        attachment_ids = values.pop('attachment_ids', [])
        attachments = values.pop('attachments', [])
        msg_id = mail_mail.create(cr, uid, values, context=context)
        mail = mail_mail.browse(cr, uid, msg_id, context=context)

        # manage attachments
        for attachment in attachments:
            attachment_data = {
                'name': attachment[0],
                'datas_fname': attachment[0],
                'datas': attachment[1],
                'res_model': 'mail.message',
                'res_id': mail.mail_message_id.id,
            }
            context.pop('default_type', None)
            attachment_ids.append(ir_attachment.create(cr, uid, attachment_data, context=context))
        if attachment_ids:
            values['attachment_ids'] = [(6, 0, attachment_ids)]
            mail_mail.write(cr, uid, msg_id, {'attachment_ids': [(6, 0, attachment_ids)]}, context=context)

        if force_send:
            mail_mail.send(cr, uid, [msg_id], raise_exception=raise_exception, context=context)
        return msg_id
    
    def generate_email_batch(self, cr, uid, template_id, res_ids, context=None, fields=None):
        """Generates an email from the template for given the given model based on
        records given by res_ids.

        :param template_id: id of the template to render.
        :param res_id: id of the record to use for rendering the template (model
                       is taken from template definition)
        :returns: a dict containing all relevant fields for creating a new
                  mail.mail entry, with one extra key ``attachments``, in the
                  format expected by :py:meth:`mail_thread.message_post`.
        """
        if context is None:
            context = {}
        if fields is None:
            fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to']

        report_xml_pool = self.pool.get('ir.actions.report.xml')
        res_ids_to_templates = self.get_email_template_batch(cr, uid, template_id, res_ids, context)

        # templates: res_id -> template; template -> res_ids
        templates_to_res_ids = {}
        for res_id, template in res_ids_to_templates.iteritems():
            templates_to_res_ids.setdefault(template, []).append(res_id)

        results = dict()
        for template, template_res_ids in templates_to_res_ids.iteritems():
            # generate fields value for all res_ids linked to the current template
            for field in ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to']:
                generated_field_values = self.render_template_batch(cr, uid, getattr(template, field), template.model, template_res_ids, context=context)
                for res_id, field_value in generated_field_values.iteritems():
                    results.setdefault(res_id, dict())[field] = field_value
            # update values for all res_ids
            for res_id in template_res_ids:
                values = results[res_id]
                if template.user_signature:
                    signature = self.pool.get('res.users').browse(cr, uid, uid, context).signature
                    values['body_html'] = tools.append_content_to_html(values['body_html'], signature)
                if values['body_html']:
                    values['body'] = tools.html_sanitize(values['body_html'])
                values.update(
                    mail_server_id=template.mail_server_id.id or False,
                    auto_delete=template.auto_delete,
                    model=template.model,
                    res_id=res_id or False,
                    attachment_ids=[attach.id for attach in template.attachment_ids],
                )

            # Add report in attachments: generate once for all template_res_ids
            if template.report_template:
                for res_id in template_res_ids:
                    attachments = []
                    report_name = self.render_template(cr, uid, template.report_name, template.model, res_id, context=context)
                    report_service = report_xml_pool.browse(cr, uid, template.report_template.id, context).report_name
                    # Ensure report is rendered using template's language
                    ctx = context.copy()
                    if template.lang:
                        ctx['lang'] = self.render_template_batch(cr, uid, template.lang, template.model, [res_id], context)[res_id]  # take 0 ?
#                     result, format = openerp.report.render_report(cr, uid, [res_id], report_service, {'model': template.model}, ctx)
                    rep_obj = self.pool.get('ir.actions.report.xml')
                    report_name = 'daily_bkng_rpt'
                    rep_data = rep_obj.pentaho_report_action(cr, uid, report_name, res_id,None,None)
                    report_instance = openerp.addons.pentaho_reports.core.Report('report.' + report_name, cr, uid, res_id, rep_data['datas'], context)
                    result, format = report_instance.execute()   
                    result = base64.b64encode(result)
                    if not report_name:
                        report_name = 'report.' + report_service
                    ext = ".xls" 
                    if not report_name.endswith(ext):
                        report_name += ext
                    attachments.append((report_name, result))
                    results[res_id]['attachments'] = attachments
                    print 'results',results

        return results

email_template()    

class cc_group_details(osv.osv):
    _name = 'cc.group.details'
    
    def _get_default_currency(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        print 'currency',user and user.company_id and user.company_id.currency_id and user.company_id.currency_id.id or False
        return user and user.company_id and user.company_id.currency_id and user.company_id.currency_id.id or False
    
    _columns = {'name':fields.char('Name',size=200),
                'location':fields.char('Location',size=200),
                'image1' : fields.binary('Image'),
                'image2' : fields.binary('Image'),
                'image3' : fields.binary('Image'),
                'image4' : fields.binary('Image'),
                'image5' : fields.binary('Image'),
                'description' : fields.text('Description'),
                'st_price':fields.float('Start Price'),
                'ed_price':fields.float('End Price'),
                'type'    : fields.selection([('std','Standard'),('vip','VIP')],'Type'),
                'active'  : fields.boolean('Active'),
                'category_id': fields.many2many('res.partner.category', id1='cdgroups_id', id2='category_id', string='Tags'),
                'toperator_id': fields.many2many('res.partner', id1='cdtoperator_ids', id2='toperator_id', string='Tour Operator'),
                'currency_id':fields.many2one('res.currency','Currency'),
                'heading_1'     : fields.char('Heading 1'),
                'heading_2'     : fields.char('Heading 2'),
                'heading_3'     : fields.char('Heading 3'),
                'heading_4'     : fields.char('Heading 4'),
                'desc_1'        : fields.text('Description 1'),
                'desc_2'        : fields.text('Description 2'),
                'desc_3'        : fields.text('Description 3'),
                'desc_4'        : fields.text('Description 4'),
                }
    _defaults={'active':True,
               'currency_id' : _get_default_currency}
    
    def create(self, cr, uid, vals, context):
        if vals is None: vals = {}
        
        if 'image1' in vals:
           vals['image1'] = tools.image_resize_image_medium(vals['image1'],(640,480) ,'base64', 'PNG', True)
        if 'image2' in vals:
           vals['image2'] = tools.image_resize_image_medium(vals['image2'],(640,480) ,'base64', 'PNG', True)
        if 'image3' in vals:
           vals['image3'] = tools.image_resize_image_medium(vals['image3'],(640,480) ,'base64', 'PNG', True)
        if 'image4' in vals:
           vals['image4'] = tools.image_resize_image_medium(vals['image4'],(640,480) ,'base64', 'PNG', True)
        if 'image5' in vals:
           vals['image5'] = tools.image_resize_image_medium(vals['image5'],(640,480) ,'base64', 'PNG', True)
        
        return super(cc_group_details,self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context):
        if vals is None: vals = {}
        
        if 'image1' in vals:
           vals['image1'] = tools.image_resize_image_medium(vals['image1'],(640,480) ,'base64', 'PNG', True)
        if 'image2' in vals:
           vals['image2'] = tools.image_resize_image_medium(vals['image2'],(640,480) ,'base64', 'PNG', True)
        if 'image3' in vals:
           vals['image3'] = tools.image_resize_image_medium(vals['image3'],(640,480) ,'base64', 'PNG', True)
        if 'image4' in vals:
           vals['image4'] = tools.image_resize_image_medium(vals['image4'],(640,480) ,'base64', 'PNG', True)
        if 'image5' in vals:
           vals['image5'] = tools.image_resize_image_medium(vals['image5'],(640,480) ,'base64', 'PNG', True)
        
        return super(cc_group_details,self).write(cr, uid, ids, vals, context)
    
cc_group_details()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
