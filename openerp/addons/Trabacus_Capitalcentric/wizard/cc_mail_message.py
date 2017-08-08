from openerp import tools
from openerp.osv import osv, fields
from openerp import netsvc
import base64
import xmlrpclib
from openerp.tools import config
from dateutil.relativedelta import relativedelta
from dateutil import parser
from datetime import datetime
import openerp
from openerp import SUPERUSER_ID

host = str(config["xmlrpc_interface"])  or str("localhost"),
port = str(config["xmlrpc_port"])
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (host[0],port))


class mail_compose_message(osv.TransientModel):
    _inherit = 'mail.compose.message'
   
    def _get_msg_body(self, cr, uid, context=None):
        message_obj = self.pool.get('mail.message')
        body = ''
        if context and context.get('mail_foward',False):
           message_id = context.get('default_parent_id',False)
           if message_id:
              email_to = ''
              message = message_obj.browse(cr,uid,message_id)
              for pp in message.partner_ids:
                  email_to += pp.name + ' ,'
              email_to = email_to[:-1]
              body = '<font face="verdana">From: ' + str(message.author_id and message.author_id.name or message.email_from or '') + '<br>Sent: ' + str(message.date or '') + ' <br>To: ' + str(email_to or '') + '<br> Subject: ' + str(message.subject or '') +'</font>'              
              body += message.body
        return body 
    
    def _get_attachments(self, cr, uid, context=None):
        message_obj = self.pool.get('mail.message')
        attach = []
        if context and context.get('mail_foward',False):
           message_id = context.get('default_parent_id',False)
           if message_id:
              message = message_obj.browse(cr,uid,message_id)
              for att in message.attachment_ids:
                  attach.append(att.id)
        return attach
    
    def get_default_Partnermap(self, cr, uid, context=None):    
        
        model_obj = context and context.get('active_model',False)
        data = context and context.get('active_id',False)
        
        val=[]
        if model_obj == 'crm.lead' and data:
           parent_obj = self.pool.get(model_obj)  
           lead = parent_obj.browse(cr,uid,data)
           for i in lead.info_ids:
               val.append(i.restaurant_id.id)
        return val

    def _get_partner_ids(self, cr, uid,ids,field_name, args, context=None):
        
        res = {}
        for case in self.browse(cr,uid,ids):
            val = self.get_default_Partnermap(cr, uid, context=context)
            res[case.id] = val
        return res
    
    _columns = {'partner_mapping': fields.function(_get_partner_ids, method=True, string='Partner Mapping', type='text'),
                'ccattachment_id': fields.many2one('ir.attachment','Venue Documents', domain="[('partner_id', 'in', partner_mapping)]"),
                'reminder_time' : fields.integer('Reminder Time'),
                }
    
    _defaults={
               'partner_mapping':get_default_Partnermap,
               'body':_get_msg_body,
               'attachment_ids':_get_attachments,
               }
    
    def onchange_attachments(self, cr, uid, ids, ccattachment_id, attachment_ids,context=None):
        res = {}
        s = set()
        if ccattachment_id:
           s.add(ccattachment_id)
           for at in attachment_ids:
                s.add(at[1])
        attach_ids = list(s)
        res['attachment_ids'] = [(4,attach_ids)]
        return{'value':res}
     
    #Inherited     
    def send_mail(self, cr, uid, ids, context=None):    
        template_obj = self.pool.get('email.template')
        for case in self.browse(cr,uid,ids):       
            if case.template_id: 
               template = case.template_id 
               context.update({'mail_server_id':template.mail_server_id.id, 'email_from':template.email_from,'reply_to':template.reply_to})
        
        res = super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)
        
        if not context:
           return context
            
        model_obj = self.pool.get(context.get('active_model'))        
        data = context.get('active_id')
        Lead_obj = self.pool.get('crm.lead')
        sale_obj = self.pool.get('sale.order')        
        reminder_obj = self.pool.get('cc.reminder.time')
        attachment_obj = self.pool.get('ir.attachment')
        stage_obj = self.pool.get('crm.case.stage')
        
        for case in self.browse(cr,uid,ids):
            template_name =''
            if case.template_id:
               template_name = template_obj.browse(cr,uid,case.template_id).name 
               
            if context.get('active_model') == 'cc.send.rest.info':
               if context.get('service_type') == 'venue' :
                  context.update({'default_type' :'venue'})
               elif context.get('service_type') == 'noontea':
                  context.update({'default_type' :'noontea'})  
                
               rest_info = model_obj.browse(cr,uid,data)               
               if rest_info and rest_info.lead_id:
                  stage_id = False 
                  lead = Lead_obj.browse(cr,uid,rest_info.lead_id.id)
                  #To change Venue&Afternoon Tea Enquiry Stages                
                  if template_name in ('Enquiry - Send Quotation','AT-Offer'):
                     stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Offered')], context=context)
                                         
                  if template_name in ('Enquiry - Booking Confirmation To Venue','Enquiry - Booking Confirmation To Customer'):
                     stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Confirmed')], context=context)
                        
                  if template_name == 'AT - Guest Confirmation':
                     stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Guest Confirmation')], context=context)
                     
                  if template_name == 'AT - Restaurant Confirmation':
                     stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Restaurant Confirmation')], context=context)
                  
                  if template_name in ('Enquiry - Request Availability','AT-Request'):                            
                     stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Requested')], context=context)
                     model_obj.write(cr,uid,[data],{'request_sent':True})
                  
                  stage = stage_obj.browse(cr,uid,stage_id)                                          
                  if stage_id and stage.sequence > lead.stage_id.sequence:
                     Lead_obj.write(cr, uid, [lead.id], {'stage_id': stage_id}, context=context)                 
                  
                  reminder_ids = reminder_obj.search(cr, uid, [('template_id','=',case.template_id and case.template_id.id or False),('lead_id','=',lead.id)])
                  remind_time  = (parser.parse(datetime.now().strftime('%Y-%m-%d %H:%M')) + relativedelta(hours =+ case.reminder_time)).strftime('%Y-%m-%d %H:%M'),     
                  reminder_obj.write(cr,uid,reminder_ids,{'reminder_date':remind_time})
                      
            elif context.get('active_model') == 'crm.lead': 
               if template_name in ('Enquiry - Send With Menu and Pricing Details','Enquiry - Send With Menu Details'):               
                   if data:
                    lead = Lead_obj.browse(cr, uid, data)
                    stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Information Sent')], context=context)
                    stage = stage_obj.browse(cr,uid,stage_id)
                    
                    if stage_id and stage.sequence > lead.stage_id.sequence:
                        Lead_obj.write(cr, uid, [lead.id], {'stage_id': stage_id}, context=context) 
                    
                    reminder_ids = reminder_obj.search(cr, uid, [('template_id','=',case.template_id or False),('lead_id','=',lead.id)])
                    remind_time  = (parser.parse(datetime.now().strftime('%Y-%m-%d %H:%M')) + relativedelta(hours =+ case.reminder_time)).strftime('%Y-%m-%d %H:%M'),
                    reminder_obj.write(cr,uid,reminder_ids,{'reminder_date':remind_time})    

              
