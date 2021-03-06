
from openerp.osv import fields, osv

class website_config_settings(osv.osv_memory):
    _name = 'website.config.settings'
    _inherit = 'base.config.settings'

    _columns = {
        'website_id': fields.many2one('website', string="website", required=True),

        'language_ids': fields.related('website_id', 'language_ids', type='many2many', relation='res.lang', string='Languages'),
        'default_lang_id': fields.related('website_id', 'default_lang_id', type='many2one', relation='res.lang', string='Default language'),
        'default_lang_code': fields.related('website_id', 'default_lang_code', type="char", string="Default language code"),
        'google_analytics_key': fields.related('website_id', 'google_analytics_key', type="char", string='Google Analytics Key'),
        
        'social_twitter': fields.related('website_id', 'social_twitter', type="char", string='Twitter Account'),
        'social_facebook': fields.related('website_id', 'social_facebook', type="char", string='Facebook Account'),
        'social_github': fields.related('website_id', 'social_github', type="char", string='GitHub Account'),
        'social_linkedin': fields.related('website_id', 'social_linkedin', type="char", string='LinkedIn Account'),
        'social_youtube': fields.related('website_id', 'social_youtube', type="char", string='Youtube Account'),
        'social_googleplus': fields.related('website_id', 'social_googleplus', type="char", string='Google+ Account'),
    }

    def on_change_website_id(self, cr, uid, ids, website_id, context=None):
        website_data = self.pool.get('website').read(cr, uid, [website_id], [], context=context)[0]
        values = {}
        for fname, v in website_data.items():
            if fname in self._columns:
                values[fname] = v[0] if v and self._columns[fname]._type == 'many2one' else v
        return {'value' : values}

    _defaults = {
        'website_id': lambda self,cr,uid,c: self.pool.get('website').search(cr, uid, [], context=c)[0],
    }
