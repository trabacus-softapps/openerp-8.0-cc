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

class account_invoice_refund(osv.osv_memory):
    _inherit = "account.invoice.refund"

    _columns = {
                # Overridden:
                'filter_refund': fields.selection([('refund', 'Refund')], "Refund Type", required=True, help='Refund invoice base on this type. You can not Modify and Cancel if the invoice is already reconciled'),
                
                # New:
                'travel_type' : fields.selection(TRAVEL_TYPES, 'Service Type'),
                
                'flight_ids'    : fields.many2many('tr.invoice.flight','refund_flight_rel','refund_id','flight_id','Flight',),
                'insurance_ids' : fields.many2many('tr.invoice.insurance', 'refund_ins_rel','refund_id', 'ins_id', 'Insurance'),
                'visa_ids'      : fields.many2many('tr.invoice.visa', 'refund_visa_rel','refund_id', 'visa_id', 'Visa'),
                'cruise_ids'    : fields.many2many('tr.invoice.cruise', 'refund_cruise_rel','refund_id', 'cruise_id', 'Cruise'),
                'car_ids'       : fields.many2many('tr.invoice.car', 'refund_car_rel','refund_id', 'car_id', 'Transfers'),
                'railway_ids'   : fields.many2many('tr.invoice.railway', 'refund_rail_rel','refund_id', 'rail_id', 'Railway'),
                'hotel_ids'     : fields.many2many('tr.invoice.hotel', 'refund_hotel_rel','refund_id', 'hotel_id', 'Hotel'),
                'activity_ids'  : fields.many2many('tr.invoice.activity', 'refund_activity_rel','refund_id', 'activity_id', 'Activity'),
                'addon_ids'     : fields.many2many('tr.invoice.addon', 'refund_addon_rel','refund_id', 'addon_id', 'Addon'),
                
                }
    _defaults = {       
                 'filter_refund': 'refund',
                 'travel_type': lambda self,cr,uid,c: c.get('travel_type', ''),
                 }
    
    # Overridden:
    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        """
            Overridden: Refunds the Invoice
        """
        
        inv_obj = self.pool.get('account.invoice')
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
        FT_obj = self.pool.get('tr.invoice.flight')
        ftln_obj = self.pool.get('tr.invoice.flight.lines')
        if context is None:
            context = {}

        for form in self.browse(cr, uid, ids, context=context):
            created_inv = []
            date = False
            period = False
            description = False
            company = res_users_obj.browse(cr, uid, uid, context=context).company_id
            journal_id = form.journal_id.id
            
            for inv in inv_obj.browse(cr, uid, context.get('active_ids'), context=context):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise osv.except_osv(_('Error!'), _('Cannot %s draft/proforma/cancel invoice.') % (mode))
                                           
                if form.period.id:
                    period = form.period.id
                else:
                    period = inv.period_id and inv.period_id.id or False

                if not journal_id:
                    journal_id = inv.journal_id.id

                if form.date:
                    date = form.date
                    if not form.period.id:
                            cr.execute("select name from ir_model_fields \
                                            where model = 'account.period' \
                                            and name = 'company_id'")
                            result_query = cr.fetchone()
                            if result_query:
                                cr.execute("""select p.id from account_fiscalyear y, account_period p where y.id=p.fiscalyear_id \
                                    and date(%s) between p.date_start AND p.date_stop and y.company_id = %s limit 1""", (date, company.id,))
                            else:
                                cr.execute("""SELECT id
                                        from account_period where date(%s)
                                        between date_start AND  date_stop  \
                                        limit 1 """, (date,))
                            res = cr.fetchone()
                            if res:
                                period = res[0]
                else:
                    date = inv.date_invoice
                    
                if form.description:
                    description = form.description
                else:
                    description = inv.name

                if not period:
                    raise osv.except_osv(_('Insufficient Data!'), \
                                            _('No period found on the invoice.'))
                    
                ctx = context.copy()
                # TODO:
                # For other services
                wizlines = []
                wizlines = form.flight_ids or form.hotel_ids or form.insurance_ids or form.visa_ids \
                           or form.cruise_ids or form.car_ids or form.railway_ids or form.activity_ids or form.addon_ids
                    
                ctx.update({'wiz_lines': wizlines})
                refund_id = inv_obj.refund(cr, uid, [inv.id], date, period, description, journal_id, context=ctx)
                refund = inv_obj.browse(cr, uid, refund_id[0], context=context)
                inv_obj.write(cr, uid, [refund.id], {'date_due': date,
                                                'check_total': inv.check_total})
                
                if inv.travel_type in ('dom_flight','int_flight'):
                    a = FT_obj.compute_refund_amount(cr,uid,refund.flight_ids,refund_id,context)
                
                inv_obj.button_compute(cr, uid, refund_id)

                created_inv.append(refund_id[0]) 
                
            # TODO: other services
            ttype_map = {'dom_flight': 'domflight', 'int_flight': 'intflight',
                         'dom_hotel': 'domhotel', 'int_hotel': 'inthotel',
                         'insurance': 'ins', 'railway': 'rail',
                         'visa': 'visa', 'cruise': 'cruise', 'add_on': 'addon',
                         'activity': 'activity', 'car':'car'
                         }
            
            if context.get('sale_view') == True:
                xml_id = (inv.type == 'out_refund') and ('action_trpurchaserefund_' + str(ttype_map[inv.travel_type])) or \
                         (inv.type == 'in_refund') and 'action_invoice_tree2' or \
                         (inv.type == 'in_invoice') and 'action_invoice_tree4' or \
                         (inv.type == 'out_invoice') and ('action_trsalerefund_' + str(ttype_map[inv.travel_type]))
            else:
                xml_id = (inv.type == 'out_refund') and ('action_trdebitnote_' + str(ttype_map[inv.travel_type])) or \
                         (inv.type == 'in_refund') and 'action_invoice_tree2' or \
                         (inv.type == 'in_invoice') and 'action_invoice_tree4' or \
                         (inv.type == 'out_invoice') and ('action_trcreditnote_' + str(ttype_map[inv.travel_type]))
                      
                                          
            result = mod_obj.get_object_reference(cr, uid, 'Trabacus', xml_id)
            id = result and result[1] or False
            result = act_obj.read(cr, uid, id, context=context)
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
        
account_invoice_refund()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: