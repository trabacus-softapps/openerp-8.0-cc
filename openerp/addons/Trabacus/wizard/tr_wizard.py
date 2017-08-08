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
import time

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
    ]

ttype_XMLmap = {'dom_flight': 'domflight', 
                         'int_flight': 'intflight',
                         'insurance': 'ins'
                         }

class tr_duplicate_ftpax(osv.osv_memory):
    _name = 'tr.duplicate.ftpax'
    _description = "Duplicating The Flight Passenger Ticket"
    _columns = {
              'no_ticket'  : fields.integer('No Of Tickets'),
              }
    _defaults = {
                'no_ticket' : 1,
                }
 
    def get_duplicate_ftpax(self, cr, uid, ids, context=None):
        """
            To Duplicate Flight Tickets
        """
        if context == None: context = {}
         
        FT_obj = self.pool.get('tr.invoice.flight')
        ftid = context.get('active_id')
        
        if not ftid: return False
        
        for case in self.browse(cr,uid,ids):
            for p in range(0, case.no_ticket):
                ftvals = FT_obj.copy_data(cr, uid, ftid) or {}
                
#                 tkno = ftvals['ticket_no']
#                 if tkno: 
#                     tkno = tkno + str(int(p + 1)).zfill(3)
                
                ftvals.update({
                               'ticket_no': '',
                               'pax_name' : '',
                               'paxpartner_id' : False,
                               'is_refunded' : False
                               })
                FT_obj.create(cr, uid, ftvals)
                 
        return {
                    'type': 'ir.actions.client',
                    'res_model': 'account.invoice', 
                    'tag': 'reload',
                    'context': context,
                } 
        
class tr_request_lead(osv.osv_memory):
    _name = 'tr.request.lead'
    _description = "Requesting for a particular lead"
    _columns = {
                'desc'  : fields.text('Description'),
              }
 
    def get_lead_request(self, cr , uid, ids,  context=None): 
        
        lead_obj = self.pool.get('crm.lead')
        Mail_obj = self.pool.get('mail.followers')
        user_obj = self.pool.get('res.users')
        mail_msg_obj = self.pool.get('mail.message')
        Subtype_obj = self.pool.get('mail.message.subtype')
        userdata = user_obj.read(cr, uid, [uid], ['tr_rptmanager_id','name'])[0]        
        rptuser = userdata['tr_rptmanager_id'] or False
        req_action = context.get('request_action')
        
        if context == None: context = {}
        if not context.get('active_id'): return

        for case in self.browse(cr, uid, ids):
            lead = lead_obj.read(cr, uid, [context.get('active_id')],['requested_to_id','requested_by_id'])
            if lead: 
                lead = lead[0]
                if not rptuser:
                    raise osv.except_osv(_('Warning'),_('Reporting Manager not configured for ' + lead['requested_to_id'][1] + '.'))             
                if uid != lead['requested_to_id'][0] and req_action in ('escalated','rejected'):
                    raise osv.except_osv(_('Warning'),_('This request can be ' + req_action + ' by ' + lead['requested_to_id'][1] + ' only.'))
                if uid != lead['requested_by_id'][0] and req_action in ('requested','cancelled'):
                    raise osv.except_osv(_('Warning'),_('This request can be ' + req_action + ' by ' + lead['requested_by_id'][1] + ' only.'))
            vals1 = {

                        'body'          : '</div>' + '<div>' + '<b>' + '. Requested By : ' + '</b>' + userdata['name'] + '</div>' + '<div>' + '<b>' + ' . Requested To : ' + '</b>' + (rptuser[1] or '') + '</div>' + '</div>' + '<b>' + ' . Description : ' + '</b>' + case.desc + '</div>' + '</div>' ,
                        'subject'       : 'Lead has been' + ' ' + req_action,
                        'model'         : 'crm.lead',
                        'res_id'        : context.get('active_id'),
                        'subtype_id'    : 1,
                        'type'          : 'comment'      
                        }
            msg_id = mail_msg_obj.create(cr, uid, vals1)
            if req_action in ('requested','escalated'):
                lead_obj.write(cr, uid, [context.get('active_id')], {'requisition_state': req_action, 'requested_by_id':uid, 'requested_to_id' :rptuser[0]})
            else:
                lead_obj.write(cr, uid, [context.get('active_id')], {'requisition_state': req_action})   
        
        return {
                'type': 'ir.actions.client',
                'res_model': 'crm.lead', 
                'tag': 'reload',
                'context': context,
                }  
        
class crm_make_sale(osv.osv_memory):
    _inherit = "crm.make.sale"
    _columns = {
                # Overridden:
        #         'shop_id': fields.many2one('sale.shop', 'Shop', required=False),
                'partner_id': fields.many2one('res.partner', 'Customer', required=False, domain=[('customer','=',True)]),
                
                # New:
                'action': fields.selection([
                        ('exist', 'Link to an existing customer'),
                        ('create', 'Create a new customer'),
                        ], 'Related Customer', required=True),
                'travel_type' : fields.selection(TRAVEL_TYPES,'Service Type'),
                }
    
    
    def default_get(self, cr, uid, fields, context=None):
        """
        Default get for name.
        If there is an exisitng partner link to the lead, 
        else create New Customer..
        """
        lead_obj = self.pool.get('crm.lead')

        res = super(crm_make_sale, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            partner_id = res.get('partner_id')
            lead = lead_obj.browse(cr, uid, int(context['active_id']), context=context)

            if 'action' in fields:
                res.update({'action' : partner_id and 'exist' or 'create'})
            if 'partner_id' in fields:
                res.update({'partner_id' : partner_id})

        return res
    
    # Overridden:
    def makeOrder(self, cr, uid, ids, context=None):
        """
          Creates Quotation (Invoice) on given case. 
        """
        if context is None: context = {}
        # update context: if come from phonecall, default state values can make the quote crash lp:1017353
        context.pop('default_state', False)        
        
        lead_obj = self.pool.get('crm.lead')
        invoice_obj = self.pool.get('account.invoice')
        partner_obj = self.pool.get('res.partner')
        obj_journal = self.pool.get('account.journal')
        models_data = self.pool.get('ir.model.data')
        
        data = context and context.get('active_ids', []) or []
        
        for make in self.browse(cr, uid, ids, context=context):
            
            # Create / link Partner
            partner_id = make.partner_id and make.partner_id.id or False
            leaddict = lead_obj.handle_partner_assignation(cr, uid, data, make.action, partner_id, context=context)
            # Assigning newly created partner
            if not partner_id:
                partner_id = leaddict[data[0]]
            
            partner = partner_obj.browse(cr, uid, partner_id)
            new_ids = []
            
            for case in lead_obj.browse(cr, uid, data, context=context):
                if not partner and case.partner_id:
                    partner = case.partner_id
                
                journal_ids = obj_journal.search(cr, uid, [('type','=','sale')], context=context)
                account_id = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
                vals = {
                    'origin': _('Lead: %s') % str(case.id),
                    'section_id': case.section_id and case.section_id.id or False,
                    'partner_id': partner.id,
                    'date_invoice': fields.date.context_today(self,cr,uid,context=context),
                    'journal_id': journal_ids and journal_ids[0] or False,
                    'account_id': account_id.id,
                    'state': 'quotation',
                    'type': 'out_invoice',
                    'travel_type': make.travel_type,
                    'lead_id': case.id,
                    'name'   : case.name,
                    'paxtype': case.paxtype,
                    'purpose': case.purpose,
                }
                if partner.id:
                    vals['user_id'] = partner.user_id and partner.user_id.id or uid
                new_id = invoice_obj.create(cr, uid, vals, context=context)
                invoice = invoice_obj.browse(cr, uid, new_id, context=context)
                lead_obj.write(cr, uid, [case.id], {'ref': 'account.invoice,%s' % new_id})
                new_ids.append(new_id)
                message = _("Lead has been <b>converted</b> to the Quotation <em>%s</em>.") % (invoice.name)
                case.message_post(body=message)
                
            if not new_ids:
                return {'type': 'ir.actions.act_window_close'}
           
            order_form = models_data.get_object_reference(cr, uid, 'Trabacus', 'view_invoice_form')[1]
            order_tree = models_data.get_object_reference(cr, uid, 'account', 'invoice_tree')[1]
            
            if len(new_ids)<=1:
                value = {
                    'domain'   : str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'form,tree',
                    'res_model': 'account.invoice',
                    'view_id'  : False,
                    'views'    : [(order_form, 'form'),
                                   (order_tree, 'tree')],
                    'type'  : 'ir.actions.act_window',
                    'name'  : _('Quotation'),
                    'res_id': new_ids and new_ids[0]
                }
            else:
                value = {
                    'domain'   : str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.invoice',
                    'view_id'  : False,
                    'views'    : [(order_form, 'form'),
                                   (order_tree, 'tree')],
                    'type'     : 'ir.actions.act_window',
                    'name'     : _('Quotation'),
                    'res_id'   : new_ids
                }
            return value
     
crm_make_sale()



class tr_make_partial_invoice(osv.osv_memory):
    _name = "tr.make.partial.invoice"
    _description = 'Line wise Invoicing'
    _columns = {
                
                'partner_id': fields.many2one('res.partner', 'Customer', required=False, domain=[('customer','=',True)]),
                'travel_type' : fields.selection(TRAVEL_TYPES,'Service Type'),
                'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        
                'action': fields.selection([('exist', 'Link to an existing Invoice'),
                                            ('create', 'Create a new Invoice')], 'Related Invoice', required=True), 
                
                }
    
    def default_get(self, cr, uid, fields, context=None):
        """
      
        """
        if not context: context = {}
        res = super(tr_make_partial_invoice, self).default_get(cr, uid, fields, context=context)
        
        invoice_id = res.get('invoice_id')

        if 'action' in fields:
            res.update({'action' : invoice_id and 'exist' or 'create'})
            
        if 'travel_type' in fields:
            res.update({'travel_type' : context.get('travel_type', '')})

        return res
    
    
    def _prepare_customerInvoice(self, cr, uid, invoice, partner_id, lines, date=None, context=None):
        """ 
            Prepare the dict of values to create the Invoice for the selected Invoice Lines.
            return: dict of value to create() the Invoice
        """
        invoice_obj = self.pool.get('account.invoice')

        invoice_data = {}
        for field in ['name', 'reference', 'comment', 'date_due', 'company_id', 'lead_id',
                'currency_id', 'payment_term', 'user_id', 'fiscal_position', 'period_id', 'journal_id',
                'paxtype', 'purpose', 'travel_type', 'type']:
            if invoice._all_columns[field].column._type == 'many2one':
                invoice_data[field] = invoice[field].id
            else:
                invoice_data[field] = invoice[field] if invoice[field] else False

        invoice_lines = []
        
        lines_list = invoice_obj._refund_cleanup_lines(cr, uid, lines, context=context)
        
        if invoice.travel_type in ('dom_flight','int_flight'):            
            invoice_data.update({'flight_ids':  lines_list}) 
            
        if not date:
            date = time.strftime('%Y-%m-%d')
            
        if partner_id:
            invoice_data.update(invoice_obj.onchange_partner_id(cr, uid, [invoice], invoice_data['type'], partner_id,
                                date, invoice_data['payment_term'], False, invoice_data['company_id'])['value'])
            
        invoice_data.update({
            'partner_id': partner_id,
            'date_invoice': date,
            'state': 'draft',
            'number': False,
        })
        return invoice_data

    def createInvoice(self, cr, uid, ids, context=None):
        """
            Creates Partial Invoice for selected Invoice Line
        """ 
        if context is None: context = {}
        invoice_obj = self.pool.get('account.invoice')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        
        data = context.get('active_ids', [])
        data_model = context.get('active_model', '')
        currentInv_id = context.get('invoice_id', False)
        
        # [delete]: current Invoice's Partner:
        if 'partner_id' in context:
            del context['partner_id']
        
        if not (data or data_model or currentInv_id):
            return False
        
        case = invoice_obj.browse(cr, uid, currentInv_id)
        data_model = self.pool.get(data_model)
        
        for make in self.browse(cr, uid, ids):
            lines = data_model.browse(cr, uid, data)
            target_invids = []
            updatevals = {}
            
            tot_curILines = [x.id for x in case.flight_ids]
            tot_curILines.remove(lines[0].id)
            if len(tot_curILines) == 0: updatevals['state'] = 'order_cancel'
            
            # TODO: 
            # For all other services
             
            if make.action == 'create':
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # Creating New Lines:
                inv_vals = self._prepare_customerInvoice(cr, uid, case, date=case.date_invoice,
                                                         partner_id=make.partner_id.id, lines=lines, context=context)
                newid = invoice_obj.create(cr, uid, inv_vals, context)
                invoice_obj.button_reset_taxes(cr, uid, [newid])
                target_invids.append(newid)
            else:
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # Merge to existing Invoice
                appendLines = []
                 
                newline = invoice_obj._refund_cleanup_lines(cr, uid, lines, context)
                # TODO:
                # Other services
                givenInv_lines = [x.id for x in make.invoice_id.flight_ids]
                givenInv_lines = map(lambda x: (4,x,False), givenInv_lines) 
                
                appendLines = givenInv_lines + newline
                invoice_obj.write(cr, uid, [make.invoice_id.id], {'flight_ids':appendLines})
                target_invids.append(make.invoice_id.id)

            # TODO:
            # For other services                
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Deleting Invoiced line in the Current Invoice:
            updatevals.update({'flight_ids':[(2,data[0])]})
            invoice_obj.write(cr, uid, [currentInv_id], updatevals)
            invoice_obj.button_reset_taxes(cr, uid, [currentInv_id])
            
            # TODO:
            # Need to fine tune opening action based on groups & Travel type
            xml_id = ('action_trinvoice_' + str(ttype_XMLmap[case.travel_type]))
            
            result = mod_obj.get_object_reference(cr, uid, 'Trabacus', xml_id)
            id = result and result[1] or False
            result = act_obj.read(cr, uid, id, context=context)
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', target_invids))
            result['domain'] = invoice_domain
            return result
        
class tr_assingn_leads(osv.osv_memory):
    """
    """

    _name = 'tr.assingn.leads'
    _description = 'Assigning Leads To Consultant '
    _columns = {
        'consultant_id': fields.many2one('res.users', 'Consultant', select=True),
    }
    
    def action_assign(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        lead_obj = self.pool.get('crm.lead')
        wizard = self.browse(cr, uid, ids[0], context=context)
        lead_ids = context.get('active_ids',False)
        lead_obj.write(cr,uid,lead_ids,{'consultant_id': wizard.consultant_id.id})
            
tr_assingn_leads()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: