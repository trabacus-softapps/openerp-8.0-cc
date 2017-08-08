import copy

from lxml import etree, html

from openerp.osv import osv, fields
from openerp.http import request
from openerp import SUPERUSER_ID

class view(osv.osv):
    _inherit = "ir.ui.view"
    
    def _get_title(self, cr, uid, ids, name, arg, context=None):     
        res = {}
        httprequest = request.httprequest
        h = httprequest.environ['HTTP_HOST'].split(':')[0]          
        for case in self.browse(cr, SUPERUSER_ID, ids, context):
            res[case.id] = ''
            if case.type =='qweb':
                cr.execute("select id from res_users where wlabel_url='%s'"%(h))
                user_ids = cr.fetchone()  
                if user_ids:
                   user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, user_ids[0])
                   user_name = user.partner_id.name 
                   if user.role != 'client':
                      user_name = user.partner_id.parent_id.name             
                   res[case.id] = user_name + '-' + case.name                
        return res
        
    _columns = {'website_meta_title': fields.function(_get_title,string="Website meta title",type='char', size=70, translate=True),        
                }
view()
