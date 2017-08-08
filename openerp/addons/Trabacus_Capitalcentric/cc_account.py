from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import base64
from openerp.osv.orm import browse_record, browse_null
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import calendar

class account_invoice(osv.osv):     
    
    _inherit='account.invoice' 
    
    def _get_bank_details(self, cr, uid, context=None):
        if context is None:context={}
        if context.get('type') in ('out_invoice','out_refund'):
           return """Please make cheques payable to Capital Centric           
BACS:           
Nat West
Season & Vine Ltd TA Capital Centric
Sort Code: 60-50-06
Account Number: 37803034
IBAN: GB89 NWBK 605006 37803034
BIC: NWBK GB 2 L"""        
        return ''
    def _get_payments(self, cr, uid, ids, name, args, context=None):  
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            voucher_ids = []
            cr.execute("""select avl.voucher_id from account_move am
                          inner join account_move_line aml on aml.move_id = am.id
                          inner join account_voucher_line avl on avl.move_line_id = aml.id
                          inner join account_voucher av on av.id = avl.voucher_id
                          where avl.amount > 0 and av.state not in ('cancel','draft')                        
                          and am.name = '""" + str(invoice.number) + """'""")
                        
            voucher = cr.fetchall()  
            if voucher:
               for v in voucher:
                   voucher_ids.append(v[0])             
            result[invoice.id] = voucher_ids
        return result
      
    _columns={#Overriden:
              'origin': fields.char('Source Document', size=500, help="Reference of the document that produced this invoice.", readonly=True, states={'draft':[('readonly',False)]}),
              #New:
              'create_date': fields.datetime('Creation Date', readonly=True,help="Date on which Invoice is created."),
              'write_date' : fields.datetime('Write Date', readonly=True,help="Date on which Invoice is Changed."),
              'service_type':fields.selection([('venue','Venue'),('noontea','Afternoon Tea')],'Service Type'),
              'passen_type'  : fields.selection([('group','Group'), ('fit','FIT For Purpose')],'Passenger Type'),
              'lead_id':fields.many2one('crm.lead','Enquiry No'),
              'booking_date' : fields.datetime('Date of Booking'),
              'purchase_order' : fields.char('Purchase Order',size=20),
              'info_id'        : fields.many2one('cc.send.rest.info','Restaurant Info'),
              'cc_payment_ids': fields.function(_get_payments, relation='account.voucher', type="many2many", string='Payments'),
              'sales_person'  : fields.many2one('res.users', 'Booked By'),
			  'cc_notes'      : fields.char('Notes',size=200),   
			  'vat_period_id' : fields.many2one('account.period','Vat Period'),
              }
    _defaults = {'comment':_get_bank_details}
    _order = 'id desc'

    def onchange_date_invoice(self, cr, uid, ids, date_invoice=None,context=None):
#         res=super(stock_picking,self).onchange_partner_in(cr, uid, ids,partner_id=False,context=None)
        g_ids = []
        res={}
        dom={}
        p_id = False
        state_id=0
        group_obj=self.pool.get('res.groups')
        user_id = self.pool.get('res.users').browse(cr,uid,uid)
        period_obj=self.pool.get('account.period')
        if date_invoice:

            cr.execute("select id from account_period where company_id='"+ str(user_id.company_id.id) +"'and date_start <= '" + date_invoice + "' and date_stop >='" + date_invoice + "'")
            p_ids = cr.fetchone()
            if p_ids:
                p_id = p_ids[0]
                vat_period_id = period_obj.browse(cr,uid,p_id)
                if vat_period_id.vat_status == 'close':
                    p_id = self.get_next_period(cr,uid,ids,date_invoice)

        res['vat_period_id'] = p_id

        return {'value':res}


    def onchange_booking_date(self, cr, uid, ids, booking_date=None,context=None):
        g_ids = []
        res={}
        dom={}
        p_id = False
        state_id=0
        group_obj=self.pool.get('res.groups')
        user_id = self.pool.get('res.users').browse(cr,uid,uid)
        partner_obj=self.pool.get('res.partner')
        if booking_date:
            cr.execute("select id from account_period where company_id='"+ str(user_id.company_id.id) +"'and date_start <= '" + booking_date + "' and date_stop >='" + booking_date + "'")
            p_ids = cr.fetchone()
            if p_ids:
                p_id = p_ids[0]
        res['period_id'] = p_id
        return {'value':res}

    def invoice_validate(self, cr, uid, ids, context=None):
        Lead_obj = self.pool.get('crm.lead')
        self.write(cr, uid, ids, {'state':'open'}, context=context)
        for case in self.browse(cr,uid,ids):
            if case.type == 'out_invoice':
               lead_ids = Lead_obj.search(cr,uid,[('lead_no','in',case.origin and case.origin.split(', ') or [])])
               for lead in Lead_obj.browse(cr,uid,lead_ids):
                   stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Invoiced')], context=context)
                   if stage_id:
                      Lead_obj.write(cr, uid, [lead.id], {'stage_id': stage_id}, context=context)
            if case.type == 'in_invoice':
               if not case.date_due:
                  raise osv.except_osv(_('Warning!'), _('Due Date is missing.'))
               elif not case.supplier_invoice_number:
                  raise osv.except_osv(_('Warning!'), _('Please enter Supplier Invoice Number.'))
               elif not case.vat_period_id:
                  raise osv.except_osv(_('Warning!'), _('VAT Period is missing.'))

        return True
    
    def print_invoice(self, cr, uid, ids, context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res = rep_obj.pentaho_report_action(cr, uid, 'Invoice', ids,None,None) 
        return res
    
    def confirm_paid(self, cr, uid, ids, context=None):
        
        Lead_obj = self.pool.get('crm.lead')
        
        res = super(account_invoice,self).confirm_paid(cr, uid, ids,context) 
        if res:
           for case in self.browse(cr,uid,ids):
               if case.type == 'out_invoice':
                   lead_ids = Lead_obj.search(cr,uid,[('lead_no','in',case.origin and case.origin.split(', ') or[])])
                   for lead in Lead_obj.browse(cr,uid,lead_ids):
                       stage_id = Lead_obj.stage_find(cr, uid, [lead], False, [('name','=','Paid')], context=context)
                       if stage_id:
                           Lead_obj.write(cr, uid, [lead.id], {'stage_id': stage_id}, context=context)
        return res
                
        
    def action_invoice_sent(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi invoice template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'account', 'email_template_edi_invoice')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'account.invoice',
            'default_res_id': ids[0],
#            'default_use_template': bool(template_id),
#            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }  
        
    def merge_monthly_invoice(self, cr, uid, ids, context=None):
        
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr,uid,[('payment_type','in',['monthly','pay_adv']),('partner_type','=','client')])
        start_dt = time.strftime("%Y-%m-01")
        end_dt = time.strftime("%Y-%m-%d")
        for case in partner_obj.browse(cr, uid, partner_ids):
            cr.execute("""select id from account_invoice 
                                    where partner_id =""" + str(case.id) + """
                                    and date_invoice between '""" + str(start_dt) + """' and '""" + str(end_dt) + """'
                                    and state='draft' and passen_type = 'fit'""" )
            invoice = cr.fetchall()
            invoice_ids = []
            for i in invoice:
                invoice_ids.append(i[0])
            if invoice_ids:
               self.do_merge(cr, uid, invoice_ids, context) 
        return True
            
             
    def do_merge(self, cr, uid, ids, context=None):
            """
            To merge similar type of Invoices.
            Invoices will only be merged if:
            * Invoices are in draft
            * Invoices belong to the same partner
            * Invoices are have same Service Type
            Lines will only be merged if:
            * Invoice lines are exactly the same except for the quantity and unit
    
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary
    
             @return: new Invoice id
    
            """
            #TOFIX: merged invoice line should be unlink
            wf_service = netsvc.LocalService("workflow")
            def make_key(br, fields):
                list_key = []
                for field in fields:
                    field_val = getattr(br, field)
                    if field in ('product_id', 'account_id'):
                        if not field_val:
                            field_val = False
                    if isinstance(field_val, browse_record):
                        field_val = field_val.id
                    elif isinstance(field_val, browse_null):
                        field_val = False
                    elif isinstance(field_val, list):
                        field_val = ((6, 0, tuple([v.id for v in field_val])),)
                    list_key.append((field, field_val))
                list_key.sort()
                return tuple(list_key)
    
            # Compute what the new Invoice should contain
    
            new_invoices = {}
    
            for inv in [invoice for invoice in self.browse(cr, uid, ids, context=context) if invoice.state == 'draft']:
                invoice_key = make_key(inv, ('partner_id', 'service_type'))
                new_invoice = new_invoices.setdefault(invoice_key, ({}, []))
                new_invoice[1].append(inv.id)
                invoice_infos = new_invoice[0]
                if not invoice_infos:
                    invoice_infos.update({
                                          'name': '',
                                          'origin': inv.origin or '',
                                          'type': inv.type,
                                          'account_id': inv.account_id.id,
                                          'partner_id': inv.partner_id.id,
                                          'journal_id': inv.journal_id.id,
                                          'invoice_line': {},
                                          'currency_id': inv.currency_id.id,
                                          'date_invoice' :inv.date_invoice,
                                          'service_type' :inv.service_type,
                                          'comment' : inv.comment or '',
                                          'passen_type':inv.passen_type})

                else:
                    if inv.date_invoice < invoice_infos['date_invoice']:
                        invoice_infos['date_invoice'] = inv.date_invoice
                    if inv.comment and invoice_infos['comment'] != inv.comment:
                        invoice_infos['comment'] = (invoice_infos['comment'] or '') + ('\n%s' % (inv.comment,))
                    if inv.origin and inv.origin not in invoice_infos['origin'].split():
                        invoice_infos['origin'] = (invoice_infos['origin'] or '') + (invoice_infos['origin'] != '' and ', ' or '') + str(inv.lead_id and inv.lead_id.lead_no or '')
    
                for invoice_line in inv.invoice_line:
                    line_key = make_key(invoice_line, ('name', 'invoice_line_tax_id', 'price_unit', 'product_id', 'account_id', 'sc_included','enq_dob','lead_id'))
                    i_line = invoice_infos['invoice_line'].setdefault(line_key, {})
                    if i_line:
                        # merge the line with an existing line
                        i_line['quantity'] += invoice_line.quantity * invoice_line.uos_id.factor / i_line['uom_factor']
#                         i_line['enq_dob'] = 
                    else:
                        # append a new "standalone" line
                        for field in ('quantity', 'uos_id'):
                            field_val = getattr(invoice_line, field)
                            if isinstance(field_val, browse_record):
                                field_val = field_val.id
                            i_line[field] = field_val
                        i_line['uom_factor'] = invoice_line.uos_id and invoice_line.uos_id.factor or 1.0
    
    
    
            allinvoices = []
            invoices_info = {}
            for invoice_key, (invoice_data, old_ids) in new_invoices.iteritems():
                # skip merges with only one Invoice
                if len(old_ids) < 2:
                    allinvoices += (old_ids or [])
                    continue
    
                # cleanup Invoice line data
                for key, value in invoice_data['invoice_line'].iteritems():
                    del value['uom_factor']
                    value.update(dict(key))
                invoice_data['invoice_line'] = [(0, 0, value) for value in invoice_data['invoice_line'].itervalues()]
    
                # create the new Invoice
                newinvoice_id = self.create(cr, uid, invoice_data)
                invoices_info.update({newinvoice_id: old_ids})
                allinvoices.append(newinvoice_id)
    
                # make triggers pointing to the old Invoices point to the new Invoice
                for old_id in old_ids:
                    wf_service.trg_redirect(uid, 'account.invoice', old_id, newinvoice_id, cr)
                    wf_service.trg_validate(uid, 'account.invoice', old_id, 'invoice_cancel', cr)
                
                self.button_reset_taxes(cr, uid, [newinvoice_id], context)
            return invoices_info


    def button_myview(self, cr, uid, ids, context=None): 
        if context is None:
            context = {}
        value = {}
        data_obj = self.pool.get('ir.model.data') 
        view_id = False 

        for case in self.browse(cr, uid, ids, context=context):  
             if case.type in ('out_invoice','out_refund'):                  
                data_id = data_obj._get_id(cr, uid, 'account', 'invoice_form')
            
             elif case.type in ('in_invoice','in_refund'):
                data_id = data_obj._get_id(cr, uid, 'account', 'invoice_supplier_form')                                
                 
             if data_id:
                view_id = data_obj.browse(cr, uid, data_id, context=context).res_id
                         
             value = {
                        'view_type' : 'form',
                        'view_mode' : 'form,tree',
                        'res_model' : 'account.invoice',
                        'res_id' : int(case.id),
                        'view_id': False,
                        'context': context,
                        'views': [(view_id, 'form')],
                        'type': 'ir.actions.act_window',
                        'target': 'current',           
                      }     
        return value


    def create(self, cr, uid, vals, context=None):
        user_id = self.pool.get('res.users').browse(cr,uid,uid)
        period_obj=self.pool.get('account.period')
        if vals.get('date_invoice',False):
            date_invoice = vals.get('date_invoice',False)
            cr.execute("select id from account_period where company_id='"+ str(user_id.company_id.id) +"'and date_start <= '" + date_invoice + "' and date_stop >='" + date_invoice + "'")
            p_ids = cr.fetchone()
            if p_ids:
                p_id= p_ids[0]
                vat_period_id = period_obj.browse(cr,uid,p_id)
                if vat_period_id.vat_status == 'close':
                    p_id = self.get_next_period(cr,uid,[],date_invoice)

                vals['vat_period_id'] =p_id

        if vals.get('booking_date',False):
            booking_date = vals.get('booking_date',False)
            cr.execute("select id from account_period where company_id='"+ str(user_id.company_id.id) +"'and date_start <= '" + booking_date + "' and date_stop >='" + booking_date + "'")
            p_ids = cr.fetchone()
            if p_ids:
                vals['period_id'] = p_ids[0]

        return super(account_invoice,self).create(cr, uid ,vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        p_id = False
        period_obj=self.pool.get('account.period')
        for case in self.browse(cr,uid,ids):
            if vals.get('date_invoice',False):
                date_invoice = vals.get('date_invoice',False)
                cr.execute("select id from account_period where company_id='"+ str(case.company_id.id) +"'and date_start <= '" + str(date_invoice) + "' and date_stop >='" + str(date_invoice) + "'")
                p_ids = cr.fetchone()
                if p_ids:
                    p_id= p_ids[0]
                    vat_period_id = period_obj.browse(cr,uid,p_id)
                    if vat_period_id.vat_status == 'close':
                        p_id = self.get_next_period(cr,uid,ids,date_invoice)

                vals['vat_period_id'] =p_id

            if vals.get('booking_date',False):
                booking_date = vals.get('booking_date',False)
                cr.execute("select id from account_period where company_id='"+ str(case.company_id.id) +"'and date_start <= '" + str(booking_date) + "' and date_stop >='" + str(booking_date) + "'")
                p_ids = cr.fetchone()
                if p_ids:
                    vals['period_id'] = p_ids[0]

        return super(account_invoice,self).write(cr, uid ,ids,vals, context)

    def get_next_period(self,cr,uid,ids,invdate,context=None):
        print "inv_date",invdate
        p_id=False
        user_id = self.pool.get('res.users').browse(cr,uid,uid)
        next_month = int(invdate[5:7])+1
        next_day = str(invdate[8:])
        if next_month == 2:
           invdate = str(invdate[:4])+"-"+str(next_month)+"-"+str('28')
        if next_month<10:
            next_month = "0"+str(next_month)
        if int(invdate[8:])<10:
            next_day = "0"+str(invdate[8:])
        if int(invdate[8:])>30:
            next_day ="30"

        invdate = str(invdate[:4])+"-"+str(next_month)+"-"+str(next_day)
        if next_month == 13:
            next_month = "01"
            next_year = int(invdate[:4])+1
            invdate = str(next_year)+"-"+str(next_month)+"-"+str(invdate[8:])

        print "next_month",next_month,"-",invdate
        if invdate:
            cr.execute("select id from account_period where company_id='"+ str(user_id.company_id.id) +"'and date_start <= '" + invdate + "' and date_stop >='" + invdate + "'")
            p_ids = cr.fetchone()
            if p_ids:
                p_id = p_ids[0]

        print "inv_dd",p_id
        return p_id

    def unlink(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr,uid,uid)
        mod_obj = self.pool.get('ir.model.data')
        
        for case in self.browse(cr,uid,ids):
            if case.lead_id:
                xml_id = (case.lead_id.service_type == 'venue') and 'action_cclead_venue' or \
                            (case.lead_id.service_type == 'noontea') and 'action_cclead_ntea'
                     
                result = mod_obj.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', xml_id)          
                vals1 = {
                         'body':'Invoice <b>' + str(case.number or '')+'</b> has been deleted by <b>'+ str(user.name or '')+'.',
                         'subject'   : 'Invoice <b>' + str(case.number or '')+'</b> has been deleted',
                         'type'      : 'notification',
                         'model'     : 'crm.lead',
                         'res_id'    : case.lead_id.id,
                         'ccaction_id'    : result and result[1] or 0
                        }                    
                self.pool.get('mail.message').create(cr, uid, vals1)
        return super(account_invoice,self).unlink(cr, uid ,ids, context)
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
#         today = 
        if context is None:
           context={} 
        res = []   
        first_day = last_day = False
        user = self.pool.get('res.users').browse(cr, uid, uid) 
        def get_utc(user, bking_date):
            dob_frmt = bking_date
            local = pytz.timezone (user.tz or 'Europe/London') 
            naive = datetime.strptime (dob_frmt, "%Y-%m-%d %H:%M")
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone (pytz.utc)
            return utc_dt.strftime("%Y-%m-%d %H:%M")

        if context.get('search_bkingdate'):
           for ar in args:
               idx = args.index(ar)
               if ar[0] == 'booking_date':
                  first_day = (datetime.strptime(ar[2],"%Y-%m-%d %H:%M:%S")).strftime("%Y-%m-%d %H:%M")
                  last_day = get_utc(user, (datetime.strptime(ar[2],"%Y-%m-%d %H:%M:%S") + relativedelta(days=1)).strftime("%Y-%m-%d 23:59"))
                  del args[idx]
                  args.append(['booking_date','>=',first_day])
                  args.append(['booking_date','<=',last_day])
                  break

        if context.get('prev_month',False):
           last_day = get_utc(user,(datetime.strptime(time.strftime("%Y-%m-01"),"%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d 23:59"))
           first_day = get_utc(user,(datetime.strptime(time.strftime("%Y-%m-01"),"%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-01 00:00"))  
           args.append(['booking_date','>=',first_day])
           args.append(['booking_date','<=',last_day])
           
        elif context.get('curr_month',False):
           dday = datetime.strptime(time.strftime("%Y-%m-%d"),"%Y-%m-%d")           
           last_day = get_utc(user,dday.strftime("%Y-%m-" + str(calendar.mdays[dday.month]) +" 23:59"))
           first_day = get_utc(user,time.strftime("%Y-%m-01 00:00"))  
           args.append(['booking_date','>=',first_day])
           args.append(['booking_date','<=',last_day])
           
        elif context.get('nxt_month',False):
           dday = datetime.strptime(time.strftime("%Y-%m-%d"),"%Y-%m-%d") + relativedelta(months=1) 
           last_day = get_utc(user,dday.strftime("%Y-%m-" + str(calendar.mdays[dday.month]) +" 23:59"))
           first_day = get_utc(user,dday.strftime("%Y-%m-01 00:00"))  
           args.append(['booking_date','>=',first_day])
           args.append(['booking_date','<=',last_day])
               
        res = super(account_invoice, self).search(cr, uid, args, offset, limit, order, context, count)
        
        if context.get('curr_month_inv',False): 
           dday = datetime.strptime(time.strftime("%Y-%m-%d"),"%Y-%m-%d")           
           last_day = get_utc(user,dday.strftime("%Y-%m-" + str(calendar.mdays[dday.month]) +" 23:59"))
           first_day = get_utc(user,time.strftime("%Y-%m-01 00:00"))
        
        if context.get('prev_month_inv',False):
           last_day = get_utc(user,(datetime.strptime(time.strftime("%Y-%m-01"),"%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d 23:59"))
           first_day = get_utc(user,(datetime.strptime(time.strftime("%Y-%m-01"),"%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-01 00:00"))  

        if context.get('nxt_month_inv',False):
           dday = datetime.strptime(time.strftime("%Y-%m-%d"),"%Y-%m-%d") + relativedelta(months=1) 
           last_day = get_utc(user,dday.strftime("%Y-%m-" + str(calendar.mdays[dday.month]) +" 23:59"))
           first_day = get_utc(user,dday.strftime("%Y-%m-01 00:00"))   
        
        if first_day and last_day:
           cr.execute(""" select distinct(ai.id)
                          from account_invoice ai 
                          inner join account_invoice_line ail on ail.invoice_id = ai.id 
                          inner join crm_lead cl on cl.id = ail.lead_id 
                          where cl.date_requested between %s and %s 
                          and ai.id in %s""",(first_day,last_day,tuple(res),))
           res = [x[0] for x in cr.fetchall()]
        
        return res


account_invoice()

class account_invoice_line(osv.osv):
    _inherit='account.invoice.line'

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            res[line.id] = {'price_subtotal' : 0.00 , 'tax_amt':0.00}
            price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
            res[line.id]['price_subtotal'] = taxes['total']
            for tx in taxes['taxes']:                
                res[line.id]['tax_amt'] += tx.get('amount',0.00)
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, res[line.id]['price_subtotal'])
        return res
   
    _columns={
              #Overridden
              'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
                                                digits_compute= dp.get_precision('Account'), store=True,multi='subtotal'),
              'tax_amt': fields.function(_amount_line, string='Tax Amount', type="float", store=True,multi='subtotal'),
              'quantity': fields.integer('Covers' ,required=True),
             
              #New
              'descp_details' : fields.char('Description',size=75),
              'sale_line_id'  : fields.many2one('sale.order.line','Sale Order Line'),              
              'sc_included' : fields.boolean('Service Charge(Included)'),
              'enq_dob'     : fields.datetime('Date of Booking'),
              'lead_id'     : fields.many2one('crm.lead','Lead No.'),
              }
    _order = 'enq_dob'
   
account_invoice_line()

class account_voucher(osv.osv):
    _inherit='account.voucher'
    _columns={'date':fields.date('Date', required=1,readonly=True, select=True, states={'draft':[('readonly',False)]}, help="Effective date for accounting entries"),
              'passen_type'  : fields.selection([('group','Group'), ('fit','FIT For Purpose')],'Passenger Type'),
              }
    _defaults ={'date': False}    
    
            
    def print_voucher(self, cr, uid, ids, context=None):
        if context is None:context = {}
        rep_obj = self.pool.get('ir.actions.report.xml')
        res = rep_obj.pentaho_report_action(cr, uid, 'Receipt_Payment', ids,{},None) 
        return res

    def action_voucher_sent(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi invoice template message loaded by default
        '''
        if context is None: context = {}
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'Trabacus_Capitalcentric', 'template_voucher_receipt')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'account.voucher',
            'default_res_id': ids[0],
            'active_model' :'account.voucher',
           'default_use_template': bool(template_id),
           'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


    def proforma_voucher(self, cr, uid, ids, context=None):
        super(account_voucher,self).proforma_voucher(cr, uid, ids, context)
        case = self.browse(cr, uid, ids and ids[0])
        if case.type == 'payment':
           return self.action_voucher_sent(cr, uid, ids, context)
        return True

    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')

        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'

        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_lines_found = []

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_lines_found.append(line.id)
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_lines_found.append(line.id)
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_lines_found.append(line.id)
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        #voucher line creation
        for line in account_move_lines:

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)

            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency

                amount_original = round(currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency),2)
                amount_unreconciled = round(currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency),2)

            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (line.id in move_lines_found) and min(abs(price), amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            price -= rs['amount']
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_lines_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        print 'rs[amount]',amount
                        rs['amount'] = amount
                        total_debit -= amount
                        total_debit = round(total_debit,2)
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount
                        total_credit = round(total_credit,2)

            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
        return default

    
account_voucher()

class account_period(osv.osv):
    _inherit='account.period'
    _columns={'vat_status':fields.selection([('open','Open'),('close','Closed')],'Vat Status')}
    _defaults={'vat_status':'open'}
    def close_vat_period(self, cr, uid,ids,context=None):
        if not context:
            context={}
        if context.get("close",False):
            self.write(cr,uid,ids,{'vat_status':'close'})
        if context.get("reopen",False):
            self.write(cr,uid,ids,{'vat_status':'open'})

        return True
account_period()

    
class account_invoice_report(osv.osv):
    _inherit='account.invoice.report'    
    _auto = False
    _columns={'service_type':fields.selection([('venue','Venue'),('noontea','Afternoon Tea')],'Service Type'),
              'amount_tax':fields.float('Tax'),
              'amount_total':fields.float('Total'),
             }
    
    def _select(self):
        res = super(account_invoice_report,self)._select()
        if res:
           res += ' ,sub.service_type, sub.amount_tax, sub.amount_total' 
        return res

#     def _sub_select(self):
#         select_str = super(account_invoice_report,self)._sub_select()
#         select_str = """
#                 SELECT min(ail.id) AS id,
#                     ai.date_invoice AS date,
#                     to_char(ai.date_invoice::timestamp with time zone, 'YYYY'::text) AS year,
#                     to_char(ai.date_invoice::timestamp with time zone, 'MM'::text) AS month,
#                     to_char(ai.date_invoice::timestamp with time zone, 'YYYY-MM-DD'::text) AS day,
#                     ail.product_id, ai.partner_id, ai.payment_term, ai.period_id,
#                     CASE
#                      WHEN u.uom_type::text <> 'reference'::text
#                         THEN ( SELECT product_uom.name
#                                FROM product_uom
#                                WHERE product_uom.uom_type::text = 'reference'::text
#                                 AND product_uom.active
#                                 AND product_uom.category_id = u.category_id LIMIT 1)
#                         ELSE u.name
#                     END AS uom_name,
#                     ai.currency_id, ai.journal_id, ai.fiscal_position, ai.user_id, ai.company_id,
#                     count(ail.*) AS nbr,
#                     ai.type, ai.state, pt.categ_id, ai.date_due, ai.account_id, ail.account_id AS account_line_id,
#                     ai.partner_bank_id,
#                     SUM(CASE
#                          WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
#                             THEN (- ail.quantity) / u.factor
#                             ELSE ail.quantity / u.factor
#                         END) AS product_qty,
#                     SUM(CASE
#                          WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
#                             THEN - ail.price_subtotal
#                             ELSE ail.price_subtotal
#                         END) AS price_total,
#                     CASE
#                      WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
#                         THEN SUM(- ail.price_subtotal)
#                         ELSE SUM(ail.price_subtotal)
#                     END / CASE
#                            WHEN SUM(ail.quantity / u.factor) <> 0::numeric
#                                THEN CASE
#                                      WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
#                                         THEN SUM((- ail.quantity) / u.factor)
#                                         ELSE SUM(ail.quantity / u.factor)
#                                     END
#                                ELSE 1::numeric
#                           END AS price_average,
#                     CASE
#                      WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
#                         THEN - ai.residual
#                         ELSE ai.residual
#                     END AS residual,
#                     ai.service_type, 
#                     sum(CASE
#                             WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
#                             THEN - ail.tax_amt
#                             ELSE ail.tax_amt
#                         END) AS amount_tax,
#                     CASE
#                             WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
#                             THEN - ai.amount_total
#                             ELSE ai.amount_total
#                     END AS amount_total 
#         """
#         return select_str


    def _sub_select(self):
        res = super(account_invoice_report,self)._sub_select()
        res = res.replace("""/ CASE
                           WHEN (( SELECT count(l.id) AS count
                                   FROM account_invoice_line l
                                   LEFT JOIN account_invoice a ON a.id = l.invoice_id
                                   WHERE a.id = ai.id)) <> 0
                               THEN ( SELECT count(l.id) AS count
                                      FROM account_invoice_line l
                                      LEFT JOIN account_invoice a ON a.id = l.invoice_id
                                      WHERE a.id = ai.id)
                               ELSE 1::bigint
                          END::numeric AS residual""", 'AS residual')
        res += """                
                    ,ai.service_type, 
                    sum(CASE
                            WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN - ail.tax_amt
                            ELSE ail.tax_amt
                        END) AS amount_tax,
                    sum(CASE
                            WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN - (ail.price_subtotal + ail.tax_amt)
                            ELSE ail.price_subtotal + ail.tax_amt
                    END )AS amount_total      
        """
        return res
     
    def _group_by(self):
        res = super(account_invoice_report,self)._group_by()
        if res:
           res += ' ,ai.service_type, ai.amount_tax' 
        return res
    
account_invoice_report()

class account_account(osv.osv):
    _inherit='account.account'
    _parent_order = 'name'
    _columns={'cc_type':fields.selection([('a_turnover','Turnover'),('b_cost_sales','Cost Of Sales'),('c_expense','Expense')],'Type')}
account_account()
    