#             for att in case.attachment_ids: 
#                 if att.name in ('MenuOptions.pdf','Invoice.pdf','BookingConfirmation.pdf','AT-BookingConfirmation.pdf','Restaurant-Menu Options.pdf'):
#                    attachment_obj.unlink(cr,uid,att.id)  
  
        return True
       #Inherited
#     def onchange_template_id(self, cr, uid, ids, template_id, composition_mode, model, res_id, context=None):
#         res={}
#         user_obj = self.pool.get('res.users')
#         for user in user_obj.browse(cr,uid,[uid]):
#             USERPASS = user.password
#         partner_obj = self.pool.get('res.partner')
#         model_obj = context.get('active_model',False)
#         data = context.get('active_id',False)
#         temp_obj = self.pool.get('email.template')
#         soln_obj = self.pool.get('sale.order.line')
#         rest_info_obj = self.pool.get('cc.send.rest.info')
#         rep_obj = self.pool.get('ir.actions.report.xml')        
#         ir_attach_obj = self.pool.get('ir.attachment')
#         temp_name = temp_obj.browse(cr,uid,template_id)
#         vlus = super(mail_compose_message, self).onchange_template_id(cr, uid, ids, template_id, composition_mode, model, res_id, context=context)
#         if vlus:
#             res =  vlus['value']
#             
#             if not context:
#                 return vlus    
#             
#             if model_obj == 'crm.lead':
#                 
#                 lead_obj = self.pool.get(model_obj)
#                 temp_obj = self.pool.get('email.template')
#                 lead = lead_obj.browse(cr,uid,data)
#                 temp_name = temp_obj.browse(cr,uid,template_id)
#                 
#                 if temp_name.name in ('Enquiry - Send With Menu Details','Enquiry - Send With Menu and Pricing Details'):
#                     
#                     if temp_name.name == 'Enquiry - Send With Menu Details':
#                        sock.execute(cr.dbname,uid,USERPASS,'crm.lead','write',[lead.id],{'is_checked':False})
#                     elif temp_name.name == 'Enquiry - Send With Menu and Pricing Details':
#                          sock.execute(cr.dbname,uid,USERPASS,'crm.lead','write',[lead.id],{'is_checked':True})                
#                         
# #                    body = """<table border='2'> 
# #                                  <tr style='background-color:#AD4BC2;'> 
# #                                  <th><font color="white">Restaurant Name</font></th>
# #                                  <th><font color="white">Menu Description</font></th>
# #                                  <th><font color="white">Area</font></th>"""
# #                    if temp_name.name == 'Enquiry - Send With Menu and Pricing Details':
# #                       body += """<th><font color="white">Price/Cover</font></th>"""
# #                        
# #                    body += """</tr>"""
#                                    
# #                    for re in lead.info_ids:
# #                        row_cnt = 0
# #                        restaurant = '' 
# #                        cr.execute("select count(id) from cc_menus where partner_id = %d"%(re.restaurant_id.id))
# #                        count = cr.fetchone()
# #                        if count:row_cnt = count[0]  
# #                        flag = False
# #                        if re.restaurant_id and re.restaurant_id.parent_id:                            
# #                           restaurant += re.restaurant_id.parent_id and re.restaurant_id.parent_id.name + ',' 
# #                        body += """<tr style='background-color:#E3C9E8;'>
# #                                       <td>"""+ str(restaurant + re.restaurant_id.name or '') + """</td>
# #                                       <td> """ + str(re.menu_id and re.menu_id.description or '').replace("\n", "<br>")+""" </td>
# #                                       <td> """ + str(re.area or '') + """ </td>"""
# #                        
# #                        if temp_name.name == 'Enquiry - Send With Menu and Pricing Details':               
# #                           body += "<td>" + str(re.top_tot_top_price or 0.00) + "</td>"
# #                           
# #                        body += "</tr>"
# #                             
# #                    body += "</table>"
# #                    mail_body = res['body']
# #                    #Appending the content of a body to restaurant info template
# #                    mail_body = mail_body.replace('[Restaurant Info]',  body or '')
# #                    res['body'] = mail_body
#                     
#                     # report name is the service name given in pentaho report menu
#                     report_name = 'MenuOptions'  
#                     report_service = "report." + report_name
#                     service = netsvc.LocalService(report_service)
#                     (result, format) = service.create(cr, uid, [res_id], {'model': 'crm.lead'}, context)
#                     result = base64.b64encode(result)
#                     if not report_name:
#                         report_name = report_service
#                     ext = "." + format
#                     if not report_name.endswith(ext):
#                         report_name += ext                    
#                    
#                     attachment_obj = self.pool.get('ir.attachment')
#                     attval = {}
#                     """ To Execute the Queries outside the Openerp context due to concurrency """
#                     mId = sock.execute(cr.dbname,uid,USERPASS, 'ir.attachment' ,  'search', [('res_id','=',str(res_id)),('res_model','=','crm.lead'),('name','=',str(report_name))])
#                     file_att = cr.fetchall()
#                     for usr in user_obj.browse(cr,uid,[uid]):
#                         partner = usr.partner_id.id
#                  
#                     if not mId:
#                         attval = {
#                             'res_model'  : 'crm.lead',
#                             'res_name'   : str(report_name),
#                             'res_id'     : str(res_id),
#                             'datas'      : str(result) ,
#                             'type'       : 'binary',
#                             'datas_fname': str(report_name),
#                             'name'       : str(report_name),
#                             'partner_id' : partner,
#                              }
#                      
#                         attach_ids = sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','create',attval) 
#                         res['attachment_ids'] = [(4,[attach_ids] + res['attachment_ids'])]
#                     else:
#                          for f in mId:
#                             attval = { 
#                                 'datas'   :str(result) , 
#                                 }
#                             sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','write',mId,attval)
#                             res['attachment_ids'] = [(4,mId + res['attachment_ids'])]
#            
#                 
#             if model_obj == 'account.invoice':
#                 if temp_name.name in ('Invoice - Send Invoice','Invoice - Venues','Invoice - Afternoon Tea','Credit Note - Venues','Credit Note - Afternoon Tea','Invoice Reminder - Afternoon Tea','Invoice Reminder - Venues'):
#                     # report name is the service name given in pentaho report menu
#                     report_name = ''
#                     if temp_name.name in ('Invoice - Send Invoice','Invoice - Venues','Invoice - Afternoon Tea','Invoice Reminder - Afternoon Tea','Invoice Reminder - Venues'):
#                        report_name = 'Invoice'
#                     elif temp_name.name in ('Credit Note - Venues','Credit Note - Afternoon Tea'):
#                         report_name = 'Credit Note'  
#                     report_service = "report.Invoice" 
#                     rep_data = rep_obj.pentaho_report_action(cr, uid, report_name, res_id,None,None)
#                     report_instance = openerp.addons.pentaho_reports.core.Report('report.' + report_name, cr, uid, res_id, rep_data['datas'], context)                                
#                     result, output_type = report_instance.execute()
#                     result = base64.b64encode(result)
#                     
#                     if not report_name:
#                         report_name = report_service
#                     ext = "." + output_type
#                     if not report_name.endswith(ext):
#                         report_name += ext                    
# 
#                     """ To Execute the Queries outside the Openerp context due to concurrency """
# #                     vId = sock.execute(cr.dbname,uid,USERPASS, 'ir.attachment' ,  'search', [('res_id','=',str(res_id)),('res_model','=','account.invoice'),('name','=',str(report_name))])
# 
# #                     if not vId:
#                     attval = {
#                             'name': str(report_name),
#                             'datas': str(result),
#                             'datas_fname': str(report_name),
#                             'res_model': 'mail.compose.message',
#                             'res_id': 0,
#                             'type': 'binary'}
#               
#                     attach_ids = sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','create',attval)
# #                     attach_ids = ir_attach_obj.create(cr, SUPERUSER_ID, attval) 
#                     res['attachment_ids'].append(attach_ids)
# #                     else:
# #                         for f in vId:
# #                             attval = { 
# #                                 'name'   :str(report_name) , 
# #                                 }
# # #                             sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','write',vId,attval)
# #                             ir_attach_obj.write(cr, uid, vId, attval)
# #                             res['attachment_ids'].append(vId)
#                                         
#             if model_obj == 'cc.send.rest.info':
#                 if temp_name.name == 'Enquiry - Booking Confirmation To Venue':
#                         
#                      # report name is the service name given in pentaho report menu
#                     report_name = 'BookingConfirmation' 
#                     report_service = "report." + report_name
#                     service = netsvc.LocalService(report_service)
#                     (result, format) = service.create(cr, uid, [res_id], {'model': 'cc.send.rest.info'}, context)
#                     result = base64.b64encode(result)
#                     if not report_name:
#                         report_name = report_service
#                     ext = "." + format
#                     if not report_name.endswith(ext):
#                         report_name += ext
#                     
#                     aId = sock.execute(cr.dbname,uid,USERPASS, 'ir.attachment' ,  'search', [('res_id','=',str(res_id)),('res_model','=','cc.send.rest.info'),('name','=',str(report_name))])
#                     for usr in user_obj.browse(cr,uid,[uid]):
#                         partner = usr.partner_id.id
#                  
#                     if not aId:
#                         attval = {
#                             'res_model'  : 'cc.send.rest.info',
#                             'res_name'   : str(report_name),
#                             'res_id'     : str(res_id),
#                             'datas'      : str(result) ,
#                             'type'       : 'binary',
#                             'datas_fname': str(report_name),
#                             'name'       : str(report_name),
#                             'partner_id' : partner,
#                              }
#                      
#                         attach_ids = sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','create',attval)
#                         res['attachment_ids'] = [(4,[attach_ids] + res['attachment_ids'])]
#                     else:
#                          for f in aId:
#                             attval = { 
#                                 'datas'   :str(result) , 
#                                 }
#                             sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','write',aId,attval)
#                             res['attachment_ids'] = [(4,aId + res['attachment_ids'])]
#                     
#                 if temp_name.name in ('AT - Restaurant Confirmation','AT - Guest Confirmation'):
# #                    rest_info = rest_info_obj.browse(cr,uid,[res_id])
#                         
#                      # report name is the service name given in pentaho report menu
#                     report_name = 'AT-BookingConfirmation' 
#                     report_service = "report." + report_name
#                     service = netsvc.LocalService(report_service)
#                     (result, format) = service.create(cr, uid, [res_id], {'model': 'cc.send.rest.info'}, context)
#                     result = base64.b64encode(result)
#                     if not report_name:
#                         report_name = report_service
#                     ext = "." + format
#                     if not report_name.endswith(ext):
#                         report_name += ext
#                     
#                     aId = sock.execute(cr.dbname,uid,USERPASS, 'ir.attachment' ,  'search', [('res_id','=',str(res_id)),('res_model','=','cc.send.rest.info'),('name','=',str(report_name))])
#                     for usr in user_obj.browse(cr,uid,[uid]):
#                         partner = usr.partner_id.id
#                  
#                     if not aId:
#                         attval = {
#                             'res_model'  : 'cc.send.rest.info',
#                             'res_name'   : str(report_name),
#                             'res_id'     : str(res_id),
#                             'datas'      : str(result) ,
#                             'type'       : 'binary',
#                             'datas_fname': str(report_name),
#                             'name'       : str(report_name),
#                             'partner_id' : partner,
#                              }
#                      
#                         attach_ids = sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','create',attval)
#                         res['attachment_ids'] = [(4,[attach_ids] + res['attachment_ids'])]
#                     else:
#                          for f in aId:
#                             attval = { 
#                                 'datas'   :str(result) , 
#                                 }
#                             sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','write',aId,attval)
#                             res['attachment_ids'] = [(4,aId + res['attachment_ids'])]
#                  
#                 if temp_name.name in ('Enquiry - Send Quotation'):
# #                    rest_info = rest_info_obj.browse(cr,uid,[res_id])
#                         
#                      # report name is the service name given in pentaho report menu
#                     report_name = 'Restaurant-Menu Options' 
#                     report_service = "report." + report_name
#                     service = netsvc.LocalService(report_service)
#                     (result, format) = service.create(cr, uid, [res_id], {'model': 'cc.send.rest.info'}, context)
#                     result = base64.b64encode(result)
#                     if not report_name:
#                         report_name = report_service
#                     ext = "." + format
#                     if not report_name.endswith(ext):
#                         report_name += ext
#                     
#                     aId = sock.execute(cr.dbname,uid,USERPASS, 'ir.attachment' ,  'search', [('res_id','=',str(res_id)),('res_model','=','cc.send.rest.info'),('name','=',str(report_name))])
#                     for usr in user_obj.browse(cr,uid,[uid]):
#                         partner = usr.partner_id.id
#                  
#                     if not aId:
#                         attval = {
#                             'res_model'  : 'cc.send.rest.info',
#                             'res_name'   : str(report_name),
#                             'res_id'     : str(res_id),
#                             'datas'      : str(result) ,
#                             'type'       : 'binary',
#                             'datas_fname': str(report_name),
#                             'name'       : str(report_name),
#                             'partner_id' : partner,
#                              }
#                      
#                         attach_ids = sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','create',attval)
#                         res['attachment_ids'] = [(4,[attach_ids] + res['attachment_ids'])]
#                     else:
#                          for f in aId:
#                             attval = { 
#                                 'datas'   :str(result) , 
#                                 }
#                             sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','write',aId,attval)
#                             res['attachment_ids'] = [(4,aId + res['attachment_ids'])]
# 
#                 
#         return {'value':res}
    
    def onchange_template_id(self, cr, uid, ids, template_id, composition_mode, model, res_id, context=None):
        res={}
        if context is None : context = {}
        user_obj = self.pool.get('res.users')
        for user in user_obj.browse(cr,uid,[uid]):
            USERPASS = user.password
        partner_obj = self.pool.get('res.partner')
        model_obj = context.get('active_model') or context.get('default_model') or False
        data = context.get('active_id',False)
        temp_obj = self.pool.get('email.template')
        soln_obj = self.pool.get('sale.order.line')
        rest_info_obj = self.pool.get('cc.send.rest.info')
        rep_obj = self.pool.get('ir.actions.report.xml')
        ir_attach_obj = self.pool.get('ir.attachment')
        temp_name = temp_obj.browse(cr,uid,template_id)
        vlus = super(mail_compose_message, self).onchange_template_id(cr, uid, ids, template_id, composition_mode, model, res_id, context=context)
        if vlus:
            report_service= ''
            report_name =''
            res =  vlus['value']
            output_type = ''
            type = ''
            filename = ''
            result = False
            if not context:
                return vlus

            if model_obj == 'crm.lead':

                lead_obj = self.pool.get(model_obj)
                temp_obj = self.pool.get('email.template')
                lead = lead_obj.browse(cr,uid,data)
                temp_name = temp_obj.browse(cr,uid,template_id)

                if temp_name.name in ('Enquiry - Send With Menu Details','Enquiry - Send With Menu and Pricing Details'):

                    if temp_name.name == 'Enquiry - Send With Menu Details':
                       sock.execute(cr.dbname,uid,USERPASS,'crm.lead','write',[lead.id],{'is_checked':False})
                    elif temp_name.name == 'Enquiry - Send With Menu and Pricing Details':
                         sock.execute(cr.dbname,uid,USERPASS,'crm.lead','write',[lead.id],{'is_checked':True})
                    # report name is the service name given in pentaho report menu
                    filename = report_name = 'MenuOptions'

            if model_obj == 'account.invoice':
                if temp_name.name in ('Invoice - Send Invoice','Invoice - Venues','Invoice - Afternoon Tea','Credit Note - Venues','Credit Note - Afternoon Tea','Invoice Reminder - Afternoon Tea','Invoice Reminder - Venues','Invoice Reminder 2 - Venues'):
                    # report name is the service name given in pentaho report menu
                    filename = ''
                    if temp_name.name in ('Invoice - Send Invoice','Invoice - Venues','Invoice - Afternoon Tea','Invoice Reminder - Afternoon Tea','Invoice Reminder - Venues','Invoice Reminder 2 - Venues'):
                       filename = 'Invoice'
                    elif temp_name.name in ('Credit Note - Venues','Credit Note - Afternoon Tea'):
                        filename = 'Credit Note'
                    report_name = "Invoice"

            if model_obj == 'account.voucher':
               vouch_obj = self.pool.get(model_obj)
               vouch = vouch_obj.browse(cr,uid,data)
               if vouch.type =='receipt':
                  filename = 'Receipt'
               else:
                  filename = 'Remitanceadvice'

               report_name = "Receipt_Payment"

            if model_obj == 'cc.send.rest.info':
                if temp_name.name == 'Enquiry - Booking Confirmation To Venue':
                     # report name is the service name given in pentaho report menu
                    filename = report_name = 'BookingConfirmation'
                if temp_name.name == 'Enquiry - Booking Confirmation To Venue1':
                     # report name is the service name given in pentaho report menu
                    filename = report_name = 'to_bookingconfirm'
                    type = 'rp'
                if temp_name.name == 'Enquiry - Booking Confirmation To Customer':
                     # report name is the service name given in pentaho report menu
                    filename = report_name = 'to_bookingconfirm'
                    type ='top'
#                     report_service = "report." + report_name
                if temp_name.name in ('AT - Restaurant Confirmation','AT - Guest Confirmation'):
                     # report name is the service name given in pentaho report menu
                    filename = report_name = 'AT-BookingConfirmation'
                if temp_name.name in ('Enquiry - Send Quotation'):
                     # report name is the service name given in pentaho report menu
                    filename = report_name = 'Restaurant-Menu Options'


            if report_name:
                report_service = "report." + report_name
                rep_data = rep_obj.pentaho_report_action(cr, uid, report_name, res_id,None,None)
                if type:
                   rep_data['datas']={'variables':{'cc_type' : type}}
                print 'rep_data',rep_data
                report_instance = openerp.addons.pentaho_reports.core.Report(report_service, cr, uid, res_id, rep_data['datas'], context)
                try:
                    result, output_type = report_instance.execute()
                    result = base64.b64encode(result)
                except:
                    result = {}
            if not filename and report_service:
                filename = report_service
            ext = "." + output_type
            if not filename.endswith(ext):
                filename += ext
            if result:
                attval = {
                        'name': str(filename),
                        'datas': str(result),
                        'datas_fname': str(filename),
                        'res_model': 'mail.compose.message',
                        'res_id': 0,
                        'type': 'binary'}

                attach_ids = sock.execute(cr.dbname,uid,USERPASS,'ir.attachment','create',attval)
                res['attachment_ids'].append(attach_ids)


        return {'value':res}
    
    

mail_compose_message()
