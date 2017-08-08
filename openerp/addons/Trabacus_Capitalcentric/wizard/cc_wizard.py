from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import base64
from openerp.osv.orm import browse_record, browse_null
import time
from dateutil import parser
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import orm

class cc_account_vat_details(osv.osv_memory): 
    """
    For VAT Details
    """
    def _get_period(self, cr, uid, context=None):
        """Return default period value"""
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False

    _name = "cc.account.vat.details"
    _description = "Account VAT Details"
    _columns = {
       'period_id': fields.many2one('account.period', \
                                    'Period From',  \
                                    ),
       'period_to': fields.many2one('account.period', \
                                    'Period To',  \
                                    ),
       'target_move': fields.selection([('posted', 'All Posted Entries'),
                                        ('all', 'All Entries'),
                                        ], 'Target Moves', required=True),
    }
    _defaults={
               'period_id': _get_period,
               'period_to': _get_period,
               'target_move' : 'posted'
               }
    def print_report(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            data = {}
            period_id = [case.period_id.id,case.period_to.id]
            period_name = str(case.period_id.name) +" To "+str(case.period_to.name)
            cr.execute("select id from account_period where date_start >='"+str(case.period_id.date_start)+"' and date_stop <='"+str(case.period_to.date_stop)+"'")
            period_id = [r[0] for r in cr.fetchall()]
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = 'xls'
            print "period_id",period_name
            data['variables'] = {'period_name':period_name,'period_id':period_id}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'VAT Details',
            'datas': data,
    }
      
cc_account_vat_details()

class cc_profit_commission(osv.osv_memory):
    """
    Booking Details report of Venues and Afternoon Tea
    """
    _name = "cc.profit.commission"
    _description = "Profit & Commission"
    _columns = {
                'date_filter'   : fields.selection([('date_created','Date Created'),('date_booking','Date Of Booking')],'Date Filter'),
                'start_dt'      : fields.date('Start Date'),
                'end_dt'        : fields.date('End Date'),
                'service_typ'   : fields.selection([('venue','Venue'), ('noontea','Afternoon Tea'),('both','Both')],'Service Type'),
                'stage_ids'     : fields.many2many('crm.case.stage','profit_crm_rel','profit_id','stg_id','Stage'),
                'user_ids'      : fields.many2many('res.users','profit_user_rel','profit_id','usr_id','BO User'),
                'salesp_ids'    : fields.many2many('res.users','profit_salesp_rel','profit_id','sp_id','Sales Person'),
                'is_completed'  : fields.boolean('Completed/Invoiced/Paid'),  
                'orderby'       : fields.selection([('create_date','Date Created'),('date_requested','Date Of Booking')],'Order By'),
                'jasper_output' : fields.selection([('pdf','PDF'),('xls','Raw XLS')], 'Report Output'),
                             
               }              
#     'journal': fields.many2many('account.analytic.journal', 'ledger_journal_rel', 'ledger_id', 'journal_id', 'Journals'), 
    _defaults={
               'jasper_output':'xls',
               'orderby' :'create_date',
               'date_filter':'date_created',
               'service_typ':'both',
               'is_completed' : True
               }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(cc_profit_commission, self).default_get(cr, uid, fields, context=context)
        fiscal_obj = self.pool.get('account.fiscalyear')
        user_obj = self.pool.get('res.users')
        today = time.strftime("%Y-%m-%d")
        
        user_role = user_obj.read(cr,uid,uid,['role'])
        if user_role['role'] == 'bo':
           res['user_ids'] = [(6, 0, [uid])]  
        elif user_role['role'] == 'sp':
            res['salesp_ids'] = [(6, 0, [uid])]
        fiscal_ids = fiscal_obj.search(cr,uid,[('date_start','<=',today),('date_stop','>=',today)])
        if fiscal_ids:
           start_dt = fiscal_obj.read(cr,uid,fiscal_ids[0],['date_start'])
        
        res.update({'start_dt':start_dt['date_start'],
                    'end_dt':today})
        return res
    
    def print_report(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            sqlstr = ''
            if case.date_filter == 'date_created':
               sqlstr += """ where cl.create_date::date between '%s' and '%s' """%(case.start_dt,case.end_dt)
            else:
               sqlstr += """ where cl.date_requested::date between '%s' and '%s' """%(case.start_dt,case.end_dt)
            
            if case.service_typ in ('venue','noontea'):
               sqlstr += """ and cl.service_type = '%s'"""%(case.service_typ) 
            else:
               sqlstr += """ and cl.service_type in ('venue','noontea')"""
            
            if case.stage_ids:
               if len(case.stage_ids) == 1:
                  stage_ids ='('+str([x.id for x in case.stage_ids][0])+')'
               else:
                  stage_ids =(tuple([x.id for x in case.stage_ids]),) 
               sqlstr += """ and cl.stage_id in %s"""%(stage_ids)
            
            if case.user_ids:
               if len(case.user_ids) == 1:
                  user_ids ='('+str([x.id for x in case.user_ids][0])+')'
               else:
                  user_ids =(tuple([x.id for x in case.user_ids]),) 
               sqlstr += """ and cl.user_id in %s"""%(user_ids)
            
            if case.salesp_ids:
               if len(case.salesp_ids) == 1:
                  salesp_ids ='('+str([x.id for x in case.salesp_ids][0])+')'
               else:
                  salesp_ids =(tuple([x.id for x in case.salesp_ids]),) 
               sqlstr += """ and cl.sales_person in %s"""%(salesp_ids)            
            
            if case.is_completed:
               sqlstr += """ and si.is_completed = True and cl.state in ('open','done') """
            
            if case.orderby:
               sqlstr += """ order by cl.service_type,cl.%s"""%(case.orderby)
                
             
                
            cr.execute("""create or replace view cc_vw_profit_commission as
                          select cl.date_requested,
                                 cl.lead_no,
                                 cl.service_type,
                                 (case when cl.service_type = 'venue' then (select display_name from res_partner where id = cl.partner_id)
                                       else  cl.partner_name end )as customer,          
                                 cl.covers,
                                 (select (case when rp.parent_id is null then rp.name
                                               else (select name from res_partner where id = rp.parent_id) end)
                                  from res_partner rp 
                                  where rp.id = si.restaurant_id) as restaurant,
                                 (case when si.is_completed = true then si.tot_top_price else 0.00 end) as tot_top_price,
                                 (case when si.is_completed = true then si.tot_rest_price else 0.00 end) as tot_rest_price,
                                 (case when si.is_completed = true then si.tot_comsion else 0.00 end) as tot_comsion,
                                 (case when si.is_completed = true then si.noontea_comsion else 0.00 end) as noontea_comsion,
                                 cs.name as stage_name
                          from cc_send_rest_info si
                          inner join crm_lead cl on cl.id = si.lead_id
                          inner join crm_case_stage cs on cs.id = cl.stage_id
                          inner join res_users ru on ru.id = cl.user_id
                          left outer join res_users sl on sl.id = cl.sales_person 
                      """ + sqlstr)
                        
            if case.jasper_output in ('pdf','xls'):    
                data = {}
                data['ids'] = context.get('active_ids', [])
                data['model'] = context.get('active_model', 'ir.ui.menu')
                data['output_type'] = case.jasper_output
                data['variables'] = {                                
                                    'start_dt' : case.start_dt and (parser.parse(''.join((re.compile('\d')).findall(case.start_dt)))).strftime('%d/%m/%Y') or '',
                                    'end_dt'   : case.end_dt and (parser.parse(''.join((re.compile('\d')).findall(case.end_dt)))).strftime('%d/%m/%Y') or '',
                                    'orderby'  : case.orderby or '' 
                                    }
                return {'type': 'ir.actions.report.xml',
                        'report_name':'Profit/Commission', 
                        'datas':data,
                        }
cc_profit_commission()

class cc_enquiry_details(osv.osv_memory):
    """
    Booking Details report of Venues and Afternoon Tea
    """
    _name = "cc.enquiry.details"
    _description = "Enquiry Details"
    _columns = {
                'date_filter'  : fields.selection([('date_created','Date Created'),('date_booking','Date Of Booking')],'Date Filter'),
                'venue_filter'  : fields.selection([('group','Group'),('restaurant','Restaurant')],'Filter'),
                'start_dt' : fields.date('Start Date'),
                'end_dt': fields.date('End Date'),
                'service_typ'  : fields.selection([('venue','Venue'), ('noontea','Afternoon Tea')],'Service Type'),
                'passen_type'  : fields.selection([('group','Group'), ('fit','FIT For Purpose')],'Booking Type'),
                'customer_id'      : fields.many2one('res.partner','Partner'),
                'customer'         : fields.char('Customer',size=125),
                'venue_id'         : fields.many2one('res.partner','Restaurant'),
                'venue_inv_id'     : fields.many2one('res.partner','Group'),
                'stage_id'         : fields.many2one('crm.case.stage','Stage'),  
                'orderby'          : fields.selection([('create_date','Date Created'),('date_requested','Date Of Booking')],'Order By'),
                'jasper_output': fields.selection([('pdf','PDF'),('xls','Raw XLS')], 'Report Output'),             
               }               
    _defaults={
               'jasper_output':'xls',
               'orderby' :'create_date',
               }
    def print_report(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            if case.jasper_output in ('pdf','xls'):    
                data = {}
                data['ids'] = context.get('active_ids', [])
                data['model'] = context.get('active_model', 'ir.ui.menu')
                data['output_type'] = case.jasper_output
                data['variables'] = {                                
                                    'date_filter':case.date_filter or '',
                                    'start_dt' : case.start_dt or '',
                                    'end_dt'   : case.end_dt or '',
                                    'service_typ' : case.service_typ or '',
                                    'customer_id' : case.customer_id and case.customer_id.id or 0,
                                    'customer' : case.customer or '',
                                    'venue_id' : case.venue_id and case.venue_id.id or 0,
                                    'stage_id' : case.stage_id and case.stage_id.id or 0,
                                    'orderby'  : case.orderby or '',
                                    'venue_filter':case.venue_filter or '',
                                    'venue_inv_id':case.venue_inv_id and case.venue_inv_id.id or 0, 
                                    'passen_type' : case.passen_type or ''
                                    }
                return {'type': 'ir.actions.report.xml',
                        'report_name':'Enquiry Details',
                        'datas':data,
                        }
cc_enquiry_details()

class cc_invoice_analysis(osv.osv_memory):
    """
    Booking Details report of Venues and Afternoon Tea
    """
    _name = "cc.invoice.analysis"
    _description = "Capital Centric-Invoice Analysis"
    _columns = {
                'start_dt' : fields.date('Start Date'),
                'end_dt': fields.date('End Date'),
                'service_typ'  : fields.selection([('venue','Venue'), ('noontea','Afternoon Tea'),('others','Others')],'Service Type'),
                'inv_typ'      : fields.selection([('out_invoice','Customer Invoice'), 
                                                   ('out_refund','Customer Refunds'), 
                                                   ('in_invoice','Supplier Invoice'), 
                                                   ('in_refund','Supplier Refunds')],'Invoice Type'),
                'partner_id'      : fields.many2one('res.partner','Partner'),                
                'status'       : fields.selection([('open','Invoiced'),('paid','Paid'),('both','Both')],'Status'),
                'is_draft'     : fields.boolean('Include Draft Invoices'),
                'is_open'      : fields.boolean('Open Invoices'),
                'is_paid'      : fields.boolean('Paid Invoices'),
                'jasper_output': fields.selection([('pdf','PDF'),('xls','Raw XLS')], 'Report Output'),  
                'passen_type'   : fields.selection([('group','Group'), ('fit','FIT For Purpose')],'Booking Type'),
                'is_bookingdt'  : fields.boolean('Consider booking date for search')
               }               
    _defaults={
               'jasper_output':'xls',
               'is_open': True,
               'is_paid':True,
               'is_bookingdt':True
               }
    def print_report(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            status_lst = []
            sqlstr = ""
            if case.start_dt and case.end_dt and case.is_bookingdt:
               sqlstr += """ and (case when date_invoice is not null then date_invoice between '""" + str(case.start_dt) + """' and '""" + str(case.end_dt) +"""'
                                 else case when booking_date is not null then booking_date::date between '""" + str(case.start_dt) + """' and '""" + str(case.end_dt) + """'
                                 else create_date between '""" + str(case.start_dt) + """' and '""" + str(case.end_dt) +"""' end end)"""
            if case.start_dt and case.end_dt and not case.is_bookingdt:
               sqlstr += """ and (case when date_invoice is not null then date_invoice between '""" + str(case.start_dt) + """' and '""" + str(case.end_dt) +"""'
                                 else create_date between '""" + str(case.start_dt) + """' and '""" + str(case.end_dt) +"""' end)"""

            if case.service_typ and case.service_typ != 'others':
               sqlstr += " and service_type = '" + str(case.service_typ) + "'"
            if case.service_typ and case.service_typ == 'others':
               sqlstr += " and service_type is null"               
            if case.inv_typ:
               sqlstr += " and type = '" + str(case.inv_typ) + "'"
            if case.partner_id: 
               sqlstr += " and partner_id = " + str(case.partner_id.id)
            if case.is_draft:
               status_lst.append("'draft'")
            if case.is_open:
               status_lst.append("'open'")
            if case.is_paid:
               status_lst.append("'paid'")
            if status_lst:
               status_str =   ' ,'.join(str(x) for x in status_lst)
               sqlstr += " and state in (" + status_str +")"
            
            if case.passen_type:
               sqlstr += """ and passen_type = '""" + str(case.passen_type) + """'"""
                
            if sqlstr:
               sqlstr = ' where ' + sqlstr.lstrip(' and')

            cr.execute("""select id from account_invoice """ + sqlstr)

            if case.jasper_output in ('pdf','xls'):    
                data = {}
                data['ids'] = [x[0] for x in cr.fetchall()]
                data['model'] = context.get('active_model', 'ir.ui.menu')
                data['output_type'] = case.jasper_output
                data['variables'] = {'start_dt':case.start_dt and (parser.parse(''.join((re.compile('\d')).findall(case.start_dt)))).strftime('%d/%m/%Y') or '',
                                    'end_dt':case.end_dt and (parser.parse(''.join((re.compile('\d')).findall(case.end_dt)))).strftime('%d/%m/%Y') or '',
                                     }
                print data
                return {'type': 'ir.actions.report.xml',
                        'report_name':'InvoiceAnalysis',   
                        'datas':data,
                        }
cc_invoice_analysis()

class cc_wlabel_comision_rpt_wiz(osv.osv_memory):
    """
    Booking Details report of Venues and Afternoon Tea
    """
    _name = "cc.wlabel.comision.rpt.wiz"
    _description = "Fit For Purpose - White Label Commission Report."
    _columns = {
                'start_dt'   : fields.date('Booking Date From'),
                'end_dt'     : fields.date('Booking Date To'),
                'partner_id' : fields.many2one('res.partner','White-Label Partner',domain="[('id','in',[])]"),                
                'jasper_output': fields.selection([('pdf','PDF'),('xls','Raw XLS')], 'Report Output'),             
               }               
    _defaults={
               'jasper_output':'xls',
               }
    
    def onchange_startdt(self, cr, uid, ids, start_dt, context=None):
        domain={}
        cr.execute("""select (case when rp.parent_id is not null then rp.parent_id else rp.id end) as id 
                            from res_users ru 
                            inner join res_partner rp on rp.id = ru.partner_id 
                            and wlabel_url is not null""")
        domain = {'partner_id': [('id', '=', [x[0] for x in cr.fetchall()])]}
        return {'domain':domain}
        
    def print_report(self, cr, uid, ids, context = None):
        for case in self.browse(cr, uid, ids):
            sqlstr = ""
            
            for case in self.browse(cr,uid,ids):
                if case.end_dt < case.start_dt:
                     raise osv.except_osv(_('UserError'),('Please Check the given dates!!!'))
            
            partner_ids = [case.partner_id and case.partner_id.id]
            if not case.partner_id:
               cr.execute("""select (case when rp.parent_id is not null then rp.parent_id else rp.id end) as id 
                            from res_users ru 
                            inner join res_partner rp on rp.id = ru.partner_id 
                            and wlabel_url is not null""") 
               partner_ids = [x[0] for x in cr.fetchall()] 
             
            if case.jasper_output in ('pdf','xls'):    
                data = {}
                data['ids'] = [x[0] for x in cr.fetchall()]
                data['model'] = context.get('active_model', 'ir.ui.menu')
                data['output_type'] = case.jasper_output
                data['variables'] = {'start_dt':case.start_dt and (parser.parse(''.join((re.compile('\d')).findall(case.start_dt)))).strftime('%Y-%m-%d 00:00:00')or '',
                                    'end_dt':case.end_dt and (parser.parse(''.join((re.compile('\d')).findall(case.end_dt)))).strftime('%Y-%m-%d 23:59:59') or '',
                                    'partner_ids' :partner_ids
                                     }
                print data['variables']
                return {'type': 'ir.actions.report.xml',
                        'report_name':'Wlabel Commission',   
                        'datas':data,
                        }
                
cc_wlabel_comision_rpt_wiz()

class cc_partner_ledger_rpt_wiz(osv.osv_memory):
    """
    Booking Details report of Venues and Afternoon Tea
    """
    _name = "cc.partner.ledger.rpt.wiz"
    _description = "Fit For Purpose - Partner Ledger."
    _columns = {
                'start_dt'   : fields.date('Booking Date From'),
                'end_dt'     : fields.date('Booking Date To'),
                'partner_id' : fields.many2one('res.partner','Partner',required=True,domain=[('partner_type','in',['venue','client']),('parent_id','=',False)]),                
                'jasper_output': fields.selection([('pdf','PDF'),('xls','Raw XLS')], 'Report Output'),             
               }               
    _defaults={
               'jasper_output':'pdf',
               }
    
    def print_report(self, cr, uid, ids, context = None):
        user = self.pool.get('res.users').browse(cr, uid, uid)    
        for case in self.browse(cr,uid,ids):
            if case.end_dt < case.start_dt:
                 raise osv.except_osv(_('UserError'),('Please Check the given dates!!!'))
        if case.start_dt:
           prev_date = datetime.strptime(case.start_dt,'%Y-%m-%d') - relativedelta(days=1)  
           previous_date = prev_date.strftime('%Y-%m-%d')
           
        
        if case.jasper_output in ('pdf','xls'):    
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = case.jasper_output
            data['variables'] = {                                
                                'start_dt' : case.start_dt and (parser.parse(''.join((re.compile('\d')).findall(case.start_dt)))).strftime('%Y-%m-%d') or '',
                                'end_dt'   : case.end_dt and (parser.parse(''.join((re.compile('\d')).findall(case.end_dt)))).strftime('%Y-%m-%d') or '',
                                'partner_id'  : case.partner_id and case.partner_id.id or 0,                                 
                                'company_id' : user.company_id and user.company_id.id or 0,
                                'previous_date':previous_date and (parser.parse(''.join((re.compile('\d')).findall(previous_date)))).strftime('%Y-%m-%d') or '',
                                'current_date':(parser.parse(''.join((re.compile('\d')).findall(time.strftime('%Y-%m-%d'))))).strftime('%Y-%m-%d'),
                                }
            return {'type': 'ir.actions.report.xml',
                    'report_name':'Sales Statement', 
                    'datas':data,
                    }
                
cc_partner_ledger_rpt_wiz()

class contacts_report(osv.osv_memory):
    _name = 'contacts.report'
    _description = "Contacts Report"
    
    def _get_category(self, cr, uid, context=None):
        cr.execute("select distinct(category_id) from res_partner_res_partner_category_rel")
        categ_ids = [x[0] for x in cr.fetchall()]
        return categ_ids
    
    _columns = {
              'start_dt'    : fields.date('Start Date'),
              'end_dt'      : fields.date('End Date'),
              'type'        : fields.selection([('all', 'All'),('venue', 'Venue'),('client', 'Tour Operator')],'Type', required=True),
              'partner_id'  : fields.many2one('res.partner','Venue / Tour Operator'),
              'categ_ids'   : fields.many2many('res.partner.category','con_categ_rep_rel','contacts_id', 'categ_id','Tags'),  
              'output_type' : fields.selection(
                                                [('pdf', 'Portable Document (pdf)'),
                                                 ('xls', 'Excel Spreadsheet (xls)')],
                                                'Report format', help='Choose the format for the output', required=True),
              }
    _defaults = {
                  'output_type' : 'pdf',
                  'type' :'all',
#                   'categ_ids' : _get_category
                }

    def onchange_type(self, cr, uid, ids, type, context=None):
        domain = {'partner_id' : [('partner_type','in',['venue','client']),('parent_id','=',False)]}
        if type == 'venue':
           domain = {'partner_id' : [('parent_id','=',False),('partner_type','=','venue')]}
        elif type == 'client':
           domain = {'partner_id' : [('parent_id','=',False),('partner_type','=','client')]}
        return {'domain': domain}
    
    def print_report(self, cr, uid, ids, context=None):
        for case in self.browse(cr,uid,ids):
            if case.end_dt < case.start_dt:
                 raise osv.except_osv(_('UserError'),('Please Check the given dates!!!'))
            
            user = self.pool.get('res.users').browse(cr, uid, uid)
            address = user.company_id and ((user.company_id.partner_id.street or '') 
                               + (user.company_id.partner_id.street2 and (', ' + user.company_id.partner_id.street2) or '')
                               + (user.company_id.partner_id.city_id and (', ' + user.company_id.partner_id.city_id.name) or '') 
                               + (user.company_id.partner_id.state_id and (', ' + user.company_id.partner_id.state_id.name) or '')
                               + (user.company_id.partner_id.country_id and (', ' + user.company_id.partner_id.country_id.name) or '')
                               + (user.company_id.partner_id.zip and (' - ' + user.company_id.partner_id.zip) or '')
                               ) 
            
            categ_ids = [c.id for c in case.categ_ids]
            categ = case.categ_ids and ', '.join(str(e.name) for e in case.categ_ids) or '',
            cat_ids = []           

            if case.output_type in ('pdf','xls'):   
                data = {}
                data['ids'] = context.get('active_ids', [])
                data['model'] = context.get('active_model', 'ir.ui.menu')
                data['output_type'] = case.output_type
                data['variables'] = {                                
                                    'start_dt'  : case.start_dt or '',
                                    'end_dt'    : case.end_dt or '',
                                    'p_type'      : case.type or '',
                                    'partner_id': case.partner_id.id or 0,
                                    'company_name':user.company_id.name,
                                    'company_addr':address,
                                    'categ_ids': categ_ids,
                                    'is_categ':categ_ids and True or False,
                                    'categ':categ and categ[0] or ''
                                    }
                return {'type': 'ir.actions.report.xml',
                        'report_name':'contacts_report',
                        'datas':data,
                        }
contacts_report()

class invoice_summary_rpt(osv.osv_memory):
    _name = 'invoice.summary.rpt'
    _description = "Invoice Summary Report"
    
    
    _columns = {
                'date_filter'  : fields.selection([('date_invoice','Invoice Date'),('date_booking','Date Of Booking')],'Date Filter'),
                'start_dt'    : fields.date('Start Date'),
                'end_dt'      : fields.date('End Date'),
                'srv_type'    : fields.selection([('all', 'All'),('venue', 'Venue'),('noontea', 'Afternoon Tea')],'Type', required=True),
                'partner_id'  : fields.many2one('res.partner','Venue / Tour Operator'),
                'is_draft'    : fields.boolean('Include Draft Invoices'),  
                'output_type' : fields.selection([('pdf', 'Portable Document (pdf)'),
                                                  ('xls', 'Excel Spreadsheet (xls)')],
                                                  'Report format', help='Choose the format for the output', required=True),
              }
    _defaults = {
                  'output_type' : 'xls',
                  'srv_type' :'all',
                  'is_draft': True,
                  'date_filter':'date_invoice'
                }

    def onchange_type(self, cr, uid, ids, type, context=None):
        domain = {'partner_id' : [('partner_type','in',['venue','client']),('parent_id','=',False)]}
        if type == 'venue':
           domain = {'partner_id' : [('parent_id','=',False),('partner_type','=','venue')]}
        elif type == 'client':
           domain = {'partner_id' : [('parent_id','=',False),('partner_type','=','client')]}
        return {'domain': domain}
    
    def print_report(self, cr, uid, ids, context=None):
        for case in self.browse(cr,uid,ids):
            if case.end_dt < case.start_dt:
                 raise osv.except_osv(_('UserError'),('Please Check the given dates!!!'))
            
            user = self.pool.get('res.users').browse(cr, uid, uid)
            address = user.company_id and ((user.company_id.partner_id.street or '') 
                               + (user.company_id.partner_id.street2 and (', ' + user.company_id.partner_id.street2) or '')
                               + (user.company_id.partner_id.city_id and (', ' + user.company_id.partner_id.city_id.name) or '') 
                               + (user.company_id.partner_id.state_id and (', ' + user.company_id.partner_id.state_id.name) or '')
                               + (user.company_id.partner_id.country_id and (', ' + user.company_id.partner_id.country_id.name) or '')
                               + (user.company_id.partner_id.zip and (' - ' + user.company_id.partner_id.zip) or '')
                               ) 

            if case.output_type in ('pdf','xls'):   
                data = {}
                data['ids'] = context.get('active_ids', [])
                data['model'] = context.get('active_model', 'ir.ui.menu')
                data['output_type'] = case.output_type
                data['variables'] = {                                
                                    'start_dt'  : case.start_dt or '',
                                    'end_dt'    : case.end_dt or '',
                                    'srv_type'  : case.srv_type or '',
                                    'partner_id': case.partner_id.id or 0,
                                    'company_name':user.company_id.name,
                                    'company_addr':address,
                                    'is_draft'  : case.is_draft,
                                    'date_filter':case.date_filter
                                    }
                return {'type': 'ir.actions.report.xml',
                        'report_name':'Invoice Summary',
                        'datas':data,
                        }
invoice_summary_rpt()

class referral_link_summary(osv.osv_memory):
    _name = 'referral.link.summary'
    _description = "Referral Links Summary Report"


    _columns = {
                'start_dt'    : fields.date('Start Date'),
                'end_dt'      : fields.date('End Date'),
                'partner_id'  : fields.many2one('res.partner','Tour Operator' ,domain="[('partner_type','=','client')]"),
                'output_type' : fields.selection([('pdf', 'Portable Document (pdf)'),
                                                  ('xls', 'Excel Spreadsheet (xls)')],
                                                  'Report format', help='Choose the format for the output', required=True),
              }
    _defaults = {
                  'output_type' : 'xls',
                }

    def print_report(self, cr, uid, ids, context=None):
        for case in self.browse(cr,uid,ids):
            if case.end_dt < case.start_dt:
                 raise osv.except_osv(_('UserError'),('Please Check the given dates!!!'))

            user = self.pool.get('res.users').browse(cr, uid, uid)
            address = user.company_id and ((user.company_id.partner_id.street or '')
                               + (user.company_id.partner_id.street2 and (', ' + user.company_id.partner_id.street2) or '')
                               + (user.company_id.partner_id.city_id and (', ' + user.company_id.partner_id.city_id.name) or '')
                               + (user.company_id.partner_id.state_id and (', ' + user.company_id.partner_id.state_id.name) or '')
                               + (user.company_id.partner_id.country_id and (', ' + user.company_id.partner_id.country_id.name) or '')
                               + (user.company_id.partner_id.zip and (' - ' + user.company_id.partner_id.zip) or '')
                               )

            if case.output_type in ('pdf','xls'):
                data = {}
                data['ids'] = context.get('active_ids', [])
                data['model'] = context.get('active_model', 'ir.ui.menu')
                data['output_type'] = case.output_type
                data['variables'] = {
                                    'start_dt'  : case.start_dt or '',
                                    'end_dt'    : case.end_dt or '',
                                    'partner_id': case.partner_id.id or 0,
                                    'company_name':user.company_id.name,
                                    'company_addr':address,
                                    }
                return {'type': 'ir.actions.report.xml',
                        'report_name':'Referral Links',
                        'datas':data,
                        }
referral_link_summary()

# class cc_month_sales_earnings(osv.osv_memory):
#     """
#     Booking Details report of Venues and Afternoon Tea Details/Summary
#     """
#     _name = "cc.month.sales.earnings"
#     _description = "Fit For Purpose - Monthly Sales/Commission Details/Summary"
#     _columns = {
#                 'date_filter'  : fields.selection([('date_invoice','Invoice Date'),('date_booking','Date Of Booking')],'Date Filter'),
#                 'start_dt'   : fields.date('Start Date'),
#                 'end_dt'     : fields.date('End Date'),
#                 'is_salesamt':fields.boolean('Sales Amount'),
#                 'is_refundamt':fields.boolean('Refund Amount'),
#                 'is_purchaseamt':fields.boolean('Purchase Amount'),
#                 'is_debitamt':fields.boolean('Debit Amount'),
#                 'type':fields.selection([('details','Details'),('summary','Summary')],'Type'),
#                 'output_type': fields.selection([('pdf','PDF'),('xls','Raw XLS')], 'Report Output'),
#                }
#     _defaults={
#                'output_type':'pdf',
#                'date_filter':'date_invoice',
#                }
#
#     def print_report(self, cr, uid, ids, context = None):
#         user = self.pool.get('res.users').browse(cr, uid, uid)
#         for case in self.browse(cr,uid,ids):
#             if case.end_dt < case.start_dt:
#                  raise osv.except_osv(_('UserError'),('Please Check the given dates!!!'))
#         if case.start_dt:
#            prev_date = datetime.strptime(case.start_dt,'%Y-%m-%d') - relativedelta(days=1)
#            previous_date = prev_date.strftime('%Y-%m-%d')
#
#
#         if case.output_type in ('pdf','xls'):
#             data = {}
#             data['ids'] = context.get('active_ids', [])
#             data['model'] = context.get('active_model', 'ir.ui.menu')
#             data['output_type'] = case.output_type
#             data['variables'] = {
#                                 'date_filter':case.date_filter,
#                                 'start_dt' : case.start_dt and (parser.parse(''.join((re.compile('\d')).findall(case.start_dt)))).strftime('%Y-%m-%d') or '',
#                                 'end_dt'   : case.end_dt and (parser.parse(''.join((re.compile('\d')).findall(case.end_dt)))).strftime('%Y-%m-%d') or '',
# #                                 'company_id' : user.company_id and user.company_id.id or 0,
# #                                 'current_date':(parser.parse(''.join((re.compile('\d')).findall(time.strftime('%Y-%m-%d'))))).strftime('%Y-%m-%d'),
#                                 }
#             report_name='Monthly Sales Earnings'
#             if case.type=='details':
#                data['variables'].update({'is_salesamt':case.is_salesamt and '1' or '0',
#                                          'is_refundamt':case.is_refundamt and '1' or '0',
#                                          'is_purchaseamt':case.is_purchaseamt and '1' or '0',
#                                          'is_debitamt':case.is_debitamt and '1' or '0'})
#
#                print 'data',data['variables']
#
#                report_name = 'Monthly Sales Earnings Details'
#
#             return {'type': 'ir.actions.report.xml',
#                     'report_name':report_name,
#                     'datas':data,
#                     }
#
# cc_month_sales_earnings()


class cc_month_sales_earnings(osv.osv_memory):
    """
    Booking Details report of Venues and Afternoon Tea Details/Summary
    """
    _name = "cc.month.sales.earnings"
    _description = "Fit For Purpose - Monthly Sales/Commission Details/Summary"
    _columns = {
                'date_filter'  : fields.selection([('period','Period')],'Date Filter'),
                'start_dt'   : fields.date('Start Date'),
                'end_dt'     : fields.date('End Date'),
                'is_salesamt':fields.boolean('Sales Amount'),
                'is_refundamt':fields.boolean('Refund Amount'),
                'is_purchaseamt':fields.boolean('Purchase Amount'),
                'is_debitamt':fields.boolean('Debit Amount'),
                'type':fields.selection([('details','Details'),('summary','Summary')],'Type'),
                'output_type': fields.selection([('pdf','PDF'),('xls','Raw XLS')], 'Report Output'),
               'period_id': fields.many2one('account.period', 'Period From'),
               'period_to': fields.many2one('account.period', 'Period To'),
               }
    _defaults={
               'output_type':'pdf',
               'date_filter':'period',
               }

    def onchange_date_filter(self, cr, uid, ids, date_filter=None,context=None):
        res={}
        if date_filter:
            if date_filter == 'period':
                res['start_dt'] = False
                res['end_dt'] = False
            if date_filter != 'period':
                res['period_id'] = False
                res['period_to'] = False
        return {'value':res}

    def print_report(self, cr, uid, ids, context = None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        period_id = []
        for case in self.browse(cr,uid,ids):
            period_from = str(case.period_id.name) or ''
            period_to = str(case.period_to.name) or ''
            if (case.end_dt < case.start_dt) and (case.date_filter != 'period'):
                 raise osv.except_osv(_('UserError'),('Please Check the given dates!!!'))

        if case.start_dt:
           prev_date = datetime.strptime(case.start_dt,'%Y-%m-%d') - relativedelta(days=1)
           previous_date = prev_date.strftime('%Y-%m-%d')


        if case.output_type in ('pdf','xls'):
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = case.output_type
            data['variables'] = {
                                'date_filter':case.date_filter,
                                'start_dt' : case.start_dt and (parser.parse(''.join((re.compile('\d')).findall(case.start_dt)))).strftime('%Y-%m-%d') or '',
                                'end_dt'   : case.end_dt and (parser.parse(''.join((re.compile('\d')).findall(case.end_dt)))).strftime('%Y-%m-%d') or '',
                                'period_id':period_id,
#                                 'company_id' : user.company_id and user.company_id.id or 0,
#                                 'current_date':(parser.parse(''.join((re.compile('\d')).findall(time.strftime('%Y-%m-%d'))))).strftime('%Y-%m-%d'),
                                }
            report_name='Monthly Sales Earnings'
            if case.type=='details':
               data['variables'].update({'is_salesamt':case.is_salesamt and '1' or '0',
                                         'is_refundamt':case.is_refundamt and '1' or '0',
                                         'is_purchaseamt':case.is_purchaseamt and '1' or '0',
                                         'is_debitamt':case.is_debitamt and '1' or '0',
                                         'period_id':period_id})

               report_name = 'Monthly Sales Earnings Details'

            if case.date_filter == 'period':
                period_id = [case.period_id.id,case.period_to.id]
                period_from = str(case.period_id.name)
                period_to = str(case.period_to.name)
                cr.execute("select id from account_period where date_start >='"+str(case.period_id.date_start)+"' and date_stop <='"+str(case.period_to.date_stop)+"'")
                period_id = [r[0] for r in cr.fetchall()]
                data['variables'].update({'period_id':period_id,
                                          'period_from':period_from,
                                          'period_to':period_to,
                                          'start_dt' : case.period_id.date_start and (parser.parse(''.join((re.compile('\d')).findall(case.period_id.date_start)))).strftime('%Y-%m-%d') or '',
                                          'end_dt'   : case.period_to.date_stop and (parser.parse(''.join((re.compile('\d')).findall(case.period_to.date_stop)))).strftime('%Y-%m-%d') or '',                                      })
                print 'data',data['variables']



            return {'type': 'ir.actions.report.xml',
                    'report_name':report_name,
                    'datas':data,
                    }

cc_month_sales_earnings()

class general_ledger_webkit_wizard(orm.TransientModel):
    _inherit = 'general.ledger.webkit'

    _columns={'filter': fields.selection([('filter_no', 'No Filters'),
                                          ('filter_date', 'Date'),
                                          ('filter_period', 'Periods'),
                                          ('filter_create_date', 'Create Date')], "Filter by", required=True),}

    def _print_report(self, cr, uid, ids, data, context=None):
        context = context or {}
        if context.get('xls_export'):
            # we update form with display account value
            data = self.pre_print_report(cr, uid, ids, data, context=context)
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'account.cc_account_report_general_ledger_xls',
                    'datas': data}
        else:
            return super(general_ledger_webkit_wizard, self)._print_report(cr, uid, ids, data, context=context)
