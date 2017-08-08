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

    
    
    

class res_company(osv.osv):
    _inherit = "res.company"
    _description = 'Companies'
    
    def _get_address_data(self, cr, uid, ids, field_names, arg, context=None):
        """ Read the 'address' functional fields. """        
        return super(res_company,self)._get_address_data(cr, uid, ids, field_names, arg, context)

    def _set_address_data(self, cr, uid, company_id, name, value, arg, context=None):
        """ Write the 'address' functional fields. """
        return super(res_company,self)._set_address_data(cr, uid, company_id, name, value, arg, context)
    
    _columns = {
                 'tplogin_ids'      : fields.one2many('tr.suppliersys.pcc', 'company_id', 'Supplier systems'), 
                 
                'display_compname'  : fields.char('Display On Invoice As',size=500),
                'window_inv'        : fields.integer('Window For Invoice'),
                'city_id'           : fields.function(_get_address_data, fnct_inv=_set_address_data,  type='many2one', relation='tr.city', string="City", multi='address'), 
                'comp_code'         : fields.char('Company Code',size=2),
                'window_journal'    : fields.integer('Window For Journal'),
                'window_voucher'    : fields.integer('Window For Voucher'),
                'window_bankcash'   : fields.integer('Window For Bank Statement & Cash Registers'),
                'window_move'       : fields.integer('Window For Move'),                              
#                 'discount_id'  : fields.many2one('account.account', 'Discount'),
#                 'tac_id'       : fields.many2one('account.account', 'TAC'),
#                 'tds_payable_id'      : fields.many2one('account.account', 'TDS Payable'),
#                 'tds_receivable_id'   : fields.many2one('account.account', 'TDS Receivable'),
                 }

class res_users(osv.osv):
    _inherit = 'res.users' 
    def _get_team_users(self, cr, uid, ids, name, args, context=None):
        result = {}
        incentive_obj = self.pool.get('tr.incentive')
        a = []
        for user in self.browse(cr,uid,ids):
            cr.execute("select distinct r.id from res_users r inner join tr_incentive i on i.user_id = r.id where manager_id ="+str(user.id))
            a = cr.fetchall()
            result[user.id] = [i[0] for i in a]   
        return result
   
    _columns = {
                'tplogin_ids'   : fields.one2many('tr.suppliersys.login', 'user_id', 'Supplier systems'),
                
 
                'tr_lead'       : fields.selection([('lead_user','Salesperson (See Own Data)'),('lead_consultant','Consultant (See Own Data)'),('lead_manager','Manager (See Team Data)'),('lead_branch_head','Branch Head (See Branch/All Data)')],'Lead'),
                'tr_sale'       : fields.selection([('sale_user','Salesperson (See Own Data)'),('sale_consultant','Consultant (See Own Data)'),('sale_manager','Manager (See Team Data)'),('sale_branch_head','Branch Head (See Branch/All Data)')],'Sale'),
                'tr_product'    : fields.selection([('prod_user','Manager (See All Data)')],'Product'),
                'tr_purchase'   : fields.selection([('purchase_user','Salesperson (See Own Data)'),('purchase_manager','Manager (See Team Data)'),('purchase_branch_head','Branch Head (See Branch/All Data)')],'Purchase'),
                'tr_accounting' : fields.selection([('acc_user','Salesperson (See Own Data)'),('acc_consultant','Consultant (See Own Data)'),('acc_manager','Manager (See All Data)')],'Accounting'),
                'tr_config'     : fields.selection([('config_branch_head','Branch Head (See Branch Data)'),('config_admin','Admin (See All Data)')],'Configuration'),
                'tr_incentive_ids'  : fields.one2many('tr.incentive', 'user_id', "Incentive"),
                'tr_rptmanager_id'       :fields.many2one('res.users','Reporting Manager'),
                'team_ids'   : fields.function(_get_team_users,relation="res.users",type="many2many",String="Team"),  
                'validate_ok' : fields.boolean('Validate Invoices on Confirmation of Sales'),
               }
    
    def _get_belongingGroups(self,cr, uid, belongto, context=None):
        data_obj = self.pool.get('ir.model.data') 
        
        result = super(res_users, self)._get_group(cr, uid, context)
        
        try:
            if 'acc_user' in belongto :
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_traccount_user')
                result.append(groupid)
            if 'acc_consultant' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_traccount_consultant')
                result.append(groupid)
            if 'acc_manager' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_traccount_manager')
                result.append(groupid)
            if 'config_branch_head' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trconfig_branch_head')
                result.append(groupid)
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'base', 'group_erp_manager')
                result.append(groupid)
            if 'config_admin' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trconfig_admin')
                result.append(groupid)
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'base', 'group_erp_manager')
                result.append(groupid)
            if 'lead_user' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trlead_user')
                result.append(groupid)
            if 'lead_consultant' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trlead_consultant')
                result.append(groupid)
            if 'lead_manager' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trlead_manager')
                result.append(groupid)
            if 'lead_branch_head' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trlead_branch_head')
                result.append(groupid)
            if 'sale_user' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trsale_user')
                result.append(groupid)
            if 'sale_consultant' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trsale_consultant')
                result.append(groupid)
            if 'sale_manager' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trsale_manager')
                result.append(groupid)
            if 'sale_branch_head' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trsale_branch_head')
                result.append(groupid)
            if 'prod_user' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trproduct_user')
                result.append(groupid)
            if 'purchase_user' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trpurchase_user')
                result.append(groupid)
            if 'purchase_manager' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trpurchase_manager')
                result.append(groupid)
            if 'purchase_branch_head' in belongto:
                dummy,groupid = data_obj.get_object_reference(cr, 1, 'Trabacus', 'group_trpurchase_branch_head')
                result.append(groupid)
            if 'technical_features' in belongto:
                dummy, groupid = data_obj.get_object_reference(cr, 1, 'base', 'group_partner_manager')
                result.append(groupid)
            dummy, groupid = data_obj.get_object_reference(cr, 1, 'base', 'group_multi_company')
            result.append(groupid)
            dummy, groupid = data_obj.get_object_reference(cr, 1, 'base', 'group_multi_currency')
            result.append(groupid)
            dummy, groupid = data_obj.get_object_reference(cr, 1, 'project', 'group_project_manager')
            result.append(groupid)

        except ValueError:
            # If these groups does not exists anymore
            pass
        return result
 
    
 
    def create(self, cr, uid, values, context=None):
            result = super(res_users, self).create(cr, uid, values, context=context)        
            group_list = []
            vals = {}
            group_list.append(values.get('tr_accounting',False))
            group_list.append(values.get('tr_config',False))    
            group_list.append(values.get('tr_lead',False))
            group_list.append(values.get('tr_sale',False))
            group_list.append(values.get('tr_product',False))
            group_list.append(values.get('tr_purchase',False)) 
            groupids = self._get_belongingGroups(cr, uid,group_list , context)
            vals['groups_id'] = [(6, 0, groupids)] 
            self.write(cr,uid,result,vals)
            return result
    
    def write(self, cr, uid, ids, values, context=None): 
        group_list = []
        groupids =[]
        vals = {}
        if ids and isinstance(ids, int):
           ids = [ids] 
        if hasattr(ids, '__iter__'):
            for user in self.browse(cr,uid, ids):
                if user.id != 1: # Excluding Administration
                    group_list.append(values.get('tr_accounting', user.tr_accounting))
                    group_list.append( values.get('tr_config', user.tr_config))    
                    group_list.append(values.get('tr_lead', user.tr_lead))
                    group_list.append(values.get('tr_sale', user.tr_sale))
                    group_list.append(values.get('tr_product', user.tr_product))
                    group_list.append(values.get('tr_purchase', user.tr_purchase)) 
                    if group_list: 
                        groupids = self._get_belongingGroups(cr, uid,group_list , context)
                        values['groups_id'] = [(6, 0, groupids)] 
                if user.id == 1 and uid != 1:
                    raise osv.except_osv(_('warning'), _("You do not have permission to modify the access of Administrator!!"))
                    return False
        return super(res_users, self).write(cr, uid, ids, values, context=context)
         
class tr_incentive(osv.osv):
    _name = "tr.incentive"
    _columns = { 
                'user_id'       : fields.many2one("res.users", "Users"),
                'service_type'  : fields.selection(TRAVEL_TYPES,'Service Type'),
                'manager_id'    : fields.many2one('res.users','Manager'),
                'incentive'     : fields.float("Incentive", digits=(3,2)),
               
                }

class tr_supplier_systems(osv.osv):
    _name = "tr.supplier.systems"
    _description = "Supplier Systems"
    
class tr_suppliersys_login(osv.osv):
    _name = "tr.suppliersys.login"
    _description = "Supplier Systems Login"
    _columns = {
                
                'user_id'    : fields.many2one('res.users', 'User', ondelete='cascade'),
                'tpsystem_id': fields.many2one('tr.supplier.systems', 'Supplier System'),
                'login'      : fields.char("Login", size=64),
                }
    

class tr_suppliersys_pcc(osv.osv):
    _name = "tr.suppliersys.pcc"
    _description = "Supplier Systems Company PCC"
    _columns = {
                
                 'company_id' : fields.many2one('res.company', 'Company', ondelete='cascade'),
                'tpsystem_id': fields.many2one('tr.supplier.systems', 'Supplier System'),
                'branch_pcc' : fields.char("Branch PCC", size=4),
                }
    _sql_constraints = [
                        ('name_uniq', 'unique(branch_pcc)', 'Branch-PCC Should Be Unique !'),
                       ]
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: