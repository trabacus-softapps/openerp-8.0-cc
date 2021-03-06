# -*- coding: utf-8 -*-
import copy

from lxml import etree, html

from openerp.osv import osv, fields

class view(osv.osv):
    _inherit = "ir.ui.view"
    _columns = {
        'inherit_option_id': fields.many2one('ir.ui.view','Optional Inheritancy'),
        'inherited_option_ids': fields.one2many('ir.ui.view','inherit_option_id','Optional Inheritancies'),
        'page': fields.boolean("Whether this view is a web page template (complete)"),
        'website_meta_title': fields.char("Website meta title", size=70, translate=True),
        'website_meta_description': fields.text("Website meta description", size=160, translate=True),
        'website_meta_keywords': fields.char("Website meta keywords", translate=True),
    }
    _defaults = {
        'page': False,
    }

    # Returns all views (called and inherited) related to a view
    # Used by translation mechanism, SEO and optional templates
    def _views_get(self, cr, uid, view, options=True, context=None, root=True, stack_result=None):
        if not context:
            context = {}
        if not stack_result:
            stack_result = []

        def view_obj(view):
            if isinstance(view, basestring):
                mod_obj = self.pool.get("ir.model.data")
                m, n = view.split('.')
                view = mod_obj.get_object(cr, uid, m, n, context=context)
            elif isinstance(view, (int, long)):
                view = self.pool.get("ir.ui.view").browse(cr, uid, view, context=context)
            return view

        try:
            view = view_obj(view)
        except ValueError:
            # Shall we log that ?
            return []

        while root and view.inherit_id:
            view = view.inherit_id

        result = [view]

        node = etree.fromstring(view.arch)
        for child in node.xpath("//t[@t-call]"):
            try:
                call_view = view_obj(child.get('t-call'))
            except ValueError:
                continue
            if call_view not in result:
                result += self._views_get(cr, uid, call_view, options=options, context=context, stack_result=result)

        todo = view.inherit_children_ids
        if options:
            todo += filter(lambda x: not x.inherit_id, view.inherited_option_ids)
        # Keep options in a determinitic order whatever their enabled disabled status
        todo.sort(lambda x,y:cmp(x.id,y.id))
        for child_view in todo:
            for r in self._views_get(cr, uid, child_view, options=bool(child_view.inherit_id), context=context, root=False, stack_result=result):
                if r not in result:
                    result.append(r)
        return result

    def extract_embedded_fields(self, cr, uid, arch, context=None):
        return arch.xpath('//*[@data-oe-model != "ir.ui.view"]')

    def save_embedded_field(self, cr, uid, el, context=None):
        Model = self.pool[el.get('data-oe-model')]
        field = el.get('data-oe-field')

        column = Model._all_columns[field].column
        converter = self.pool['website.qweb'].get_converter_for(
            el.get('data-oe-type'))
        value = converter.from_html(cr, uid, Model, column, el)

        if value is not None:
            # TODO: batch writes?
            Model.write(cr, uid, [int(el.get('data-oe-id'))], {
                field: value
            }, context=context)

    def to_field_ref(self, cr, uid, el, context=None):
        # filter out meta-information inserted in the document
        attributes = dict((k, v) for k, v in el.items()
                          if not k.startswith('data-oe-'))
        attributes['t-field'] = el.get('data-oe-expression')

        out = html.html_parser.makeelement(el.tag, attrib=attributes)
        out.tail = el.tail
        return out

    def replace_arch_section(self, cr, uid, view_id, section_xpath, replacement, context=None):
        # the root of the arch section shouldn't actually be replaced as it's
        # not really editable itself, only the content truly is editable.

        [view] = self.browse(cr, uid, [view_id], context=context)
        arch = etree.fromstring(view.arch.encode('utf-8'))
        # => get the replacement root
        if not section_xpath:
            root = arch
        else:
            # ensure there's only one match
            [root] = arch.xpath(section_xpath)

        root.text = replacement.text
        root.tail = replacement.tail
        # replace all children
        del root[:]
        for child in replacement:
            root.append(copy.deepcopy(child))

        return arch

    def save(self, cr, uid, res_id, value, xpath=None, context=None):
        """ Update a view section. The view section may embed fields to write

        :param str model:
        :param int res_id:
        :param str xpath: valid xpath to the tag to replace
        """
        res_id = int(res_id)

        arch_section = html.fromstring(
            value, parser=html.HTMLParser(encoding='utf-8'))

        if xpath is None:
            # value is an embedded field on its own, not a view section
            self.save_embedded_field(cr, uid, arch_section, context=context)
            return

        for el in self.extract_embedded_fields(cr, uid, arch_section, context=context):
            self.save_embedded_field(cr, uid, el, context=context)

            # transform embedded field back to t-field
            el.getparent().replace(el, self.to_field_ref(cr, uid, el, context=context))

        arch = self.replace_arch_section(cr, uid, res_id, xpath, arch_section, context=context)
        self.write(cr, uid, res_id, {
            'arch': etree.tostring(arch, encoding='utf-8').decode('utf-8')
        }, context=context)
