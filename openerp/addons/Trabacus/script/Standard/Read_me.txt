# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#						Changes In Standard Files
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

1. account_move_line.py :

Changes in _query_get Function: line no -  111
		
	        if context.get('partner_id',False):
	            partner_id  = context['partner_id'][0]
	            query += ' AND '+obj+'.partner_id IN (%s)' % (str(partner_id))   # Trabacus

2. account_general_ledger.py :

Changes In set_context Function : line no 41
		
		context=data['form']['used_context'].update({'partner_id': data['form'].get('partner_id',False)})		

Changes In __init__ Function : line no 91
		
		'get_heading' : self._get_heading, 

Add New Function : line no 312
	
		    def _get_heading(self, data):
         		a = "General Ledger"
        			if data['form']['client_heading'] == True :
	        	        a = "Client Statement"
           			return a
		        return a  

3. account_general_ledger.rml : 
	 
	table 7 - delete last 3 line style
	table 9 - delete last 3 line style
	table 10 - delete last 3 line style
	table 6 - delete last 3 line style
	

4. account_general_ledger_landscape.rml : 
	 
	table 7 - delete last 4 line style
	table 9 - delete last 4 line style
	table 10 - delete last 4 line style
	table 12 - delete last 4 line style
	

5 Removet the small block table under heading only for client statement based on the filter date

6. remove rowheight to set it dynamically 

7. Changes In Grouping Move line in Geneeral Journal