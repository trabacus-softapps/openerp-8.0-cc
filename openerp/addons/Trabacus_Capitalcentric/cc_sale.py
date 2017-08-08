from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

class sale_order(osv.osv):
    
    _inherit='sale.order'
    
    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        base_amt = line.price_unit + line.markup
        if line.tax_srvc_chrg:
           base_amt += line.service_charge
            
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, (base_amt) * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val
        
    _columns={#Overriden
              'state': fields.selection([
                        ('draft', 'Draft Quotation'),
                        ('sent', 'Offered'),
                        ('provisional','Provisional Booking'),
                        ('cancel', 'Cancelled'),
                        ('waiting_date', 'Waiting Schedule'),
                        ('progress', 'Confirmed'),
                        ('manual', 'Sale to Invoice'),
                        ('invoice_except', 'Invoice Exception'),
                        ('done', 'Done'),
                        ], 'Status', readonly=True, track_visibility='onchange',
                                     help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
              
              #New 
              'invoice_type': fields.selection([('to_client','To Client'),('to_venue','To Venue(Only Commission)'),('to_both','To Both(Commission&Purchase)')],'Invoice Type'),
              'service_type': fields.selection([('venue','Venue'),('noontea','Afternoon Tea')],'Service Type'),
              'lead_id'     : fields.many2one('crm.lead','Enquiry No'),
              'cc_datetime' : fields.datetime('Date Of Booking'),
              'group_name'  : fields.char('Group Name',size=125),
              'release_date': fields.date('Release Date'),
              }
   
    def action_button_confirm(self, cr, uid, ids, context=None):
                         
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
        Lead_obj = self.pool.get('crm.lead')
        for case in self.browse(cr,uid,ids):
            lead = Lead_obj.browse(cr,uid,case.lead_id.id)
            stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Confirmed')], context=context)
            if stage_id:
                Lead_obj.case_set(cr, uid, [lead.id], values_to_update={}, new_stage_id=stage_id, context=context)
            
                self.write(cr,uid,[case.id],{'state':'progress'})
        return res
     
    def Provisional_booking(self, cr, uid, ids, context=None):     
           
        Lead_obj = self.pool.get('crm.lead')
        for case in self.browse(cr,uid,ids):
            lead = Lead_obj.browse(cr,uid,case.lead_id.id)
            stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Provisional')], context=context)
            if stage_id:
                Lead_obj.case_set(cr, uid, [lead.id], values_to_update={}, new_stage_id=stage_id, context=context)
            
            self.write(cr,uid,case.id,{'state':'provisional'})                
        return True
    
    def _inv_get(self, cr, uid, order, context=None):
        vals={}
        if not context:
            return {}
        if 'type' in context and 'partner' in context:
            vals = {'type':context.get('type'),'partner_id':context.get('partner')}
        if 'journal' in context:
            vals['journal_id'] = context.get('journal')
        
        vals['date_invoice'] = time.strftime('%Y-%m-%d')
        vals['lead_id'] = order.lead_id.id
        vals['service_type'] = order.service_type
        vals['booking_date'] = order.cc_datetime
        return vals
    
    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        if context is None:
            context = {}

        inv = self._prepare_invoice(cr, uid, order, lines, context=context)
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv['payment_term'], time.strftime(DEFAULT_SERVER_DATE_FORMAT))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id 

    def to_add_followers(self, cr ,uid, ids, inv_id, partner, context=None):        
        Mail_obj = self.pool.get('mail.followers')
        Subtype_obj = self.pool.get('mail.message.subtype')
        subtype_ids = Subtype_obj.search(cr,uid,[('name','=','Discussions')])
        p_ids = []
        p_ids.append(partner.id)
        if partner.parent_id:
           p_ids.append(partner.parent_id.id)
        # for p in p_ids: Commented adding of followers is not required
        #     Mail_obj.create(cr,uid,{'res_model':'account.invoice',
        #                             'res_id': inv_id,
        #                             'partner_id' : p,
        #                             'subtype_ids': [(6, 0, subtype_ids)]
        #                        })
        return True

    def cc_create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the  sales order
            based on invoice type.     
            if invoice type is to_client it ill create a CI and a SI.
            if invoice type is to_venue it ill create only SI
            or invoice type is to_both it ill create 2 CI and a SI 
              """
        
        line_obj = self.pool.get('sale.order.line')
        Lead_obj = self.pool.get('crm.lead')
        
        for case in self.browse(cr, uid, ids, context):            
            
            journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'purchase'), ('company_id', '=', case.company_id.id)],
            limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error!'),
                    _('Please define purchase journal for this company: "%s" (id:%d).') % (case.company_id.name, case.company_id.id))
             
            #Creation of CI based on Customer                                   
            if case.invoice_type == 'to_client' or case.invoice_type == 'to_both':
               for line in case.order_line: 
                   #Create invoice lines with unit price
                   lines = line_obj.cc_invoice_line_create(cr, uid, [line.id],'ci_client', context)
                   sc_lines = line_obj.cc_invoice_line_create(cr, uid, [line.id],'ci_client_sc', context) 
               inv_id = self._make_invoice(cr, uid, case,sc_lines + lines, context)
               self.to_add_followers(cr, uid, ids, inv_id, case.partner_id, context)
               for line in case.order_line:                    
                   #Creation of SI based on Restaurant
                   if case.invoice_type == 'to_client':
                      inv_type = 'si_client'
                   else :
                      inv_type = 'si_both'  
                   lines = line_obj.cc_invoice_line_create(cr, uid, [line.id],inv_type, context)
                   context={'type':'in_invoice','partner':line.restaurant_id and line.restaurant_id.parent_id and line.restaurant_id.parent_id.id or line.restaurant_id.id,'journal':journal_ids[0]} 
                   inv_id = self._make_invoice(cr, uid, case, lines, context)
                   self.to_add_followers(cr, uid, ids, inv_id, line.restaurant_id, context)
            #Creation of CI based on Restaurant       
            if case.invoice_type == 'to_venue' or case.invoice_type == 'to_both' :                               
               for line in case.order_line: 
                   lines = line_obj.cc_invoice_line_create(cr, uid, [line.id],'ci_venue', context)
                   context={'type':'out_invoice','partner':line.restaurant_id and line.restaurant_id.parent_id and line.restaurant_id.parent_id.id or line.restaurant_id.id} 
                   inv_id = self._make_invoice(cr, uid, case, lines, context)
                   self.to_add_followers(cr, uid, ids, inv_id, line.restaurant_id, context)
                   
            if case.lead_id:
                lead = Lead_obj.browse(cr,uid,case.lead_id.id)
                stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Completed')], context=context)
                if stage_id:
                    Lead_obj.case_set(cr, uid, [lead.id], values_to_update={}, new_stage_id=stage_id, context=context)
            
            self.write(cr,uid,[case.id],{'state':'done'})
        return True
    
sale_order()


class sale_order_line(osv.osv):
    
    _inherit='sale.order.line'    
    
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
                         
            base_amt = line.price_unit + line.markup            
            if line.tax_srvc_chrg:
               base_amt += line.service_charge
                
            base_amt = (base_amt) * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, base_amt, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            if not line.tax_srvc_chrg:
               taxes['total'] += (line.service_charge * line.product_uom_qty)  
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total']) 
        return res
    
    def _get_menu_ids(self, cr, uid,ids,field_name, args, context=None):
        menu_obj = self.pool.get('cc.menus')
        partner_obj = self.pool.get('res.partner')           
        res = {}
        for case in self.browse(cr,uid,ids):                    
            menu_ids=[]
            if case.restaurant_id:
               menu_ids = menu_obj.search(cr,uid,['|',('partner_id','=',case.restaurant_id.id),('partner_id','=',case.restaurant_id.parent_id.id)])

            res[case.id] = menu_ids
        return res
    
    _columns={#Overriden:
              'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
              'invoiced': fields.boolean('Invoiced'),
              #New:
              'restaurant_id' : fields.many2one('res.partner','Restaurant',domain="[('partner_type','=','venue'),('supplier','=',True)]"),              
              'menu_mapping': fields.function(_get_menu_ids, method=True, string='Menu Mapping', type='text'),
              'menu_id' : fields.many2one('cc.menus','Menu', domain="[('id', 'in',menu_mapping)]"),              
              'markup' : fields.float('Markup'),
              'commission' : fields.float('Commission'),
              'room_hire' : fields.char('Room Hire',size=75),
              'set_up'    : fields.char('Set Up',size=75),
              'drinks'   : fields.char('Drinks',size=75),
              'place_cards' : fields.char('Place Cards',size=75),
              'table_plan'  : fields.char('Table Plan',size=75),
              'courses'     : fields.integer('Courses'),
              'service_charge' : fields.float('Service Charge'),
              'tax_srvc_chrg' : fields.boolean('Tax on Service Charge'),
              'sc_included' : fields.boolean('Service Charge(Included)'),
              } 
    _defaults = {'tax_srvc_chrg' : True}
    
    def onchange_menu(self, cr, uid, ids, menu_id, quantity, context=None):
        
        if not menu_id:
            return {}
        menus_obj = self.pool.get('cc.menus')
        
        value = {}
        Menu = menus_obj.browse(cr,uid,menu_id) 
        if Menu:
            value={'price_unit' : Menu.rest_price or 0.00,
                   'markup' : Menu.markup or 0.00,
                   'commission' : Menu.commission or 0.00,
                   'name' : Menu.description or '',
                   'service_charge' : Menu.service_charge or 0.00,
                   'sc_included' : Menu.sc_included or False
                   }
            
            value['price_subtotal'] = (value['price_unit'] + value['markup'] + value['service_charge']) * quantity or 0.00
            
        return {'value': value}   
    
    def get_subtotal(self, cr, uid, ids, quantity, price_unit, markup, service_charge, context=None):
        result = {}
        
        result['price_subtotal'] = (price_unit + markup + service_charge) * quantity
        
        return {'value':result}
        
    
    def cc_invoice_line_create(self, cr, uid, ids, type,context=None):
        if context is None:
            context = {}

        create_ids = []
        sales = set()
        for line in self.browse(cr, uid, ids, context=context):
            vals = self._prepare_order_line_invoice_line(cr, uid, line, False, context) 
                
            if vals:
               vals['sale_line_id'] = line.id or False
               vals['sc_included'] = line.sc_included or False 
               vals['name'] = 'Meal Booking on ' + str(line.order_id.cc_datetime)
               if line.order_id.invoice_type == 'to_client' or line.order_id.invoice_type == 'to_both' :
                  if type == 'ci_client':
                     vals.update({'price_unit':line.price_unit + line.markup})                 
                  elif type == 'ci_client_sc':
                     if line.service_charge <= 0.00 :
                        return True 
                     vals.update({'price_unit':line.service_charge,
                                  'descp_details':'Service Charge',
                                  'name':'Service Charge'})
                     if not line.tax_srvc_chrg:
                        vals.update({'invoice_line_tax_id' : False})                  
                  elif type == 'si_client':
                     vals.update({'price_unit':line.price_unit - line.commission})
                     vals.update({'invoice_line_tax_id': [(6, 0, [x.id for x in line.product_id.supplier_taxes_id])],})
                     
               if line.order_id.invoice_type == 'to_venue' or line.order_id.invoice_type == 'to_both' and type == 'ci_venue':
                     vals.update({'price_unit':line.commission}) 
                  
               inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
               self.write(cr, uid, [line.id], {'invoice_lines': [(4, inv_id)]}, context=context)
               sales.add(line.order_id.id)
               create_ids.append(inv_id)
        
        return create_ids
    
        
    def message_post(self, cr, uid, thread_id, body='', subject=None, type='comment',
                        subtype=None, parent_id=False, attachments=None, context=None, **kwargs):
        sale_obj = self.pool.get('sale.order')
        
        for case in self.browse(cr,uid,thread_id):
            sale_id = case.order_id.id
            
        return sale_obj.message_post(cr, uid, [sale_id], body=body, subject=subject, type=type, subtype=subtype, parent_id=parent_id, attachments=attachments, context=context, **kwargs)


    
sale_order_line()

    