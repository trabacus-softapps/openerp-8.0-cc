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
from dateutil import parser
from lxml import etree
import time
from lxml import etree
from datetime import datetime
from openerp.tools import float_compare

class account_voucher(osv.osv):
    _inherit ='account.voucher'
    _columns = {
        # Ovverridden
        'reference': fields.char('Ref #', size=500, readonly=True, states={'draft':[('readonly',False)]}, help="Transaction reference number."),
        
        # New                
        'cheque_no'   : fields.char('Cheque No',size=64, readonly=True, states={'draft': [('readonly', False)]}),
        'cheque_date' : fields.date('Cheque Date', readonly=True, states={'draft': [('readonly', False)]}),
        'bank_id'   : fields.many2one('res.bank','Bank', readonly=True, states={'draft': [('readonly', False)]}),
        'branch'    : fields.char('Branch',size=64, readonly=True, states={'draft': [('readonly', False)]}),
        'pay_type'  : fields.selection([('cheque','Cheque'),('credit','Credit / Debit Card'),('cash_dep','Cash Deposit')
                                       ,('cash','Cash'),('neft','NEFT/RTGS')],'Payment Type', readonly=True, states={'draft': [('readonly', False)]}),
        'deposit_in' : fields.char('Deposited IN',size=64),
        'deposit_dt' : fields.date('Deposited DT'),
        'value_date' : fields.date('Value Date'),
        'edit_voucher'   : fields.boolean('Edit Voucher Window'),
        
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account'),
                }
    
    _defaults = {
                 'pay_type' :'cash',
                 }
    def print_receipt(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        attachment_obj = self.pool.get('ir.attachment') 
        res = rep_obj.pentaho_report_action(cr, uid, 'account_receipt1', ids,None,None)

        return res
    
#     To do : need to delelte
#     def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
#         context = {}
#         if amount : amount = int(amount)
#         result = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None)
#         return result
#     
#     def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
#         context = {}
#         if amount : amount = int(amount)
#         result = super(account_voucher, self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None)
#         return result
    
    def auto_pairing(self, cr, uid, ids, context=None):
        """ To Pair the amount on click of button by calling onchange"""
        res ={}
        for case in self.browse(cr,uid,ids,context):
            if context == None: context = {}
            res = (self.onchange_partner_id(cr, uid, [case.id], case.partner_id and case.partner_id.id or False
                                     , case.journal_id and case.journal_id.id or False
                                     , case.amount, case.currency_id and case.currency_id.id or False
                                     , case.type, case.date, context=context))
        
            for i in res['value']['line_cr_ids']:
                self.write(cr, uid,ids,{
                                        'line_cr_ids':[(0,0,i)],
                                        'currency_id': res['value']['currency_id'],
                                        'pre_line ': res['value']['pre_line'],
                                        'account_id':res['value']['account_id'],
                                        'paid_amount_in_company_currency':res['value']['paid_amount_in_company_currency'],
                                        'writeoff_amount':res['value']['writeoff_amount'],
                                        'currency_help_label':res['value']['currency_help_label'],
                                        'payment_rate':res['value']['payment_rate'],
                                        'payment_rate_currency_id':res['value']['payment_rate_currency_id'],
                                        })
            for d in res['value']['line_dr_ids']:
                self.write(cr, uid,ids,{
                                        'line_dr_ids':[(0,0,d)],
                                        'currency_id': res['value']['currency_id'],
                                        'pre_line ': res['value']['pre_line'],
                                        'account_id':res['value']['account_id'],
                                        'paid_amount_in_company_currency':res['value']['paid_amount_in_company_currency'],
                                        'writeoff_amount':res['value']['writeoff_amount'],
                                        'currency_help_label':res['value']['currency_help_label'],
                                        'payment_rate':res['value']['payment_rate'],
                                        'payment_rate_currency_id':res['value']['payment_rate_currency_id'],
                                        })
        return True

# Overridden
    def proforma_voucher(self, cr, uid, ids, context=None):
        
        """ To Delete where allocation = 0 and reconcile = False"""
        voucherln_obj = self.pool.get('account.voucher.line')
        for vou in self.browse(cr,uid,ids,context):
            for vln in vou.line_ids:
                if vln.amount == 0 and vln.reconcile == False:
                    voucherln_obj.unlink(cr,1,vln.id)
        self.action_move_line_create(cr, uid, ids, context=context)
        return True   
# Overriden
    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        if voucher.type in ('purchase', 'payment'):
            credit = voucher.paid_amount_in_company_currency
        elif voucher.type in ('sale', 'receipt'):
            debit = voucher.paid_amount_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        move_line = {
                'name': voucher.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': voucher.account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                 'analytic_account_id' : voucher.account_analytic_id and voucher.account_analytic_id.id or False,
                 'amount_currency': company_currency <> current_currency and sign * voucher.amount or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due
            }
        print "2@@@",move_line
        return move_line

# Overridden    
    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []

        date = self.read(cr, uid, voucher_id, ['date'], context=context)['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = voucher.type in ('payment', 'purchase') and -1 or 1
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': voucher.reference or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id' : voucher.account_analytic_id and voucher.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date
            }
            print 'move_line',move_line
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            if move_line.get('account_tax_id', False):
                tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                if not (tax_data.base_code_id and tax_data.tax_code_id):
                    raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    sign = voucher.type in ('payment', 'purchase') and -1 or 1
                    foreign_currency_diff = sign * line.move_line_id.amount_residual_currency + amount_currency

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            print 'voucher_line',voucher_line
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                print 'new_id',new_id
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)
                print 'rec_ids',rec_ids
            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(voucher.reference or '/'),
                    'account_id': line.account_id.id,
                    'analytic_account_id' : voucher.account_analytic_id and voucher.account_analytic_id.id or False,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                }
                
                print "move_line_foreign_currency",move_line_foreign_currency
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        return (tot_line, rec_lst_ids)
                            
    def write(self, cr, uid, ids, vals, context=None):
        if context == None: context = {}
        users_obj = self.pool.get('res.users')
        usid = users_obj.browse(cr, uid, uid)
        
        for case in self.browse(cr, uid, ids): 
            if case.company_id.window_voucher:
                window_voucher = str(case.company_id.window_voucher)
                if window_voucher : 
                    cr.execute("select '" +datetime.today().strftime("%Y-%m-%d") +"'::date \
                                between v.date::date and v.date::date +'" + window_voucher +"'::int \
                                from account_voucher v where v.id in (" +str(case.id) +") limit 1" )
                    vchrdt = cr.fetchone()
                    # Checking for the group user cannot validate if cl exceeds
                    if vchrdt and vchrdt[0] == False:
                        if usid.tr_accounting and usid.tr_accounting not in ('acc_manager') and uid!=1:
                            if case.state in ('draft','posted') and case.edit_voucher == False:
                                raise osv.except_osv(_('warning'),_("You don't have a permission to edit this record!!"))
                                return False
                                
        return super(account_voucher, self).write(cr, uid, ids, vals, context)
        
class account_move(osv.osv):
    _inherit ='account.move'
    _columns = {
                # Overridden:
                'name': fields.char('Number', size=500, required=True),
                'ref': fields.char('Reference', size=500),
                 'edit_move'   : fields.boolean('Edit Move Window'),
                }
    def write(self, cr, uid, ids, vals, context=None):
        if context == None: context = {}
        users_obj = self.pool.get('res.users')
        usid = users_obj.browse(cr, uid, uid)
        
        for case in self.browse(cr, uid, ids): 
            if case.company_id.window_move:
                window_move = str(case.company_id.window_move)
                if window_move : 
                    cr.execute("select '" +datetime.today().strftime("%Y-%m-%d") +"'::date between m.date::date and m.date::date +'" + window_move +"'::int from account_move m where m.id in (" +str(case.id) +") limit 1" )
                    mvdt = cr.fetchone()
                    # Checking for the group user cannot validate if cl exceeds
                    if mvdt and mvdt[0] == False:
                            if usid.tr_accounting and usid.tr_accounting not in ('acc_manager') and uid!=1:
                                if case.state in ('draft','posted') and case.edit_move == False:
                                    raise osv.except_osv(_('Warning'),_("You don't have a permission to edit this record!!"))
                                    return False
                                
        return super(account_move, self).write(cr, uid, ids, vals, context)
    
class account_move_line(osv.osv):
    _inherit ='account.move.line'
    _columns = {
                # Overridden:
                'name': fields.char('Name', size=500, required=True),
                }
    
class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        #override of fields_view_get in order to change the label of the process button and the separator accordingly to the shipping type
        if context is None:
            context={}
        res = super(account_bank_statement, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('journal_type', False)
        if type:
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='edit_bankcash']"):
                if type in ('cash') :
                    node.set('string', _('Edit Cash Register Window'))
                elif type in ('bank'):
                    node.set('string', _('Edit Bank Statement Window'))
            res['arch'] = etree.tostring(doc)
        return res

    def _get_trbalance_end(self, cr, uid, ids, name, attr, context=None):
        res_currency_obj = self.pool.get('res.currency')
        res_users_obj = self.pool.get('res.users')
        voucher_obj = self.pool.get('account.voucher')
        stline_obj = self.pool.get('account.bank.statement.line') 
        res = {}         

        company_currency_id = res_users_obj.browse(cr, uid, uid,
                context=context).company_id.currency_id.id

        statements = self.browse(cr, uid, ids, context=context)
        for case in statements: 
            rcpt_amt = pay_amt = cash_debit = cash_credit = 0.00
            currency_id = case.currency.id
            
            res[case.id] = case.balance_start 
            if case.date: 
                for r in case.receipt_ids:                    
                    rcpt_amt += voucher_obj.browse(cr, uid, r.id).amount 
                
                for p in case.payment_ids:
                    pay_amt += voucher_obj.browse(cr, uid, p.id).amount 
                    
                for c in case.cash_ids:
                    cash_debit += stline_obj.browse(cr, uid, c.id).tr_debit 
                    cash_credit += stline_obj.browse(cr, uid, c.id).tr_credit 
                    
#            for line in case.move_line_ids:
#                if line.debit > 0:
#                    if line.account_id.id == case.journal_id.default_debit_account_id.id:
#                        res[case.id] += res_currency_obj.compute(cr,
#                                uid, company_currency_id, currency_id,
#                                line.debit, context=context)
#                else:
#                    if line.account_id.id == case.journal_id.default_credit_account_id.id:
#                        res[case.id]  -= res_currency_obj.compute(cr,
#                                uid, company_currency_id, currency_id,
#                                line.credit, context=context)
                        
            res[case.id] += rcpt_amt - pay_amt + cash_debit - cash_credit
            if case.line_ids:
              for line in case.line_ids:
                  res[case.id] += line.amount  
        
        return res    
    

    def _get_cash_lines(self, cr, uid, ids, name, args, context=None):
        res = {} 
        cash_ids = []
        stline_obj = self.pool.get('account.bank.statement.line') 
        journal_obj = self.pool.get('account.journal')
          
        for case in self.browse(cr, uid, ids): 
            if case.state == 'confirm' or case.closing_date:
                sql_str = "select id from account_bank_statement where closing_date is not null and journal_id = " + str(case.journal_id.id) + " and date < '" + str(case.date) + "' ORDER BY closing_date desc limit 1"
                cr.execute(sql_str)
                prev_id = cr.fetchone() 
                if prev_id: 
                    prev_cash_st = self.browse(cr, uid, prev_id[0])
                    cr.execute("""  select bl.id
                                    from account_bank_statement b
                                    inner join account_bank_statement_line bl on bl.statement_id = b.id
                                    where bl.account_id  = """ + str(case.journal_id.default_debit_account_id.id) + """
                                    and bl.date > '""" + str(prev_cash_st.closing_date)+ """' and bl.date <= '""" + str (case.closing_date)+ """'
                                    and b.state = 'confirm'
                                """)
                    cash = cr.fetchall()
                    if cash:
                        cash_ids = stline_obj.search(cr, uid, [('id','in',cash)]) 
                                    
            else:
                prev_id = self.search(cr, uid, [('journal_id','=',case.journal_id.id), ('state','=','confirm')], order='closing_date desc', limit=1)
                if prev_id:
                    prev_cash_st = self.browse(cr, uid, prev_id[0])
                    cr.execute("""  select bl.id
                                    from account_bank_statement b
                                    inner join account_bank_statement_line bl on bl.statement_id = b.id
                                    where bl.account_id  = """ + str(case.journal_id.default_debit_account_id.id) + """
                                    and bl.date > '""" + str(prev_cash_st.closing_date)+ """' 
                                    and b.state = 'confirm'
                                """)
                    cash = cr.fetchall()
                    if cash:
                        cash_ids = stline_obj.search(cr, uid, [('id','in',cash)]) 

            res[case.id] = cash_ids
        return res
    
    def _get_voucher_lines(self, cr, uid, ids, name, args, context=None):
        res = {} 
        rcpt_ids = []
        pay_ids = []
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal')
          
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'receipt_ids': [], 'payment_ids': []}  
            jour_ids = journal_obj.search(cr, uid, [('default_debit_account_id','=',case.journal_id.default_debit_account_id.id)])
                           
            if case.state == 'confirm' or case.closing_date:
                sql_str = "select id from account_bank_statement where closing_date is not null and journal_id = " + str(case.journal_id.id) + " and date < '" + str(case.date) + "' ORDER BY closing_date desc limit 1"
                cr.execute(sql_str)
                prev_id = cr.fetchone() 
                if prev_id:
                    prev_rec = self.browse(cr, uid, prev_id[0])
                    search_date = (parser.parse(prev_rec.closing_date)).strftime('%Y-%m-%d')
                    rcpt_ids = voucher_obj.search(cr, uid, [('date','>',search_date),('date','<=',case.closing_date),('journal_id','in',jour_ids),('type','=','receipt'),('state','=','posted')])
                    pay_ids = voucher_obj.search(cr, uid, [('date','>',search_date),('date','<=',case.closing_date),('journal_id','in',jour_ids),('type','=','payment'),('state','=','posted')])
                else:
                    search_date = (parser.parse(case.date)).strftime('%Y-%m-%d')
                    rcpt_ids = voucher_obj.search(cr, uid, [('date','<=',search_date),('journal_id','in',jour_ids),('type','=','receipt'),('state','=','posted')])
                    pay_ids = voucher_obj.search(cr, uid, [('date','<=',search_date),('journal_id','in',jour_ids),('type','=','payment'),('state','=','posted')])
                    
            else:
                prev_id = self.search(cr, uid, [('journal_id','=',case.journal_id.id), ('state','=','confirm')], order='closing_date desc', limit=1)
                if prev_id:
                    prev_rec = self.browse(cr, uid, prev_id[0])
                    search_date = (parser.parse(prev_rec.closing_date)).strftime('%Y-%m-%d')
                    rcpt_ids = voucher_obj.search(cr, uid, [('date','>',search_date),('journal_id','in',jour_ids),('type','=','receipt'),('state','=','posted')])
                    pay_ids = voucher_obj.search(cr, uid, [('date','>',search_date),('journal_id','in',jour_ids),('type','=','payment'),('state','=','posted')])
                else:
                    search_date = (parser.parse(case.date)).strftime('%Y-%m-%d')
                    rcpt_ids = voucher_obj.search(cr, uid, [('date','<=',search_date),('journal_id','in',jour_ids),('type','=','receipt'),('state','=','posted')])
                    pay_ids = voucher_obj.search(cr, uid, [('date','<=',search_date),('journal_id','in',jour_ids),('type','=','payment'),('state','=','posted')])
                    
            res[case.id]['receipt_ids'] = rcpt_ids
            res[case.id]['payment_ids'] = pay_ids 
                
        return res
    
    # overridden:
    def _get_statement(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.bank.statement.line').browse(cr, uid, ids, context=context):
            result[line.statement_id.id] = True
        return result.keys()

    _columns = {
                'edit_bankcash'   : fields.boolean('Edit Bank Statement/Cash Register Window'),
                
                'balance_end': fields.function(_get_trbalance_end,
                                 store = {
                                'account.bank.statement': (lambda self, cr, uid, ids, c={}: ids, ['line_ids','move_line_ids','balance_start'], 10),
                                'account.bank.statement.line': (_get_statement, ['amount'], 10),
                                 },
                                string="Computed Balance", help='Balance as calculated based on Opening Balance and transaction lines'),
            
                'receipt_ids': fields.function(_get_voucher_lines, relation='account.voucher', type="many2many", string='Receipts', multi=True),
                'payment_ids': fields.function(_get_voucher_lines, relation='account.voucher', type="many2many", string='Payments', multi=True),
               
                'cash_ids': fields.function(_get_cash_lines, method=True, relation='account.bank.statement.line', type="many2many", string='Cash Register'),
                }
    
    # Overridden:
    def button_dummy(self, cr, uid, ids, context=None):
        for case in self.browse(cr, uid, ids):
            calculated_bal = self._get_trbalance_end(cr, uid, [case.id], case.balance_end, None, context)[case.id]
            self.write(cr, uid, ids, {'balance_end_real': calculated_bal, 'balance_end': calculated_bal}, context=context)
        return True
    
    # Inherited:
    def button_confirm_bank(self, cr, uid, ids, context=None):
        done = []
        if context is None:
            context = {}
            
        super(account_bank_statement, self).button_confirm_bank(cr, uid, ids, context)

        for st in self.browse(cr, uid, ids, context=context):
            # updating starting balance for all next existing records
            cr.execute (""" SELECT date, id 
                            FROM account_bank_statement 
                            WHERE journal_id = %d AND NOT state = 'draft' AND id != %d AND date > '%s'   
                            ORDER BY date,id """ %(st.journal_id.id, st.id, st.date))
            next_ids = cr.fetchall()
            if next_ids:                
                open_bal = st.balance_end_real  
                for n in next_ids:
                    for bk in self.browse(cr, uid, [n[1]]):  
                        self.write(cr, uid, [bk.id], {'balance_start': open_bal})                        
                        calculated_bal = self._get_trbalance_end(cr, uid, [bk.id], bk.balance_end, None, context)[bk.id]                         
                        self.write(cr, uid, [bk.id], {'balance_end_real':calculated_bal}) 
                        open_bal = calculated_bal 
        res = {}
        if st.closing_date == False:
            res['closing_date'] = time.strftime("%Y-%m-%d %H:%M:%S")
        return self.write(cr, uid, ids, res, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context == None: context = {}
        users_obj = self.pool.get('res.users')
        usid = users_obj.browse(cr, uid, uid)
        
        for case in self.browse(cr, uid, ids): 
            if case.company_id.window_bankcash:
                window_bankcash = str(case.company_id.window_bankcash)
                if window_bankcash : 
                    cr.execute("select '" +datetime.today().strftime("%Y-%m-%d") +"'::date between b.date::date and b.date::date +'" + window_bankcash +"'::int from account_bank_statement b where b.id in (" +str(case.id) +") limit 1" )
                    bankdt = cr.fetchone()
                    # Checking for the group user cannot validate if cl exceeds
                    if bankdt and bankdt[0] == False:
                        if usid.tr_accounting and usid.tr_accounting not in ('acc_manager') and uid!=1:
                            if case.state in ('draft','open','confirm') and case.edit_bankcash == False:
                                raise osv.except_osv(_('Warning'),_("You don't have a permission to edit this record!!"))
                                return False
                                
        return super(account_bank_statement, self).write(cr, uid, ids, vals, context)
    
class account_bank_statement_line(osv.osv):
   _inherit = 'account.bank.statement.line'
       
   def _get_amount(self, cr, uid, ids, name, args, context=None):
        res = {}   
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'tr_debit':0.00, 'tr_credit':0.00}
            
            if case.amount < 0:
                res[case.id]['tr_debit'] = abs(case.amount)
            else:
                res[case.id]['tr_credit'] = abs(case.amount)
        return res

   _columns = {
                  'pay_type'  : fields.selection([('cheque','Cheque'),('credit','Credit / Debit Card'),('cash_dep','Cash Deposit')
                                       ,('cash','Cash'),('neft','NEFT/RTGS')],'Payment Type'),        
                  'cheq_no'   : fields.char('Cheque No',size=64),
                  'cheq_date' : fields.date('Cheque Date'),
                  'bank_id'   : fields.many2one('res.bank','Bank'),
                  'branch'    : fields.char('Branch',size=64),
                  'value_date': fields.date('Value Date'),
                  'tr_debit'  : fields.function(_get_amount, method=True, type="float", string='Debit', multi=True),
                  'tr_credit' : fields.function(_get_amount, method=True, type="float", string='Credit', multi=True),
               }
   _defaults = { 
                'pay_type' :'cheque',
               }
   
   def onchange_narration(self, cr, uid, ids, narration_id):
      res = {}
      if narration_id :
          narration = self.pool.get('tr.bank.narration').browse(cr, uid, narration_id).name
          res['name'] = narration
      return {'value':res} 

# class account_journal(osv.osv):
#     _inherit = "account.journal"
#     _description = "Journal"
#     _columns = {
#                 'edit_journal'   : fields.boolean('Edit Journal Window'),
#                 }
# 
#     def write(self, cr, uid, ids, vals, context=None):
#         if context == None: context = {}
#         users_obj = self.pool.get('res.users')
#         usid = users_obj.browse(cr, uid, uid)
#         
#         for case in self.browse(cr, uid, ids): 
#             if case.company_id.window_bankcash:
#                 window_bankcash = str(case.company_id.window_bankcash)
#                 if window_bankcash : 
#                     cr.execute("select b.date::date +'" + window_bankcash +"'::int from account_bank_statement b where m.id in (" +str(case.id) +") limit 1" )
#                     bankdt = cr.fetchone()
#                     # Checking for the group user cannot validate if cl exceeds
#                     if bankdt and bankdt[0]:
#                         if bankdt[0] > datetime.today().strftime("%Y-%m-%d") :
#                             if usid.tr_accounting and usid.tr_accounting not in ('acc_manager') and uid!=1:
#                                 if case.state in ('open','confirm') and case.edit_journal == False:
#                                     raise osv.except_osv(_('warning'),_("You don't have a permission to edit this record!!"))
#                                     return False
#                                 
#         result = super(account_bank_statement, self).write(cr, uid, ids, vals, context)
# 
# 
#       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
    