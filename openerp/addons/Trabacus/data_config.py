# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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
 
from openerp.osv import osv, fields

class trabacus_config_settings(osv.osv_memory):
    _name = 'trabacus.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        
        'create_partyledger'  : fields.boolean('Create Party Ledger Account on First Invoice'),
        'parent_receivable_id': fields.many2one('account.account', 'Parent Account Receivable', domain="[('type','=', 'receivable')]"),
        'parent_payable_id'   : fields.many2one('account.account', 'Parent Account Payable', domain="[('type','=', 'payable')]"),
        'receivable_id'       : fields.many2one('account.account', 'Account Receivable', domain="[('type', '=', 'receivable')]"),
        'payable_id'          : fields.many2one('account.account', 'Account Payable', domain="[('type','=', 'payable')]"),
        
        'showall_details'     : fields.boolean('Show Extended/All Details')
            }
    _defaults = {
                  'showall_details' : True
                  }  
    # GETS: latest data
    def get_default_values(self, cr, uid, ids, context=None):
        param_obj = self.pool.get("ir.config_parameter")
        create_pl = param_obj.get_param(cr, uid, "create_account")
        preceive_id = param_obj.get_param(cr, uid, "parent_receivable")
        ppayable_id = param_obj.get_param(cr, uid, "parent_payable")
        receive_id = param_obj.get_param(cr, uid, "receivable")
        payable_id = param_obj.get_param(cr, uid, "payable")
        showall_details =   param_obj.get_param(cr, uid, "showdetails")
        
        return {'create_partyledger'  : create_pl, 
                'parent_receivable_id': preceive_id,
                'parent_payable_id' : ppayable_id, 
                'receivable_id'     : receive_id,
                'payable_id'        : payable_id,
                'showall_details'   : showall_details,
                }
   
    # POST: saves new data
    def set_values(self, cr, uid, ids, context=None):
        param_obj = self.pool.get("ir.config_parameter")
        for record in self.browse(cr, uid, ids, context=context):
            param_obj.set_param(cr, uid, "create_account", record.create_partyledger or '')
            param_obj.set_param(cr, uid, "parent_receivable", record.parent_receivable_id.id or '')
            param_obj.set_param(cr, uid, "parent_payable", record.parent_payable_id.id or '')
            param_obj.set_param(cr, uid, "receivable", record.receivable_id.id or '')
            param_obj.set_param(cr, uid, "payable", record.payable_id.id or '')
            param_obj.set_param(cr, uid, "showdetails", record.showall_details or '')
  
 
trabacus_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: