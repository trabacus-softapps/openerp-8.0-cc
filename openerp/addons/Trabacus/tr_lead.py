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

# from openerp.addons.base_status.base_stage import base_stage
# from base.res.res_partner import format_address

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
# from crm import crm
import tr_config
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
    
class tr_lead_template(osv.osv):
    _name = 'tr.lead.template' 
    _description = "Lead Template"
    _columns = {

        'adults'  : fields.integer('No of Adult (Single)'),  
        'twin'    : fields.integer('No. of Adult (Double)'),
        'triple'  : fields.integer('No. of Adult (Triple)'),
        'cwb'     : fields.integer('Children with Bed'), 
        'cnb'     : fields.integer('Children without Bed'),
        'infant'  : fields.integer('Infants'),
        
        'age_child'   : fields.char('Age of Children', size=30),
        'budget'      : fields.char('Budget', size=50), 
        'traveldate'  : fields.char('Travel Date', size=30),
        'meals'       : fields.char('Meals Preference', size=100),
        'hotel_categ' : fields.char('Hotel Categ', size=30),
        'no_nights'   : fields.integer('No. of Nights'),
        'flight_categ_id'  : fields.many2one('tr.flight.category', 'Flight Category', ondelete="restrict"),
        'sector'     : fields.char('Sector', size=30),
        'pref'       : fields.char('Seats Preference', size=100),
        'ft_meals'   : fields.char('Meals Preference', size=100),
        
        'overall'       : fields.text('Overall'),
        'ov_rating_id'  : fields.many2one('tr.feedback.rating', 'Rating'), 
        'hotel_food'    : fields.text('Hotel & Food'),
        'ht_rating_id'  : fields.many2one('tr.feedback.rating', 'Rating'), 
        'veh_driver'    : fields.text('Vehicle Driver'),
        'veh_rating_id' : fields.many2one('tr.feedback.rating', 'Rating'), 
        'itinerary'     : fields.text('Itinerary'),
        'iti_rating_id' : fields.many2one('tr.feedback.rating', 'Rating'), 
        'staff'         : fields.text('Our Staff'),
        'st_rating_id'  : fields.many2one('tr.feedback.rating', 'Rating'), 
        'best_in_tour'  : fields.text('Best Part Of Tour'),
        'suggestions'   : fields.text('Improvements & Suggestion'),
        'requirement'   : fields.text('Other Requirement'),
        'staff_remarks' : fields.text('Staff Remarks'),
        'destination_ids': fields.many2many('tr.destination', 'leadtmpl_destination_rel', 'tmpl_id', 'dest_id', 'Destination'),
        'requisition_state': fields.selection([('requested','Requested'),('approved','Approved'),('rejected','Rejected'),('escalated','Escalated'),('cancelled','Cancelled')],'Requisition State',readonly=True),
        'requested_by_id':fields.many2one('res.users','Requested By', readonly=True),
        'requested_to_id':fields.many2one('res.users','Requested To',readonly=True)
                }
tr_lead_template()

# class crm_lead(base_stage, format_address, osv.osv): 
class crm_lead(osv.osv): 
    _inherit = 'crm.lead'
    _inherits = {'tr.lead.template': 'template_id' 
                }
    
    def _get_3days_prior(self, cr, uid, ids, name, args, context=None):
        res = {}  
        for case in self.browse(cr, uid, ids, context=context): 
            if case.date_deadline:
                res[case.id] =  datetime.strptime(case.date_deadline, '%Y-%m-%d') - relativedelta(days=3)
        return res 

    def _get_manager(self, cr, uid, ids, name, args, context=None):
       res = {} 
       for case in self.browse(cr, uid, ids, context=context):
#           cr.execute(""" select inc.manager_id 
#                          from fp_incentive inc 
#                          inner join fp_user_manager m on m.id = inc.usrmanager_id 
#                          where m.travel_type = '%s' and inc.user_id = %d"""%(case.travel_type, case.user_id.id))
#           mgr = cr.fetchone() 
#           res[case.id]= (mgr and mgr[0]) or (case.user_id and case.user_id.id) or False
           res[case.id]= False 
       return res
   
    def _get_login_user(self, cr, uid, ids, name, args, context=None):
       res = {} 
       for case in self.browse(cr, uid, ids, context=context):
           res[case.id]= uid 
       return res
   
#     def default_get(self, cr, uid, fields, context=None):
#          
#         # class defaults is called first:
#         res = super(crm_lead, self).default_get(cr, uid, fields, context=context) or {}
#         if not context: context = {}
#         trtype = context.get('default_travel_type')
#         
#         stage_ids = self.pool.get('crm.case.stage').search(cr, uid, [('travel_type','=',trtype)], order = 'sequence', limit = 1)
#         if stage_ids:
#             res['stage_id'] = stage_ids and stage_ids[0]
#         return res
    
    _columns = {
        # Overridden:
        'name'         : fields.char('Name', size=256),
        'user_id'      : fields.many2one('res.users', 'Salesperson', select=True, track_visibility='onchange', ondelete="restrict"),
        'title_action' : fields.char('Explanation', size=500, track_visibility='onchange'),
        'date_deadline': fields.date('Travel Date'),
        
        # New:
#         'travel_type' : fields.selection(tr_config.TRAVEL_TYPES,'Service Type'),
        'lead_no'     : fields.char('Lead No', size=30, readonly=True),
        'tour_code'   : fields.char('Tour Code', size=30),
        
        'is_package'   : fields.boolean('Holiday Package'),
        'is_domflight' : fields.boolean('Domestic Flight'),
        'is_intflight' : fields.boolean('International Flight'),
        'is_domhotel'  : fields.boolean('Domestic Hotel'),
        'is_inthotel'  : fields.boolean('International Hotel'),
        'is_car'       : fields.boolean('Transfers'),
        'is_activity'  : fields.boolean('Activities'),
        'is_addon'     : fields.boolean('Add on'),
        'is_visa'      : fields.boolean('Visa'),
        'is_insurance' : fields.boolean('Insurance'),
        'is_railway'   : fields.boolean('Railway'),
        'is_cruise'    : fields.boolean('Cruise'),
        
        'template_id'   : fields.many2one('tr.lead.template', 'Template', required=True, ondelete="cascade"),
        'manager_id'    : fields.function(_get_manager, string='Lead Manager', type='many2one', relation='res.users', store=True),
        'paxtype'       : fields.selection([('fit','FIT'),('group','Group')],'Passenger Type'), 
        'purpose'       : fields.selection([('leisure','Leisure'),('business','Business')],'Purpose'),
        'date_response' : fields.date('Last Response Date'),
        'channel'       : fields.char("Channel", size=200),
        'lostrmks_ids': fields.many2many('tr.lost.remarks', 'lead_lostremarks_rel', 'lead_id', 'lost_id', 'Lost Remarks'),
        
        'requisition_state': fields.selection([('requested','Requested'),('approved','Approved'),('rejected','Rejected'),('escalated','Escalated'),('cancelled','Cancelled')],'Requisition State',readonly=True),
        'requested_by_id':fields.many2one('res.users','Requested By', readonly=True),
        'requested_to_id':fields.many2one('res.users','Requested To',readonly=True),
        'chklist_ids'  : fields.one2many("tr.lead.checklist", "lead_id", "Checklists", ondelete="cascade"),
#        'task_ids'     : fields.one2many('tr.tasks','lead_id','Tasks', ondelete="cascade"),
        'company_id': fields.many2one('res.company', 'Company', ondelete='cascade', select=True, change_default=True),                
        'consultant_id'  : fields.many2one('res.users', 'Consultant', select=True, track_visibility='onchange'),
        'login_user'    : fields.function(_get_login_user, string='Login User', type='many2one', relation='res.users'),
         'prior_travel_date': fields.function(_get_3days_prior, string='Prior (3 days) Travel Date', method=True, type='date', store=True),
         
         'planned_revenue': fields.float('Expected Revenue'),
                }
    
    _sql_constraints = [
        ('lead_uniq', 'unique(lead_no)', 'Lead Number must beproduct_id unique !'),
    ]
    
    _order ="date_action desc"
    
    _defaults={
            'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
            'consultant_id' : lambda obj, cr, uid, context: uid,
            'user_id':False,
            'login_user' : lambda obj, cr, uid, context: uid,
               }
    
   
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        ids = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name  
            if operator in ('=ilike', '=like'):
                operator = operator[1:]
            query_args = {'name': search_name}
            limit_str = ''
            if limit:
                limit_str = ' limit %(limit)s'
                query_args['limit'] = limit
            #cr.execute('''SELECT lead.id FROM crm_lead lead WHERE lead.lead_no ilike + %(name)s ''' + limit_str, query_args)
            search_name = query_args['name'] 
            if '[' in query_args['name']:
                search_name = query_args['name'].split('[')[1].rsplit(']')[0]
            cr.execute("""select lead.id from crm_lead lead where lead.lead_no ilike '""" +str(search_name)+"""%'""")
           # cr.execute("""select id from crm_lead where lead_no ilike '""" + str(lead_num) + """%' order by to_number(substr(lead_no,6),'9999') desc limit 1""")

            ids = map(lambda x: x[0], cr.fetchall())
            ids = self.search(cr, uid, [('id', 'in', ids)] + args, limit=limit, context=context)
            if ids:
                return self.name_get(cr, uid, ids, context)
        return super(crm_lead,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)

              
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        res = []
        name = ''
        for record in self.read(cr, uid, ids, ['lead_no','partner_id','name'], context):
            if context.get('showinfo',False) == True: 
                if record['lead_no'] != False and record['partner_id'] != False and record['name']:
                    name = '[' + record['lead_no']  + '] ' + record['partner_id'][1]   + ' - ' +record['name']
                else:
                    name = record['lead_no'] or '/' 
            res.append((record['id'],name ))
        return res 
    
    def _create_checklists(self, cr, uid, vals, context=None):
        chklistpart_obj = self.pool.get("tr.chklist.particulars")
        listlines = []
        checklists = []
        
        ttlist = []
        
        if 'is_package' in vals and vals['is_package']: ttlist.append('dom_package')
        if 'is_package' in vals and vals['is_package']: ttlist.append('int_package')
        if 'is_domflight' in vals and vals['is_domflight']: ttlist.append('dom_flight')
        if 'is_intflight' in vals and vals['is_intflight']: ttlist.append('int_flight')
        if 'is_domhotel' in vals and vals['is_domhotel']: ttlist.append('dom_hotel')
        if 'is_inthotel' in vals and vals['is_inthotel']: ttlist.append('int_hotel')
        if 'is_car' in vals and vals['is_car']: ttlist.append('car')
        if 'is_visa' in vals and vals['is_visa']: ttlist.append('visa')
        if 'is_insurance' in vals and vals['is_insurance']: ttlist.append('insurance')
        if 'is_activity' in vals and vals['is_activity']: ttlist.append('activity')
        if 'is_addon' in vals and vals['is_addon']: ttlist.append('add_on')
        if 'is_railway' in vals and vals['is_railway']: ttlist.append('railway')
        if 'is_cruise' in vals and vals['is_cruise']: ttlist.append('cruise')
        
        checklists = chklistpart_obj.search(cr,uid,[('travel_type','in', tuple(ttlist))])
        
        for c in chklistpart_obj.browse(cr,uid,checklists):
            listlines.append((0,0,{'travel_type': c.travel_type,'name': c.name}
                             ))
        return listlines
    
    def _generate_LeadNo(self, cr, uid, vals, context=None):
        today = datetime.today()
        mon = today.strftime('%m')
        year = today.strftime('%Y')
        
        leadno = ''
        
#         trt_map = {'dom_package': 'DH', 'int_package': 'IH', 'dom_flight': 'DF',
#                    'int_flight': 'IF', 'dom_hotel': 'DT', 'int_hotel': 'IT',
#                    'car' : 'TR', 'visa': 'VI', 'insurance': 'NI',
#                    'activity': 'AT', 'add_on': 'AO', 'railway': 'DR', 'cruise': 'CS'
#                    }
        passen_map = {'fit': 'F', 'group': 'G'}
        
#         leadno += passen_map.get(vals.get('passenger_typ'), '') # Commented because paxtype not considered 
#         leadno += trt_map.get(vals.get('travel_type'),'')
                
        company_id = self.pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]['company_id']
        leadno += self.pool.get('res.company').read(cr,uid,[company_id[0]],['comp_code'])[0]['comp_code'] or ''
        leadno += year + mon
        
        cr.execute("""select id from crm_lead where lead_no ilike '""" + str(leadno) + """%' order by id desc limit 1""")
        lead_rec = cr.fetchone()
        if lead_rec:
            lead = self.browse(cr, SUPERUSER_ID, lead_rec[0])
            auto_gen = lead.lead_no[len(leadno) : ]
            leadno = leadno + str(int(auto_gen) + 1).zfill(4)
        else:
            leadno = leadno + '0001'
            
        return {'lead_no':leadno}
             
    def create(self, cr, uid, vals, context=None):
        vals.update(self._generate_LeadNo(cr, uid, vals, context))
        vals['chklist_ids'] = self._create_checklists(cr, uid, vals, context)
        return super(crm_lead, self).create(cr, uid, vals, context)
   
    def write(self, cr, uid, ids, vals, context=None):
        
        for case in self.browse(cr, uid, ids):
            if vals.get('date_action', case.date_action) != case.date_action:
                vals.update({'date_response': time.strftime('%Y-%m-%d %H:%M:%S')})
                if 'title_action' not in vals:
                    raise osv.except_osv(_('Warning'),_('Please enter explanation for change of Next Action Date!!'))
            
        return super(crm_lead,self).write(cr, uid, ids, vals, context)
    
    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        unlink_tmpl_ids = []
        
        for case in self.browse(cr, uid, ids, context=context):
            tmpl_id = case.template_id.id
            
            # Check if the product is last product of this service
            other_product_ids = self.search(cr, uid, [('template_id', '=', tmpl_id), ('id', '!=', case.id)], context=context)
            
            if not other_product_ids:
                unlink_tmpl_ids.append(tmpl_id)
            unlink_ids.append(case.id)
            
        res = super(crm_lead, self).unlink(cr, uid, unlink_ids, context=context)
        # delete templates after calling super, as deleting template could lead to deleting
        # Lead due to ondelete='cascade'
        self.pool.get('tr.lead.template').unlink(cr, uid, unlink_tmpl_ids, context=context)
        return res
    
    def action_lead_sendmail(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi invoice template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'crm', 'email_template_opportunity_mail')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'crm.lead',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    

    def button_approved(self, cr, uid, ids, context=None):
        
        Mail_obj = self.pool.get('mail.followers')
        mail_msg_obj = self.pool.get('mail.message')
        Subtype_obj = self.pool.get('mail.message.subtype')
        for case in self.browse(cr,uid,ids):
            if uid != case.requested_to_id.id:
                raise osv.except_osv(_('Warning'),_('This request can be approved by ' + case.requested_to_id.name + ' only.'))
        vals1 = {                    
                    'subject'       : 'Lead has been Approved',
                    'model'         : 'crm.lead',
                    'res_id'        :  ids and ids[0],
                    'subtype_id'    : 1,
                    'type'          : 'comment'  
                }
        msg_id = mail_msg_obj.create(cr, uid, vals1)
        self.write(cr, uid, ids, {'requisition_state': 'approved'})
       
crm_lead()


class tr_lead_checklist(osv.osv):
    _name = 'tr.lead.checklist' 
    _description = "Lead - Check List "
        
    _columns = {
         'lead_id'     : fields.many2one("crm.lead", "Lead", ondelete='cascade'),
         'travel_type' : fields.selection(tr_config.TRAVEL_TYPES,'Service Type'), 
         
         'name'         : fields.char('Particulars', size=500),
         'chklist_date' : fields.date('Date'),
         'remarks'      : fields.char('Remarks', size=300),
         'is_checked'   : fields.boolean('Checked'),
        }
    
    def onchange_checklist(self, cr, uid, ids, is_checked): 
        res = {}
        if is_checked:
            res['chklist_date'] = time.strftime('%Y-%m-%d')
        return {'value':res}
    
    def write(self, cr, uid, ids, vals, context=None):
        
        if vals.get('is_checked',False) == True:
           vals['chklist_date'] = time.strftime('%Y-%m-%d')
        return super(tr_lead_checklist, self).write(cr, uid, ids, vals, context=context)   
        
tr_lead_checklist()

class task(osv.osv):
    _inherit = "project.task"
    _columns = {
                }
    def onchange_lead_id(self , cr, uid, ids, lead_id):
        res= {}
        cust_det_obj = self.pool.get('crm.lead')
        if lead_id:
            case = cust_det_obj.browse(cr, uid, lead_id)
            res['partner_id'] = case.partner_id.id
        return {'value':res}
task()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


    