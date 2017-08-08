from openerp.osv import fields, osv
from lxml import etree
import urllib2
from datetime import datetime, timedelta
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import logging
import openerp
import base64
import xmlrpclib
from openerp import pooler, tools
from openerp.tools.translate import _
from openerp.http import request
from openerp import SUPERUSER_ID
from openerp.tools import config
from dateutil.relativedelta import relativedelta 
host = str(config["xmlrpc_interface"])  or str("localhost"),
port = str(config["xmlrpc_port"])
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (host[0],port))


_logger = logging.getLogger(__name__)

def now(**kwargs):
    dt = datetime.now() + timedelta(**kwargs)
    return dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

#Overriden
ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id','location_id')   

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
           
        res = super(osv.osv,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        user_obj = self.pool.get('res.users')  
        user = user_obj.browse(cr, uid, uid)     
        doc = etree.XML(res['arch'])
   
        if view_type == 'form':
            nodes = doc.xpath("//sheet/group/group[1]/div[2]/div/field[@name='state_id']")
            for node in nodes:
                node.set('placeholder', 'County')
            nodes = doc.xpath("//sheet/group/group[1]/div[2]/div/field[@name='zip']")
            for node in nodes:
                node.set('placeholder', 'Post Code')
       
            nodes = doc.xpath("//notebook/page[@string='Accounting']")
            for node in nodes:
               node.set('attrs', '{}') 
               node.set('invisible', '1')
            
#             nodes = doc.xpath("//page[@string='Drinks']/field[@name='drink_ids']")
#             for node in nodes:
#                node.set('domain', "[('cc_group','!=',False),('food_type','=','drink')]") 
            #Controlling form based on User Roles   
            if user.role == 'client':
               if 'partner_type' in context and context.get('partner_type') == 'venue':
                  nodes = doc.xpath("//form[@string='Partners']")
                  for node in nodes:
                      node.set('edit', 'false')
#             if context.get('partner_type') == 'venue':
#                 nodes = doc.xpath("//field[@name='contact_ids']")
#                 for node in nodes:
#                     node.set('domain', "[('parent_id','=',parent_id),('type','=','contact')]")
            res['arch'] = etree.tostring(doc)             
        return res
    
    #Used hide/display Alert Msg    
    def _is_form_filled(self, cr, uid, ids, name, arg, context=None): 
        
        res = {}
        for partner in self.browse(cr, uid, ids, context):
            res[partner.id] = bool(partner.street or False) and bool(partner.street2 or False) and bool(partner.city or False) and bool(partner.state_id or False)\
                              and bool(partner.country_id or False) and bool(partner.mobile or False) and bool(partner.email or False)\
                              and bool(partner.zip or False) 
        return res
 
    def _check_roles(self, cr, uid, ids, name, arg, context=None): 
        
        res = {}
        usr_obj = self.pool.get('res.users')
        user = usr_obj.browse(cr,uid,uid)
        for case in self.browse(cr, uid, ids, context):
            if user.role == 'client':
               if 'partner_type' in context and context.get('partner_type') == 'venue':
                   res[case.id] = True
            else:
                res[case.id] = False 
        return res
    
    def default_check(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr,uid,uid)
        if user.role == 'client':
           if 'partner_type' in context and context.get('partner_type') == 'venue':
              return True
        return False

    def get_cancel_hrs(self, cr, uid, context=None):
        if context is None:
            context = {}
        fit = context.get('default_cc_fit',False)
        p_type = context.get('default_partner_type','')
        if fit and p_type == 'venue':
           return 36
        return 0 
    
    def get_booking_hrs(self, cr, uid, context=None):
        if context is None:
            context = {}
        fit = context.get('default_cc_fit',False)
        p_type = context.get('default_partner_type','')
        if fit and p_type == 'venue':
           return 24
        return 0 
        
    def _opportunity_meeting_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,{'opportunity_count': 0, 'meeting_count': 0}), ids))
        # the user may not have access rights for opportunities or meetings
        try:
            for partner in self.browse(cr, uid, ids, context):
                enq_count = meet_count = 0 
                for ch in partner.child_ids:
                    enq_count += len(ch.opportunity_ids)
                    meet_count += len(ch.meeting_ids)
                res[partner.id] = {
                    'opportunity_count': len(partner.opportunity_ids) + enq_count,
                    'meeting_count': len(partner.meeting_ids) + meet_count,
                }            
        except:
            pass
        return res
    
    def _get_display_image(self, cr, uid, ids, field_name, arg, context=None):
        print 'called display image'
        res= {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = tools.image_resize_image_medium(case.image,(300,151) ,'base64', 'PNG', True) 
        return res
    
    def _get_enquiries(self, cr, uid, ids, name, arg, context=None):
        print 'called _get_enquiries'
        res = {}
        info_obj = self.pool.get('cc.send.rest.info')        
        for case in self.browse(cr, uid, ids, context):
            info_ids = []
            cr.execute("""select info.id 
                      from cc_send_rest_info info 
                      inner join crm_lead l on l.id = info.lead_id
                      where l.state = 'draft' and l.date_requested::date > '""" + str(time.strftime("%Y-%m-%d")) +"""'
                      and l.partner_id = """ + str(case.parent_id and case.parent_id.id or case.id ))
            info = cr.fetchall()
            for i in info:
                info_ids.append(i[0]) 
                
            res[case.id] = info_ids
             
        return res  
    
    def _get_invoices(self, cr, uid, ids, name, arg, context=None):
        print 'called _get_invoices'
        res = {}
        inv_obj = self.pool.get('account.invoice')        
        for case in self.browse(cr, uid, ids, context):
            acc_inv_ids = inv_obj.search(cr,uid,[('partner_id','=',case.id),('state','=','open'),('passen_type','=','fit')])
            res[case.id] = acc_inv_ids
             
        return res 
    
#     def _get_whitelabeled_url(self, cr, uid, ids, name, arg, context=None):
#         res = {}
#         for case in self.browse(cr, uid, ids, context):            
#             res[case.id] = ''
#             
#             if case.partner_type == 'client':                        
#                 cr.execute("""select wlabel_url 
#                               from res_users ru 
#                               inner join res_partner rp on rp.id = ru.partner_id 
#                               where (rp.parent_id = %s or rp.id = %s) 
#                               and wlabel_url is not null""",(case.id,case.id))
#                 wb = cr.fetchone()
#                 if wb:                
#                       res[case.id] = wb[0]
#         return res
    
    _columns = {#Overriden:
                'type'            : fields.selection([('default', 'Restaurant'),('invoice', 'Invoice'),
                                                      ('contact', 'Contact')], 'Address Type',
                                                     help="Used to select automatically the right address according to the context in sales and purchases documents."),
                
                'opportunity_ids' : fields.one2many('crm.lead', 'partner_id',\
                                                   'Leads and Opportunities'),
                'opportunity_count': fields.function(_opportunity_meeting_count, string="Opportunity", type='integer', multi='opp_meet'),
                'meeting_count'   : fields.function(_opportunity_meeting_count, string="# Meetings", type='integer', multi='opp_meet'),
                'child_ids': fields.one2many('res.partner', 'parent_id', 'Contacts'), # force "active_test" domain to bypass _search() override

                #new
                'enquiry_ids'     : fields.function(_get_enquiries, type='one2many', relation='cc.send.rest.info', string='Enquiry'),
                'invoice_ids'     : fields.function(_get_invoices, type='one2many', relation='account.invoice', string='Invoice'),
                'city_id'         : fields.many2one('cc.city','City'),
                'location_id'     : fields.many2one('cc.location','Location'),
                'tstation_id'     : fields.many2one('cc.tube.station','Tube Station'),
                'is_afternoontea' : fields.boolean('Afternoon Tea'),
                'preferred_venue' : fields.boolean('Preferred Venue'),
                'servc_chrg'      : fields.boolean('Tax On Service Charge'),
                'cc_fit'          : fields.boolean('Fit'),
                'cc_group'        : fields.boolean('Group'), 
                'accept_tc'       : fields.boolean('I Accept Terms&Conditions'),
                'show_in_homepage'       : fields.boolean('Show In Homepage'),
                
                
                'cuisine_ids'     : fields.many2many('cc.cuisine','cuisine_part_rel','partner_id','cuisine_id','Cuisine'),
                'no_of_covers'    : fields.integer('Total No. of Covers(exclusive hire)',size=30),
                'sequence'        : fields.integer('Sequence',size=10),
                'main_covers'     : fields.char('No. of Main Restaurant Covers',size=50),
                'room_covers'     : fields.char('No. of Private Room Covers',size=50),
                'semi_covers'     : fields.char('No. of Sep.Areas/Semi Private Covers',size=50),
                'share'           : fields.char('Share',size=10),                
                'phone2'          : fields.char('Phone2',size=64),
                'email2'          : fields.char('Email2',size=30),
                'cont_name'       : fields.char('Contact Name' ,size=35),
#                 'contact_id'      : fields.many2one('res.partner','Contact Name'),
#                 'inv_contact_id'  : fields.many2one('res.partner','Contact Name(Invoice)'), 
                'url_price'       : fields.char('URL for Prices',size=125),
                'company_reg_no'  : fields.char('Company Reg. No.',size=50),                
                'setup'           : fields.char('Section & Setup',size=75),
                'dining_style_ids'     : fields.many2many('cc.dining.style','dining_part_rel','partner_id','dining_id','Dining Style'),
                'dress_code'      : fields.char('Dress Code',size=75),
                'payment_opt'     : fields.char('Payment Options',size=75),
                'latitude'        : fields.char('Latitude',size=100),               #Latitude
                'longitude'       : fields.char('Longitude',size=100),             #Longitude
                'parking'         : fields.char('Parking',size=150),       
                 
                'commission'      : fields.float('Commission',digits=(16, 2)),
                'booking_limit'   : fields.float('Booking Limit',digits=(16, 2)), 
                'markup_perc'     : fields.float('Markup(for all restaurants)',digits=(16, 2)), 
                'menu_sc'         : fields.float('Service Charge (%)'),
                'menu_commsion'   : fields.float('Commission (%)'),    
                'sc_included'      : fields.boolean('Service Charge (Included)'),
                'cancellation_hrs': fields.integer('No. of hours for Cancellation'),
                'booking_hrs'     : fields.integer('No. of hours for Booking'),
                
                'is_filled'       : fields.function(_is_form_filled, type='boolean', string='Signup Token is Valid'),
                'check_role'      : fields.function(_check_roles, type='boolean', string='User Roles'),
#                 'wlabel_url'    : fields.function(_get_whitelabeled_url, string='White labeling URl', type='char',size=350),
                'partner_type'    : fields.selection([('client','Client'), ('venue','Venue'),('contact','Contact')]),
                
#                 'rest_type'     : fields.selection([('fit','FIT For Purpose'), ('group','Group')],'Passenger Type'),
                'private_rooms'   : fields.selection([('yes','Yes'),('no','No')],'Private Rooms'),
                'payment_type'    : fields.selection([('prepaid','Deposit'),('on_purchase','Payment on Purchase'),('monthly','Full Credit'),('pay_adv','Payment in Advance')],'Payment Type'),
                
                'descp_venue'     : fields.text('Description of Venue'),
                'features'        : fields.text('Outstanding Features'),
                'cancel_policy'   : fields.text('Cancellation Policy'),
                'terms_conditions': fields.text('Terms & Conditions'),
                'about_us'        : fields.text('About Us'),
                'privacy_policy'  : fields.text('Privacy Policy'),
                'additnal_details': fields.text('Additional Details'), 
                'rest_directions' : fields.text('Directions to Restaurant'),
                  
                'menus_ids'       : fields.one2many('cc.menus','partner_id','Menus', domain=['|',('active','=',False),('active','=',True),('food_type','=','meal'),('cc_group','=',True)]), 
                'fit_menu_ids'    : fields.one2many('cc.menus','partner_id','Menus',domain=['|',('active','=',False),('active','=',True),('food_type','=','meal'),('cc_fit','=',True)]), 
                'event_menu_ids'  : fields.one2many('cc.menus','partner_id','Events Menu',domain=['|',('active','=',False),('active','=',True),('food_type','=','events')]), 
                'drink_ids'       : fields.one2many('cc.menus','partner_id','Drinks',domain=['|',('active','=',False),('active','=',True),('food_type','=', 'drink'),('cc_fit','=',True)]),
                'grp_drink_ids'   : fields.one2many('cc.menus','partner_id','Drinks',domain=['|',('active','=',False),('active','=',True),('food_type','=', 'drink'),('cc_group','=',True)]),
                
                'open_hrs_ids'    : fields.one2many('cc.opening.hrs','partner_id','Opening Hours'),
                'rooms_ids'       : fields.one2many('cc.private.rooms','partner_id','Private Rooms'), 
                'time_alloc_ids'  : fields.one2many('cc.time.allocations','partner_id','Time & Allocations'),
                'blackout_ids'    : fields.one2many('cc.black.out.day','partner_id','Black Out'),
                'cc_company_id'   : fields.many2one('res.partner','Invoice Address'),     
                'addressed_email' : fields.char('Addressed In Email As',size=60),  
                'event_ids'       : fields.one2many('cc.events','partner_id','Events',domain=['|',('active','=',False),('active','=',True)]),     
                
                'max_covers'      : fields.integer('Max no. of covers per table'),     
                'display_image'   : fields.function(_get_display_image, string='Display Image', type='binary'), 
#                 'filter_drinks'   : fields.function(_get_drinks, string='Field to filter drinks', type) 
                'cc_image1'       : fields.binary('Image 1'),
                'cc_image2'       : fields.binary('Image 2'),
                'cc_image3'       : fields.binary('Image 3'),
                'cc_image4'       : fields.binary('Image 4'),
#                 'cc_image5'       : fields.binary('Image 5'),
                'desc_image1'     : fields.char('Image Description',size=125),
                'desc_image2'     : fields.char('Image Description',size=125),
                'desc_image3'     : fields.char('Image Description',size=125),
                'desc_image4'     : fields.char('Image Description',size=125),
                'desc_image5'     : fields.char('Image Description',size=125),       
                'work_dt_id'      : fields.many2one('work.detail','Work Detail'),    
                'location_ref'    : fields.text('Google Maps Location Ref'), 
#                  'place_id'        : fields.text('Google Maps Places id'), 
                'acc_name'        : fields.char('Account Name',size=125),
                'bank_name'       : fields.char('Bank Name',size=125),
                'branch_addrs'    : fields.char('Branch Address',size=125),
                'acc_no'          : fields.char('Account No.',size=125),
                'sort_code'       : fields.char('Sort Code',size=50),
                'swift'           : fields.char('Swift',size=125),
                'iban'            : fields.char('IBAN',size=125),
                'chaps'           : fields.char('CHAPS',size=125),     
                #Used to save contacts for restaurants,Used to save restaurants for TO
                'contact_ids'     : fields.many2many('res.partner','book_part_rel','partner_id','booking_id','Booking Contact',domain=['|',('active','=',True),('active','=',False)]),
                'inv_contact_ids' : fields.many2many('res.partner','inv_part_rel','partner_id','invoice_id','Invoice Contact'),                
                'op_mrkup_ids'    : fields.one2many('cc.operator.markup','partner_id','Markup',domain=[('mrkup_lvl', '=', 'menu_lvl')]),
                'rest_mrkup_ids'  : fields.one2many('cc.operator.markup','partner_id','Markup',domain=[('mrkup_lvl', '=', 'rest_lvl')]),
                'wbsite_color'    : fields.char('Primary Website Color',size=30),
                'submenu_color'   : fields.char('Submenu Website Color',size=30),
                'header_color'    : fields.char('Header Color',size=30),         
                'font_website'    : fields.char('Font Website',size=30),      
                'debit_charges'   : fields.float('Debit Card Charges (%)'),
                'credit_charges'  : fields.float('Credit Card Charges (%)'),      
                'comision_type'   : fields.selection([('markup','Markup'),('fixed_amt','Fixed Amount'),('fixed_perc','Fixed (%)')],'Commission Type'),
                'send_daily_rpt'  : fields.boolean('Send Daily Report'),
                'rpt_to'          : fields.char('Send Mail to',size=300,help='Enter email-ids here.'),     
                'remove_htls_to'  : fields.many2many('res.partner','venue_top_hide_rel','partner_id','top_id','Hide this venue from'),
                'show_htls_to'    : fields.many2many('res.partner','venue_top_show_rel','partner_id','top_id','Show this venue only to'),
                'top_rmd_opt'     : fields.boolean('Send Booking Reminders?'),

                'is_default'     : fields.boolean('Use Menus/Drinks From'),
                'parent_res_id'  : fields.many2one('res.partner','Menus/Drinks From'),
                'write_date'     : fields.datetime('Write Date', readonly=True,help="Date on which Restaurant is Modified."),
                
                        
                }
    
    _defaults={'private_rooms' : 'no',
               'check_role'    : default_check,
               'servc_chrg':True,
               'cancellation_hrs':get_cancel_hrs,
               'booking_hrs' : get_booking_hrs,
                'booking_limit':0.00,                
                'markup_perc':0.00,
                'sequence':9999,
                'debit_charges' : 1.2,
                'credit_charges' : 3.00,
                'comision_type'  : 'markup',
                'top_rmd_opt' : True,
                'max_covers'  : 2
}
    
    #Overriden    
    def onchange_type(self, cr, uid, ids, is_company, context=None):
        value = {}
        value['title'] = False
        if is_company:
            domain = {'title': [('domain', '=', 'partner')]}
            value['type'] = 'invoice'
        else:
            domain = {'title': [('domain', '=', 'contact')]}
            if context and context.get('default_partner_type') == 'venue':
               value['type'] = 'default'
        return {'value': value, 'domain': domain}

    
    #use to update child record partner type
    def onchange_address_type(self, cr, uid, ids, type, partner_type):
        res={}
        if type == 'contact':
           res['partner_type'] = 'contact'
        elif type != 'contact':
           res['partner_type'] = partner_type 
                       
        return {'value':res}
    
    def onchange_location(self, cr, uid, ids, location_id, context=None):
        if location_id:
            locat_obj = self.pool.get('cc.location')
            location = locat_obj.browse(cr, uid, location_id, context)
            city_id = location.city_id and location.city_id.id or False
            state_id = location.city_id and location.city_id.state_id and location.city_id.state_id.id or False
            zip = location.code or ''
            return {'value':{'city_id':city_id,'state_id':state_id,'zip':zip}}
        return {}
    
    def get_price(self, cr, uid, partner, context=None):
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid)
        operator = user.partner_id
        if user and user.role in ('client_user','client_mng','client_cust'):
           operator = user.partner_id.parent_id and user.partner_id.parent_id or 0
           
        if operator:
            cr.execute(""" select  y.rest_id
                                 , least( y.min_mon_price
                                         ,y.min_tue_price
                                         ,y.min_wed_price
                                         ,y.min_thu_price
                                         ,y.min_fri_price
                                         ,y.min_sat_price
                                         ,y.min_sun_price) as min_price
                                 , greatest( y.max_mon_price
                                            ,y.max_tue_price
                                            ,y.max_wed_price
                                            ,y.max_thu_price
                                            ,y.max_fri_price
                                            ,y.max_sat_price
                                            ,y.max_sun_price) as max_price 
                           from
                           (
                            select x.rest_id
                                  ,max(x.mon_price) as max_mon_price 
                                  ,min(x.mon_price) as min_mon_price 
                                  ,max(x.tue_price) as max_tue_price 
                                  ,min(x.tue_price) as min_tue_price 
                                  ,max(x.wed_price) as max_wed_price 
                                  ,min(x.wed_price) as min_wed_price 
                                  ,max(x.thu_price) as max_thu_price 
                                  ,min(x.thu_price) as min_thu_price 
                                  ,max(x.fri_price) as max_fri_price 
                                  ,min(x.fri_price) as min_fri_price 
                                  ,max(x.sat_price) as max_sat_price 
                                  ,min(x.sat_price) as min_sat_price 
                                  ,max(x.sun_price) as max_sun_price 
                                  ,min(x.sun_price) as min_sun_price 
                            from
                            (
                                select a.rest_id
                                      ,sum(case when a.menu_mrkup is not null then round((a.mon_price * a.menu_mrkup),1) + a.mon_price 
                                           else case when a.rest_mrkup is not null then round((a.mon_price * a.rest_mrkup),1) + a.mon_price
                                           else round((a.mon_price * a.glb_mrkup),1) + a.mon_price end end) as mon_price
                                      ,sum(case when a.menu_mrkup is not null then round((a.tue_price * a.menu_mrkup),1) + a.tue_price 
                                           else case when a.rest_mrkup is not null then round((a.tue_price * a.rest_mrkup),1) + a.tue_price
                                           else round((a.tue_price * a.glb_mrkup),1) + a.tue_price end end) as tue_price
                                      ,sum(case when a.menu_mrkup is not null then round((a.wed_price * a.menu_mrkup),1) + a.wed_price 
                                           else case when a.rest_mrkup is not null then round((a.wed_price * a.rest_mrkup),1) + a.wed_price
                                           else round((a.wed_price * a.glb_mrkup),1) + a.wed_price end end) as wed_price
                                      ,sum(case when a.menu_mrkup is not null then round((a.thu_price * a.menu_mrkup),1) + a.thu_price 
                                           else case when a.rest_mrkup is not null then round((a.thu_price * a.rest_mrkup),1) + a.thu_price
                                           else round((a.thu_price * a.glb_mrkup),1) + a.thu_price end end) as thu_price
                                     ,sum(case when a.menu_mrkup is not null then round((a.fri_price * a.menu_mrkup),1) + a.fri_price 
                                          else case when a.rest_mrkup is not null then round((a.fri_price * a.rest_mrkup),1) + a.fri_price
                                          else round((a.fri_price * a.glb_mrkup),1) + a.fri_price end end) as fri_price
                                     ,sum(case when a.menu_mrkup is not null then round((a.sat_price * a.menu_mrkup),1) + a.sat_price 
                                          else case when a.rest_mrkup is not null then round((a.sat_price * a.rest_mrkup),1) + a.sat_price
                                          else round((a.sat_price * a.glb_mrkup),1) + a.sat_price end end) as sat_price
                                     ,sum(case when a.menu_mrkup is not null then round((a.sun_price * a.menu_mrkup),1) + a.sun_price 
                                          else case when a.rest_mrkup is not null then round((a.sun_price * a.rest_mrkup),1) + a.sun_price
                                          else round((a.sun_price * a.glb_mrkup),1) + a.sun_price end end) as sun_price
                                from
                                (    
                                    select rp.id as rest_id
                                          ,pr.id as pricing_id
                                          ,cm.id as menu_id
                                          ,case when pr.mon_total = 0 then null else pr.mon_total end  as mon_price 
                                          ,case when pr.tue_total = 0 then null else pr.tue_total end  as tue_price 
                                          ,case when pr.wed_total = 0 then null else pr.wed_total end  as wed_price 
                                          ,case when pr.thu_total = 0 then null else pr.thu_total end  as thu_price 
                                          ,case when pr.fri_total = 0 then null else pr.fri_total end  as fri_price 
                                          ,case when pr.sat_total = 0 then null else pr.sat_total end  as sat_price 
                                          ,case when pr.sun_total = 0 then null else pr.sun_total end  as sun_price 
                                          ,(select (case when '""" + str(operator.comision_type) + """' = 'markup' then (om.markup_perc/100) else 0 end) as menu_mrkup
                                            from rel_om_menu rom
                                            inner join cc_operator_markup om on om.id = rom.omarkup_id
                                            where om.partner_id = """ +str(operator.id)+""" and restaurant_id = rp.id and rom.menu_id = cm.id) as menu_mrkup
                                          ,(select (case when '""" + str(operator.comision_type) + """' = 'markup' then (markup_perc/100) else 0 end) from cc_operator_markup where partner_id = """ +str(operator.id)+""" and restaurant_id = rp.id and mrkup_lvl = 'rest_lvl') as rest_mrkup
                                          ,(select (case when '"""  + str(operator.comision_type) + """' = 'markup' then (markup_perc/100) else 0 end) from res_partner where id = """ +str(operator.id)+""") as glb_mrkup
                                    from res_partner rp             
                                    inner join cc_menus cm on cm.partner_id = rp.id
                                    inner join cc_menu_pricing pr on pr.menu_id = cm.id 
                                    where rp.active = True         
                                    and rp.type = 'default' and rp.partner_type = 'venue'
                                    and rp.cc_fit = True
                                    and pr.active = True
                                    and cm.active = True and cm.kids_menu != True 
                                    and cm.food_type ='meal'
                                    order by rp.id,cm.id,pr.id
                                     
                                )a 
                                group by a.rest_id,a.pricing_id
                                order by a.rest_id
                            )x group by x.rest_id
                        )y""")
            
            return cr.dictfetchall()    
        
        return [] 
    
    #Overriden
    def _address_fields(self, cr, uid, context=None):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set. """
        return list(ADDRESS_FIELDS)
    
    #Overriden
    def _display_address(self, cr, uid, address, without_company=False, context=None):
            
        # get the information that will be injected into the display format
        # get the address format
        address_format = address.country_id and address.country_id.address_format or \
              "%(street)s\n%(street2)s %(location)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'country_code': address.country_id and address.country_id.code or '',
            'country_name': address.country_id and address.country_id.name or '',
            'company_name': address.parent_id and address.parent_id.name or '',
            'city'        :address.city or '',
            'location'    :address.location_id and address.location_id.name or '',
        }
        for field in self._address_fields(cr, uid, context=context):
            args[field] = getattr(address, field) or ''
        if without_company:
            args['company_name'] = ''
        elif address.parent_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    
    def onchange_ccparent_id(self, cr, uid, ids,parent_id, context=None):
        if context is None:
           context ={}
        res ={}       
        ptype = context.get('default_partner_type','')
        if ptype == 'venue':
            if parent_id:
               res.update({'type':'default'})
            else:
               res.update({'type':'invoice'}) 
        return {'value':res}
    
    def _Send_daily_detail_rpt(self, cr, uid, automatic=False, use_new_cursor=False, context=None):       
#     def Send_daily_detail_rpt(self, cr, uid, ids, context=None):        
        mail_tmp_obj = self.pool.get('email.template')
        mod_obj = self.pool.get('ir.model.data')
        email_obj = self.pool.get('email.template')
        mail_msg = self.pool.get('mail.message')
        users_obj = self.pool.get('res.users')
        remind_obj = self.pool.get('cc.reminder.time')
        rep_obj = self.pool.get('ir.actions.report.xml') 
        Today = time.strftime("%Y-%m-%d")
        USERPASS = users_obj.browse(cr,uid,1).password
        part = self.search(cr, uid, [('send_daily_rpt','=', True),('rpt_to','!=',''),('partner_type','=','client')])
        msg_id = attach_ids = False
        for case in self.browse(cr, uid, part):
            cr.execute("""select id
                          from crm_lead c 
                          where create_date::date = '""" + str(Today) + """' 
                          and state in ('open','done') 
                          and c.partner_id = """ + str(case.id))
            if cr.fetchall():
               try:
                   template_id = mod_obj.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', 'daily_booking_details')[1] 
               except ValueError:
                   template_id = False
                    
               email_obj.send_mail(cr, uid, template_id, case.id, force_send=False, raise_exception=False, context=None)
              
        return True

    def mark_as_reconciled(self, cr, uid, ids, context=None):
        cr.execute("update res_partner set last_reconciliation_date=%s where id in %s",(time.strftime('%Y-%m-%d %H:%M:%S'),(tuple(ids), )))
        return True
        
    def create(self, cr, uid, vals, context=None):
        user_ids = False
        if context is None:
           context={}            
        if vals is None:vals={}        
        if context.get('frm_oprtor',False):
           vals['active'] = False
            
        if 'cc_image1' in vals:
           vals['cc_image1'] = tools.image_resize_image_medium(vals['cc_image1'],(640,480) ,'base64', 'PNG', True)
        if 'cc_image2' in vals:
           vals['cc_image2'] = tools.image_resize_image_medium(vals['cc_image2'],(640,480) ,'base64', 'PNG', True)
        if 'cc_image3' in vals:
           vals['cc_image3'] = tools.image_resize_image_medium(vals['cc_image3'],(640,480) ,'base64', 'PNG', True)
        if 'cc_image4' in vals:
           vals['cc_image4'] = tools.image_resize_image_medium(vals['cc_image4'],(640,480) ,'base64', 'PNG', True)
               
        res = super(res_partner,self).create(cr, uid, vals, context)
        case = self.browse(cr,uid,res)
        
        chkwhich = context.get('chkwhich','')
        if 'active' in vals and chkwhich == 'partner':
            if case.parent_id and not case.parent_id.active:
               cr.execute("update res_partner set active = True where id = %s",(case.parent_id.id)) 
                
            user_ids = self.pool.get('res.users').search(cr,uid,['|',('active','=',True),('active','=',False),('partner_id','=',res)])
            self.pool.get('res.users').write(cr,uid,user_ids,{'active':vals['active']})
            if vals['active'] and user_ids:                 
               from openerp.addons.base.ir.ir_mail_server import MailDeliveryException
               try:
                   self.pool.get('res.users').action_reset_password(cr, uid, user_ids, context.update({'create_user':True}))               
               except MailDeliveryException:
                   pass    
        if case.partner_type == 'venue' and case.cc_fit:
            alloc_ids = []                  
            allocation_obj = self.pool.get('cc.time.allocations') 
            for type in ['break_fast','lunch','dinner','at']:
                for name in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']: 
                    alloc_ids.append(allocation_obj.create(cr,uid,{'type':type,
                                                                   'name':name,
                                                                   'partner_id':case.id,})) 
        
        if res:
           menu_obj = self.pool.get('cc.menus')
           menu_ids = menu_obj.search(cr, uid, ['|',('active','=',True),('active','=',False),('partner_id', '=', res),('cc_group','=', True)])
           for m in menu_obj.browse(cr, uid, menu_ids):
               menu_obj.write(cr, uid, [m.id], {})                                            
        return res
        
    def write(self, cr, uid, ids, vals, context=None):
        print 'partner ids',ids
        if context is None:context={}
        if vals is None:vals={}
        context1 = context.copy()       
        param_obj = self.pool.get("ir.config_parameter")
        user_ids = False   
        #Resize image
        if 'cc_image1' in vals:
           vals['cc_image1'] = tools.image_resize_image_medium(vals['cc_image1'],(640,480) ,'base64', 'PNG', True)
        if 'cc_image2' in vals:
           vals['cc_image2'] = tools.image_resize_image_medium(vals['cc_image2'],(640,480) ,'base64', 'PNG', True)
        if 'cc_image3' in vals:
           vals['cc_image3'] = tools.image_resize_image_medium(vals['cc_image3'],(640,480) ,'base64', 'PNG', True)
        if 'cc_image4' in vals:
           vals['cc_image4'] = tools.image_resize_image_medium(vals['cc_image4'],(640,480) ,'base64', 'PNG', True)
        
        chkwhich = context.get('chkwhich','')
        if 'active' in vals and chkwhich == 'partner':
           case = self.browse(cr, uid , ids[0]) 
           cr.execute("update res_users set active = %s where partner_id = %s",(vals['active'],case.id))
           if case.parent_id and not case.parent_id.active:
              cr.execute("update res_partner set active = %s where id = %s",(vals['active'],case.parent_id.id))
           elif not case.parent_id:
               partner_ids = self.search(cr, uid, ['|',('active','=',True),('active','=',False),('parent_id','=',case.id),('partner_type','=','contact')])
               if partner_ids:
                  cr.execute('update res_partner set active = %s where id in %s',(vals['active'],tuple(partner_ids),))   
                  cr.execute('update res_users set active = %s where partner_id in %s',(vals['active'],tuple(partner_ids),))                  
                  cr.execute('select id from res_users where partner_id in %s',(tuple(partner_ids),))
                  user_ids = [x[0] for x in cr.fetchall()]
           if vals['active'] and user_ids:          
               context.update({'create_user':True})                
               from openerp.addons.base.ir.ir_mail_server import MailDeliveryException
               try:   
                   self.pool.get('res.users').action_reset_password(cr, uid, user_ids, context)
               except MailDeliveryException:
                   pass    
        res = super(res_partner,self).write(cr, uid, ids, vals, context)
        if res and ids:
           menu_obj = self.pool.get('cc.menus')
           menu_ids = menu_obj.search(cr, uid, ['|',('active','=',True),('active','=',False),('partner_id', '=', ids[0]),('cc_group','=', True)])
           for m in menu_obj.browse(cr, uid, menu_ids):
               menu_obj.write(cr, uid, [m.id], {}, context1)
        return res 
    
    def update_pricing(self, cr, uid, ids, context=None):
        pricing_obj = self.pool.get('cc.menu.pricing')
        pricing_ids = pricing_obj.search(cr,uid,[('menu_id.partner_id','=',ids[0])])
        if context is None:
           context = {}
        context.update({'mu_update':False})            
        for case in pricing_obj.browse(cr,uid,pricing_ids):
            vals={}
            sc_inc = case.menu_id.sc_included
            sc = case.menu_id.service_charge or 0.00
            sc_disc = case.menu_id.sc_disc
            vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'mon', case.mon_price, case.mon_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
            vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'tue', case.tue_price, case.tue_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
            vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'wed', case.wed_price, case.wed_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
            vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'thu', case.thu_price, case.thu_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
            vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'fri', case.fri_price, case.fri_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
            vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'sat', case.sat_price, case.sat_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
            vals.update(pricing_obj.onchange_pricing(cr, uid, ids, 'sun', case.sun_price, case.sun_ffp_mu, sc, sc_inc, sc_disc, context)['value'])
            pricing_obj.write(cr,uid,[case.id],vals,{})
        return True
            
            
                        
res_partner()

class res_users(osv.osv):
    
    _inherit='res.users'
    
    def _get_mycart_count(self, cr, uid, ids, name, arg, context=None):     
        res = {}
        for case in self.browse(cr, uid, ids, context):
            res[case.id] = {
                'mycart_count'  : 0,
                'to_count'      : 0,
            }
            operator = case.partner_id            
            if case.role in ('client_user','client_mng','client_cust'):
               operator = case.partner_id and case.partner_id.parent_id and case.partner_id.parent_id or False 
            cr.execute("""select count(info.id) 
                      from cc_send_rest_info info 
                      inner join crm_lead l on l.id = info.lead_id
                      where l.state = 'draft' and l.date_requested::date > '""" + str(time.strftime("%Y-%m-%d")) +"""'
                      and l.partner_id = """ + str(operator.id) + 
                      """ and l.sales_person=""" + str(case.id))
            mycart = cr.fetchone()
            res[case.id]['mycart_count'] = mycart and mycart[0]
            
            #In case of Public User
            if not request.httprequest.session.get('uid', False):
              lead_ids = request.httprequest.session.get('website_lead_id',[])
              res[case.id]['mycart_count'] = len(lead_ids) 
              
            # To count the TO's
            cr.execute("""select count(*) from cc_group_details cc
                            inner join cc_group_details_res_partner_rel cg on cg.cdtoperator_ids = cc.id
                            where toperator_id = """+str(operator.id)+""" and active = True
                        """)
            to_count = cr.fetchone()
            res[case.id]['to_count'] = to_count and to_count[0]
        
        return res
    
    def _is_whitelabeled(self, cr, uid, ids, name, arg, context=None):
        res = {}
        h = False
        try:
            h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
        except:
            pass 
        for case in self.browse(cr, uid, ids, context):
            res[case.id] = case.wlabel_url == h and True or False                        
            if case.role in ('client_user','client_mng','client_cust') and not res[case.id]:
               cr.execute("""select case when ru.id is null then False else True end as wb from res_users ru 
                             inner join  res_partner rp on rp.id = ru.partner_id 
                             where ru.wlabel_url = '""" + str(h) + """' 
                             and (case when ru.role = 'client' then rp.id = """ + str(case.partner_id.parent_id and case.partner_id.parent_id.id or 0) + """ else rp.parent_id = """ + str(case.partner_id.parent_id and case.partner_id.parent_id.id or 0) + """ end) """)
               wb = cr.fetchone()
               if wb:                
                  res[case.id] = True
        return res
    
    def _get_url(self, cr, uid, ids, name, arg, context=None):
        res = {}
        h = ''
        try:
            h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
        except:
            pass 
        for case in self.browse(cr, uid, ids, context):
            res[case.id] = h
        return res
    
    def _is_group_website(self, cr, uid, ids, name, arg, context=None):     
        res = {}
        h = request.httprequest.environ['HTTP_HOST'].split(':')[0]         
        for case in self.browse(cr, uid, ids, context):
            res[case.id] = False
            if h in ('www.groupcc.test'):
                res[case.id] = True                
        return res
    
    def _is_loggedin(self, cr, uid, ids, name, arg, context=None):     
        res = {}
        h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
        cr.execute("select distinct(name) from login_time_tracking where name in %s and logout is null",(tuple(ids),))
        result = [x[0] for x in cr.fetchall()]         
        for case in self.browse(cr, uid, ids, context):
            res[case.id] = False
            if case.id in result:
               res[case.id] = True               
        return res
    
    def _get_user_list(self, cr, uid, ids, name, arg, context=None):     
        res = {}
        usr_ids = self.search(cr, uid, [('role','in',['client','client_mng','client_user'])],order='display_name')         
        for case in self.browse(cr, uid, ids, context):
            res[case.id] = usr_ids              
        return res 
    
    _columns={              
              #Client & Venue Admin Level Access
              #Client Mng & Venue Mng Manager Level Access
              #Client User & Venue User User level Access 
              'role':fields.selection([('admin','Capital Centric Administrator'),('bo','Capital Centric Back Office'),('client','Client Admin'),('venue','Venue Admin'),('client_user','Client User'),('venue_user','Venue User'),('client_mng','Client Manager'),('venue_mng','Venue Manager'),('client_cust','Customer')],'Role'),
              'mycart_count'    : fields.function(_get_mycart_count, type='integer', string='My Cart Count',multi='count'),
              'to_count'        : fields.function(_get_mycart_count, type='integer', string='TO Count',multi='count'),   # To Check the TO in White Labeling
              'fav_rest_ids'    : fields.many2many('res.partner','fav_part_rel','user_id','fav_rest_id','Favourite Restaurant'),
              'api_key'         : fields.char('API Key',size=300),
              'wlabel_url'      : fields.char('White labeling URl',size = 300),
              'is_wlabeling'    : fields.function(_is_whitelabeled, string='White labeling URl', type='boolean'),
              'is_group'        : fields.function(_is_group_website, string='is Group Website?', type='boolean'),
              'is_login'        : fields.function(_is_loggedin , string='Is user Logged In?', type='boolean'),
              'prev_booking_id' : fields.many2one('crm.lead','Booking'),
              'create_date'     : fields.datetime('Create Date'),
              'emulation'       : fields.boolean('Emulation'),
              'usr_ids'         : fields.function(_get_user_list, type='one2many', relation='res.users', string='List of Users'),
              'cc_url'          : fields.function(_get_url, string='URL', type='char',size=500)
              }
    
    def _get_belongingGroups(self,cr, uid, belongto, context=None):
        data_obj = self.pool.get('ir.model.data') 
        result = super(res_users, self)._get_group(cr, uid, context)        
        try:
            if belongto == 'admin': 
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus_Capitalcentric', 'cc_object_admin')
                result.append(groupid)
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus_Capitalcentric', 'cc_admin')
                result.append(groupid)
                result.append(3)
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'account', 'group_account_manager')
                result.append(groupid)
            elif belongto == 'bo':
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus_Capitalcentric', 'cc_object_admin')
                result.append(groupid)
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus_Capitalcentric', 'cc_bo')
                result.append(groupid)
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'account', 'group_account_user')
                result.append(groupid)
            elif belongto in ('client','client_user','client_mng','client_cust'):
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus_Capitalcentric', 'cc_object_admin')
                result.append(groupid)
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus_Capitalcentric', 'cc_client')
                result.append(groupid)                
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'base', 'group_partner_manager')
                result.remove(groupid)

            elif belongto in ('venue','venue_user','venue_mng'):
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus_Capitalcentric', 'cc_object_admin')
                result.append(groupid)
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus_Capitalcentric', 'cc_venues')
                result.append(groupid)              
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'base', 'group_partner_manager')
                result.remove(groupid)
                                
        except ValueError:
            # If these groups does not exists anymore
            pass
        return result
    
    def genrate_APIKey(self, cr, uid, ids, context=None):
        import hashlib
        import random
        import base64
        import urllib
        import hmac
        
        encodedSignature = base64.b64encode(hashlib.sha256( str(random.getrandbits(256)) ).digest(), random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')
        print encodedSignature
        user_ids = self.search(cr,uid,[('api_key','=',encodedSignature)])
        if user_ids:
           self.genrate_APIKey(cr, uid, ids, context)
           return True 
        self.write(cr, uid, ids, {'api_key':encodedSignature})
        return True
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []        
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name or False    
            if context.get('show_user_email') and record.login:
                name = "%s <%s>" % (name, record.login)
            res.append((record.id, name))
        return res
    
    def create(self, cr, uid, values, context=None):
         
        vals={}
        data_obj = self.pool.get('ir.model.data') 
        res = super(res_users, self).create(cr, uid, values, context=context)
         
        usr_roles = ''        
         
#         if 'partner_type' in values and values['partner_type']:
#             usr_roles = vals['role'] = values['partner_type']            
                         
        if 'role' in values and values['role']: # Here we are checking the field 'usr_roels' adn value for 'usr_Roles' present
            usr_roles = vals['role'] = values['role']
         
        if usr_roles:   
            groupids = self._get_belongingGroups(cr, uid, usr_roles, context)
            for fl in groupids:
                vals['in_group_'+str(fl)] = True   
        
        if 'active' in vals:
           case = self.browse(cr,uid,res) 
           if case.partner_id.parent_id and not case.partner_id.parent_id.active:
              cr.execute("update res_partner set active = True where id = %s",(case.partner_id.parent_id.id)) 
           partner_ids = self.pool.get('res.partner').search(cr,uid,['|',('active','=',True),('active','=',False),('id','=',case.partner_id and case.partner_id.id or 0)])
           self.pool.get('res.partner').write(cr,uid,partner_ids,{'active':vals['active']})
        
        self.write(cr, uid, [res], vals, context)
         
        return res  
 
    def write(self,cr,uid,ids,vals,context=None):
        print 'user ids',ids
        if hasattr(ids, '__iter__'):
            for case in self.browse(cr,uid,ids,context=context):
                if 'role' in vals and vals['role']:
                    groupids = self._get_belongingGroups(cr, uid, case.role, context)
                    for fl in groupids:
                        vals['in_group_'+str(fl)] = False
                if 'role' in vals and vals['role']:
                    groupids = self._get_belongingGroups(cr, uid, vals['role'], context)
                    for fl in groupids:
                        vals['in_group_'+str(fl)] = True
            
                if 'active' in vals:
                    if case.partner_id.parent_id and not case.partner_id.parent_id.active:
                       cr.execute("update res_partner set active = True where id = " + str(case.partner_id.parent_id.id))
                    partner_ids = self.pool.get('res.partner').search(cr,uid,['|',('active','=',True),('active','=',False),('id','=',case.partner_id and case.partner_id.id or 0)])
                    self.pool.get('res.partner').write(cr,uid,partner_ids,{'active':vals['active']})
        return super(res_users, self).write(cr, uid, ids,vals, context=context)
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
           context = {}         
        
        if context.get('today'):
           date1 = datetime.strptime(time.strftime("%Y-%m-%d 18:30"), "%Y-%m-%d %H:%M") - relativedelta(days=1)
           args1 = ['|',('active','=',False),('active','=',True),('create_date','>=',date1.strftime("%Y-%m-%d %H:%M"))]    
           args = args1
        res = super(res_users, self).search(cr, uid, args, offset, limit, order, context, count)
        
        return res
res_users()

class res_company(osv.osv):
    _inherit='res.company'
    
    def update_google(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        venue_ids = partner_obj.search(cr, uid,[('partner_type','=','venue'),('type','=','default')],order='id')
        for case in partner_obj.browse(cr,uid, venue_ids):
            partner_obj.write(cr,uid,[case.id],{'latitude':case.latitude,'longitude':case.longitude,'name':case.name})
        return True
    
    def button_prpt_rml(self, cr, uid, ids, context=None):
        """
            To Call the Penthao Onchange Function by that not to check and uncheck everytime to update
        """
        result = {'value': {}}
        is_pentaho_report = True
        act_obj = self.pool['ir.actions.report.xml']
        prpt_ids = act_obj.search(cr,uid, [('is_pentaho_report', '=', True)], context=context)
        for prpt_id in act_obj.browse(cr,uid,prpt_ids):
            result = act_obj.onchange_is_pentaho( cr, uid, [prpt_id.id] or [], is_pentaho_report, context=None)['value']
            try:
                act_obj.write(cr,uid,prpt_id.id,result)
            except:
                pass
        return True

    _columns={

        'b_frm_id' : fields.many2one('cc.time','Breakfast From'),
        'b_to_id' : fields.many2one('cc.time','Breakfast To'),
        'l_frm_id' : fields.many2one('cc.time','Lunch From'),
        'l_to_id' : fields.many2one('cc.time','Lunch To'),
        'a_frm_id' : fields.many2one('cc.time','Afternoon Tea From'),
        'a_to_id' : fields.many2one('cc.time','Afternoon Tea To'),
        'd_frm_id' : fields.many2one('cc.time','Dinner From'),
        'd_to_id' : fields.many2one('cc.time','Dinner To'),
        'about_html' : fields.html('About Us'),
        'privacy_html' : fields.html('Privacy Policy'),
        'terms_html' : fields.html('Terms'),
        'help_html' : fields.html('Help'),
        'banner_ids'     : fields.one2many('tr.company.banner', 'company_id', 'Banner', copy=True),

    }
    
res_company()

class tr_company_banner(osv.osv):
    _name = 'tr.company.banner'
    _description = 'Banner'

    # def _get_image(self, cr, uid, ids, name, args, context=None):
    #     result = dict.fromkeys(ids, False)
    #     for obj in self.browse(cr, uid, ids, context=context):
    #         result[obj.id] = tools.image_get_resized_images(obj.image)
    #     return result
    #
    # def _set_image(self, cr, uid, id, name, value, args, context=None):
    #     return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)

    _columns = {
                 'company_id'     : fields.many2one('res.company', 'Company', ondelete='cascade'),
                 'image'        : fields.binary("Image",
                                     help="This field holds the image used as image for the cateogry, limited to 1024x1024px."),
                 # 'image_medium' : fields.function(_get_image, fnct_inv=_set_image,
                 #                     string="Medium-sized image", type="binary", multi="_get_image",
                 #                     store={
                 #                            'tr.company.banner': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
                 #                           },
                 #                     help="Medium-sized image of the category. It is automatically "\
                 #                             "resized as a 128x128px image, with aspect ratio preserved. "\
                 #                             "Use this field in form views or some kanban views."),
                 'img_alt_tag'  : fields.char('Image Alt Tag', size=300),
                }
tr_company_banner()