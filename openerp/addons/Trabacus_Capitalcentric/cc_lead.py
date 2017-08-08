# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, timedelta
from openerp.osv import fields
from lxml import etree
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from dateutil import parser
import re
from openerp.addons.crm import crm
import pytz
from dateutil.relativedelta import relativedelta
from openerp.tools import html2plaintext
from HTMLParser import HTMLParser
from openerp import netsvc
import logging
_logger = logging.getLogger(__name__)

Invoice_Type = [('to_client','To Client'),
                ('to_venue','To Venue(Only Commission)'),
                ('to_both','To Both(Commission&Purchase)')]

AVAILABLE_STATES = [
    ('draft', 'New'),
    ('cancel', 'Cancelled'),
    ('open', 'In Progress'),
    ('pending', 'Pending'),
    ('done', 'Closed')
]

class crm_case_stage(osv.osv):
    _inherit='crm.case.stage'
    _columns={'state': fields.selection(AVAILABLE_STATES, 'Related Status', required=True,
                                        help="The status of your document will automatically change regarding the selected stage. " \
                                        "For example, if a stage is related to the status 'Close', when your document reaches this stage, it is automatically closed."),
              'type': fields.selection([('lead','Lead'),
                                        ('opportunity', 'Opportunity'),
                                        ('venue','Venue'),
                                        ('noontea', 'Afternoon Tea'),
                                        ('both', 'Both')],
                                       string='Type', size=16, required=True,
                                       help="This field is used to distinguish stages related to Leads from stages related to Opportunities, or to specify stages available for both types."),
              }
