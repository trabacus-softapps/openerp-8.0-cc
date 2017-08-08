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

from lxml import etree

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
        
    def default_get(self, cr, uid, fields, context=None):
        if not context: context = {}
        res = super(res_partner, self).default_get(cr, uid, fields, context=context) or {}

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Fetch: Account set under Configurations
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        param_obj = self.pool.get("ir.config_parameter")
        receive_id = param_obj.get_param(cr, uid, "receivable")
        payable_id = param_obj.get_param(cr, uid, "payable")
        
        if receive_id: res['property_account_receivable'] = int(receive_id)
        if payable_id: res['property_account_payable'] = int(payable_id)
        
        return res

    _columns = {
            # Overridden:
            'ref': fields.char('ID', size=200, select=1),
            
            # New:
            'tpartner_type' : fields.selection([('tp_hotel', 'Hotel'), ('tp_car', 'Transfers'), ('tp_dmc', 'DMC')
                                          , ('tp_visa', 'Visa'), ('tp_ins', 'Insurance'), ('tp_airticket', 'Air Ticket')
                                          , ('tp_cruise', 'Cruise'), ('tp_rail', 'Railway'), ('tp_other', 'Others')],'Service'),
            
            'city_id' : fields.many2one('tr.city', 'City', ondelete="restrict"),
            'city'    : fields.related('city_id', 'name', type='char', size=128, string='City', store=True),
            
            'tax_no'  : fields.char('Tax No.', size=64),
            'pan_no'  : fields.char('Pan No.', size=64),
            'sec'     : fields.char('Sector', size=100),
            
            'passport_no' : fields.char('Passport No.', size=30),
            'nation'      : fields.char('Nationality', size=30),
            'valid_from'  : fields.date('Valid From'),
            'valid_till'  : fields.date('Expiry Date'),
            'place_issue' : fields.char('Place of Issue', size=30),
            'dob'         : fields.date('DOB'),
            'anniversary' : fields.date('Anniversary'),
            'meal_pref'   : fields.char('Meal Preference', size=50),
            'remarks'     : fields.text('Remarks'),
            
            'flyer_ids' : fields.one2many('tr.flyer.details', 'partner_id', 'Frequent Flyer'),
            'stmt_ids'  : fields.one2many('tr.partner.statement', 'partner_id', 'Statement Details'),
            
            'industry'  : fields.char('Industry', size=30),
            'credit_rating' : fields.selection([('c', 'Credit'),('cwa','Credit with approval')
                                                ,('cac', 'Cash and carry'),('bl','Black List')], 'Credit Rating'),
            'dest_ids'    : fields.many2many('tr.destination', 'tr_partner_destination_rel', 'partner_id', 'dest_id', 'Destination'),
            'has_account' : fields.boolean('Has Ledger Account'),
            'hotel_id'    : fields.many2one('product.product', 'Hotel', ondelete="cascade"),
            
            'lead_ids'    : fields.one2many('crm.lead','partner_id','Leads'),
            'sale_ids'    : fields.one2many('account.invoice','partner_id','Sales Orders', domain=[('type','=','out_invoice'), ('state','in',('quotation', 'order_cancel'))]),
            'purchase_ids': fields.one2many('account.invoice','partner_id','Purchase Orders', domain=[('type','=','in_invoice'), ('state','in',('quotation', 'order_cancel'))]),
            'invoice_ids' : fields.one2many('account.invoice','partner_id','Customer Invoice', domain=[('type','=','out_invoice'), ('state','not in',('quotation', 'order_cancel'))]),
            'sinvoice_ids': fields.one2many('account.invoice','partner_id','Supplier Invoice', domain=[('type','=','in_invoice'), ('state','not in',('quotation', 'order_cancel'))]),
            'credit_ids'  : fields.one2many('account.invoice','partner_id','Credit Note', domain=[('type','=','out_refund'), ('state','not in',('quotation', 'order_cancel'))]),
            'debit_ids'   : fields.one2many('account.invoice','partner_id','Debit Note', domain=[('type','=','in_refund'), ('state','not in',('quotation', 'order_cancel'))]),
            'receipt_ids' : fields.one2many('account.voucher','partner_id','Customer Receipts'),
            'payment_ids' : fields.one2many('account.voucher','partner_id','Supplier Payments'),
            'group_id'    : fields.many2one('tr.group','Group'),      
                  }
    _defaults = {
                 'has_account': False,
#                  'company_id' : False
                'customer' : False
 
                 }
    
    def _generate_CustNo(self, cr, uid, vals, context=None):
                
        custno = 'C'
                
        cr.execute("""select id from res_partner where ref ilike '""" + str(custno) + """%' and customer=True order by id desc limit 1""")
        cust_rec = cr.fetchone()
        if cust_rec:
            cust = self.browse(cr, uid, cust_rec[0])
            auto_gen = cust.ref[len(custno) : ]
            custno += str(int(auto_gen) + 1).zfill(4)
        else:
            custno = custno + '0001'
            
        return {'ref' : custno}
    
    def _create_PartyLedger(self, cr, uid, ids, vals, context=None): 
        """
            Creates Ledger Account for Partner, when 'create_partyledger' is set True under Configuration
        """
        if context == None: context = {}
        
        partner_obj = self.pool.get('res.partner')
        config_obj = self.pool.get('trabacus.config.settings')
        account_obj = self.pool.get('account.account')
        company_id = self.pool.get('res.users').browse(cr, uid, uid,context).company_id.id
        
        new_vals = {}
        config = config_obj.get_default_values(cr, uid, [])
        
        if not config.get('create_partyledger', False):
            return True
        
        name = vals.get('name')
            
        try:
            drParent = config.get('parent_receivable_id')
            crParent = config.get('parent_payable_id')
             
            debit_parent = account_obj.browse(cr, uid, int(drParent))
            credit_parent = account_obj.browse(cr, uid, int(crParent))
            
            cr_ids = account_obj.search(cr, uid, [('code', 'like', str(credit_parent.code) + '%')], order='id desc', limit = 1)
            dr_ids = account_obj.search(cr, uid, [('code', 'like', str(debit_parent.code) + '%')], order='id desc', limit = 1)
            
            crCode = account_obj.read(cr, uid, cr_ids, ['code'])[0]['code']
            if crCode.isdigit():
                # When No child exists:
                if crCode == credit_parent.code:
                    crCode = credit_parent.code + '1'
                else: 
                    crCode = credit_parent.code + str(int(crCode[len(credit_parent.code):])+1) 
            else:
                crCode = str(crCode) + name.replace(' ','_'),
                    
            drCode = account_obj.read(cr, uid, dr_ids, ['code'])[0]['code']
            if drCode.isdigit():
                # When No child exists:
                if drCode == debit_parent.code:
                    drCode = debit_parent.code + '1'
                else:
                    drCode = debit_parent.code + str(int(drCode[len(debit_parent.code):])+1) 
            else:
                drCode = str(drCode) + name.replace(' ','_'),
            
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # [Customer] Both Receviable / Payable are set to Receviable Acc 
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if vals.get('customer', False) == True:
                debit_id = account_obj.create(cr, uid, {
                      'code'      : drCode,
                      'name'      : str(name + ' - Receivable'),
                      'parent_id' : debit_parent.id,
                      'type'      : 'receivable',
                      'reconcile' : True,
                      'user_type' : debit_parent.user_type.id,
                      'company_id': company_id,
                })
                new_vals.update({'property_account_receivable': debit_id})
                new_vals.update({'property_account_payable': debit_id})
           
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # [Supplier] Both Receviable / Payable are set to Payable Acc 
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if vals.get('supplier', False) == True:
                credit_id = account_obj.create(cr, uid, {
                      'code'      : crCode,
                      'name'      : str(name + ' - Payable'),
                      'parent_id' : credit_parent.id,
                      'type'      : 'payable',
                      'reconcile' : True,
                      'user_type' : credit_parent.user_type.id,
                      'company_id': company_id,
                  }) 
                new_vals.update({'property_account_payable': credit_id})
                new_vals.update({'property_account_receivable': credit_id})
                
            new_vals.update({'has_account':True})
        except:
            pass
        
        return self.write(cr, uid, ids, new_vals)
            
    def create(self, cr, uid, vals, context=None):
        if vals.get('customer', False) == True:
            vals.update(self._generate_CustNo(cr, uid, vals, context))
            
        return super(res_partner, self).create(cr, uid, vals, context)

res_partner()


class tr_partner_statement(osv.osv):
    _name = 'tr.partner.statement' 
    _description = "Customer Statement Details"
    _columns = {
        'partner_id'  : fields.many2one('res.partner','Partner', ondelete="cascade"),        
        'name'       : fields.char('Statement Name', size=60, required=True),
        'stmt_day'   : fields.selection([('01','01'),('02','02'),('03','03'),('04','04'),('05','05'),('06','06'),
                                         ('07','07'),('08','08'),('09','09'),('10','10'),('11','11'),('12','12'),
                                         ('13','13'),('14','14'),('15','15'),('16','16'),('17','17'),('18','18'),
                                         ('19','19'),('20','20'),('21','21'),('22','22'),('23','23'),('24','24'),
                                         ('25','25'),('26','26'),('27','27'),('28','28'),('29','29'),('30','30'),
                                         ('31','31')], 'Statement Day', required=True),
        'day_period' : fields.selection([('this','This Month'),('next','Next Month')], 'Period', required=True),
                                        
        'cycle_start'  : fields.selection([('01','01'),('02','02'),('03','03'),('04','04'),('05','05'),('06','06'),
                                         ('07','07'),('08','08'),('09','09'),('10','10'),('11','11'),('12','12'),
                                         ('13','13'),('14','14'),('15','15'),('16','16'),('17','17'),('18','18'),
                                         ('19','19'),('20','20'),('21','21'),('22','22'),('23','23'),('24','24'),
                                         ('25','25'),('26','26'),('27','27'),('28','28'),('29','29'),('30','30'),
                                         ('31','31')], 'Cycle Start Day', required=True),
        'cs_period' : fields.selection([('this','This Month'),('next','Next Month')], 'Period', required=True),
        
        'cycle_end'   : fields.selection([('01','01'),('02','02'),('03','03'),('04','04'),('05','05'),('06','06'),
                                         ('07','07'),('08','08'),('09','09'),('10','10'),('11','11'),('12','12'),
                                         ('13','13'),('14','14'),('15','15'),('16','16'),('17','17'),('18','18'),
                                         ('19','19'),('20','20'),('21','21'),('22','22'),('23','23'),('24','24'),
                                         ('25','25'),('26','26'),('27','27'),('28','28'),('29','29'),('30','30'),
                                         ('31','31')], 'Cycle End Day', required=True),
        'ce_period' : fields.selection([('this','This Month'),('next','Next Month')], 'Period', required=True),
                                         
        'cutoff'   : fields.selection([('01','01'),('02','02'),('03','03'),('04','04'),('05','05'),('06','06'),
                                         ('07','07'),('08','08'),('09','09'),('10','10'),('11','11'),('12','12'),
                                         ('13','13'),('14','14'),('15','15'),('16','16'),('17','17'),('18','18'),
                                         ('19','19'),('20','20'),('21','21'),('22','22'),('23','23'),('24','24'),
                                         ('25','25'),('26','26'),('27','27'),('28','28'),('29','29'),('30','30'),
                                         ('31','31')], 'Payment Cutoff Day', required=True),
        'co_period' : fields.selection([('this','This Month'),('next','Next Month')], 'Period', required=True),
        
        'credit_days':fields.integer('Credit Days'),
               }
    
tr_partner_statement() 
 


class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'
    _columns = {
       'branch'     : fields.char('Branch', size=30),
       'ifsc_code'  : fields.char('IFSC Code', size=30),
       'swift_address': fields.char('Swift Address' ,size=100),
                }
res_partner_bank()    

class tr_group(osv.osv):
    _name = 'tr.group' 
    _description = "Customer Group"
    _columns = {
                'name' : fields.char('Name', size=100, required=True),
                'customer' : fields.boolean('Customer'),
                'supplier' : fields.boolean('Supplier'),
                'company_id': fields.many2one('res.company', 'Company'),
               }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: