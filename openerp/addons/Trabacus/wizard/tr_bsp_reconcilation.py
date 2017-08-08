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
import base64
import StringIO
import csv
import sys
import xlrd
from xlrd import open_workbook
from xlsxwriter.workbook import Workbook
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
import logging
import tempfile
import os
from openerp import workflow
_logger = logging.getLogger(__name__)
class tr_bsp_reconcilation(osv.osv_memory):
    _name = 'tr.bsp.reconcilation'
    _columns={
              'start_dt'    : fields.date('Start Date'),
              'end_dt'      : fields.date('End Date'),
              'bsp_xlsdata' : fields.binary('BSP-Excel File'),
              }
    def is_number(self,cr,uid,ids,s):
        try:
            float(s)
            return True
        except ValueError:
            pass
     
        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except (TypeError, ValueError):
            pass
     
        return False
    
    def _update_taxline(self,cr,uid,ids,cell_value6,cell_value8,ftln_ids,ft_id,context):
           comp_obj = self.pool.get('tr.airlines.taxcomp')
           arlntax_obj = self.pool.get('tr.airlines.taxes')
           ftln_obj = self.pool.get('tr.invoice.flight.lines')
           ft_obj = self.pool.get('tr.invoice.flight')
           arlntax_ids = arlntax_obj.search(cr,uid,[('component_id.name','=',cell_value8),('ftline_id','in',ftln_ids)])
           # If Airline tax is there map the amount or else create the taxline with comp
           if arlntax_ids:
               arlntax_amount = arlntax_obj.browse(cr,uid,arlntax_ids[0]).amount
#                if not arlntax_amount == cell_value6:
#                    if cell_value8 != 'CP': arlntax_obj.write(cr,uid,arlntax_ids,{'amount' : cell_value6})
           if not arlntax_ids : 
               cmp_ids = comp_obj.search(cr, uid, [('name','=', cell_value8)])
#                if not cmp_ids:                                
#                    cmp_ids.append(comp_obj.create(cr, uid, {'name': cell_value8}))
#                if context.get('flight_line',False) or context.get('previous',False) or context.get('tax_line',False):
#                    if cell_value8 != 'CP':
#                        arlntax_obj.create(cr,uid,{'component_id': cmp_ids and cmp_ids[0] or False,
#                                                    'amount'      : cell_value6,
#                                                'ftline_id'   : ftln_ids and ftln_ids[0]})
#                    if cell_value8 == 'CP':
#                        ft_obj.write(cr,uid,[ft_id.id],{'cancel_charges' : ft_id.cancel_charges + cell_value6,'a_other':0,'a_tds' : 0,'a_raf' : 0,'a_vendor' : 0,
#                                                        'a_markup' : 0,'a_servicechrg' : 0,'a_reissue' : 0,'a_tptax' : 0 })
           return True 
       
#     def import_bsp_data(self, cr, uid, res, main_obj, workbook, worksheet, bold, right_align, dataFile):
    def import_bsp_data(self,cr,uid,ids,context=None):
        ft_obj = self.pool.get('tr.invoice.flight')
        ftln_obj = self.pool.get('tr.invoice.flight.lines')
        arln_obj = self.pool.get('tr.airlines')
        comp_obj = self.pool.get('tr.airlines.taxcomp')
        arlntax_obj = self.pool.get('tr.airlines.taxes')
        inv_obj = self.pool.get('account.invoice')
        invln_obj = self.pool.get('account.invoice.line')
        for x in self.browse(cr,uid,ids):
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #    Reading The XLS File
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#             workbook = xlrd.open_workbook('/home/serveradmin/Desktop/refd 01-12-13 to 07-12-13.xls')
            dataFile = tempfile.mkstemp(".xls")[1]
            fp = open(dataFile,'wb')
            fp.write(base64.decodestring(x.bsp_xlsdata))
            fp.close()
            fp = open(dataFile,'rb')
            workbook = xlrd.open_workbook(dataFile)
            _logger.info('Date  %s Reading The BSP File %s', ((datetime.today() + relativedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")),dataFile)
            a = "\n \t Date : "+ (datetime.today() + relativedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S") +", Reading The BSP File " +dataFile + "\n"
            fplog_comp = open("/home/serveradmin/Desktop/bsp_complaints.log","ab") 
            fplog_comp.write(a)
            fplog_dscrpncs = open("/home/serveradmin/Desktop/bsp_discrepancies.log","ab") 
            fplog_dscrpncs.write(a)
            fplog_misng = open("/home/serveradmin/Desktop/bsp_missing.log","ab") 
            fplog_misng.write(a)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #    Reading The First Sheet 
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            worksheet = workbook.sheet_by_name('Sheet1')
            num_rows = worksheet.nrows - 1
            num_cells = worksheet.ncols - 1
            curr_row = -1
            ft_ids = []
            pre_airno = 0
            pre_tikno = 0
            inv_id = []
            issue = False
            refund = False
            pre_air_stat = ""
            reconcile = False
            
            while curr_row < num_rows:
                curr_row += 1
                row = worksheet.row(curr_row)
                context = {}
                print 'Row:', curr_row ,' ===>',row # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #    Fetching Ticket Information
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                 
                cell_type0 = worksheet.cell_type(curr_row, 0) # Air-Number 
                cell_value0 = worksheet.cell_value(curr_row, 0)
                if type(cell_value0) == float or type(cell_value0) == int: cell_value0 = int(cell_value0) # Typecasting
                elif type(cell_value0) == str or type(cell_value0) == unicode: cell_value0 = str(re.sub(r'\s+', '', cell_value0)) # Typecasting
                
                cell_type1 = worksheet.cell_type(curr_row, 1) # Ticket Number
                cell_value1 = worksheet.cell_value(curr_row, 1)
                if type(cell_value1) == float or type(cell_value1) == int: cell_value1 = int(cell_value1) # Typecasting
                elif type(cell_value1) == str or type(cell_value1) == unicode: cell_value1 = str(re.sub(r'\s+', '', cell_value1)) # Typecasting

                cell_type4 = worksheet.cell_type(curr_row, 4) # Basic
                cell_value4 = worksheet.cell_value(curr_row, 4)
                if (type(cell_value4) == float or type(cell_value4) == int) and (cell_value4<0) : cell_value4 = abs(int(cell_value4)) # for debit Note Changing negative values to positive
                elif type(cell_value4) == str or type(cell_value4) == unicode: 
                    if self.is_number(cr,uid,ids,cell_value4) == True: 
                        cell_value4 = abs(int(cell_value4))
                cell_type6 = worksheet.cell_type(curr_row, 6) # Tax Amount
                cell_value6 = worksheet.cell_value(curr_row, 6)
                if (type(cell_value6) == float or type(cell_value6) == int) and (cell_value6<0) : cell_value6 = abs(int(cell_value6))
                elif type(cell_value6) == str or type(cell_value6) == unicode: 
                    if self.is_number(cr,uid,ids,cell_value6) == True:  cell_value6 = abs(float(cell_value6))
                
                cell_type8 = worksheet.cell_type(curr_row, 8) # Tax Code
                cell_value8 = worksheet.cell_value(curr_row, 8)
                
                cell_type10 = worksheet.cell_type(curr_row, 10) # TAC Amount
                cell_value10 = worksheet.cell_value(curr_row, 10)
                if (type(cell_value10) == float or type(cell_value10) == int) and (cell_value10<0) : cell_value10 = abs(int(cell_value10))
                elif type(cell_value10) == str or type(cell_value10) == unicode: 
                    if self.is_number(cr,uid,ids,cell_value10) == True:  cell_value10 = abs(float(cell_valu10))
                
                cell_type12 = worksheet.cell_type(curr_row, 12) # Discount Amount
                cell_value12 = worksheet.cell_value(curr_row, 12)
                if (type(cell_value12) == float or type(cell_value12) == int) and (cell_value12<0) : cell_value12 = abs(int(cell_value12))
                elif type(cell_value12) == str or type(cell_value12) == unicode: 
                    if self.is_number(cr,uid,ids,cell_value12) == True:  cell_value12 = abs(float(cell_value12))
                
                cell_type14 = worksheet.cell_type(curr_row, 14) # Total Amount
                cell_value14 = worksheet.cell_value(curr_row, 14)
                if (type(cell_value14) == float or type(cell_value14) == int) and (cell_value14<0) : cell_value14 = abs(int(cell_value14))
                elif type(cell_value14) == str or type(cell_value14) == unicode: 
                    if self.is_number(cr,uid,ids,cell_value14) == True:  cell_value14 = abs(float(cell_value14))
                
                cell_type15 = worksheet.cell_type(curr_row, 15) # Comments
                cell_value15 = worksheet.cell_value(curr_row, 15)
                
                # Check For The Refunds Or Issues
                if cell_value0 == "***REFUNDS" or cell_value1 == "***REFUNDS": 
                    refund = True 
                    issue = False
                    context.update({'refund':True})
                if cell_value0 == "***ISSUES" or cell_value1 == "***ISSUES": 
                    issue = True 
                    context.update({'issue':True})
                
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #  Check If The Air And Ticket Number Column Data Exists
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                if cell_value0 and cell_value1:
                    tik_num = cell_value1
                    ft_ids = []
                   
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~
                    #  Check If Airline Exisit
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~
                    
                    arln_ids = arln_obj.search(cr,uid,[('number','=',cell_value0)])
                    if arln_ids:
                        #  Check If Flight Line Exists
                        
                        if issue == True : 
                            ft_ids =  ft_obj.search(cr,uid,[('ticket_no','=',cell_value1),('invoice_id.type','=','in_invoice')])
                            inv_type = "issue"
                        if refund == True :
                            ft_ids =  ft_obj.search(cr,uid,[('ticket_no','=',cell_value1),('invoice_id.type','=','in_refund')])
                            inv_type = "refund"
                        if not ft_ids :
                            b = "Date : " +str((datetime.today() + relativedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"))+", Ticket Number: "+str(cell_value1)+" Not Found \n"
                            if (type(cell_value1) == str or type(cell_value1) == unicode) :
                                if (cell_value1.isalpha() != True):
                                    _logger.info('Date : %s , Ticket Number %s ->  Not Found \n' ,str((datetime.today() + relativedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")),cell_value1)
                                    fplog_misng.write(b)
                            elif (type(cell_value1) == int or type(cell_value1) == float) :
                                    _logger.info('Date : %s , Ticket Number %s ->  Not Found \n' ,str((datetime.today()+ relativedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")),cell_value1)
                                    fplog_misng.write(b)
                        if ft_ids:
                           
                           # Fetching Flight ID, Invoice ID 
                           ft_id  = ft_obj.browse(cr,uid,ft_ids[0])
#                            ft_id = ftln_id and ftln_id.flight_id or False
                           
                           inv_id =  ft_id and  ft_id.invoice_id and ft_id.invoice_id.id or False
                           if inv_id:
                               invid = inv_obj.browse(cr,uid,inv_id)
                               # checking for the start dt and dt lies between psr date
                               if invid.psr_date:
                                   if (not x.start_dt and not x.end_dt) or (x.start_dt <= invid.psr_date and x.end_dt >= invid.psr_date ):  
                                       # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                       #  Check For The Previous Air And Tiket No Is Same As Current
                                       # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                       if pre_airno == cell_value0 and pre_tikno == cell_value1 and pre_invtype == inv_type:
                                           if cell_value6 and cell_value8:
                                               context.update({'previous':True}) 
#                                                self._update_taxline(cr, uid, [],cell_value6, cell_value8, ftln_ids,ft_id,context)
                                           continue
                                       pre_airno = cell_value0
                                       pre_invtype = issue and "issue" or "refund" 
                                       pre_tikno = cell_value1
                                        
                                       # Checking For The Same Values : Skip ? Update
                                       log_basic = log_cmmson = log_discount = log_total = log_equal = rec_basic = rec_cmmson = rec_discount = rec_total = rec_invno =''
                                       if ft_id.a_basic != cell_value4 and cell_value4 !='':
                                           _logger.info('Invoice_No. : %s , Ticket Number %s , Actual Basic : %s , BSP Amount : %s \n' ,
                                                                ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '',
                                                                cell_value1,ft_id.a_basic,cell_value4)
                                           log_basic = "Invoice_No. : " +str(ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '') +","+"\t" +" Ticket Number :" +str(cell_value1)+","+ "\t"+"Actual Basic : " +str(ft_id.a_basic)+","+ "\t"+"BSP Amount : "+str(cell_value4) +"\n" 
                                           fplog_dscrpncs.write(log_basic)
                                           # To Write in Recincile remarks Field 
                                           rec_basic = "Actual Basic : " +str(ft_id.a_basic)+"0"+ "\n"+"BSP Amount : "+str(cell_value4)+"0" +"\n" 

                                           
            #                                ftln_obj.write(cr,uid,ftln_ids,{'a_basic' : cell_value4 })
                                       if ft_id.a_tac != cell_value10:
                                           _logger.info('Invoice_No. : %s , Ticket Number %s , Actual Commission : %s , BSP Commission : %s \n' ,
                                                                 ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '',
                                                                cell_value1,ft_id.a_tac,cell_value10)
                                           log_cmmson = "Invoice_No. : " +str(ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '')+","+"\t"+" Ticket Number :" +str(cell_value1)+","+"\t"+ "Actual Commission : " +str(ft_id.a_tac)+","+"\t"+ "BSP Commission : "+str(cell_value10) +"\n" 
                                           fplog_dscrpncs.write(log_cmmson)
                                           rec_cmmson = "Actual Commission : " +str(ft_id.a_tac)+"0"+"\n"+ "BSP Commission : "+str(cell_value10)+"0" +"\n" 
            
            #                                ftln_obj.write(cr,uid,ftln_ids,{'a_tac' : cell_value10 })
                                           
                                       if ft_id.a_discount != cell_value12:
                                           _logger.info('Invoice_No. : %s , Ticket Number %s , Actual Discount : %s , BSP Discount : %s \n' ,
                                                                 ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '',
                                                                cell_value1,ft_id.a_discount,cell_value12)
                                           log_discount = "Invoice_No. : " +str(ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '')+","+"\t"+" Ticket Number :" +str(cell_value1)+","+"\t"+ "Actual Discount : " +str(ft_id.a_discount)+"\t"+","+ "BSP Discount : "+str(cell_value12) +"\n" 
                                           fplog_dscrpncs.write(log_discount)
                                           rec_discount = "Actual Discount : " +str(ft_id.a_discount)+"0"+"\n"+ "BSP Discount : "+str(cell_value12)+"0" +"\n" 
                                           
            #                                ftln_obj.write(cr,uid,ftln_ids,{'a_discount' : cell_value12 })
                                           
                                       if ft_id.a_total != cell_value14:
                                           _logger.info('Invoice_No. : %s , Ticket Number %s , Actual Total Payable: %s , BSP Balance Payable : %s \n' ,
                                                                ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '',
                                                                cell_value1,ft_id.a_total,cell_value14)
                                           log_total = "Invoice_No. : " +str(ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '')+","+"\t"+" Ticket Number :" +str(cell_value1)+","+"\t"+ "Actual Total Payable : " +str(ft_id.a_total)+"\t"+","+ "BSP Total Payable : " +str(cell_value14) +"\n" 
                                           fplog_dscrpncs.write(log_total)
                                           rec_total = "Actual Total Payable : " +str(ft_id.a_total)+"0"+"\n"+ "BSP Total Payable : " +str(cell_value14)+"0" +"\n" 
                                           ftln_obj.write(cr,uid,ft_ids,{'reconcile_amount' : cell_value14 })
            #                                ftln_obj.write(cr,uid,ftln_ids,{'a_total' : cell_value14 })
                                       # Only For Log info    
                                       if ft_id.a_basic == cell_value4 and ft_id.a_tac == cell_value10 and ft_id.a_discount == cell_value12 and ft_id.a_total == cell_value14:
                                           _logger.info('Invoice_No. : %s , Ticket Number %s --> Reconciled \n' , 
                                                                 ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '',
                                                                cell_value1)
                                           log_equal = "Invoice_No. : " +str(ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '')+","+"\t"+" Ticket Number :" +str(cell_value1)+" --> Reconciled"+"\n" 
                                           fplog_comp.write(log_equal)
                                       # only for log info 
                                       if ft_id.a_basic != cell_value4 or ft_id.a_tac != cell_value10 or ft_id.a_discount != cell_value12 or ft_id.a_total != cell_value14:
                                           rec_invno = "Invoice_No. : " +str(ft_id and ft_id.invoice_id and ft_id.invoice_id.number or '') +"\n"

                                       # To Do : delete airtax ids 
            #                            if ftln_id.airtax_ids: del[ftln_id.airtax_ids]
                                       ft_obj.write(cr,uid,ft_ids,{'is_reconciled' : True ,'reconcile_date' : datetime.today().strftime('%Y-%m-%d'),
                                                                       'reconcile_amount' : cell_value14,'reconcile_remarks' : (rec_invno + rec_basic + rec_cmmson + rec_discount +rec_total ),
                                                                   'a_other' : 0,'a_reissue' : 0,'a_vendor' : 0,'a_raf' : 0,'a_discount' : 0,
                                                                   'a_tds' : 0,'a_tds1' : 0,'a_markup' : 0,'a_servicechrg' : 0,
                                                                   })
                                       reconcile = True 
                                       
                                       context.update({'flight_line':True})
#                                        self._update_taxline(cr,uid,[],cell_value6,cell_value8,ftln_ids,ft_id,context)
            
                                       if inv_id : inv_obj.button_reset_taxes(cr, uid, [inv_id], context) 
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #  If Air And Ticket Not There and IF Taxlines Exists 
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                elif cell_value6 and cell_value8 and ft_ids and inv_id:
                    context.update({'tax_line':True})
#                     self._update_taxline(cr, uid, [],cell_value6, cell_value8, ftln_ids,ft_id,context)
                    if inv_id : inv_obj.button_reset_taxes(cr, uid, [inv_id], context) 
#           To Do :Call Validate Button only if All flight Lines Reconcile is True
#             inv_ids = inv_obj.search(cr,uid,[('state','=','open'),('type','in',('in_invoice','in_refund'))])
#             for inv in inv_obj.browse(cr,uid,inv_ids):
#                 for ft in inv.flight_ids:
#                     count = 0
#                     for ftln in ft.flight_lines:
#                         if ftln.is_reconciled == True:
#                             count = count + 1
#                     if len(ft.flight_lines) == count :
#                         workflow.trg_validate(uid, 'account.invoice', inv_id, 'open', cr)
            os.remove(dataFile)
            fplog_comp.close()
            fplog_misng.close()
            fplog_dscrpncs.close()
            fp.close()
            return True         

tr_bsp_reconcilation()










# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: