# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
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

import lxml
import urlparse

from openerp.osv import osv, fields
from openerp.tools.translate import _


class EmailTemplate(osv.Model):
    _inherit = 'email.template'

    def _get_website_link(self, cr, uid, ids, name, args, context=None):
        return dict((id, _('<a href="website_mail/email_designer/%s">Edit in Website</a>') % id) for id in ids)

    _columns = {
        'website_link': fields.function(
            _get_website_link, type='text',
            string='Website Link',
            help='Link to the website',
        ),
    }

    def _postprocess_html_replace_links(self, cr, uid, body_html, context=None):
        """ Post-processing of body_html. Indeed the content generated by the
        website builder contains references to local addresses, for example
        for images. This method changes those addresses to absolute addresses. """
        html = body_html
        if not body_html:
            return html

        # form a tree
        root = lxml.html.fromstring(html)
        if not len(root) and root.text is None and root.tail is None:
            html = '<div>%s</div>' % html
            root = lxml.html.fromstring(html)

        base_url = self.pool['ir.config_parameter'].get_param(cr, uid, 'web.base.url')
        (base_scheme, base_netloc, bpath, bparams, bquery, bfragment) = urlparse.urlparse(base_url)

        def _process_link(url):
            new_url = url
            (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)
            if not scheme and not netloc:
                new_url = urlparse.urlunparse((base_scheme, base_netloc, path, params, query, fragment))
            return new_url

        # check all nodes, replace :
        # - img src -> check URL
        # - a href -> check URL
        for node in root.iter():
            if node.tag == 'a':
                node.set('href', _process_link(node.get('href')))
            elif node.tag == 'img' and not node.get('src', 'data').startswith('data'):
                node.set('src', _process_link(node.get('src')))

        html = lxml.html.tostring(root, pretty_print=False, method='html')
        # this is ugly, but lxml/etree tostring want to put everything in a 'div' that breaks the editor -> remove that
        if html.startswith('<div>') and html.endswith('</div>'):
            html = html[5:-6]
        return html

    def create(self, cr, uid, values, context=None):
        if 'body_html' in values:
            values['body_html'] = self._postprocess_html_replace_links(cr, uid, values['body_html'], context=context)
        return super(EmailTemplate, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        if 'body_html' in values:
            values['body_html'] = self._postprocess_html_replace_links(cr, uid, values['body_html'], context=context)
        return super(EmailTemplate, self).write(cr, uid, ids, values, context=context)