crm_case_stage()
class crm_lead(osv.osv):
    _inherit = 'crm.lead'

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
            res = super(osv.osv,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #  Controlling Domain Filter for restaurant based on service typr
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                              
            doc = etree.XML(res['arch'])     
            user_obj = self.pool.get('res.users')
            user = user_obj.browse(cr, uid , uid)
            nodes = doc.xpath("//notebook/page[2]/group/group[1]/div/div/field[@name='state_id']")
            for node in nodes:
                node.set('placeholder', 'County')
            nodes = doc.xpath("//notebook/page[2]/group/group[1]/div/div/field[@name='zip']")
            for node in nodes:
                node.set('placeholder', 'Post Code')
            res['arch'] = etree.tostring(doc)
                           
            return res
        
    def _get_invoice(self, cr, uid, ids, name, arg, context=None):        
        res = {}
        inv_obj = self.pool.get('account.invoice')        
        for case in self.browse(cr, uid, ids, context):
            inv_ids = []
            cr.execute("select id from account_invoice where to_tsvector(origin) @@ to_tsquery('" + str(case.lead_no) + "');")
            invoice = cr.fetchall()
            for inv in invoice:
                inv_ids.append(inv[0]) 
                
            res[case.id] = inv_ids
             
        return res
   
    def _get_user(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        user = []        
        if context and 'service_type' in context and context.get('service_type','') == 'venue':
           user = user_obj.search(cr,uid,[('login','=','monnique')])
        elif context and 'service_type' in context and context.get('service_type','') == 'noontea':
           user = user_obj.search(cr,uid,[('login','=','vanessa')]) 
        return user and user[0] or False
     
    def _get_usr_roles(self, cr, uid, ids, name, arg, context=None): 
        
        res = {}
        usr_obj = self.pool.get('res.users')
        user = usr_obj.browse(cr,uid,uid)
        for case in self.browse(cr, uid, ids, context):
            res[case.id] = user.role or '' 
        return res
    
    def _get_restaurant(self, cr, uid, ids, name, arg, context=None): 
        
        res = {}
        send_info_obj = self.pool.get('cc.send.rest.info')
        for case in self.browse(cr, uid, ids, context):
            info = False
            info_ids = send_info_obj.search(cr,uid,[('lead_id','=',case.id)],order='id' ,limit=1)
            if info_ids:
               info = send_info_obj.browse(cr,uid,info_ids[0])                
            res[case.id] = info and info.restaurant_id and info.restaurant_id.id or False 
        return res

    def default_usr_roles(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr,uid,uid)
        return user.role or ''
     
    def _get_partner(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr,uid,uid)
        if user and user.role == 'client':
           return user.partner_id.id
        return False
    
    def _get_datetime(self, cr, uid, ids, field_names, args, context=None):
        res={}
        for case in self.browse(cr, uid,ids, context):
            res[case.id] = ''
            date_requested  = self.onchange_DOB(cr, uid, ids, case.date_requested, context=None)['value']
            if date_requested:
                time = date_requested.values()[0]
                date = date_requested.values()[1]
                cr.execute("update crm_lead set conv_dob ='" + str(date) +"',conv_tob='"+ str(time) +"' where id =" + str(case.id))
        return res
    
    def _get_inv_status(self, cr, uid, ids, field_names, args, context=None):
        res={}
        invoice_obj = self.pool.get('account.invoice.line')
        for case in self.browse(cr, uid,ids, context):
            res[case.id] = ''
            cr.execute(""" select distinct(ai.id),
                                  ai.state 
                           from account_invoice_line ail 
                           inner join account_invoice ai on ai.id = ail.invoice_id 
                           where ai.state in ('open','paid') and type = 'in_invoice'
                           and ail.lead_id = """ + str(case.id) + """ order by ai.id desc limit 1""")
            inv_status = cr.fetchone()
            if inv_status:
               res[case.id] = inv_status[1]
        return res
        
    _columns = {
                # Overridden:
                'name'           : fields.char('Description', size=64, required=True, select=1),
                'user_id'        : fields.many2one('res.users', 'BO User', select=True, track_visibility='onchange',domain="[('role','in',['admin','bo'])]"),
                'date_action'    : fields.date('Next Action Date', select=True,track_visibility='onchange'),
                'planned_revenue': fields.float('Expected Revenue',digits=(16, 2)),
                
                # New: 
                'state': fields.related('stage_id', 'state', type="selection", store=True,
                                        selection=AVAILABLE_STATES, string="Status", readonly=True,
                                        help='The Status is set to \'Draft\', when a case is created. If the case is in progress the Status is set to \'Open\'. When the case is over, the Status is set to \'Done\'. If the case needs to be reviewed then the Status is  set to \'Pending\'.'),

                'is_checked'    : fields.boolean('Is_Checked'),
                'send_confirmation' : fields.boolean('Send Guest Confirmation Mail'),  
                'is_cancelled'    : fields.boolean('IS Booking Cancelled?'),                
                'restrt_name'   : fields.char('Name of Restaurant',size=75),
                'area'          : fields.char('Area or Location',size=75),
                'cuisine'       : fields.char('Cuisine',size=75),
                'budget'        : fields.char('Budget Per Person',size=25),   
                'lead_no'       : fields.char('Enquiry No.',size=15), 
                'transaction_no': fields.char('Transaction No.',size=15),
                'event_type'    : fields.char('Type of Event',size=100),
                'reason_event'  : fields.char('Reason For Event' ,size=50),
                'alt_hotel'     : fields.char('Alternative Hotel or Restaurant' ,size=75),
                'notes'         : fields.char('Notes' ,size=500),
                'cust_ref'      : fields.char('Customer Reference',size=100),
                'website_session_id': fields.char('Session UUID4'),
                #internal field
                'conv_dob'      : fields.char('Date of Booking' ,size=15),
                'conv_tob'      : fields.char('Time of Booking' ,size=10),
                'dummy_date'     : fields.function(_get_datetime, type='char', string='Dummy Date', size=20),
                
                
                'date_requested': fields.datetime('Date of Booking', select=True),
                'alt_date'      : fields.datetime('Alternative Date'),
                
                'covers'  :fields.integer('No. of Covers (Paid)' ,track_visibility='onchange'),
                'prev_covers' : fields.integer('Previous Covers',),
                'foc'         : fields.integer('FOC'),
                'enquiry_covers' : fields.char('No. of Covers(Enquiry)',size=15),
                'info_ids'      : fields.one2many('cc.send.rest.info','lead_id','Send Information'),
                'remind_ids'    : fields.one2many('cc.reminder.time','lead_id','Reminder Time',ondelete='cascade'),                
                'invoice_ids'   : fields.function(_get_invoice, type='one2many', relation='account.invoice', string='Invoice'),
                
                'service_type'  : fields.selection([('venue','Venue'), ('noontea','Afternoon Tea')],'Service Type'),
                'passen_type'  : fields.selection([('group','Group'), ('fit','FIT For Purpose')],'Passenger Type'), 
                
                
                'business_type' : fields.selection([('restaurant','Restaurant'),('bar','Bar'),('pub','Pub'),('nightclub','Nightclub')],'Type of Business'),
                'dining_room'   : fields.selection([('yes','Yes'),('no','No'),('notessential','Not Essential')],'Private Dining Room Required'),
                'hire_required' : fields.selection([('yes','Yes'),('no','No')],'Exclusive Hire Required'),
                'usr_role'      : fields.function(_get_usr_roles, type='char', size=75, string='User Roles'),
                'restaurant_id' : fields.function(_get_restaurant, type='many2one',relation='res.partner', string='Restaurant',store=True),
                'invoice_status' : fields.function(_get_inv_status, type='char',size=40, string='Invoice Status'),
                'sales_person'  : fields.many2one('res.users', 'Sales Person'),       
                'event_id'      : fields.many2one('cc.events','Events'),
                'alloc_id'      : fields.many2one('cc.time.allocations','Allocations'),        
                'is_servccharge':fields.boolean('Service Charge Removed'),
                'referral_link'  : fields.char('Referral Link'),

                'lead_day'           : fields.selection([('monday','Monday'),('tuesday','Tuesday'),('wednesday','Wednesday'),('thursday','Thursday'),('friday','Friday'),('saturday','Saturday'),('sunday','Sunday')],'Day'),
                'lead_res_type'      : fields.selection([('break_fast','Break Fast'),('lunch','Lunch'),('at','Afternoon Tea'),('dinner','Dinner')],'Type'),
                'booker_name'          : fields.char('Booker Name',size=250),
                }
    _defaults={
               #Overriden:
#                'user_id': lambda s, cr, uid, c: s._get_user(cr, uid, c),
               'business_type':'restaurant',
               'partner_id':_get_partner,
               'usr_role':default_usr_roles,
               'state':'draft'
               } 
    
    _order = "create_date desc,date_action desc"
    
#     def default_get(self, cr, uid, fields, context=None):
#          
#         res = super(crm_lead, self).default_get(cr, uid, fields, context=context)
#         user_obj = self.pool.get('res.users')
#         user = False        
#         if context and 'service_type' in context and context.get('service_type','') == 'venue':
#            user = 14
#         elif context and 'service_type' in context and context.get('service_type','') == 'noontea':
#            user = 14              
#         res.update({'user_id': user or False })
#         return res
    
    #Overriden
    def stage_find(self, cr, uid, cases, section_id, domain=None, order='sequence', context=None):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - type: stage type must be the same or 'both'
            - section_id: if set, stages must belong to this section or
              be a default stage; if not set, stages must be default
              stages
        """
        if isinstance(cases, (int, long)):
            cases = self.browse(cr, uid, cases, context=context)
        # collect all section_ids
        section_ids = []
        types = ['both']
        if not cases :
            type = context.get('default_type')
            types += [type]
        if section_id:
            section_ids.append(section_id)
        for lead in cases:
            if lead.section_id:
                section_ids.append(lead.section_id.id)
            if lead.type not in types:
                types.append(lead.type)
            if lead.service_type not in types:
               types.append(lead.service_type) 
        # OR all section_ids and OR with case_default
        search_domain = []
        if section_ids:
            search_domain += [('|')] * len(section_ids)
            for section_id in section_ids:
                search_domain.append(('section_ids', '=', section_id))
        else:
            search_domain.append(('case_default', '=', True))
        # AND with cases types
        search_domain.append(('type', 'in', types))
        # AND with the domain in parameter
        search_domain += list(domain)
        # perform search, return the first found
        stage_ids = self.pool.get('crm.case.stage').search(cr, uid, search_domain, order=order, context=context)
        if stage_ids:
            return stage_ids[0]
        return False

    def onchange_covers(self, cr, uid, ids, covers, state,context=None):
        res = {}
        if state in ('draft','pending'):
           res['prev_covers'] = covers 
        return {'value':res}
        
    
    def onchange_DOB(self, cr, uid, ids, date_requested, context=None):
        res = {}
        if not date_requested:
            return {}
        if context is None:context ={}
        if context and 'new_lead' in context and context.get('new_lead'):
           Default_dateformat = '%d-%m-%Y %H:%M' 
        elif context.get('from_web'):
            Default_dateformat = '%Y-%m-%d %H:%M'
        else :
           Default_dateformat = '%Y-%m-%d %H:%M:%S'  
        zone = self.pool.get('res.users').browse(cr,uid,uid).tz or 'Europe/London'
        local_tz = pytz.timezone(zone) # time zone name from Olson database
        
        
        def utc_to_local(utc_dt):
            return utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)

        rfc3339s = date_requested
        utc_dt = datetime.strptime(rfc3339s, Default_dateformat) 
        local_dt = utc_to_local(utc_dt)
        res['conv_dob'] = str(local_dt.strftime('%d-%b-%Y'))
        res['conv_tob'] = str(local_dt.strftime('%H:%M'))
        return {'value': res}
    
    
    
    def create_contacts(self,cr,uid,ids,context):
        partner_obj = self.pool.get('res.partner')
        
        for case in self.browse(cr,uid,ids):
            if case.partner_name and case.email_from:
               partner_ids = partner_obj.search(cr,uid,[('email','=',case.email_from)])
            else:
                raise osv.except_osv(_('Warning!'), _('Please ensure that customer and email is Entered before creating a contact.'))
            if not partner_ids:
               partner_id = partner_obj.create(cr,uid,{'name':case.partner_name,
                                                       'street'     : case.street or '',
                                                       'street2'    : case.street2 or '',
                                                       'city'       : case.city or '',
                                                       'state_id'   : case.state_id and case.state_id.id or False,
                                                       'country_id' : case.country_id and case.country_id.id or False,
                                                       'phone'      : case.phone or '',
                                                       'mobile'     : case.mobile or '',
                                                       'email'      : case.email_from or '',
                                                       'fax'        : case.fax or '',
                                                       'customer'   : True})
               
               self.write(cr,uid,[case.id],{'partner_id' : partner_id or False}) 
            
            else:
                raise osv.except_osv(_('Warning!'), _('Contact already exists.'))
        return True
    
    def Send_Info(self,cr,uid,ids,context):
        for lead in self.browse(cr, uid, ids):
            stage_id = self.stage_find(cr, uid, [lead],  False, [('name','=','Information Sent')], context=context)
            if stage_id:
                self.write(cr, uid, [lead.id], {'stage_id': stage_id}, context=context)
        return True
    
    def compute_all(self,cr,uid,ids,context):
        send_info_obj = self.pool.get('cc.send.rest.info')
        menu_dt_obj = self.pool.get('cc.menu.details')
        for case in self.browse(cr, uid, ids):
            for s in case.info_ids:                
                count=len(s.menu_dt_ids)                
                menu_count =0                
                for md in s.menu_dt_ids:
                    covers= 0.00
                    menu_count += 1
                    covers = float(case.covers)/float(count or 1)
                    if count > 1 and menu_count ==1:
                       covers = round(covers)
                    menu_dt_obj.write(cr,uid,[md.id],{'no_of_covers':covers,'previous_covers':covers})               
                send_info_obj.write(cr,uid,[s.id],{})
        return True
    
    def button_dummy(self, cr, uid, ids, context=None):
        send_info_obj = self.pool.get('cc.send.rest.info')
        menu_dt_obj = self.pool.get('cc.menu.details')
        for case in self.browse(cr, uid, ids):
            for s in case.info_ids:                
                for md in s.menu_dt_ids:
                    menu_dt_obj.write(cr,uid,[md.id],{})                
                send_info_obj.write(cr,uid,[s.id],{})
            self.write(cr,uid,[case.id],{})
        return True
    
    def send_request_avail(self,cr,uid,ids,context):
        send_info_obj = self.pool.get('cc.send.rest.info')
        message_obj = self.pool.get('mail.compose.message')
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', 'email_template_lead_request_avail')[1]
        except ValueError:
            template_id = False
        for case in self.browse(cr, uid, ids):
            for s in case.info_ids:
                fetch_temp = message_obj.onchange_template_id(cr, uid, ids, template_id, 'comment', 'cc.send.rest.info', s.id, context)['value']
                if fetch_temp :
                   message_id = message_obj.create(cr,uid,{'body'           : fetch_temp['body'],
                                                           'subject'        : fetch_temp['subject'],
                                                           'partner_ids'    : (6,0,fetch_temp['partner_ids']),
                                                           'attachment_ids' : (6,0,fetch_temp['partner_ids'])})
                   if message_id:
                      msg_succesful = message_obj.send_mail(cr, uid, [message_id], context)
                      if msg_succesful:
                         send_info_obj.write(cr,uid,[s.id],{'request_sent':True})  
                      
            stage_id = self.stage_find(cr, uid, [case], False, [('name','=','Requested')], context=context)
            if stage_id:
               self.write(cr, uid, [lead.id], {'stage_id': stage_id}, context=context)
        return True

    def _Send_mesg_BOuser(self, cr, uid, automatic=False, use_new_cursor=False, context=None):       
#     def Send_mesg_BOuser(self, cr, uid, ids, context=None):        
        mail_tmp_obj = self.pool.get('email.template')
        mod_obj = self.pool.get('ir.model.data')
        mail_comp = self.pool.get('mail.compose.message')
        mail_msg = self.pool.get('mail.message')
        users_obj = self.pool.get('res.users')
        remind_obj = self.pool.get('cc.reminder.time')
        Today = time.strftime("%Y-%m-%d %H:%M:00")
        Lead = self.search(cr, uid, [])
        for case in self.browse(cr, uid, Lead):
            for r in case.remind_ids:
                if r.reminder_date and Today >= r.reminder_date and not r.reminded: 
                   xml_id = (case.service_type == 'venue') and 'action_cclead_venue' or \
                            (case.service_type == 'noontea') and 'action_cclead_ntea'
                     
                   result = mod_obj.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', xml_id)                
                   vals1 = {
                            'body':'You had set a reminder for the <b>' + str(r.template_id.name)+'</b> mail for the Enquiry No.<b>'+ case.lead_no +'</b><br> <b>Did you receive a response?</b>',
                            'subject': 'Reminder for reply',
                            'partner_ids': [(6,0,[case.user_id and case.user_id.partner_id and case.user_id.partner_id.id or False])],
                            'subtype_id':1,
                            'type'      : 'notification',
                            'model'     : 'crm.lead',
                            'res_id'    : case.id,
                            'ccaction_id'    : result and result[1] or 0
                            }                    
                   msg_id = mail_msg.create(cr, uid, vals1)
                   remind_obj.write(cr, uid, [r.id], {'reminded': True})        
            
        return True
    
    def message_new(self, cr, uid, msg, custom_values=None, context=None):
        """ This functionality is To Create Lead Automatically From Mails 
        """
        if 'subject' not in msg:
            return False
        body = ''
        custom_values = {}
        mail_date = msg['date']
        subject = msg['subject']
        email_from = msg.get('from')
        email_from_add = email_from[email_from.find("<")+1:email_from.find(">")]
        body = html2plaintext(msg.get('body').replace("\n",""))        
        if subject[:42] != 'AfternoonTea.co.uk Group Booking Enquiry -':
           return False 
        elif mail_date < '2013-10-01 00:00:00':
            return False
        
        context.update({'user_update':True})
        custom_values.update(self.Create_vals(cr, uid, body, subject, context))
        return super(crm_lead, self).message_new(cr, uid, msg, custom_values, context=context)    
    
    def Create_vals(self,cr,uid,body,subject,email_from,context=None):
        custom_values = {}
        if not context:
            context = {}
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr,uid,uid)
        
        Rest_name = body[body.find('Venue:')+6:body.find('Name:')].strip()
        cust_name = body[body.find('Name:')+5:body.find('Email:')].strip()
        email = body[body.find('Email:')+6:body.find('Tel:')].strip()
        phone = body[body.find('Tel:')+4:body.find('Mobile:')].strip()
        mobile = body[body.find('Mobile:')+7:body.find('Reason for event:')].strip()
        reason_event = body[body.find('Reason for event:')+17:body.find('Event Type:')].strip()
        event_type = body[body.find('Event Type:')+11:body.find('Number of people:')].strip()
        covers = body[body.find('Number of people:')+17:body.find('Private room:')].strip()
        is_private = body[body.find('Private room:')+13:body.find('Budget per head:')].strip()
        budget = body[body.find('Budget per head:')+16:body.find('Preferred Date:')].strip()
        dob_date = body[body.find('Preferred Date:')+15:body.find('Preferred Time:')].strip()
        dob_time = body[body.find('Preferred Time:')+15:body.find('Alternative hotel or restaurant:')].strip()
        alt_hotel= body[body.find('Alternative hotel or restaurant:')+32:body.find('Alternative date:')].strip()
        alt_date= body[body.find('Alternative date:')+17:body.find('Additional Information:')].strip()
        add_inform= body[body.find('Additional Information:')+22].strip()
        
        import datetime
        utc_dt = False
        if dob_date:
           if not dob_time or dob_time == 'Please select':
              dob_time = '00:00' 
           else:
              dob_time 
           dob_frmt = dob_date + ' ' + dob_time.replace('.', ':')  
           dob_timezone = self.onchange_DOB(cr, uid, [], dob_frmt, {'new_lead':True})['value']
#        dob = (datetime.strptime(dob_frmt, "%d-%m-%Y %H:%M") + relativedelta(hours =- 5,minutes =- 30)) 
           local = pytz.timezone (user.tz)
           naive = datetime.datetime.strptime (dob_frmt, "%d-%m-%Y %H:%M")
           local_dt = local.localize(naive, is_dst=None)
           utc_dt = local_dt.astimezone (pytz.utc)
        
        if alt_date: 
           alter_date = datetime.datetime.strptime (alt_date, "%d-%m-%Y")
           alt_dt = local.localize(alter_date, is_dst=None)
           alt_date = alt_dt.astimezone (pytz.utc)
        
        custom_values={
                       'restrt_name' : Rest_name or '',
                       'partner_name' : cust_name or '',
                       'email_from' : email or '',
                       'phone' : phone or '',
                       'mobile' : mobile or '',
                       'reason_event':reason_event or '',
                       'event_type' : event_type or '',
                       'enquiry_covers' : covers or '',
                       'dining_room':is_private or 'no',
                       'budget' : budget or '',
                       'alt_hotel':alt_hotel or '',
                       'alt_date':alt_date or False,
                       'description':add_inform or '',
                       'service_type':'noontea',
                       'type':'opportunity',
                       'date_requested':utc_dt,
                       'date_action': time.strftime("%Y-%m-%d"),
                       'conv_dob':dob_timezone['conv_dob'],
                       'conv_tob':dob_timezone['conv_tob'],
                       'user_id':14
                       }
        return custom_values
    
    def create_payment_rec(self, cr, uid, inv_ids, post, context=None):
        """This function is called from Capitalcentric_webiste module were it creates payment records based on To payment type """
        
        if post is None:post = {}
        if context is None:context = {}
        wf_service = netsvc.LocalService("workflow")
        voucher_obj = self.pool.get('account.voucher')
        invoice_obj = self.pool.get('account.invoice')
        account_obj = self.pool.get('account.account')
        journal_obj = self.pool.get('account.journal')
        prod_obj    = self.pool.get('product.product')       
        user_obj    = self.pool.get('res.users')
        moveln_obj  = self.pool.get('account.move.line')
        
        prod = False
        inv_num = []
        card_chrgs = 0.00          
        amount = post.get('amount')           
        
        login_id = post.get('CM_loginid') and int(post.get('CM_loginid')) or uid
        user = user_obj.browse(cr,uid,login_id)
        
        partner = user.partner_id   
        if user.role != 'client':
           partner = user.partner_id.parent_id  
           
        prod_ids = prod_obj.search(cr, uid, [('name','=', 'Credit/Debit Card Charges')])
        if prod_ids:prod = prod_obj.browse(cr, uid, prod_ids and prod_ids[0])
        
        if inv_ids:     
           for inv in invoice_obj.browse(cr, uid, inv_ids):
                if inv.state == 'draft':  
                   wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_open', cr)
                inv_num.append(inv.number)              
           _logger.error('Lead %s',context,inv_num)                  
           context['move_line_ids'] = moveln_obj.search(cr, uid, [('state','=','valid'),('journal_id.name','in', inv_num)])
           _logger.error('Inv_ids %s',inv_ids)
           _logger.error('inv num %s',inv_num)         
                               
        if post.get('CM_acc_type') in ('prepaid','monthly','pay_adv'):
           amount = post.get('CM_amount') 
           card_chrgs = float(post.get('amount') or 0.00) - float(post.get('CM_amount') or 0.00)  
             
        account_id = account_obj.search(cr,uid,[('name','=','Bank')])
        values = {'partner_id':partner.id,
                  'amount':amount,
                  'reference':post.get('transId'),
                  'type':'receipt',
                  'date':time.strftime("%Y-%m-%d"),
                  'account_id':account_id[0],
                  'passen_type':user.is_group and 'group' or 'fit'
                  }
        voucher_id = voucher_obj.create(cr,uid,values,{})
        vch = voucher_obj.browse(cr,uid,voucher_id)
        values = voucher_obj.onchange_partner_id(cr, uid, [], vch.partner_id.id, vch.journal_id.id, vch.amount, vch.currency_id.id, vch.type, vch.date, context)['value']
        values.update({'line_cr_ids' : map(lambda x:(0,0,x),values['line_cr_ids']),
                       'line_dr_ids' : map(lambda x:(0,0,x),values['line_dr_ids'])})

        voucher_obj.write(cr,uid,[voucher_id],values,context)    
        voucher_obj.proforma_voucher(cr, uid, [voucher_id], context=None)
        
        if card_chrgs > 0:
           voch_id = voucher_obj.copy(cr, uid, voucher_id, {'amount'          : card_chrgs, 
                                                            'payment_option'  : 'with_writeoff',
                                                            'writeoff_acc_id' : prod.property_account_income and prod.property_account_income.id or False,
                                                            'reference'       : post.get('transId'),
                                                            'line_ids'        : [],
                                                            'line_cr_ids'     : [],
                                                            'line_dr_ids'     : [],
                                                            })           
           voucher_obj.proforma_voucher(cr, uid, [voch_id], context=None)
                
        return True

             
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['lead_no'], context=context)
        res = []
        for record in reads:
            name =''
            if record['lead_no']:
                name = record['lead_no']
            res.append((record['id'], name))
        return res
    
    #Overriden 
    def unlink(self,cr,uid,ids,context=None):
        
        sale_obj = self.pool.get('sale.order')        
        sale_ids = sale_obj.search(cr,uid,[('lead_id','in',ids)])
        if sale_ids:
           raise openerp.exceptions.Warning(_('You cannot delete an Lead which is already converted to Sale Order'))
       
        return super(crm_lead, self).unlink(cr, uid, ids, context=context) 
    
    #Overriden
    def write(self, cr, uid, ids, vals, context=None):
                
        send_info_obj = self.pool.get('cc.send.rest.info')
        menu_dt_obj = self.pool.get('cc.menu.details')
        stage_obj = self.pool.get('crm.case.stage')
        msg_obj = self.pool.get('mail.message')
        mod_obj =self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
                
        menu_ids = []
        is_completed = False
        print "ids",ids,type(ids)
        for st in self.browse(cr,uid,ids):
            print "st.stage_id.id",st,st.stage_id,st.stage_id.id
            stage = st.stage_id.id
            ldCovers = vals.get('covers') or st.covers or 0
            db_stage = stage_obj.browse(cr,uid,stage).name
            for si in st.info_ids:
                menu_covers = 0
                is_completed = si.is_completed  
                #if Change in FOC
                if 'foc' in vals and vals['foc']:              
                    cr.execute("update cc_send_rest_info set foc =" + str(vals['foc']) + "where id =" + str(si.id))
                #validation for No. of covers            
                if 'info_ids' in vals:
                    for info in vals['info_ids']:
                        if info[1] == si.id:
                           if info[2] and 'menu_dt_ids' in info[2]:
                              for md in info[2]['menu_dt_ids']:
                                  if md[2] and ('no_of_covers' in md[2] or 'food_type' in md[2]):
                                     menu_dts = md[1] and menu_dt_obj.browse(cr,uid,md[1]) or False
                                     no_of_covers = md[2].get('no_of_covers',0) or menu_dts and menu_dts.no_of_covers or 0
                                     food_type = md[2].get('food_type','') or menu_dts and menu_dts.food_type or ''
                                     menu_ids.append(md[1])
                                     if (food_type == 'meal'):
                                         menu_covers += no_of_covers

                    for mdt in si.menu_dt_ids:
                        if mdt.id not in menu_ids and mdt.food_type == 'meal': 
                           menu_covers += mdt.no_of_covers    
                        if st.covers < menu_covers and not is_completed:
                           raise osv.except_osv(
                               _('Warning!'),
                               _('The no. of covers entered on main screen and the menu screens do not match. Please Check.')
                           )
                                                     
        if context and 'frm_function' not in context and 'stage_id' in vals:
            stage = stage_obj.browse(cr,uid,vals['stage_id']).name                
            if stage == 'Completed' and db_stage not in ('Invoiced','Paid'):
               raise osv.except_osv(
                    _('Warning!'),
                    _('Please use MARK COMPLETED button in Send information Lines')
                )
            if stage == 'Lost':
               for ld in self.browse(cr,uid,ids): 
                   cr.execute("select id from account_invoice where state != 'cancel' and origin like '%" + str(ld.lead_no) +"%'")  
                   invoice = cr.fetchone()
                   if invoice:
                      raise osv.except_osv(_('Warning!'),
                                           _('This enquiry cannot be marked as Lost as there are invoices against the same')) 
        res = super(crm_lead, self).write(cr, uid, ids, vals, context=context)
        for case in self.browse(cr,uid,ids):
            stage_ids = stage_obj.search(cr,uid,[('state','in',['draft','pending'])])
            for s in case.info_ids:                
                if case.stage_id.id in stage_ids and s.is_completed:
                   send_info_obj.write(cr,uid,[s.id],{'is_completed':False})
                else: 
                   send_info_obj.write(cr,uid,[s.id],{})
                for md in s.menu_dt_ids:
                    menu_dt_obj.write(cr,uid,[md.id],{})
            
            msg_ids = msg_obj.search(cr,uid,[('res_id','=',ids[0]),('model','=','crm.lead')],order='id desc',limit=1)
            xml_id = (case.service_type == 'venue') and 'action_cclead_venue' or \
                     (case.service_type == 'noontea') and 'action_cclead_ntea'
                     
            result = mod_obj.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', xml_id)
            if msg_ids:
               msg_obj.write(cr,uid,msg_ids,{'ccaction_id':result and result[1] or 0}) 
        return res
    
    #Overriden    
    def create(self, cr, uid, vals, context=None):
         
        send_info_obj = self.pool.get('cc.send.rest.info')
        menu_dt_obj = self.pool.get('cc.menu.details')
        user_obj = self.pool.get('res.users')
        Mail_obj = self.pool.get('mail.followers')
        user = user_obj.browse(cr,uid,uid)
        subtype_ids = self.pool.get('mail.message.subtype').search(cr,uid,[('name','=','Discussions')])
         
        year = time.strftime('%Y')
        lead_no = ''
        if 'service_type' in vals and vals['service_type'] == 'venue':
            if 'passen_type' in vals and vals['passen_type'] == 'group':
               lead_no = 'CCV' + year
            if 'passen_type' in vals and vals['passen_type'] == 'fit':
               lead_no = 'FFP' + year
        elif 'service_type' in vals and vals['service_type'] == 'noontea':
            lead_no = 'CCT' + year 
        cr.execute("""select id from crm_lead where lead_no ilike '""" + str(lead_no) + """%' order by id desc limit 1""")
        lead_id = cr.fetchone()
        if lead_id:
            lead = self.browse(cr,uid,lead_id[0])
            auto_gen = lead.lead_no[7:]
            lead_no = lead_no + str(int(auto_gen)+1).zfill(4)
        else:
            lead_no = lead_no + '0001'
             
        vals['lead_no'] = lead_no
         
        remind_time = []
        template_ids= []
        if vals['service_type'] == 'venue':
           template_ids = self.pool.get('email.template').search(cr, uid, [('name','ilike','Enquiry')])
        elif vals['service_type'] == 'noontea':
             template_ids = self.pool.get('email.template').search(cr, uid, [('name','like','AT -')])
        for t in template_ids:  
                remind_time.append([0, 0, {'template_id':t or False}])
        vals['remind_ids'] = remind_time
         
        #validation for No. of covers
        menu_covers = 0
        if 'info_ids' in vals:
            for info in vals['info_ids']:
                if 'menu_dt_ids' in info[2]:
                    for md in info[2]['menu_dt_ids']:
                        if md[2]['food_type'] == 'meal':
                            menu_covers += md[2]['no_of_covers']        
                        if 'covers' in vals and menu_covers > vals['covers']: 
                           raise osv.except_osv(_('Error!'),_('The no. of covers entered on main screen and the menu screens do not match. Please Check.')) 
                         
        if 'covers' in vals:
            vals['prev_covers'] = vals['covers']  
        res = super(crm_lead, self).create(cr, uid, vals, context)
         
        for case in self.browse(cr,uid,[res]):
            for s in case.info_ids:                
                send_info_obj.write(cr,uid,[s.id],{})
                for md in s.menu_dt_ids:
                    menu_dt_obj.write(cr,uid,[md.id],{})
            user_ids = user_obj.search(cr,uid,[('role','in',('admin','bo')),('login','!=','ffpaccounts@capitalcentric.co.uk')])
            if case.user_id.id in user_ids:
               user_ids.remove(case.user_id.id)
            # for u in user_obj.browse(cr,uid,user_ids):Commented adding of followers is not required
            #     Mail_obj.create(cr,uid,{'res_model':'crm.lead',
            #                             'res_id': res,
            #                             'partner_id' : u.partner_id.id,
            #                             'subtype_ids': [(6, 0, subtype_ids)]
            #                        })
        return res     
    
crm_lead()


class cc_send_rest_info(osv.osv): 
    _name='cc.send.rest.info'

    def default_get(self, cr, uid, fields, context=None): 
        
        # class defaults is called
        res = super(cc_send_rest_info, self).default_get(cr, uid, fields, context=context)
        if context == None: context = {}

        lead_id = context.get('active_id', False)
  
        if context.get('service_type') == 'noontea':           
           res['invoice_type'] = 'to_venue'
        return res

    def _get_state(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
        for case in self.browse(cr,uid,ids):
            res[case.id] = ''
            if case.lead_id:
               res[case.id] = case.lead_id.state or ''  
        return res
    
    def _get_rest_parent(self, cr, uid, ids, field_name, arg, context=None):
        res = {}        
        for case in self.browse(cr,uid,ids):
            res[case.id] = False
            if case.restaurant_id:
               res[case.id] = case.restaurant_id.parent_id and case.restaurant_id.parent_id.id or case.restaurant_id.id or False  
        return res
    
    def _get_mailids(self, cr, uid, ids, field_name, arg, context=None):
        res = {}        
        for case in self.browse(cr,uid,ids):
            res[case.id] = False
            if case.restaurant_id:
               res[case.id] =  ', '.join(str(e.email) for e in case.restaurant_id.contact_ids) 
        return res
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        menu_dt_obj = self.pool.get('cc.menu.details')
        for case in self.browse(cr,uid,ids):
            res[case.id] = {'tot_top_price' : 0.00, 'tot_rest_price' : 0.00,'tot_comsion':0.00}
            for md in case.menu_dt_ids:         
                getamt = menu_dt_obj.get_pricing(cr, uid, ids, md.no_of_covers, md.rp_menu, md.rp_service_charge, md.rp_drinks, md.rp_additnal_srvc_chrg, md.rp_room_hire, md.rp_others, md.top_mp_markup, md.top_service_charge, md.top_drinks_markup, md.top_additnal_srvc_chrg, md.comsion_pprsn, md.top_rh_markup, md.comsion_rh, md.top_others_markup,context)['value']   
                res[case.id]['tot_top_price'] += getamt['top_tot_top_price']
                res[case.id]['tot_rest_price'] += getamt['rp_tot_rest_price']
                res[case.id]['tot_comsion'] += getamt['profit_on_comsion']
        return res
  
    def _get_default_product(self, cr, uid, context=None):
        service_type = ''
        if context:
           service_type = context.get('service_type','') 
           passen_type = context.get('default_passen_type','')
        if service_type:
           if service_type == 'venue':
              search_domain = [('name_template','=','Venues')]
           elif service_type == 'noontea':
              search_domain = [('name_template','=','Afternoon Tea')] 
           elif service_type == 'venue' and passen_type == 'fit':
              search_domain = [('name_template','=','FIT for Purpose')] 
           product_ids = self.pool.get('product.product').search(cr, uid, search_domain, context=context)
           return product_ids[0]
        else:
           return False 
       
    def _get_menu_dt(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('cc.menu.details').browse(cr, uid, ids, context=context):
            result[line.info_id.id] = True
        return result.keys()
    
    _columns={'name'                 : fields.char('Name',size=10),              
              'request_sent'         : fields.boolean('Request Sent',help='Checked if request availability is sent '),              
              'tax_srvc_chrg'        : fields.boolean('Tax On Service Charge (Customer)'),
              'srvc_chrg_sup'        : fields.boolean('Tax On Service Charge (Supplier)'),    
              'bvrges_extra'         : fields.boolean('Beverages & Extra'),
              'is_completed'         : fields.boolean('Mark Completed'),
              
              'date_avail'           : fields.char('Date Available',size=20),
              'area'                 : fields.char('Area',size=30),
              'room_hire'            : fields.char('Room Hire',size=75),
              'set_up'               : fields.char('Set Up',size=75),
              'drinks'               : fields.char('Drinks',size=75),
              'place_cards'          : fields.char('Place Cards',size=75),
              'table_plan'           : fields.char('Table Plan',size=75),
              'group_name'           : fields.char('Group Name',size=125),
              'hire_charge'          : fields.char('Hire Charge',size=50),    
                        
              'release_date'         : fields.date('Release Date'),
              
              'courses'              : fields.integer('Courses'),
              'foc'                  : fields.integer('FOC(Free of Cost)'),
              'noontea_comsion'      : fields.float('Commission',digits=(16, 2)),
              'tot_top_price'        : fields.function(_amount_all, string='Tour Operator Price'    , type='float', multi='pricing',store=True),
              'tot_rest_price'       : fields.function(_amount_all, string='Restaurant Price'       , type='float', multi='pricing',store=True),
              'tot_comsion'          : fields.function(_amount_all, string='Profit On Commission'   , type='float', multi='pricing',store=True),
              'state'                : fields.function(_get_state,    string='state'                , type='char' , size=15),
              'rest_parent_id'       : fields.function(_get_rest_parent, string='Restaurant Parent Object', type='many2one', relation='res.partner'),
              'contact_email'        : fields.function(_get_mailids, string= 'Mail Ids to send Booking comfirmation mail', type='text'),
              
              'price_subtotal'       : fields.float('Tour Operator Price',digits=(16, 2)),
              'purchase_amt'         : fields.float('Purchase Amount',digits=(16, 2)),

              'lead_id'              : fields.many2one('crm.lead','Leads'),
              'restaurant_id'        : fields.many2one('res.partner','Restaurant'), 
              'inv_address_id'       : fields.many2one('res.partner','Invoice Address'),
              'cont_address_id'      : fields.many2one('res.partner','Contact Address'),           
              'product_id'           : fields.many2one('product.product','Product'),
              
              'menu_dt_ids'          : fields.one2many('cc.menu.details','info_id','Menus & Pricing'),
              
              'invoice_type'         : fields.selection(Invoice_Type,'Invoice Type'),
              'availability'         : fields.boolean('Availability'),
              
              'description'          : fields.text('Description'),
              'special_requirement'  : fields.text('Special Requirement'),
              'payment_term'         : fields.text('Payment Term'),
              'spcl_req'             : fields.text('Special / Dietary Requirements'),
              'rp_notes'             : fields.text('Notes - Restaurant'),
              'to_notes'             : fields.text('Notes - Tour Operator'),
              'price_type'           : fields.char('Meal Type',size=100),

           }
    
    _defaults={'product_id'   : _get_default_product, 
               'bvrges_extra' : True,
#               'srvc_chrg_sup' : True,
               'tax_srvc_chrg': True,
               'noontea_comsion': 2.50,
               'payment_term':'PLEASE FORWARD YOUR VAT INVOICE TO CAPITAL CENTRIC WHO WILL PAY YOU DIRECTLY'
              }
    
   
    def onchange_restaurant_id(self, cr, uid, ids, restaurant_id,service_type):
        res={}
        menu_obj = self.pool.get('cc.menus') 
        partner_obj = self.pool.get('res.partner')
        menu_ids = []
        if restaurant_id:
           restaurant = partner_obj.browse(cr,uid,restaurant_id)
           res['inv_address_id'] = restaurant.parent_id and restaurant.parent_id.cc_company_id and restaurant.parent_id.cc_company_id.id or restaurant.parent_id.id or False
           res['rest_parent_id'] = restaurant.parent_id and restaurant.parent_id.id or False
           res['srvc_chrg_sup'] = restaurant.parent_id and restaurant.parent_id.servc_chrg or restaurant.servc_chrg or False
                      
           if service_type and service_type == 'noontea':
              res['noontea_comsion'] = restaurant.parent_id.commission or restaurant.commission or 0.00
              res['set_up'] = restaurant.parent_id.setup or restaurant.setup or 0.00 
                       
        return {'value':res
               }
        
    def print_voucher(self, cr, uid, ids, context=None):
        if context is None:context = {}
        rep_obj = self.pool.get('ir.actions.report.xml')
        type = '' 
        data = None       
        _logger.error('WORLD PAY FORM: %s',context)  
        for case in self.browse(cr,uid,ids):
            rec_ids = ids
            if case.lead_id.service_type == 'venue':
               if case.lead_id.passen_type == 'fit':
                  rec_ids = [case.lead_id.id] 
                  type = context.get('is_rp') and 'rp' or 'top'
                  data= {'cc_type' : type}
               res = rep_obj.pentaho_report_action(cr, uid, 'to_bookingconfirm', ids,data,None) 
            elif case.lead_id.service_type == 'noontea':
               res = rep_obj.pentaho_report_action(cr, uid, 'AT-BookingConfirmation', ids,None,None)  
        return res
    
    def _Send_mail_to_Restaurant(self, cr, uid, automatic=False, use_new_cursor=False, context=None):       
#     def Send_mail_to_Restaurant(self, cr, uid, ids, context=None):        
        mail_tmp_obj = self.pool.get('email.template')
        ir_model_data = self.pool.get('ir.model.data')
        
        try:
            venue_template_id = ir_model_data.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', 'reminder_email_template')[1] 
        except ValueError:
            venue_template_id = False
            
#        try:
#            top_template_id = ir_model_data.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', 'top_reminder_email_template')[1] 
#        except ValueError:
#            top_template_id = False
            
#        Afternoon tea
#         try:
#             tea_template_id = ir_model_data.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', 'reminder_email_template_noontea')[1] 
#         except ValueError:
#             tea_template_id = False
            
        Tomorrow  = (parser.parse(datetime.now().strftime('%Y-%m-%d')) + relativedelta( days=1)).strftime('%Y-%m-%d')
#         venue_info_ids = self.search(cr, uid, [('lead_id.state','in',['open','done']),('availability','=',True),('lead_id.service_type','=','venue'),('lead_id.date_requested::date','=',Tomorrow)])
        cr.execute("""select ri.id from cc_send_rest_info ri 
                      inner join crm_lead cl on ri.lead_id = cl.id 
                      where cl.state in ('open','done')
                      and ri.is_completed = True 
                      and cl.service_type = 'venue'
                      and cl.date_requested :: date = '""" +str(Tomorrow)+"""'""")
        info_ids = cr.fetchall()
#         noontea_info_ids = self.search(cr, uid, [('lead_id.state','in',['open','done']),('availability','=',True)],('lead_id.service_type','=','noontea'))
        #Looping based on venue service type
        for venue in info_ids: 
#             DOB = (parser.parse(''.join((re.compile('\d')).findall(venue.lead_id.date_requested)))).strftime('%Y-%m-%d')
            info = self.browse(cr, uid, venue[0])
            mail_tmp_obj.send_mail(cr, uid, venue_template_id, venue[0], True, context=None)
#            if info.lead_id.partner_id.top_rmd_opt:
#               mail_tmp_obj.send_mail(cr, uid, top_template_id, venue[0], True, context=None)
        #Looping based on afternoon tea service type          
#         for tea in self.browse(cr,uid,noontea_info_ids): 
#             DOB = (parser.parse(''.join((re.compile('\d')).findall(tea.lead_id.date_requested)))).strftime('%Y-%m-%d')
#             if Tomorrow == DOB:
#                mail_tmp_obj.send_mail(cr, uid, tea_template_id, tea.id, force_send=False, context=None)         
        return True

    def update_InvoiceType(self,cr,uid,ids,context):
        menu_dt_obj = self.pool.get('cc.menu.details')
        for case in self.browse(cr, uid, ids):
            for md in case.menu_dt_ids:
                  res = {}
                  if not case.invoice_type:
                     return True
                  if case.invoice_type == 'to_client':
                     res={'comsion_pprsn'      : 0.00, 
                          'comsion_pprsn_perc' : 0.00, 
                          'comsion_menu'       : 0.00,
                          'comsion_rh'         : 0.00,
                          'comsion_rh_perc'    : 0.00,
                          'sc_included'        : 0.00,
                          'invoice_type'       : 'to_client'
                         }
                                 
                  if case.invoice_type == 'to_venue':
                     res={'top_drinks_markup' : 0.00, 
                          'top_mp_markup'     : 0.00, 
                          'top_rh_markup'     : 0.00,
                          'top_others_markup' : 0.00,
                          'invoice_type'      : 'to_venue'
                         }   
                  menu_dt_obj.write(cr,uid,[md.id],res)
        return True   
    
    def _prepare_invoice(self, cr, uid, case, lines, chkwhich, context=None):

        if context is None:
            context = {}
        journal_ids = []
        type = comment = ''
        Account = Partner = False
        if chkwhich in ('CI_client','CI_venue'):
           type = 'out_invoice'
           comment = """Please make cheques payable to Capital Centric
BACS:
Barclays
Season & Vine Ltd TA Capital Centric
Sort Code: 20-59-14
Account Number: 73320707
IBAN: GB63 BARC 2059 1473 3207 07
Barclays UK SWIFT (or SWIFTBIC) code: BARCGB22"""

           journal_ids = self.pool.get('account.journal').search(cr, uid,
                         [('type', '=', 'sale'), ('company_id', '=', case.lead_id.company_id.id)], limit=1)
           if not journal_ids:
              raise osv.except_osv(_('Error!'),
                                   _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
              
           if chkwhich == 'CI_client': 
              Account = case.lead_id.partner_id and case.lead_id.partner_id.parent_id and case.lead_id.partner_id.parent_id.property_account_receivable.id or case.lead_id.partner_id and case.lead_id.partner_id.property_account_receivable.id or False
              Partner = case.lead_id.partner_id and case.lead_id.partner_id.parent_id and case.lead_id.partner_id.parent_id.id or case.lead_id.partner_id and case.lead_id.partner_id.id or False
                       
           if chkwhich == 'CI_venue': 
              Account = case.inv_address_id.property_account_receivable and case.inv_address_id.property_account_receivable.id or case.restaurant_id.property_account_receivable.id
              Partner = case.inv_address_id.id or case.restaurant_id.id
        elif chkwhich == 'SI_venue':
            type = 'in_invoice'    
            Account = case.inv_address_id.property_account_payable.id or case.restaurant_id.property_account_payable.id 
            Partner = case.inv_address_id.id or case.restaurant_id.id
            journal_ids = self.pool.get('account.journal').search(cr, uid,
                          [('type', '=', 'purchase'), ('company_id', '=', case.lead_id.company_id.id)], limit=1)
            if not journal_ids:
               raise osv.except_osv(_('Error!'),
                                    _('Please define purchase journal for this company: "%s" (id:%d).') % (case.company_id.name, case.company_id.id))
        
        if case.lead_id.service_type == 'noontea':
            #Invoice Date :1st of next month based on DOB
            #DueDate :InvoiceDate + 30days
            if case.lead_id.date_requested:
               dob_parse = (parser.parse(''.join((re.compile('\d')).findall(case.lead_id.date_requested)))).strftime('%Y-%m-%d')
               invfrmt_date = dob_frmt = (datetime.strptime(dob_parse, "%Y-%m-%d"))
               try:
                   invoice_date = invfrmt_date.replace(month=invfrmt_date.month+1,day =1)                
                   due_date = invoice_date + relativedelta(days=30)
                   
               except ValueError:
                   if invfrmt_date.month == 12:
                      invoice_date = invfrmt_date.replace(year=invfrmt_date.year+1,month=1,day=1)          
                      due_date = invoice_date + relativedelta(days=30) 
            try:
               pay_term = self.pool.get('account.payment.term').search(cr,uid,[('name','=','30 Net Days')])[0]
            except ValueError:
               pay_term = 3
            
        else:
            invoice_date= time.strftime("%Y-%m-%d")
            due_date = False
            pay_term = False 
            if chkwhich == 'SI_venue':
               invoice_date = False            
            
        invoice_vals = {
                        'name'  : '',
                        'origin': case.lead_id.lead_no,
                        'type': type,
                        'reference': case.lead_id.name,
                        'account_id': Account,
                        'partner_id': Partner,
                        'journal_id': journal_ids[0],
                        'invoice_line': [(0,0,x) for x in lines],
                        'currency_id': case.lead_id.company_id.currency_id.id,
                        'comment': comment,
                        'date_invoice': invoice_date or False,
                        'company_id': case.lead_id.company_id.id,
                        'lead_id'  : case.lead_id.id,
                        'service_type' : case.lead_id.service_type,
                        'booking_date' : case.lead_id.date_requested,
                        'user_id': case.lead_id.user_id and case.lead_id.user_id.id or False,
                        'info_id': case.id,
                        'payment_term': pay_term,
                        'date_due':due_date,
                        'passen_type':case.lead_id.passen_type,
                        'sales_person':case.lead_id.sales_person and case.lead_id.sales_person.id or False
                        }

        return invoice_vals

    def _make_invoice(self, cr, uid, case, lines, chkwhich, context=None):
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        user_obj = self.pool.get('res.users')
        Mail_obj = self.pool.get('mail.followers')
        user = user_obj.browse(cr,uid,uid)
        subtype_ids = self.pool.get('mail.message.subtype').search(cr,uid,[('name','=','Discussions')])
        if context is None:
            context = {}
            
        inv_id = False            
        if lines:
           inv = self._prepare_invoice(cr, uid, case, lines, chkwhich, context=context)
           inv_id = inv_obj.create(cr, uid, inv, context=context)
           inv_obj.button_compute(cr, uid, [inv_id])
           user_ids = user_obj.search(cr,uid,[('role','in',('admin','bo')),('login','!=','ffpaccounts@capitalcentric.co.uk')])
           if case.lead_id.user_id.id in user_ids:
              user_ids.remove(case.lead_id.user_id.id)
           # for u in user_obj.browse(cr,uid,user_ids):Commented adding of followers is not required
           #     Mail_obj.create(cr,uid,{'res_model':'account.invoice',
           #                             'res_id': inv_id,
           #                             'partner_id' : u.partner_id.id,
           #                             'subtype_ids': [(6, 0, subtype_ids)]
           #                            })

        return inv_id

    def cc_invoice_line_create(self, cr, uid, ids,chktype, context=None):
        if context is None:
            context = {}

        create_ids = []
        CI_grouped = {}
        SI_grouped = {}
        ci_lines = []
        si_lines = []
        ci_venue_lines = []
        sales = set()
        inv_type = ''        
        custchk = supchk = False
        cicheck = sicheck = ''
        account_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.invoice.journal')
        for case in self.browse(cr, uid, ids, context):  
            for md in case.menu_dt_ids:
                    #To create invoice                                              
                    if case.invoice_type == 'to_client':
                       chklist = ['CI_client', 'CI_client_SC', 'CI_client_RH', 'CI_client_OTH','SI_venue', 'SI_venue_SC', 'SI_venue_RH', 'SI_venue_OTH']                       
                    if case.invoice_type == 'to_venue':
                       chklist = ['ci_venue']                       
                    if case.invoice_type == 'to_both':
                       chklist = ['CI_client', 'CI_client_SC', 'CI_client_RH', 'CI_client_OTH','SI_venue', 'SI_venue_SC', 'SI_venue_RH', 'SI_venue_OTH','ci_venue']

                    if case.lead_id.state in ('draft','pending'):
                       cr.execute("update cc_menu_details set cached_tot_prcprsn=%s,cached_tot_rmprc=%s,cached_tot_otrprc=%s where id = %s",(md.top_tot_price_pprsn, md.top_room_hire_price, md.top_others_price, md.id))

                    elif case.lead_id.state in ('cancel','open','done'):
                       if (md.cached_tot_prcprsn != md.top_tot_price_pprsn) or (md.cached_tot_rmprc != md.top_room_hire_price) or (md.cached_tot_otrprc != md.top_others_price):
                          raise osv.except_osv(_('Warning!'),_('Price has been changed,please change the stage and use mark complete button'))


                    for chkwhich in chklist:            
                        res = {}
                        account = False
                        covers = 0
                        menu_covers = 0
                        if case.invoice_type in ('to_client','to_venue','to_both'):
                           if chkwhich in ('CI_client','CI_client_SC','CI_client_RH','CI_client_OTH','ci_venue'):
                              inv_type = 'out_invoice'
                              if not custchk:
                                 check = chktype                                 
                                 custchk = True                              
                              cicheck = check 
                              account = case.product_id.property_account_income and case.product_id.property_account_income.id
                              if not account: 
                                 account = case.product_id.categ_id.property_account_income_categ and case.product_id.categ_id.property_account_income_categ.id                                 
                           elif chkwhich in ('SI_venue', 'SI_venue_SC','SI_venue_RH','SI_venue_OTH'):
                              inv_type='in_invoice'                              
                              if not supchk:
                                 check = chktype
                                 supchk = True                              
                              sicheck = check 
                              account = case.product_id.property_account_expense and case.product_id.property_account_expense.id
                              if not account: 
                                 account = case.product_id.categ_id.property_account_expense_categ and case.product_id.categ_id.property_account_expense_categ.id
                    
                        vacc_ids = account_obj.search(cr,uid,[('lead_id','=',case.lead_id.id), ('type','=',inv_type),('state','not in',['draft','cancel'])])
                        cr.execute(""" select ai.id 
                                       from account_invoice ai 
                                       where ai.origin like '%""" + case.lead_id.lead_no + """%' 
                                       and ai.type= '""" + inv_type + """'
                                       and ai.state != 'cancel'
                                       group by ai.id
                                       having (
                                                select count(distinct lead_id) 
                                                from account_invoice_line 
                                                where invoice_id = ai.id
                                              ) > 1""")
                        mainv_ids = cr.fetchall()
                        if vacc_ids and mainv_ids:
                            for al in mainv_ids + vacc_ids:
                                context.update({'active_ids' : [al]
                                                ,'active_id' : al})
                                journal_ids = self.pool.get("account.journal").search(cr,uid,[('name','ilike','Sales Refund Journal')])[0]
                                ref_wiz_vals = { 'filter_refund' : 'refund'
                                                 ,'description'  : 'Amend Invoice'
                                                 ,'date'         :  datetime.strptime(now, "%Y-%m-%d")
                                                 ,'journal_id'   :  journal_ids
                                                 }
                                refund_wiz_id = journal_obj.create(cr, uid, ref_wiz_vals, context)
                                if refund_wiz_id:
                                    journal_obj.invoice_refund(cr, uid, refund_wiz_id, context)



                        if not vacc_ids and not mainv_ids:
                           dacc_ids = account_obj.search(cr,uid,[('lead_id','=',case.lead_id.id),('type','=',inv_type),('state','in',['draft','cancel'])])
                           if dacc_ids: 
                              account_obj.unlink(cr,uid,dacc_ids)
                              check = 'create'
                              if chkwhich == 'ci_venue':
                                 cicheck = check 
                        if check == 'create':
                           covers = case.lead_id.covers + (context.get('main_covers',0))
                           menu_covers = md.no_of_covers
                        elif check == 'update':                                
                           menu_covers = md.no_of_covers - md.previous_covers
                           if menu_covers < 0:
                              menu_covers = -(menu_covers) 
                           covers = context and context.get('ld_covers',0)                             
                                  
                        res = {
                                'origin': case.lead_id.name,
                                'account_id' : account,
                                'quantity': covers,
                                'discount': 0,
                                'uos_id': 1,
                                'product_id': case.product_id.id or False,
                                'invoice_line_tax_id': [(6, 0, [x.id for x in case.product_id.taxes_id])],
                                'sc_included' : md.sc_included,
                                'enq_dob' :case.lead_id.date_requested or False,
                                'lead_id' : case.lead_id.id
                              }
                        
                        req_date = False
                        flag_ok = True
                        restaurant_name = str(case.restaurant_id.name.encode('utf-8'))
                        if case.lead_id.date_requested:
                           req_date = (parser.parse(''.join((re.compile('\d')).findall(case.lead_id.date_requested)))).strftime('%d/%m/%Y')
                        if case.lead_id.service_type == 'venue' and menu_covers != 0:
                           fst_name = case.lead_id.partner_name or ''
                           sec_name = case.lead_id.contact_name or ''
                           title = case.lead_id.title and case.lead_id.title.name or ''
                           if md.food_type == 'meal':  
                              res['name'] = 'Meal Booking' + (fst_name and sec_name and (' for '+title+' '+ (fst_name or '') + ' '+ (sec_name or '')) or '') + ' at ' + (restaurant_name or '') + ' on ' + str(req_date) + ' (' + str(case.lead_id and case.lead_id.cust_ref or '') +')' + ' - ' + str(case.lead_id.lead_no or '')
                                                                                                                              
                           elif md.food_type == 'drink':
                                res['name'] = (md.menu_id and md.menu_id.name or 'Drinks' )+ (fst_name and sec_name and (' for '+title+' '+ (fst_name or '') + ' '+ (sec_name or '')) or '') + ' at ' + (restaurant_name or '') + ' on ' + str(req_date) + ' (' + str(case.lead_id and case.lead_id.cust_ref or '') +')' + ' - ' + str(case.lead_id.lead_no or '')
                           
                           if case.invoice_type in ('to_client','to_both'):
                              if chkwhich == 'CI_client':                      
                                 #Deducting Service Charge because to add it as separate line
                                 flag_ok = False 
                                 res.update({'price_unit' : md.top_tot_price_pprsn - (md.top_service_charge + md.top_additnal_srvc_chrg), 'quantity':menu_covers}) 
                                                 
                              elif chkwhich == 'CI_client_SC' and (md.top_service_charge > 0.00  or md.top_additnal_srvc_chrg > 0.00):
                                   flag_ok = False  
                                   res.update({'price_unit': md.top_service_charge + md.top_additnal_srvc_chrg, 
                                               'quantity'  : menu_covers,
                                               'descp_details':'Service Charge',
                                               'name':'Service Charge' + str(md.menu_id and ' on' ) +  str(md.menu_id and md.menu_id.name or '') + ' - ' + str(case.lead_id.lead_no or '')})
                                   if not case.tax_srvc_chrg:
                                      res.update({'invoice_line_tax_id' : False})  
                                      
                              elif chkwhich == 'CI_client_RH' and md.top_room_hire_price > 0.00 and check == 'create':
                                   flag_ok = False
                                   res.update({'price_unit':float(md.top_room_hire_price) / float(covers or 1),
                                               'name': 'Room Hire on ' + str(req_date) + ' - ' + str(case.lead_id.lead_no or '')}) 
                              
                              elif chkwhich == 'CI_client_OTH' and md.top_others_price > 0.00 and check == 'create':
                                   flag_ok = False
                                   res.update({'price_unit':(float(md.top_others_price) / float(covers or 1)),
                                               'name': 'Others on ' + str(req_date) + ' - ' + str(case.lead_id.lead_no or '')}) 
                                                      
                              elif md.invoice_type in ('to_client','to_both') and chkwhich == 'SI_venue':
                                   flag_ok = False
                                   price_pprsn = 0
                                   if not case.srvc_chrg_sup:
                                      price_pprsn =  md.rp_tot_price_pprsn - (md.rp_service_charge + md.rp_additnal_srvc_chrg)
                                   else:
                                      price_pprsn =  md.rp_tot_price_pprsn  
                                   res.update({'price_unit':price_pprsn,
                                               'invoice_line_tax_id': [(6, 0, [x.id for x in case.product_id.supplier_taxes_id])],
                                               'quantity' : menu_covers})                 
                              
                              elif not case.srvc_chrg_sup and chkwhich == 'SI_venue_SC' and (md.rp_service_charge > 0.00  or md.rp_additnal_srvc_chrg > 0.00):
                                   flag_ok = False  
                                   res.update({'price_unit': md.rp_service_charge + md.rp_additnal_srvc_chrg, 
                                               'quantity'  : menu_covers,
                                               'descp_details':'Service Charge',
                                               'invoice_line_tax_id': False,
                                               'name':'Service Charge' + str(md.menu_id and ' on' ) + str(md.menu_id and md.menu_id.name or '') + ' - ' + str(case.lead_id.lead_no or '')})
                              
                              elif chkwhich == 'SI_venue_RH' and md.rp_room_hire > 0.00 and check == 'create':
                                   flag_ok = False
                                   res.update({'price_unit':(float(md.rp_room_hire) / float(covers or 1)),
                                               'name': 'Room Hire on ' + str(req_date) + ' - ' + str(case.lead_id.lead_no or ''),
                                               'invoice_line_tax_id': [(6, 0, [x.id for x in case.product_id.supplier_taxes_id])]})
                                   
                              elif chkwhich == 'SI_venue_OTH' and md.rp_others > 0.00 and check == 'create' :
                                   flag_ok = False
                                   res.update({'price_unit':(float(md.rp_others) / float(covers or 1)),
                                               'name': 'Others on ' + str(req_date) + ' - ' + str(case.lead_id.lead_no or ''),
                                               'invoice_line_tax_id': [(6, 0, [x.id for x in case.product_id.supplier_taxes_id])]})
                                      
                           if md.invoice_type in ('to_venue','to_both')  and chkwhich == 'ci_venue':
                              flag_ok = False 
                              res.update({'price_unit':(float(md.profit_on_comsion) / float(menu_covers or 1)),
                                          'quantity' : menu_covers})                        
                        
                        
                        if flag_ok:
                           continue 
                        
                        if chkwhich in ('CI_client', 'CI_client_SC', 'CI_client_RH', 'CI_client_OTH'):
                           if 'name' in res and res.get('name') and res.get('name','').split()[0] in ('Room' ,'Others'):                                     
                               key = (res['name'])
                               if not key in CI_grouped:
                                  CI_grouped[key] = res 
                               else:
                                  CI_grouped[key]['price_unit'] += res['price_unit']
                           else:
                               ci_lines.append(res) 
                        
                        if chkwhich in ('SI_venue', 'SI_venue_SC', 'SI_venue_RH', 'SI_venue_OTH'):
                           if 'name' in res and res.get('name') and res.get('name').split()[0] in ('Room' ,'Others'):                                    
                               key = (res['name'])
                               if not key in SI_grouped:
                                  SI_grouped[key] = res 
                               else:
                                  SI_grouped[key]['price_unit'] += res['price_unit']
                           else:
                               si_lines.append(res) 
                               
                        if chkwhich == 'ci_venue':
                           ci_venue_lines.append(res) 
            
            for inv in CI_grouped.values():
                ci_lines.append(inv)
                
            for siv in SI_grouped.values():
                si_lines.append(siv)
            
            if case.lead_id.service_type == 'noontea':
               acc_ids = account_obj.search(cr,uid,[('lead_id','=',case.lead_id.id),('type','=','out_invoice'),('state','=','draft')])
               if acc_ids:
                  account_obj.unlink(cr,uid,acc_ids)
                  chktype = 'create'
                  cicheck = chktype
               if chktype == 'update':
                  covers = case.lead_id.covers - case.lead_id.prev_covers
                  if covers < 0 :
                     covers = -(covers)  
               else:
                  covers = case.lead_id.covers    
               if case.lead_id.date_requested:
                           req_date = (parser.parse(''.join((re.compile('\d')).findall(case.lead_id.date_requested)))).strftime('%d/%m/%Y')  
               res = {'origin': case.lead_id.name,
                                 'account_id' : case.product_id.property_account_income and case.product_id.property_account_income.id,
                                 'quantity': covers,
                                 'discount': 0,
                                 'uos_id': 1,
                                 'product_id': case.product_id.id or False,
                                 'invoice_line_tax_id': [(6, 0, [x.id for x in case.product_id.taxes_id])],
                                 'name': 'AfterNoon Tea Booking on ' + str(req_date) + ' for ' + str(case.lead_id.partner_name or ''),  
                                 'price_unit': case.noontea_comsion,                                 
                                 'enq_dob' :case.lead_id.date_requested or False
                      }
               ci_venue_lines.append(res)
               
            inv_ids = []    
            if case.invoice_type in ('to_client','to_both'):
               ci_lines and inv_ids.append(self._make_invoice(cr, uid, case, ci_lines, 'CI_client', context))
               si_lines and inv_ids.append(self._make_invoice(cr, uid, case, si_lines, 'SI_venue', context))
            if case.invoice_type in ('to_venue', 'to_both'):
               inv_ids.append(self._make_invoice(cr, uid, case, ci_venue_lines, 'CI_venue', context))
        
        return inv_ids,cicheck,sicheck

    
    def cc_create_invoices(self, cr, uid, ids, context=None):
        """ create invoices from Send Info
            based on invoice type.     
            if invoice type is to_client it ill create a CI and a SI.
            if invoice type is to_venue it ill create only SI
            or invoice type is to_both it ill create 2 CI and a SI 
              """
        Lead_obj = self.pool.get('crm.lead')     
        
        for case in self.browse(cr,uid,ids):               
            if not case.invoice_type:
               raise osv.except_osv(_('Warning!'),_('Please select Invoice Type before proceeding'))
            
            if context:
               context.update({'frm_function':True})
                
            self.cc_invoice_line_create(cr, uid, ids, 'create', context)
            self.write(cr,uid,[case.id],{'is_completed':True})
            
            Lead = Lead_obj.browse(cr,uid,case.lead_id.id)
            stage_id = Lead_obj.stage_find(cr, uid, [Lead], False, [('name','=','Completed')], context=context)
            if stage_id:
               Lead_obj.write(cr, uid, [Lead.id], {'stage_id': stage_id}, context=context)
                    
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
               }
    
    #Create new invoice for the extra covers added    
    def update_invoice(self, cr, uid, ids, context=None):
        lead_obj = self.pool.get('crm.lead')
        account_obj = self.pool.get('account.invoice')
        menu_dt_obj = self.pool.get('cc.menu.details')
        for case in self.browse(cr, uid, ids):
            inv_ids = []
            if case.lead_id.service_type == 'venue':
               m_covers = 0
               pm_covers = 0
               chk_covers = 0
               for md in case.menu_dt_ids:
                   if md.food_type == 'meal':                      
                      chk_covers += md.no_of_covers - md.previous_covers
                   m_covers += md.no_of_covers
                   pm_covers += md.previous_covers               
        
               covers = ld_covers = m_covers - pm_covers
               stage_ids = False
               is_cancelled = False
               
               if covers > 0 :
                  if case.lead_id.passen_type == 'fit':
                        if case.lead_id.event_id:# Food type Events will be changed to meal while creating lead
                           event = case.lead_id.event_id
                           alloc_covers = (str(event.covers),)
                        else:
                            #Checking Availability
                            alloc_id = case.lead_id.alloc_id
                            alloc_covers = (str(alloc_id.covers),)
                            
                        if alloc_covers:
                           cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) 
                                         from crm_lead 
                                         where state = 'open' 
                                         and conv_dob = '""" + str(case.lead_id.conv_dob) +"""' 
                                         and conv_tob='"""+ str(case.lead_id.conv_tob) + """'
                                         and restaurant_id = """ + str(case.restaurant_id.id))
                           tot_covers = cr.fetchone()
                           if int(tot_covers[0]) + covers > int(alloc_covers[0]) :
                              raise osv.except_osv(_('Warning!'),_('There is no availability for the number of covers entered.'))   
                               
#                         #Balance Validation 
#                         limit = operator.booking_limit or 0.00
#                         acc_bal = -(operator.credit + limit)
#                         if operator.payment_type == 'prepaid' and acc_bal < (subtotal + vat_total):
#                             return 'low_balance'
 
               if m_covers == 0:
                  is_cancelled = True
                  stage_ids = self.pool.get('crm.case.stage').search(cr, uid, [('name','=','Lost'),('type','=','both'),('state','=','cancel')])
                     
#                   #if on change covers ,covers is 0 then delete if any draft invoice is there 
#                   #and do not create any invoice                   
#                   invids = account_obj.search(cr, uid, [('lead_id','=',case.lead_id.id),('state','=','draft')])
#                   account_obj.unlink(cr, uid, invids)
#                   for md in case.menu_dt_ids:#updating current covers to previous covers
#                       menu_dt_obj.write(cr,uid,[md.id],{'previous_covers':md.no_of_covers})

#                   lead_obj.write(cr,uid,[case.lead_id.id],{'covers':(case.lead_id.covers + covers), 'is_cancelled':True, 'stage_id':stage_ids and stage_ids[0] or case.lead_id.stage_id}) 
#                   
#                   return {'type': 'ir.actions.client',
#                           'tag': 'reload',
#                          }  
                
               if ld_covers == 0:
                  raise osv.except_osv(_('Warning!'),_('Please enter revised no. of covers before proceeding.'))   
              
               if ld_covers < 0:
                  ld_covers = -(ld_covers)
                   
               if context is None:
                  context = {}
               context.update({'ld_covers':ld_covers,'main_covers':covers})              
                    
               inv_ids,cicheck,sicheck = self.cc_invoice_line_create(cr, uid, ids, 'update' ,context)               
               #adding covers in lead with difference in updated covers
                
               vals = {'covers':(case.lead_id.covers + chk_covers),'is_cancelled': is_cancelled}
               
               if stage_ids:
                  vals['stage_id'] = stage_ids and stage_ids[0] or case.lead_id.stage_id
               lead_obj.write(cr,uid,[case.lead_id.id],vals) 
               for md in case.menu_dt_ids:#updating current covers to previous covers
                   menu_dt_obj.write(cr,uid,[md.id],{'previous_covers':md.no_of_covers})
            elif case.lead_id.service_type == 'noontea':                 
                 covers = case.lead_id.covers - case.lead_id.prev_covers
                 if covers == 0:
                  raise osv.except_osv(_('Warning!'),_('Change in covers can proceed with this action.'))                  
                 inv_ids = self.cc_invoice_line_create(cr, uid, ids, 'update' ,context)
                 vals = {'prev_covers':(case.lead_id.covers),'is_cancelled':is_cancelled}
                 
                 if stage_ids:
                    vals['stage_id'] = stage_ids and stage_ids[0] or case.lead_id.stage_id 
                 lead_obj.write(cr,uid, [case.lead_id.id], vals)
            
            _logger.error('Invoice Ids',inv_ids) 
            if inv_ids and covers < 0:
               for inv in account_obj.browse(cr,uid,inv_ids):
                   if inv.type == 'out_invoice' and cicheck == 'update': 
                      account_obj.write(cr, uid, [inv.id], {'type':'out_refund'})
                   elif inv.type == 'in_invoice' and sicheck == 'update':   
                      account_obj.write(cr, uid, [inv.id], {'type':'in_refund'})  
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'inv_ids':inv_ids,
               }    
        
      
    def message_post(self, cr, uid, thread_id, body='', subject=None, type='comment',
                        subtype=None, parent_id=False, attachments=None, context=None, **kwargs):
        sale_obj = self.pool.get('crm.lead')
        
        for case in self.browse(cr,uid,thread_id):
            lead_id = case.lead_id.id
            
        return sale_obj.message_post(cr, uid, [lead_id], body=body, subject=subject, type=type, subtype=subtype, parent_id=parent_id, attachments=attachments, context=context, **kwargs)    
  
