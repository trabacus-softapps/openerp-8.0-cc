from openerp.osv import fields, osv

class website_config_settings(osv.osv_memory):
    _inherit = 'website.config.settings'
    _columns = {'google_api':fields.char('Google Maps API Key',size=1000)
                }    
    # GETS: latest data
    def get_default_values(self, cr, uid, ids, context=None):
        param_obj = self.pool.get("ir.config_parameter")
        maps_api_key = param_obj.get_param(cr, uid, "mapsapi_key")
        return {'google_api'  : maps_api_key,
                }

    # POST: saves new data
    def set_values(self, cr, uid, ids, context=None):
        param_obj = self.pool.get("ir.config_parameter")
        for record in self.browse(cr, uid, ids, context=context):
            param_obj.set_param(cr, uid, "mapsapi_key", record.google_api or '')
                
website_config_settings()
