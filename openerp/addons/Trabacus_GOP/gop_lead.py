from openerp.osv import fields, osv
from openerp.tools.translate import _
import re
from datetime import datetime
from dateutil import parser
import time
from openerp import tools
 
class crm_lead(osv.osv):
    _inherit = 'crm.lead'
     
        # Automatically creation of Lead from website interface
    def message_new(self, cr, uid, msg, custom_values=None,  context=None): 
        """ This functionality To Create Lead Automatically From Mails 
        """
        res = False
        subject = 'subject' in msg and msg.get('subject') or ''
        email_from = msg.get('from')
        email_from_add = email_from[email_from.find("<")+1:email_from.find(">")]
        contact  = '' 
        body = re.sub("<.*?>", "", msg.get('body'))
        body = re.sub("\s\s+" , " ", body)
        body = re.sub(r'<.+?>', '', body)
        body = re.sub('<[^>]*>', '', body)
        body = body.replace("*", "")
        body = body.replace("\n", " ")
        body = body.replace("&nbsp;", "")
        body = body.replace("&amp;", "&")
        body = body.replace("&#13;", "")
        body = body.replace("&gt;", "")
        body  = re.sub(' +',' ',body) # To Remove Multiple spaces
         
        if body:
            body_new = body.replace('*', '')
            body_msg = re.sub('[ \t]+', ' ', body_new)
            body = body_msg.encode('ascii', 'ignore')
            sub = subject.strip() 
            Rply =  sub[0:sub.find('Re:')+3].strip()
            Fwd =  sub[0:sub.find('Fwd:')+4].strip()
            if Rply == 'Re:' or Fwd == 'Fwd:':
                return True 
            if 'We have selected Purple Voyages' in subject : 
                res = self.Lead_frm_Purple_Voyages(cr,uid,body,subject,contact,email_from_add,context=None)   
            if 'Booking Enquiry No' in subject and 'HolidayIQ' in subject :
                res = self.Lead_Frm_HolidayIQ(cr,uid,body,subject,email_from_add,context=None)    
            if 'Enquiry on Gopurple.in' in subject :
                res = self.Lead_Frm_Gopurple_in(cr,uid,body,subject,email_from_add,context=None)    
            elif 'Enquiry on Gopurple' in subject :
                res = self.Lead_Frm_Gopurple(cr,uid,body,subject,email_from_add,context=None)    
            if 'Enquiry from website' in subject :
                res = self.Lead_Frm_website(cr,uid,body,subject,email_from_add,context=None)    
        return 

    def Lead_Frm_website(self,cr,uid,body,subject,email_from_add,context=None):
        
        country_obj = self.pool.get('res.country')
        leadtmp_obj = self.pool.get('tr.lead.template')
        if body:
           
            cus_email =cus_name = cus_city =cus_mob = dest =pack = cus_country = no_nyt = country = dest_nonyt=''
            cat =strt_dt = ppl = adult = kid = flex_dt =ref = comment = trvl_typ =fp_trvl_typ =fp_categ =source = ''
            cur_lead_id = country_ids = False
            if 'Email-ID:' in body:
                cus_email = body[body.find('Email-ID:')+9:body.find('Name:')].strip()
            if 'Name:' in body:
                cus_name = body[body.find('Name:')+5:body.find('City:')].strip()
            if 'City:' in body:
                cus_city = body[body.find('City:')+5:body.find('Phone No:')].strip()
            if 'Phone No:' in body:
                cus_mob = body[body.find('Phone No:')+9:body.find('Destination')].strip()
            if 'Destination' in body: 
                dest_nonyt = body[body.find('Destination')+11:body.find('No of nights')].strip()
                if 'Packagename' in dest_nonyt:
                    pack = dest_nonyt[dest_nonyt.find('Packagename')+11:body.find('No of nights')].strip()
                elif 'Country' in dest_nonyt: 
                    cus_country =  dest_nonyt[dest_nonyt.find('Country')+7:body.find('No of nights')].strip()
                    if cus_country: country_ids = country_obj.search(cr, uid, [('name', '=', cus_country) ])
            if 'No of nights' in body: 
                no_nyt = body[body.find('No of nights')+12:body.find('Category')].strip()
            if 'Category' in body: 
                cat = body[body.find('Category')+8:body.find('Start Date')].strip()
                if cat == 'Domestic': 
                    trvl_typ = 'dom_package'
                    fp_trvl_typ = 'domestic'
                    fp_categ = 'holiday'
                if cat == 'International': 
                    trvl_typ = 'int_package'
                    fp_trvl_typ = 'international'
                    fp_categ = 'holiday'
                if cat == 'Cruise': 
                    trvl_typ = 'cruise'
                    fp_trvl_typ = 'international'
                    fp_categ = 'cruise'                    
            if 'Start Date' in body: 
                strt_dt = body[body.find('Start Date')+10:body.find('No of adults')].strip()
            if 'No of adults' in body: 
                ppl = body[body.find('No of adults')+12:body.find('Start date flexible')].strip()
                if 'No. of children' in ppl:
                    adult = ppl[0:ppl.find('No. of children')].strip()
                    try:
                        adult = int(adult)
                    except ValueError:
                        adult=0
                    kid = ppl[ppl.find('No. of children')+15:].strip()  
                    try:
                        kid = int(kid)
                    except ValueError:
                        kid=0
            if 'Start date flexible' in body:
                if 'Comment' in body: 
                    flex_dt = body[body.find('Start date flexible')+19:body.find('Comment')].strip()
                    comment = body[body.find('Comment')+7:body.find('Reference')].strip()
                elif 'Reference' in body:
                    flex_dt = body[body.find('Start date flexible')+19:body.find('Reference')].strip()
            if 'Source' in body:
                ref = body[body.find('Reference')+9:body.find('Source')].strip()
                source  = body[body.find('Source')+6:].strip()
            channel = self.pool.get('crm.case.channel').search(cr,uid,[('name','=','Website')])
            
            # To Create a tmplatevals in tr_lead_template Object and pass template_id in crm_lead
            tmplatevals = {
                         'traveldate'       : strt_dt and strt_dt or '',
                         'adults'           : adult and adult or 0,
                         'cwb'              : kid and kid or 0,
                         'infant'           : 0,
                         'requirement'      : (flex_dt and 'Start date flexible :' + flex_dt+ '\n' + '\n' or '')+
                                                (comment and 'Comment :' + comment or ''),
                       }
            
            lead_tmplate_id = leadtmp_obj.create(cr, uid, tmplatevals, context)
            
            leadvals = {
                 'name'             : (dest and dest or ''  )+ (pack and ' - '+pack or ' ' ) + (no_nyt and ' - '+no_nyt or ''),
                 'partner_name'     : cus_name and cus_name or '',
                 'email_from'       : cus_email and cus_email or '',   
                 'mobile'           : cus_mob and cus_mob or  '',
                 'country_id'       : country_ids and country_ids[0] or False,
                 'city'             : cus_city or '',
                'template_id'       : lead_tmplate_id and lead_tmplate_id or False,
    # defaults
                 'type'             : 'opportunity',
                 'channel_id'       :  channel and channel[0] or False,
                 'channel'          :  (ref and ref + ' - ' or '') + (source and source or ''),
                 'paxtype'          : 'fit',
                 'purpose'          : 'leisure',
                 'date_action'      :  datetime.today(),
                 'user_id'          :  False,  'consultant_id'          :  False, 
                 'manager_id'       :  False  
                   }
            cur_lead_id = self.create(cr, uid, leadvals, context)
        return True

    def Lead_Frm_Gopurple(self,cr,uid,body,subject,email_from_add,context=None):
       
        country_obj = self.pool.get('res.country')
        leadtmp_obj = self.pool.get('tr.lead.template')
        if body:
            cus_email = cus_name = cus_city = cus_mob = dest = cus_country = no_nyt =room = strt_dt = budget = ppl = adult = kid = flex_dt = ''
            cur_lead_id = False
            
            if 'Email-ID:' in body:
                cus_email = body[body.find('Email-ID:')+9:body.find('Name:')].strip()
            if 'Name:' in body:
                cus_name = body[body.find('Name:')+5:body.find('City:')].strip()
            if 'City:' in body:
                cus_city = body[body.find('City:')+5:body.find('Phone No:')].strip()
            if 'Phone No:' in body:
                cus_mob = body[body.find('Phone No:')+9:body.find('Destination')].strip()
            if 'Destination' in body: 
                dest = body[body.find('Destination')+11:body.find('Country')].strip()
            if 'Country:' in body: 
                cus_country = body[body.find('Country:')+8:body.find('No of nights')].strip()
                if cus_country: country_ids = country_obj.search(cr, uid, [('name', '=', cus_country) ])
            if 'No of nights' in body: 
                no_nyt = body[body.find('No of nights')+12:body.find('No of adults')].strip()
            if 'No of adults' in body: 
                ppl = body[body.find('No of adults')+12:body.find('No. of rooms')].strip()
                if 'No. of children' in ppl:
                    adult = ppl[0:ppl.find('No. of children')].strip()
                    try:
                        adult = int(adult)
                    except ValueError:
                        adult=0
                    kid = ppl[ppl.find('No. of children')+15:].strip()  
                    try:
                        kid = int(kid)
                    except ValueError:
                        kid=0
            if 'No. of rooms' in body: 
                room = body[body.find('No. of rooms')+12:body.find('Budget per day')].strip()
            if 'Budget per day' in body: 
                budget = body[body.find('Budget per day')+14:body.find('Start Date')].strip()
            if 'Start Date:' in body: 
                strt_dt = body[body.find('Start Date:')+11:body.find('Start date flexible')].strip()
            if 'Start date flexible' in body: 
                flex_dt = body[body.find('Start date flexible')+19:].strip()
            channel = self.pool.get('crm.case.channel').search(cr,uid,[('name','=','Website')])    
            # To Create a Vals in tr_lead_template Object and pass template_id in crm_lead
            tmplatevals = {
                         'traveldate'       : strt_dt and strt_dt or '',
                         'adults'           : adult and adult or 0,
                         'cwb'              : kid and kid or 0,
                         'infant'           : 0,
                         'requirement'      :(room and 'No. of rooms :' + room+ '\n' + '\n' or '' ) + 
                                                (flex_dt and 'Start date flexible :' + flex_dt or ''),
                        'budget'           : budget and budget or '',                                                     
                       }
            
            lead_tmplate_id = leadtmp_obj.create(cr, uid, tmplatevals, context)

            leadvals = {
                 'name'             : (dest and dest or ''  )+ (no_nyt and ' - ' + no_nyt or ''),
                 'partner_name'     : cus_name and cus_name or '',
                 'email_from'       : cus_email and cus_email or '',   
                 'mobile'           : cus_mob and cus_mob or '',
                 'country_id'       : country_ids and country_ids[0] or False,
                 'city'             : cus_city and cus_city or '',
                 'template_id'      : lead_tmplate_id and lead_tmplate_id or False,
                 # defaults
                 'type'             : 'opportunity',
                 'channel_id'       : channel and channel[0] or False,
                 'paxtype'          : 'fit',
                 'purpose'          : 'leisure',
                 'date_action'      :  datetime.today(),
                 'user_id'          :  False,  'consultant_id'          :  False, 
                 'manager_id'       :  False  
                   }
            cur_lead_id = self.create(cr, uid, leadvals, context)
        return True

    def Lead_Frm_Gopurple_in(self,cr,uid,body,subject,email_from_add,context=None):
       
        leadtmp_obj = self.pool.get('tr.lead.template')
        country_obj = self.pool.get('res.country')
        if body:
            cus_email =cus_name =cus_city =cus_mob =dest =pack =cus_country= no_nyt =pack_cat =strt_dt =ppl =adult =kid =flex_dt = ''
            cur_lead_id = False
            
            if 'Email-ID:' in body:
                cus_email = body[body.find('Email-ID:')+9:body.find('Name:')].strip()
            if 'Name:' in body:
                cus_name = body[body.find('Name:')+5:body.find('City:')].strip()
            if 'City:' in body:
                cus_city = body[body.find('City:')+5:body.find('Phone No:')].strip()
            if 'Phone No:' in body:
                cus_mob = body[body.find('Phone No:')+9:body.find('Destination')].strip()
            if 'Destination' in body: 
                dest = body[body.find('Destination')+11:body.find('Packagename')].strip()
            if 'Packagename' in body: 
                pack = body[body.find('Packagename')+11:body.find('No of nights')].strip()
            if 'No of nights' in body: 
                no_nyt = body[body.find('No of nights')+12:body.find('Package Category')].strip()
            if 'Package Category' in body: 
                pack_cat = body[body.find('Package Category')+16:body.find('Start Date')].strip()
            if 'Start Date' in body: 
                strt_dt = body[body.find('Start Date')+10:body.find('No of adults')].strip()
            if 'No of adults' in body: 
                ppl = body[body.find('No of adults')+12:body.find('Start date flexible')].strip()
                if 'No. of children' in ppl:
                    adult = ppl[0:ppl.find('No. of children')].strip()
                    try:
                        adult = int(adult)
                    except ValueError:
                        adult=0
                    kid = ppl[ppl.find('No. of children')+15:].strip()  
                    try:
                        kid = int(kid)
                    except ValueError:
                        kid=0
            if 'Start date flexible' in body: 
                flex_dt = body[body.find('Start date flexible')+19:25].strip()
            else:
                flex_dt = ''
            channel = self.pool.get('crm.case.channel').search(cr,uid,[('name','=','Website')])     
            
            # To Create a Vals in tr_lead_template Object and pass template_id in crm_lead
            tmplatevals = {
                         'traveldate'       : strt_dt and strt_dt or '',
                         'adults'           : adult and adult or 0,
                         'cwb'              : kid and kid or 0,
                         'infant'           : 0,
                         'requirement'      :  (pack_cat and 'Package Category :' + pack_cat  + '\n' + '\n' or '') + 
                                               (flex_dt and 'Start date flexible :' + flex_dt or ''),
                       }
            lead_tmplate_id = leadtmp_obj.create(cr, uid, tmplatevals, context)
            
            leadvals = {
                 'name'             : (dest and dest or ''  )+ (pack and ' - '+pack or ' ' ) + (no_nyt and ' - '+no_nyt or ''),
                 'partner_name'     : cus_name and cus_name or '',
                 'email_from'       : cus_email and cus_email or '',   
                 'mobile'           : cus_mob and cus_mob or '',
                 'country_id'       : False,
                 'city'             : cus_city and cus_city or '',
                 'template_id'      : lead_tmplate_id and lead_tmplate_id or False,
                 
                 # defaults
                 'type'             : 'opportunity',
                 'channel_id'       :  channel and channel[0] or False,
                 'paxtype'         : 'fit',
                 'purpose'          : 'leisure',
                 'date_action'      :  datetime.today(),
                 'user_id'          :  False,  'consultant_id'          :  False, 
                 'manager_id'       :  False  
                   }
            cur_lead_id = self.create(cr, uid, leadvals, context)
        return True
            
    def Lead_Frm_HolidayIQ(self,cr,uid,body,subject,email_from_add, context=None):  

        leadtmp_obj = self.pool.get('tr.lead.template')
        country_obj = self.pool.get('res.country')
        if body:
            cus_name = cus_city = cus_mob = cus_email = adult = kid = infant =trvl_dt =sel_pack =url = pref =ppl =pref_url = ''
            cur_lead_id = country_ids = False            
            if 'User Name:' in body:
                cus_name = body[body.find('User Name:')+10:body.find('City of Residence')].strip()
            if 'City of Residence' in body:
                cus_city = body[body.find('City of Residence:')+18:body.find('Phone Number')].strip()
            if 'Phone Number' in body:
                cus_mob = body[body.find('Phone Number:')+13:body.find('Email')].strip()
            if 'Email' in body: 
                cus_email = body[body.find('Email:')+6:body.find('Adults')].strip()
            if 'Email' in body and 'Date of Travel[From Date]' in body:
                ppl = body[body.find('Adults:')+7:body.find('Date of Travel[From Date]')].strip() 
                if 'Children' in ppl: 
                    adult = ppl[0:ppl.find('Children')].strip()
                    try:
                        adult = int(adult)
                    except ValueError:
                        adult=0
                    if 'Infants' in ppl:
                        kid = ppl[ppl.find('Children:')+9:ppl.find('Infants')].strip()  
                        try:
                            kid = int(kid)
                        except ValueError:
                            kid=0
                        infant = ppl[ppl.find('Infants:')+8:].strip()  
                        try:
                            infant = int(infant)
                        except ValueError:
                            infant=0
                    else:
                        kid = ppl[ppl.find('Children:')+9:].strip()
                        try:
                            kid = int(kid)
                        except ValueError:
                            kid=0
            if 'Date of Travel[From Date]' in body:
                trvl_dt = body[body.find('Date of Travel[From Date]:')+26:body.find('Selected Package')].strip()
            if 'Selected Package' in body:
                sel_pack = body[body.find('Selected Package:')+17:body.find('Package URL')].strip()
            if 'Package URL' in body:
                pref_url = body[body.find('Package URL:')+12:body.find('If you need assistance on this matter')].strip()
                if 'Preferences' in body:
                    url = pref_url[:pref_url.find('Preferences')].strip()
                    pref = pref_url[pref_url.find('Preferences:')+12:pref_url.find('If you need assistance on this matter')].strip()
                else:
                    url = pref_url    
            country_ids = country_obj.search(cr, uid, [('name', '=', 'India')])
            channel = self.pool.get('crm.case.channel').search(cr,uid,[('name','=','Website')])
            # To Create a Vals in tr_lead_template Object and pass template_id in crm_lead
            tmplatevals = {
                         'traveldate'       : trvl_dt and trvl_dt or '',
                         'adults'           : adult and adult or 0,
                         'cwb'              : kid and kid or 0,
                         'infant'           : infant and infant or 0,
                         'requirement'      :  (sel_pack and 'Selected Package :' + sel_pack + '\n' + '\n' or '') + (pref and 'Preferences & requirements : ' + pref or '') ,
                       }
            
            lead_tmplate_id = leadtmp_obj.create(cr, uid, tmplatevals, context)

            leadvals = {
                 'name'             : subject or '',
                 'partner_name'     : cus_name or '',
                 'email_from'       : cus_email or '',   
                 'mobile'           : cus_mob or '',
                 'country_id'       : country_ids and country_ids[0] or False,
                 'city'             : cus_city or '',
                 'channel'          : url or '',
                 'template_id'      : lead_tmplate_id and lead_tmplate_id or False,
                 # defaults
                 'type'             : 'opportunity',
                 'channel_id'       : channel and channel[0] or False,
                 'paxtype'          : 'fit',
                 'purpose'          : 'leisure',
                 'date_action'      :  datetime.today(),
                 'user_id'          :  False,  'consultant_id'          :  False, 
                 'manager_id'       :  False  
                   }
            cur_lead_id = self.create(cr, uid, leadvals, context)
        return True

    def Lead_frm_Purple_Voyages(self,cr,uid,body,subject,contact,email_from_add, context=None):  
        
        leadtmp_obj = self.pool.get('tr.lead.template')
        country_obj = self.pool.get('res.country')
        if body:
            cus_det = cus_name = cus_country= adult= kid= cus_mob= cus_email= psg_type= ''
            plnd_arr= enq_page= duration= tour_styl= budget=intrsd = pref = ''
            cur_lead_id = False    
            if 'Your Trip Information' in body:
                cus_det = body[body.find('Your Trip Information')+21:].strip()
                cus_name = cus_det[0:cus_det.find('India')].strip()
                cus_country = cus_det [cus_det.find('(')+1:cus_det.find(')')].strip()
                if cus_country: country_ids = country_obj.search(cr, uid, [('name', '=', cus_country) ])
                if 'Interested in :' in cus_det:
                    intrsd = cus_det[cus_det.find('Interested in :')+15:cus_det.find('Requirements')].strip()
                if 'Requirements :' in cus_det:
                    pref = cus_det[cus_det.find('Requirements :')+14:cus_det.find('Phone')].strip()
                if 'Phone:' in cus_det:
                    cus_mob = cus_det[cus_det.find('Phone:')+6:cus_det.find('People')].strip()
                if 'Email :' in cus_det:                        
                    cus_email = cus_det[cus_det.find('Email :')+7:cus_det.find('Duration')].strip()
            if 'People :' in body:
                adult_kid = body[body.find('People :')+8:body.find('Planned Arrival')].strip()
                if 'Adult' in adult_kid:
                    adult = adult_kid[0:adult_kid.find('Adult')].strip()
                    psg_type = 'fit'
                    try:
                        adult = int(adult)
                    except ValueError:
                        adult=0
                else:
                    adult = 0    
                if 'Group' in adult_kid:
                    psg_type = 'group' 
                if 'Kid' in adult_kid:
                    kid1 = adult_kid[:adult_kid.find('Kid')].strip()
                    kid = kid1[-2:]  
                    try:
                        kid = int(kid)
                    except ValueError:
                        kid=0
                else:
                    kid = 0
            if 'Planned Arrival :' in body:                        
                plnd_arr = body[body.find('Planned Arrival :')+17:body.find('Enquiry Page:')].strip()
            if 'Enquiry Page:' in body:                        
                enq_page = body[body.find('Enquiry Page:')+13:body.find('Email')].strip()
            if 'Duration :' in body:
                duration = body[body.find('Duration :')+10:body.find('Tour Style')].strip()
            if 'Tour Style :' in body:                        
                tour_styl = body[body.find('Tour Style :')+12:body.find('Budget')].strip()
            if 'Budget :' in body:                        
                budget = body[body.find('Budget :')+8:body.find('Note')].strip()
            channel = self.pool.get('crm.case.channel').search(cr,uid,[('name','=','Website')])  
            # To Create a Vals in tr_lead_template Object and pass template_id in crm_lead
            tmplatevals = {
                         'traveldate'       : plnd_arr and plnd_arr or '',
                         'adults'           : adult and adult or 0,
                         'cwb'              : kid and kid or 0,
                         'requirement'      : (pref and 'Requirements : ' + pref + '\n' + '\n' or '' )+(intrsd and 'Interested in : ' + intrsd + '\n' + '\n' or '' )+ (tour_styl and 'Tour Style : ' + tour_styl + '\n' + '\n' or '' )+ (duration and 'Duration of Visit : ' + duration or ''),
                         'budget'           : budget and budget or '',                                                     
                       }
            
            lead_tmplate_id = leadtmp_obj.create(cr, uid, tmplatevals, context)

            leadvals = {
                 'name'             : 'Interested In ' + intrsd ,
                 'partner_name'     : cus_name or '',
                 'email_from'       : cus_email or '',   
                 'mobile'           : cus_mob or '',
                 'country_id'       : country_ids and country_ids[0] or False,
                 'channel'          : enq_page or '',
                 'template_id'      : lead_tmplate_id and lead_tmplate_id or False,
                 'type'            : 'opportunity',
                 'channel_id'      : channel and channel[0] or False,
                 'paxtype'         :  psg_type or 'fit',
                 'purpose'         : 'leisure',
                 'date_action'     :  datetime.today(),
                 'user_id'         :  False,  'consultant_id'          :  False, 
                 'manager_id'      :  False  
                   }
            cur_lead_id = self.create(cr, uid, leadvals, context)
        return True

# To Create Customer When We Click On Create Customer and also That name Should pop up in partenr_id                    
#     def create_customer(self, cr, uid, ids, context=None):
#         """ For Creating New Partner 
#         """
#         partner_obj = self.pool.get('res.partner')
#         country_obj = self.pool.get('res.country')
#         state_obj = self.pool.get('res.country.state')
#         
#         for case in self.browse(cr, uid, ids):
# #            if not case.lead_no:
# #                raise osv.except_osv(_('Warning!'), _('Please Select The Qualify Button TO Qualify The Record.'))
#             if case.partner_name==False or case.mobile==False or case.email_from==False:
#                 raise osv.except_osv(_('Warning'), _('Ensure That Customer Name , Phone And Email Are Entered Properly'))
#             partner_ids = partner_obj.search(cr,uid,['|',('mobile','=',case.mobile ),('email','=',case.email_from)])
#             if not partner_ids:
#                partner_id = partner_obj.create(cr, uid, {'name'     : case.partner_name,
#                                                        'state_id'   : state_ids and state_ids[0] or False,
#                                                        'zip'        : case.gop_zip and case.gop_zip or '',
#                                                        'country_id' : country_ids and country_ids[0] or False,
#                                                        'mobile'     : case.mobile and case.mobile or '',
#                                                        'email'      : case.email_from and case.email_from or '',
#                                                        'customer'   : True,
#                                                        'is_company' : True})
#                self.write(cr, uid, [case.id], {'partner_id' : partner_id or False}) 
#             else:
#                 raise osv.except_osv(_('Warning!'), _('Contact already exists.'))
#                      
#         return True
     
crm_lead()        