cc_send_rest_info()

class cc_menu_details(osv.osv):
   
    _name='cc.menu.details'
    
    def _amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for case in self.browse(cr,uid,ids):
            res[case.id] = {'rp_tot_price_pprsn': 0.00, 'rp_tot_price'      : 0.00, 'rp_tot_rest_price'   : 0.00, 
                            'top_menu_price'    : 0.00, 'top_drinks_price'  : 0.00, 'top_tot_price_pprsn' : 0.00, 
                            'comsion_menu'      : 0.00, 'top_tot_price'     : 0.00, 'top_room_hire_price' : 0.00, 
                            'top_others_price'  : 0.00, 'top_tot_top_price' : 0.00, 'tot_profit'          : 0.00,
                            'profit_on_comsion' : 0.00}
            
            getamt = self.get_pricing(cr, uid, ids, case.no_of_covers, case.rp_menu, case.rp_service_charge, case.rp_drinks, case.rp_additnal_srvc_chrg
                                           , case.rp_room_hire, case.rp_others, case.top_mp_markup, case.top_service_charge, case.top_drinks_markup
                                           , case.top_additnal_srvc_chrg, case.comsion_pprsn, case.top_rh_markup, case.comsion_rh, case.top_others_markup, context)['value']
            if getamt:
               res[case.id] = getamt 
 
        return res
    
    def _get_restaurant(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for case in self.browse(cr,uid,ids):
            res[case.id] = {'restaurant_id':False, 'invaddrs_id' : False}
            if case.info_id:
               res[case.id] = {'restaurant_id':case.info_id.restaurant_id.parent_id and case.info_id.restaurant_id.parent_id.id or case.info_id.restaurant_id.id or False, 
                               'invaddrs_id' : case.info_id.inv_address_id.id}  
 
        return res

    def _get_covers(self, cr, uid, context=None):
        service_type = ''
        if context is None: context = {}
        state = context.get('ld_state','') 
        if state in ('draft','pending'):           
           return context.get('default_no_of_covers',0)
        else:
           return 0

    _columns = {'name'                 : fields.char('Name',size=10),
                'sc_included'          : fields.boolean('Service Charge(Included)'),
                'mrkup_included'       : fields.boolean('Top Markup included'),
                'menu_id'              : fields.many2one('cc.menus','Menus'),
                'menu_desc'            : fields.text('Description'),
                'info_id'              : fields.many2one('cc.send.rest.info','Restaurant Info.'),
                'no_of_covers'         : fields.integer('No. of Covers'),  
                'previous_covers'      : fields.integer('Previous Covers'),               
              
                'rp_menu'              : fields.float('Menu Price (A)',digits=(16, 2)),
				'rp_sc_perc'           : fields.float('Service Charge (%)',digits=(16, 2)),
                'rp_service_charge'    : fields.float('Service Charge (B)',digits=(16, 2)),
                'rp_drinks'            : fields.float('Drinks (C)',digits=(16, 2)),
                'rp_additnal_srvc_chrg': fields.float('Additional Service Charge (D)',digits=(16, 2)),
                'rp_room_hire'         : fields.float('Room Hire (G)',digits=(16, 2)),
                'rp_others'            : fields.float('Others (H)',digits=(16, 2)), 
                'top_mp_markup'        : fields.float('Menu Price Markup (1)',digits=(16, 2)),
                'top_sc_perc'          : fields.float('Service Charge (%)',digits=(16, 2)),
                'top_markup'           : fields.float('TO Markup display purpose in website',digits=(16, 2)),
                'top_service_charge'   : fields.float('Service Charge (3)',digits=(16, 2)),
                'top_drinks_markup'    : fields.float('Drinks Markup (4)',digits=(16, 2)),
                'top_additnal_srvc_chrg': fields.float('Additional Service Charge (6)',digits=(16, 2)),
                'comsion_pprsn_perc'   : fields.float('Commission Per Person(%)',digits=(16, 2)),
                'comsion_pprsn'        : fields.float('Commission Per Person', digits=(16,2)),
                'top_rh_markup'        : fields.float('Room Hire Markup (9)',digits=(16, 2)),
                'comsion_rh_perc'      : fields.float('Commission For Room Hire(%)',digits=(16, 2)),
                'comsion_rh'           : fields.float('Commission For Room Hire',digits=(16, 2)),
                'top_others_markup'    : fields.float('Others Markup (11)',digits=(16, 2)),
                'rp_tot_price_pprsn'   : fields.function(_amount_total, string='Total Price Per Person (E = A + B + C + D)'   , type='float', store=True, multi='pricing',digits=(16, 2)),
                'rp_tot_price'         : fields.function(_amount_total, string='Total Price (F = E * NOC)'                    , type='float', store=True, multi='pricing',digits=(16, 2)),
                'rp_tot_rest_price'    : fields.function(_amount_total, string='Total Restaurant Price (I = F + G + H)'       , type='float', store=True, multi='pricing',digits=(16, 2)),
                'top_menu_price'       : fields.function(_amount_total, string='Menu Price (2 = A + 1)'                       , type='float', store=True, multi='pricing',digits=(16, 2)),
                'top_drinks_price'     : fields.function(_amount_total, string='Drinks Price (5 = C + 4)'                     , type='float', store=True, multi='pricing',digits=(16, 2)),
                'top_tot_price_pprsn'  : fields.function(_amount_total, string='Total Price Per Person (7 = 2 + 3 + 5 + 6)'   , type='float', store=True, multi='pricing',digits=(16, 2)),
                'comsion_menu'         : fields.function(_amount_total, string='Commission For Menu'                          , type='float', store=True, multi='pricing',digits=(16, 2)),
                'top_tot_price'        : fields.function(_amount_total, string='Total Price (8 = 7 * NOC)'                    , type='float', store=True, multi='pricing',digits=(16, 2)),
                'top_room_hire_price'  : fields.function(_amount_total, string='Room Hire Price (10 = G + 9)'                 , type='float', store=True, multi='pricing',digits=(16, 2)),
                'top_others_price'     : fields.function(_amount_total, string='Others Price (12 = H + 11)'                   , type='float', store=True, multi='pricing',digits=(16, 2)),
                'top_tot_top_price'    : fields.function(_amount_total, string='Total Tour Operator Price (13 = 8 + 10 + 12)' , type='float', store=True, multi='pricing',digits=(16, 2)),
                'tot_profit'           : fields.function(_amount_total, string='Total Profit (13 - I)'                        , type='float', store=True, multi='pricing',digits=(16, 2)),
                'profit_on_comsion'    : fields.function(_amount_total, string='Profit On Commission'                         , type='float', store=True, multi='pricing',digits=(16, 2)),                
                'restaurant_id'        : fields.function(_get_restaurant,string='Restaurant Parent'                            , type='many2one', relation='res.partner', multi='rest'),
                'invaddrs_id'          : fields.function(_get_restaurant,string='Invoice Address'                              , type='many2one', relation='res.partner', multi='rest'),
#                'restaurant_id'        : fields.function(_get_rest, string='Restaurant', type='many2one',relation='res.partner',multi='menus'),
#                'menu_mapping'         : fields.function(_get_rest, string='Menu Mapping', type='text' ,multi='menus'),
                'invoice_type'                : fields.related('info_id','invoice_type', type="char", size=20
                                                        , string="Invoice Type", readonly=True),
                'food_type'            : fields.selection([('meal','Meal'),('drink','Drink')],'Type'),
# field to display menu-option in menu pricing
                'menu_option'           : fields.selection([('option1','Option-1'),('option2','Option-2')],'Menu Option'),                
                'state': fields.related('info_id', 'invoice_type', type="selection",
                                        selection=Invoice_Type, string="Status", readonly=True),
                'foc'                  : fields.integer('FOC(Free of Cost)'),
                #Fields to cache few total values of the fields after mark complete
                'cached_tot_prcprsn'   : fields.float('Cache Total Price Per Person'),
                'cached_tot_rmprc'     : fields.float('Cache Total Room Hire Price'),
                'cached_tot_otrprc'    : fields.float('Cache Total Others Price'),
                }
    _defaults ={'food_type':'meal',
                'previous_covers':_get_covers}
    
    def onchange_menu_option(self, cr, uid, ids, menu_id,menu_option,no_of_covers, is_completed, invoice_type,context=None):
        context = context or {}
        if not menu_id:
            return {}
        if context is None:context={}
        res = {}
        getamt = {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        drink_price = drink_mu = 0
        if context.get('fit_purpose',False):
           menus_obj = self.pool.get('cc.menus.table')
           Menu = menus_obj.browse(cr,uid,menu_id)
           res = {'food_type'         : Menu.food_type == 'events' and 'meal' or Menu.food_type or '',#if food type is events changing to meal
                  'rp_service_charge' : Menu.service_charge or 0.00,
                  'top_service_charge': Menu.service_charge or 0.00,
                  'menu_desc'         : Menu.menu_id.description or '',
                  'sc_included'       : Menu.menu_id.sc_included or False,
                  'no_of_covers'      : Menu.guest or 0,
                  'menu_id'           : Menu.menu_id.id or False}
           
           Markup = Menu.ffp_mu
           if user.is_group:
              sc_included = Menu.menu_id.partner_id.sc_included 
              if sc_included:
                 sc_included = Menu.menu_id.partner_id.parent_id and Menu.menu_id.partner_id.parent_id.sc_included or False 
              res.update({'sc_included':sc_included})
              
           if user.is_wlabeling: #if its whitelabeled customer then TO markup to be included in price
              Markup = Menu.ffp_mu + Menu.to_mu
              res.update({'mrkup_included': Menu.operator_id.comision_type == 'markup' and True or False})
              
           if Menu.food_type in ('meal','events'):
               res.update({'rp_menu'       : Menu.pp_person or 0.00 , 
                           'top_mp_markup' : Markup or 0.00,})
               res['rp_service_charge'] = round(res['rp_menu'] * (Menu.service_charge/(res['rp_menu']+Menu.ffp_mu)),1)

           elif Menu.food_type == 'drink':
               res.update({'rp_drinks'         : Menu.pp_person or 0.00 , 
                           'top_drinks_markup' : Markup or 0.00,
                           })
               res['rp_service_charge'] = round(res['rp_drinks'] * (Menu.service_charge/(res['rp_drinks']+Menu.ffp_mu)),1)

           getamt = self.onchange_pricing(cr, uid, ids,'res_sc',  no_of_covers, is_completed, res.get('rp_menu',0), res.get('rp_service_charge',0), res.get('rp_drinks',0), 0.00, 0.00, 0.00, res.get('top_mp_markup',0), res.get('top_service_charge',0), res.get('top_drinks_markup',0), 0.00, 0.00, 0.00, 0.00, 0.00, res.get('food_type'), res.get('sc_included'),context)['value']
           
        else: 
            res = {'rp_service_charge'  : 0.00,
                   'top_service_charge' : 0.00,
                   'rp_sc_perc'         : 0.00,
                   'top_sc_perc'        : 0.00,
                   'comsion_pprsn_perc' : 0.00,
                   'sc_included'        : False}       
               
            menus_obj = self.pool.get('cc.menus')        
            Menu = menus_obj.browse(cr,uid,menu_id)
        
            if context.get('food_type','') == 'drink':
               res.update({'rp_drinks'         : Menu.rest_price or 0.00 , 
                           'top_drinks_markup' : Menu.markup or 0.00, 
                           'menu_desc'         : Menu.description or '',
                           'rp_service_charge' : (Menu.to_price - (Menu.rest_price + Menu.markup)),
                           'top_service_charge': (Menu.to_price - (Menu.rest_price + Menu.markup)),
                          })
               context.update({'fit_purpose':True})
               getamt = self.onchange_pricing(cr, uid, ids,'res_sc',  no_of_covers, is_completed, 0, res.get('rp_service_charge',0), res.get('rp_drinks',0), 0.00, 0.00, 0.00, 0, res.get('top_service_charge',0), res.get('top_drinks_markup',0), 0.00, 0.00, 0.00, 0.00, 0.00, 'drink', res.get('sc_included'),context)['value']
               res.update(getamt)  
               return {'value':res}
        
            if Menu and menu_option=='option1':
                res.update({'rp_menu'       : Menu.rest_price or 0.00 , 
                            'top_mp_markup' : Menu.markup or 0.00,
                            'menu_desc'     : Menu.description or '',
                           })
                
            if Menu and menu_option=='option2':
                res.update({'rp_menu'       : Menu.rest_price1 or 0.00, 
                            'top_mp_markup' : Menu.markup1 or 0.00,
                            'menu_desc'     : Menu.description1 or '',
                           })
                
            if Menu and menu_option and not res['sc_included']:   
                sc_perc = Menu.partner_id.menu_sc or Menu.partner_id.cc_company_id and Menu.partner_id.cc_company_id.menu_sc or 0.00                       
                res.update({'rp_service_charge'  : float(sc_perc / 100.00) * res['rp_menu'],
                            'top_service_charge' : float(sc_perc / 100.00) * (res['rp_menu']),
                            'rp_sc_perc'         : sc_perc,
                            'top_sc_perc'        : sc_perc,                        
                            'sc_included'        : Menu.partner_id.sc_included or Menu.partner_id.cc_company_id and Menu.partner_id.cc_company_id.sc_included or False,})
                
                if invoice_type in ('to_venue','to_both'):
                   res.update({'comsion_pprsn_perc' : Menu.partner_id.menu_commsion or Menu.partner_id.cc_company_id and Menu.partner_id.cc_company_id.menu_commsion or 0.00}) 
                getamt = self.onchange_pricing(cr, uid, ids,'',  no_of_covers, is_completed, res['rp_menu'], res.get('rp_sc_perc',0.00), 0.00, 0.00, 0.00, 0.00, res['top_mp_markup'], res.get('top_sc_perc',0.00), 0.00, 0.00, res.get('comsion_pprsn_perc',0.00), 0.00, 0.00, 0.00, 'meal', res.get('sc_included'),context)['value']
                
        if getamt:
            res.update(getamt)            
        return {'value': res}
                
 
    
    def onchange_cost(self, cr, uid, ids, no_of_covers, comsion_pprsn, comsion_rh):
        res={}
#         res['comsion_pprsn_perc']  = (float(comsion_pprsn) / (float(top_tot_price_pprsn or 1))) * 100
        res['comsion_menu']        = comsion_pprsn * float(no_of_covers)
#         res['comsion_rh_perc']     = (float(comsion_rh) / (float(top_room_hire_price or 1))) * 100
        res['profit_on_comsion']   = res['comsion_menu'] + comsion_rh
        return {'value':res}
    
    def get_pricing(self, cr, uid, ids, no_of_covers, rp_menu, rp_service_charge, rp_drinks, rp_additnal_srvc_chrg, rp_room_hire, rp_others, top_mp_markup, top_service_charge, top_drinks_markup, top_additnal_srvc_chrg, comsion_pprsn, top_rh_markup, comsion_rh, top_others_markup, context=None):
        res = {}
        res['rp_tot_price_pprsn']  = rp_menu + rp_service_charge + rp_drinks + rp_additnal_srvc_chrg
        res['rp_tot_price']        = res['rp_tot_price_pprsn'] * float(no_of_covers)
        res['rp_tot_rest_price']   = res['rp_tot_price'] + rp_room_hire + rp_others
        res['top_service_charge']  = rp_service_charge
        res['top_menu_price']      = rp_menu + top_mp_markup
        res['top_drinks_price']    = rp_drinks + top_drinks_markup
        res['top_tot_price_pprsn'] = res['top_menu_price'] + top_service_charge + res['top_drinks_price'] + top_additnal_srvc_chrg         
        res['comsion_pprsn_perc']  = (float(comsion_pprsn) / (float(res['top_tot_price_pprsn'] or 1))) * 100
        res['comsion_menu']        = float(comsion_pprsn) * float(no_of_covers)
        res['top_tot_price']       = res['top_tot_price_pprsn'] * float(no_of_covers)
        res['top_room_hire_price'] = rp_room_hire + top_rh_markup
        res['comsion_rh_perc']     = (float(comsion_rh) / (float(res['top_room_hire_price'] or 1))) * 100
        res['top_others_price']    = rp_others + top_others_markup
        res['top_tot_top_price']   = res['top_tot_price'] + res['top_room_hire_price'] + res['top_others_price'] 
        res['tot_profit']          = res['top_tot_top_price'] - res['rp_tot_rest_price']
        res['profit_on_comsion']   = res['comsion_menu'] + comsion_rh         
        return{'value':res}
    
    def onchange_pricing(self, cr, uid, ids,chkwhich, no_of_covers, is_completed, rp_menu, rp_sc_perc, rp_drinks, rp_additnal_srvc_chrg, rp_room_hire, rp_others, top_mp_markup, top_sc_perc, top_drinks_markup, top_additnal_srvc_chrg, comsion_pprsn_perc, top_rh_markup, comsion_rh_perc, top_others_markup, food_type, sc_included = False, context=None):
        res = {}
        if context is None:context = {}
        if not is_completed:
           res['previous_covers']  =  no_of_covers         
        
        if chkwhich == 'res_sc' :
           res['top_additnal_srvc_chrg'] = top_additnal_srvc_chrg =rp_additnal_srvc_chrg
        
        elif chkwhich == 'rp_sc_perc' :
            res['top_sc_perc'] = top_sc_perc = rp_sc_perc
            
        if not sc_included:        
              res['rp_service_charge']   = round(float(rp_sc_perc / 100.00) * (rp_menu),1)
              res['top_service_charge']  = round(float(top_sc_perc/ 100.00) * (rp_menu + top_mp_markup),1)
              
              if food_type == 'drink':
                 res['rp_service_charge'] =  res['top_service_charge'] = round(float(rp_sc_perc / 100.00) * (rp_drinks + top_drinks_markup),2)

        else:
            res['rp_service_charge']   = 0
            res['top_service_charge']  = 0
        
        if context.get('fit_purpose'):
           res['rp_service_charge'] =  rp_sc_perc
           res['top_service_charge'] = top_sc_perc
                    
        res['rp_tot_price_pprsn']  = rp_menu + res['rp_service_charge'] + rp_drinks + rp_additnal_srvc_chrg
        res['rp_tot_price']        = res['rp_tot_price_pprsn'] * float(no_of_covers)
        res['rp_tot_rest_price']   = res['rp_tot_price'] + rp_room_hire + rp_others
        res['top_menu_price']      = rp_menu + top_mp_markup
        res['top_drinks_price']    = rp_drinks + top_drinks_markup
        res['top_tot_price_pprsn'] = res['top_menu_price'] + res['top_service_charge'] + res['top_drinks_price'] + top_additnal_srvc_chrg         
        res['comsion_pprsn']       = (float(comsion_pprsn_perc) / 100) * (res['top_menu_price']+res['top_drinks_price'])
        res['comsion_menu']        = res['comsion_pprsn'] * float(no_of_covers)
        res['top_tot_price']       = res['top_tot_price_pprsn'] * float(no_of_covers)
        res['top_room_hire_price'] = rp_room_hire + top_rh_markup
        res['comsion_rh']          = (float(comsion_rh_perc) / 100 ) * res['top_room_hire_price']
        res['top_others_price']    = rp_others + top_others_markup
        res['top_tot_top_price']   = res['top_tot_price'] + res['top_room_hire_price'] + res['top_others_price'] 
        res['tot_profit']          = res['top_tot_top_price'] - res['rp_tot_rest_price']
        res['profit_on_comsion']   = res['comsion_menu'] + res['comsion_rh']         
        return{'value':res}
                 
cc_menu_details()   
