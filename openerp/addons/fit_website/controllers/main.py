# -*- coding: utf-8 -*-
import openerp
import simplejson
import logging
import time
import json
import yaml
import re
import calendar 
import hashlib
import cStringIO 
import contextlib  
import math
import sys
import pytz
import urllib 
import urllib2
import werkzeug.urls
from openerp.osv import fields, osv
from openerp import http
from openerp.tools.translate import _
from openerp.addons.website.models import website
from openerp.tools.safe_eval import safe_eval  
from urllib import quote_plus
from datetime import datetime
from openerp import SUPERUSER_ID
from dateutil import parser
from dateutil.relativedelta import relativedelta 
from dateutil import rrule
from sys import maxint
from PIL import Image
from random import shuffle
from openerp.osv.orm import except_orm 
from openerp import pooler
from openerp.http import request, serialize_exception as _serialize_exception, LazyResponse
from openerp.addons.web.controllers.main import content_disposition
from openerp import netsvc
import xmlrpclib
from openerp.tools import config
from operator import itemgetter
import uuid
import requests
import os 
_logger = logging.getLogger(__name__)

host = str(config["xmlrpc_interface"])  or str("localhost"),
port = str(config["xmlrpc_port"])
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (host[0],port))
               
# Inherited
class Website(openerp.addons.web.controllers.main.Home):
    
    #Overriden
    @http.route('/page/<page:page>', type='http', auth="public", website=True, multilang=True)
    def page(self, page, **opt):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        h = request.httprequest.environ['HTTP_HOST'].split(':')[0]

        if opt.get('utm_source') and opt.get('utm_campaign'):
           request.httprequest.session['referral_link'] = 'http://'+opt.get('utm_source')+'/'+opt.get('utm_campaign')

        user_obj = request.registry.get('res.users')
        user = user_obj.browse(cr,uid,uid)
        if user.name == 'Public user':
            user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
            user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
        _logger.error('WORLD PAY POST: %s',page)
#         request.session.authenticate(request.db, user.login, user.password)      
        partner_obj = request.registry.get('res.partner')
        recent_venues_ids = partner_obj.search(cr, SUPERUSER_ID, [('type','=','default'),('partner_type','=','venue')])
        #this will give 5 random venues
        recent_venues_ids = recent_venues_ids[shuffle(recent_venues_ids):6]
        recent_venues = partner_obj.browse(cr,SUPERUSER_ID,recent_venues_ids) 
        cr.execute(""" select distinct (p.city_id) as id
                           , cc.name
                           , cc.sequence
                           from res_partner p
                           inner join cc_city cc on cc.id = p.city_id
                           where p.type = 'default' and p.partner_type = 'venue' and p.is_company is False and p.active is True and p.city_id is not null order by cc.sequence, cc.name"""
                    )
        city_obj = request.registry.get('cc.city')
        city_ids = [x[0] for x in cr.fetchall()]
        city_browse = city_ids and city_obj.browse(cr, uid, city_ids) or []
        resv_date = (parser.parse(time.strftime("%Y-%m-%d"))+relativedelta(days=1)).strftime("%d/%m/%Y")
        cr.execute(""" select
                              distinct (p.id)
                            , p.name
                        from res_partner p
                        where p.type = 'default'
                        and p.partner_type = 'venue'
                        and p.is_company is False
                        and p.active is True and p.show_in_homepage is True order by p.name limit 5""")
        venue_ids = [x[0] for x in cr.fetchall()]
        venue_browse = partner_obj.browse(cr, uid, venue_ids)
        values = {
                  'path': page,
                  'recent_venues' : recent_venues,
                  'user' : user,
                  'city_browse' : city_browse,
                  'resv_date'   : resv_date,
                  'venue_browse' : venue_browse
                 }

        # allow shortcut for /page/<website_xml_id>
        if '.' not in page:
            page = 'website.%s' % page

        # TODO:CHECK
        # if user.is_wlabeling and 'redirect' not in opt:
        # return request.redirect('/')

        try:
            request.website.get_template(page)
        except ValueError, e:
            # page not found
            if request.context['editable']:
                page = 'website.page_404'
            else:
                return request.registry['ir.http']._handle_exception(e, 404)
        if (user.partner_id.parent_id and user.partner_id.parent_id.partner_type == 'venue') or user.partner_id.partner_type == 'venue':
                return request.redirect("/capital_centric/restaurant/bookings")
        return request.website.render(page, values) 

#Overriden
    @http.route([
    '/website/image',
    '/website/image/<model>/<id>/<field>'
    ], auth="public", website=True)
    def website_image(self, model, id, field, max_width=maxint, max_height=maxint):
        Model = request.registry[model]

        response = werkzeug.wrappers.Response()

        id = int(id)
        srch_domain = [('id', '=', id)]
        
        if  model=='res.partner':
            srch_domain = ['|',('active','=',True),('active','=',False),('id', '=', id)]
             
        ids = Model.search(request.cr, request.uid,
                           srch_domain, context=request.context) \
            or Model.search(request.cr, openerp.SUPERUSER_ID,
                            srch_domain, context=request.context)

        if not ids:
            return self.placeholder(response)

        concurrency = '__last_update'
        [record] = Model.read(request.cr, openerp.SUPERUSER_ID, [id],
                              [concurrency, field], context=request.context)

        if concurrency in record:
            server_format = openerp.tools.misc.DEFAULT_SERVER_DATETIME_FORMAT
            try:
                response.last_modified = datetime.strptime(
                    record[concurrency], server_format + '.%f')
            except ValueError:
                # just in case we have a timestamp without microseconds
                response.last_modified = datetime.strptime(
                    record[concurrency], server_format)

        # Field does not exist on model or field set to False
        if not record.get(field):
            # FIXME: maybe a field which does not exist should be a 404?
            return self.placeholder(response)

        response.set_etag(hashlib.sha1(record[field]).hexdigest())
        response.make_conditional(request.httprequest)

        # conditional request match
        if response.status_code == 304:
            return response

        data = record[field].decode('base64')
        fit = int(max_width), int(max_height)

        buf = cStringIO.StringIO(data)

        image = Image.open(buf)
        image.load()
        response.mimetype = Image.MIME[image.format]

        w, h = image.size
        max_w, max_h = fit

        if w < max_w and h < max_h:
            response.data = data
        else:
            image.thumbnail(fit, Image.ANTIALIAS)
            image.save(response.stream, image.format)
            # invalidate content-length computed by make_conditional as writing
            # to response.stream does not do it (as of werkzeug 0.9.3)
            del response.headers['Content-Length']

        return response

# fetching day wise price from restaurant table 
def get_price(cr,day,pr,operator_id):    
    cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context               
    price = ffp_mu = ffp_co = to_mu = srvc_chrg = sc = 0
    partner_obj = request.registry.get('res.partner')
    operator  = partner_obj.browse(cr, uid, operator_id)
    if not (pr.menu_id and pr.menu_id.sc_included):
       srvc_chrg = ((pr.menu_id.service_charge or 0.00)/100)              
    if day == 'monday':
      price  = pr.mon_price
      ffp_mu = pr.mon_ffp_mu  
      ffp_co = pr.mon_to_mu
      tot    = pr.mon_total                  
    elif day == 'tuesday':
      price  = pr.tue_price
      ffp_mu = pr.tue_ffp_mu  
      ffp_co = pr.tue_to_mu
      tot    = pr.tue_total
    elif day == 'wednesday':
      price  = pr.wed_price
      ffp_mu = pr.wed_ffp_mu  
      ffp_co = pr.wed_to_mu
      tot    = pr.wed_total
    elif day == 'thursday':
      price  = pr.thu_price
      ffp_mu = pr.thu_ffp_mu  
      ffp_co = pr.thu_to_mu
      tot    = pr.thu_total
    elif day == 'friday':
      price  = pr.fri_price
      ffp_mu = pr.fri_ffp_mu  
      ffp_co = pr.fri_to_mu
      tot    = pr.fri_total
    elif day == 'saturday':
      price  = pr.sat_price
      ffp_mu = pr.sat_ffp_mu  
      ffp_co = pr.sat_to_mu
      tot    = pr.sat_total
    elif day == 'sunday':
      price  = pr.sun_price
      ffp_mu = pr.sun_ffp_mu  
      ffp_co = pr.sun_to_mu
      tot    = pr.sun_total

    cr.execute(""" select 
                        (select (om.markup_perc/100) as menu_mrkup
                         from rel_om_menu rom
                         inner join cc_operator_markup om on om.id = rom.omarkup_id
                         where om.partner_id = """+str(operator_id)+""" and om.restaurant_id = """+str(pr.menu_id.partner_id.id)+""" and rom.menu_id = """+str(pr.menu_id.id)+"""
                        ) as menu_mrkup
                       ,(select (markup_perc/100) from cc_operator_markup where partner_id = """+str(operator_id)+""" and restaurant_id = """+str(pr.menu_id.partner_id.id)+""" and mrkup_lvl = 'rest_lvl') as rest_mrkup
                       ,(select (markup_perc/100) from res_partner where id = """+str(operator_id)+""") as glb_mrkup""")
    result = cr.dictfetchone()
    if result and operator and operator.comision_type == 'markup':
       to_mu = round(tot * (result['menu_mrkup'] or result['rest_mrkup'] or result['glb_mrkup'] or 0),1)
          
    sc = srvc_chrg * price
    if not (pr.menu_id and pr.menu_id.sc_included) and pr.menu_id.sc_disc :  
       sc = round(srvc_chrg * (price + ffp_mu),1) 
       
    return price,ffp_mu,ffp_co,to_mu,sc

class login(http.Controller):
    
#-------------------------------
#           VENUES
#-------------------------------

      @http.route(['/sign-in'], type='http' ,auth="public" ,website=True ,multilang=True)
      def login_signup(self, **post):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False})
        country_obj = request.registry.get('res.country')
        cc_city_obj = request.registry.get('cc.city')
        user_obj = request.registry.get('res.users')
        user = user_obj.browse(cr,uid,uid)

        if user.name == 'Public user':
            h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
            user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
            user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)

        country_ids = country_obj.search(cr, uid, [])
        countries = country_obj.browse(cr, suid, country_ids)
        city_ids = cc_city_obj.search(cr, uid, [])
        cities   = cc_city_obj.browse(cr, suid, city_ids)
        type = 'Customer'
        # if path == 'restaurant':
        #     type = 'Restaurant'
        # if path == 'operator' and not user.is_wlabeling:
        #     type = 'Tour Operator'
        values = {
                    'country_ids' : countries,
                    'city_ids'    : cities,
                    'type' : type,
                    'req':'signup',
                    'user':user,
                    }
        if post.get('error'):values['error'] = post.get('error')
        if post.get('forget_password'):values['forget_password'] = post.get('forget_password')
        if post.get('venue_mode'):values['venue_mode'] = post.get('venue_mode')
        if post.get('client_mode'):values['client_mode'] = post.get('client_mode')
        if post.get('mode'):values['mode'] = post.get('mode')

        return request.website.render("fit_website.capitalcentric_login", values)

      @http.route(['/capital_centric/restaurant_login'], type='http', auth="public", multilang=True, website=True)
      def restaurant_login(self,*arg, **post ):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False})
        user_obj = request.registry.get('res.users')
        user = user_obj.browse(cr,uid,uid)
        return request.website.render("fit_website.res_layout",{'user':user})
    
# SIGN IN 
      @http.route(['/capital_centric/siginin/<path>'], login=None, type='http' ,auth="public" ,website=True ,multilang=True)
      def signin(self, path, *arg, **post):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False})
        values = request.params.copy()
        user_obj = request.registry.get('res.users')
        partner_obj = request.registry.get('res.partner')
        user_agent_env = {'base_location': 'http://localhost:8069', 'HTTP_HOST': 'localhost:8069', 'REMOTE_ADDR': '127.0.0.1'} # TODO: send http information
        loginuid = user_obj.authenticate(cr, post.get('login'), post.get('password'), user_agent_env)
        uid = request.session.authenticate(request.db, post.get('login'), post.get('password'))     
        # Todo: check later
        if loginuid:#to check if its group website and not allow fit user to login until he his a group user
           user = user_obj.browse(cr, uid, loginuid)
#            if user.prev_booking_id:
# #               cr.execute("update res_users set prev_booking_id = null where id = %s",(user.id,))
#               sock.execute(cr.dbname,1,'fitadmin','res.users','write', [user.id],{'prev_booking_id':False})
#            if user.is_group and not user.partner_id.cc_group:
#               passen_type = 'group'
#               loginuid = False
        
        if post.get('login_type') == 'client' or path == 'client_mode':
            partner_obj = request.registry.get('res.partner')
            recent_venues_ids = partner_obj.search(cr, SUPERUSER_ID, [('type','=','default'),('partner_type','=','venue')])
            #this will select 5 random venues
            recent_venues_ids = recent_venues_ids[shuffle(recent_venues_ids):6]
            recent_venues = partner_obj.browse(cr,SUPERUSER_ID,recent_venues_ids)              
            values['recent_venues'] = recent_venues

        if loginuid and post.get('fromwch') != 'forget_password':
            user = user_obj.browse(cr,uid,loginuid)
            child_user = user.partner_id.child_ids
            usr_role = {'venue_user':'venue','venue':'venue','client_user':'client','client':'client','client_mng':'client','venue_mng':'venue','client_cust':'client'}
            symbol = user.company_id.currency_id.symbol or ''
                         
            if post.get('login_type') == usr_role[user.role]:
               tracking_obj = request.registry.get('login.time.tracking')
               tt_ids =  tracking_obj.search(cr, uid, [('name','=',user.id),('logout','=',False)],order='id desc')
               if tt_ids:
                  cr.execute("update login_time_tracking set logout=%s where id in %s",(time.strftime("%Y-%m-%d %H:%M:%S"),tuple(tt_ids),))
               sock.execute(cr.dbname,uid,user.password,'login.time.tracking','create',{'name':user.id, 'login':time.strftime("%Y-%m-%d %H:%M:%S")})
#                tracking_obj.create(cr, uid, {'name':user.id, 'login':time.strftime("%Y-%m-%d %H:%M:%S")})
               
               if post.get('login_type') == 'venue':
                    if(user.partner_id.accept_tc == True):
                        return request.redirect("/capital_centric/restaurant/bookings")
                    else:
                        values = {
                                  'user' : user,
                                  'login_user' : user,
                                  'path' : 'restaurant',                                  
                                  'uid' : user,
                                  }
                        return request.redirect("/capital_centric/restaurant/bookings")
                   
               if post.get('login_type') == 'client':
                  session_id = request.httprequest.session.get('website_session_id')
                  cr.execute("delete from cc_menus_table where operator_id = %s or website_session_id = %s",(user.partner_id.id,session_id))
                        
                  #Genrate session_id on user login.
                  if not request.httprequest.session.get('website_session_id'):
                     request.httprequest.session['website_session_id'] = str(uuid.uuid4())
                
                  #Get lead_ids of public user for this session   
                  if request.httprequest.session.get('website_lead_id'): 
                     lead_obj = request.registry.get('crm.lead')
                     lead_ids = request.httprequest.session.get('website_lead_id')
                     sock.execute(cr.dbname, uid, user.password,'crm.lead','write', lead_ids, {'sales_person':user.id})
                     request.httprequest.session['website_lead_id'] = False
                     
                  if (user.partner_id.accept_tc == True):                           
                     if post.get('wch_page') == 'my_cart':
                        return request.redirect('/capital_centric/operator/my_cart')
                     else:
                        return request.redirect('/')

                  else:
                     values.update({
                                    'user' : user,
                                    'login_user' : user,
                                    'path' : 'operator',                      
                                    'uid' : user,
                                   })
                     return request.redirect('/')
                     # return request.website.render("fit_website.tc", values)
                   
            if post.get('login_type') != usr_role[user.role]:
                values['user'] = user
                if post.get('login_type') == 'venue':
                        values['error'] = "Wrong Login/Password"
                        return request.redirect('/sign-in?error=True')
                        # return request.website.render("fit_website.res_layout", values)
                else:    
                        values['error'] = "Incorrect Email or Password"
                        return request.redirect('/sign-in?error=True')
                        # return request.website.render("website.homepage", values)

        else:
            h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
            user_obj = request.registry.get('res.users')
            user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
            user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
            values['user'] = user  
            if post.get('login_type') == 'venue':
                if post.get('fromwch') == 'forget_password' :
                    user_ids = user_obj.search(cr, SUPERUSER_ID, [('login','=',post.get('login'))])
                    if user_ids:
                        values['error'] = "An email has been sent with credentials to reset your password"
                        user_obj.reset_password(cr, SUPERUSER_ID, post.get('login'), context=None)
                        return request.redirect('/sign-in?forget_password=True')
                    else:
                        values['error'] = "Wrong Email Address"
                elif post.get('fromwch') == 'submit':
                    user_ids = user_obj.search(cr, SUPERUSER_ID, [('login','=',post.get('login'))])
                    if user_ids:
                       user_obj.write(cr,SUPERUSER_ID,user_ids,{'password':post.get('password')})
                       user = user_obj.browse(cr,SUPERUSER_ID,user_ids[0])
                       return request.redirect('/sign-in')
                       # return request.website.render("fit_website.res_layout", {'user':user})
                    else:
                       values['error'] = "Wrong Email Address"
                       values['mode'] = 'reset'
                else:
                    values['error'] = "Incorrect Email or Password"
                return request.redirect('/sign-in?error=True')
                # return request.website.render("fit_website.res_layout", values)
            
            if path == 'venue_mode':
                values['mode'] = 'reset'
                return request.redirect('/sign-in?venue_mode=True&mode=reset')
                # return request.website.render("fit_website.res_layout", values)
            
            if path == 'client_mode':
                values['mode'] = 'reset'
                return request.redirect('/sign-in?client_mode=True&mode=reset')
                # return request.website.render("website.homepage", values)
                
            if post.get('login_type') == 'client':
                if post.get('fromwch') == 'forget_password' :
                    user_ids = user_obj.search(cr, SUPERUSER_ID, [('login','=',post.get('login'))])
                    if user_ids:
                        values['error'] = "An email has been sent with credentials to reset your password"
                        user_obj.reset_password(cr, SUPERUSER_ID, post.get('login'), {'client_reset_pwd':True})
                        return request.redirect('/sign-in?forget_password=True')
                        if post.get('wch_page') == 'my_cart':
                            return request.redirect('/capital_centric/operator/my_cart?modal=True&&email_sent=True')
                    else:
                        values['error'] = "Wrong Email Address"
                        if post.get('wch_page') == 'my_cart':
                            return request.redirect('/capital_centric/operator/my_cart?modal=True&&wrong_email=True')
                    
                
                elif post.get('fromwch') == 'submit':
                    user_ids = user_obj.search(cr, SUPERUSER_ID, [('login','=',post.get('login'))])
                    if user_ids:
                       user_obj.write(cr,SUPERUSER_ID,user_ids,{'password':post.get('password')})
                       user = user_obj.browse(cr,SUPERUSER_ID,user_ids[0])     
                       values['user'] = user                   
                       return request.redirect('/sign-in')
                    else:
                       values['error'] = "Wrong Email Address"
                       values['mode'] = 'reset'
                else:
                    values['error'] = "Incorrect Email or Password"
                    
                if post.get('wch_page') == 'my_cart':
                    return request.redirect('/capital_centric/operator/my_cart?modal=True&&error=True')
                else:
                    return request.redirect('/sign-in?error=True')
                    # return request.website.render("website.homepage", values)
                
      @http.route(['/capital_centric/fit/emulation'], type='http', auth='public', website=True, multilang=True)
      def emulation(self, **post):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          partner_obj = request.registry.get('res.partner')
                         
          request.session.logout(keep_db=True)
          if not request.httprequest.session.get('website_previous_uid'):
             request.httprequest.session['website_previous_uid'] = uid
          user = user_obj.browse(cr, suid, int(post.get('emu_user')))
          user_agent_env = {'base_location': 'http://localhost:8069', 'HTTP_HOST': 'localhost:8069', 'REMOTE_ADDR': '127.0.0.1'} # TODO: send http information
          loginuid = user_obj.authenticate(cr, user.login, user.password, user_agent_env)
          uid = request.session.authenticate(request.db, user.login, user.password)                              
          return request.redirect('/')

      @http.route(['/capital_centric/get/emulation'], type='json', auth='public', website=True, multilang=True)
      def get_emulation(self, **post):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          
          user = user_obj.browse(cr, uid, uid).emulation
          if not user and request.httprequest.session.get('website_previous_uid'):
             user = True
                                        
          return user                    
          
      #SIGN UP LINK
      @http.route(['/capital_centric/sign_up/<path>/'], type='http' ,auth="public" ,website=True ,multilang=True)
      def signup(self, path,**post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          request.context.update({'editable':False}) 
          country_obj = request.registry.get('res.country')
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,uid)
          
          if user.name == 'Public user':
              h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
              user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
              user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
           
          country_ids = country_obj.search(cr, uid, [])
          countries = country_obj.browse(cr, suid,country_ids)
          type = 'Customer'
          if path == 'restaurant': 
              type = 'Restaurant'
          if path == 'operator' and not user.is_wlabeling:
              type = 'Tour Operator'
          values = {
                    'country_ids' : countries,
                    'type' : type,
                    'req':'signup',
                    'user':user
                    }
          
          if post.get('error'):values['error'] = post.get('error')
          
          return request.website.render("fit_website.signup_page", values)
      

#SIGN UP FORM
      @http.route(['/fit_website/sign_up_details/'], type='http' ,auth="public" ,website=True ,multilang=True)
      def sign_up_details(self, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context 
          context = {}
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,uid)
          
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
          
          required_fields = ['name','email','password']
          error = set()
          values = dict((key, post.get(key)) for key in post)
          values['error'] = error
          err_msg = 'Thank You. Your request has been registered. We will get back to you shortly'
          if post.get('accept_tc') == 'on':
              accept_tc = True
          else:
              accept_tc = False
              
          # fields validation
          for field in required_fields:
            if not post.get(field):
                error.add(field)
          if error:
            type = post.get('type')
            if post.get('type') == 'venue':
                type = 'restaurant'
            return self.signup(type, **values) 
        
          
          user_vals = {
                       'login'      : post.get('email'),
                       'password'   : post.get('password'),
                       'customer'   : True,
                       'cc_fit'     : True,
                       'name'       : post.get('name',''),
                       'mobile'     : post.get('mobile',''),
                       'phone'      : post.get('phone',''),
                       'zip'        : post.get('zip',''),
                       'email'      : post.get('email'),
                       'street'     : post.get('street',''),
                       'street2'    : post.get('street2',''),
                       'state_id'   : post.get('State',''),
                       'country_id' : post.get('Country',''),
                       'location_id':post.get('Location',''), 
                       'city_id'    : post.get('city',''),
                       'vat'        : post.get('vat',''),
                       'is_company' : False,
                       'accept_tc'  : accept_tc, 
                       }
          
          if user.is_group:
              user_vals.update({'cc_fit' : False,
                                'cc_group' : True})
          
          if post.get('type') == 'operator':
             user_vals.update({'active'  : False,
                               'role'    : 'client_mng',
                               'type'    : 'invoice',
                               'partner_type' : 'client',
                               'payment_type' : post.get('payment_type'),
                               })
             context['frm_oprtor'] = True
             err_msg = 'Thank You. Your request has been registered. We will get back to you shortly'
            
          if post.get('type') == 'venue':
             user_vals.update({'active'  : True,
                               'role'    : 'venue_mng',
                               'type'    : 'invoice',
                               'partner_type' : 'venue',
                               'supplier': True,
                               })
             err_msg = 'Thank You for signing up. Please login to continue'
        
            
          if post.get('type') not in ('venue','operator'):
             operator_id = user.partner_id.id 
             if user.role == 'client_mng':
                operator_id = user.partner_id.parent_id.id
             user_vals.update({'active'  : True,
                               'role'    : 'client_cust',
                               'type'    : 'contact',
                               'partner_type' : 'contact',
                               'supplier': True,
                               'parent_id' : operator_id
                               })
             err_msg = 'Thank You for signing up. Please login to continue'
          if post.get('type') in ('venue','operator'):
             res_id = request.registry.get('res.partner').create(cr, SUPERUSER_ID, user_vals)
             user_vals.update({'parent_id' : res_id,
                          'name'      : post.get('contact_name'),
                          'type'      : 'contact',
                          'partner_type':'contact',
                          'use_parent_address': True})
            
          user_obj.create(cr, SUPERUSER_ID, user_vals,context)
          return request.website.render("fit_website.signup_page",{'req':'requested','error':err_msg,'user':user,'post':post})
      
      
#JSON FOR CHECKING E-MAIL IS EXISTING OR NOT IN DATABASE
      @http.route(['/fit_website/check_email/'], type='json', auth="public", website=True, multilang=True)
      def check_email(self, value, db_id, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          user_id = user_obj.search(cr,SUPERUSER_ID,['|',('active','=',False),('active','=',True),('login','=',value)])
          if user_id:
              user = user_obj.browse(cr,suid,user_id[0])
              if user and user.partner_id.id != db_id:  
                 return True
          return False
        
        
# 'Cancellation' link in Operator 'BOOKINGS'    
      @http.route(['/fit_website/menu_and_covers_for_bookings/'], type='json', auth="public", website=True)
      def menu_and_covers_for_bookings(self,lead_id,json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          crmlead_obj = request.registry.get('crm.lead')
          cc_menu_details_obj = request.registry.get('cc.menu.details')
          lead =  crmlead_obj.browse(cr, suid, lead_id)
          
          today = (parser.parse(time.strftime("%Y-%m-%d %H:%M"))+relativedelta(hours=+36)).strftime("%Y-%m-%d %H:%M")
          menus = []
          title_obj = request.registry.get('res.partner.title')
          title_ids = title_obj.search(cr, uid, [])
          titles = title_obj.browse(cr, suid, title_ids)
          info = False
          for info in lead.info_ids:
            if info.is_completed == True:
                for mdtls in info.menu_dt_ids:
                    menus.append(cc_menu_details_obj.browse(cr, suid, mdtls.id))
          
          if lead.date_requested < today:
             return request.website._render("fit_website.menu_and_covers", {'not_allowed': 'not_allowed','menus':menus,'lead':lead,'title_ids':titles,'info':info})
                    
          return request.website._render("fit_website.menu_and_covers", {'menus': menus,'lead':lead,'title_ids':titles,'info':info})

      
# Invoice link in Invoice Table
      @http.route(['/fit_website/invoice_json/'], type='json', auth="public", website=True)
      def invoice_json(self,invoice_id,json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          acc_inv_obj = request.registry.get('account.invoice')  
          acc_inv = acc_inv_obj.browse(cr, suid, invoice_id)
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,uid)         
          return request.website._render("fit_website.invoice_link_template", {'invoice': acc_inv ,'user':user})


#Fetching Covers from dialog box in Bookings of Tour Operators    
      @http.route(['/fit_website/menu_covers_save/'], type='json', auth="public", website=True)
      def menu_covers_save(self, menu_list, send_confirmation, info_dict=None, json=None):  
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          mdetails_obj = request.registry.get('cc.menu.details')
          info_obj = request.registry.get('cc.send.rest.info')
          user_obj = request.registry.get('res.users')
          invoice_obj = request.registry.get('account.invoice')
          lead_obj = request.registry.get('crm.lead') 
          tmpl_obj = request.registry.get("email.template")
          
          user = user_obj.browse(cr, uid, uid)
          payment_type = user.partner_id and user.partner_id.payment_type or ''
          
          mdetails = False
          if user.role in ('client_user','client_mng','client_cust'):
             payment_type = user.partner_id and user.partner_id.parent_id and user.partner_id.parent_id.payment_type or ''
             
          mflag = cflag = False 
          for x in menu_list:
              mdetails = mdetails_obj.browse(cr, uid, int(x['menu_id']))
              if payment_type == 'on_purchase':
                 if int(x['covers']) > mdetails.no_of_covers:
                    return 'false'
              if int(x['covers']) != mdetails.no_of_covers:
                 mflag = True                 
                 mdetails_obj.write(cr, uid, [int(x['menu_id'])], {'no_of_covers':x['covers']})              
          info_obj.write(cr,uid, [mdetails.info_id.id],{})
          
          if mflag:
            try:  
                res = info_obj.update_invoice(cr, uid, [mdetails.info_id.id],context=None)
            except:
               cr.rollback()  
               return 'unavailability'
               
          if payment_type == 'prepaid':
             for inv in invoice_obj.browse(cr,uid,res['inv_ids']):
                 if inv.type in ('out_invoice','out_refund'):
                   lead_obj.create_payment_rec(cr, uid, inv, {}, context=None)
          
          if len(info_dict):
              self.save_input_my_cart(mdetails.info_id.id, info_dict)
              cflag = True
              
          if not mflag and not cflag:
              cr.rollback()    
              return 'exception'
          
          if mdetails:         
             toptemplate_id = tmpl_obj.search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Customer')])
             vtemplate_id = tmpl_obj.search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Venue')])
             gutemplate_id  = tmpl_obj.search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Guest')])
             if toptemplate_id:
                tmpl_obj.send_mail(cr, uid, toptemplate_id[0], mdetails.info_id.id, force_send=True, context=None)
             if vtemplate_id:
                tmpl_obj.send_mail(cr, uid, vtemplate_id[0], mdetails.info_id.id, force_send=True, context= {'tmp_name':'Enquiry - Amendment Confirmation To Venue'})
             if send_confirmation:
                context = {} 
                tmpl_obj.send_mail(cr, uid, gutemplate_id[0], mdetails.info_id.id, force_send=True, context=None)                 

          return 
               
      def conv_to_utc(self,cr, uid, date, chkwch):
          user = request.registry.get('res.users').browse(cr,uid,uid)
          local = user and user.tz and pytz.timezone (user.tz) or pytz.timezone ('Europe/London')
          naive = datetime.strptime (date, "%d/%m/%Y")
#           local_dt = local.localize(naive, is_dst=None)
#           utc_dt = local_dt.astimezone (pytz.utc)
          if chkwch == 'st_date':
             return naive.strftime("%Y-%m-%d 00:00")
          else: 
              return naive.strftime("%Y-%m-%d 23:59")
          
#BOOKINGS link in Venues & Tour Operators with filter
      @http.route(['/capital_centric/<path>/bookings'], type='http', auth="public", website=True, multilang=True)
      def fit_bookings(self,path,*arg, **post ):  
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        loginuid = request.session.uid or request.uid
        user = request.registry.get('res.users').browse(cr,uid,loginuid)        
        crmlead_obj = request.registry.get('crm.lead')
        sqlstr = ''        
        domain = [('type','=','opportunity'),('service_type','=','venue')]
        partner = user.partner_id
        today   = time.strftime("%Y-%m-%d")
        title_obj = request.registry.get('res.partner.title')
        title_ids = title_obj.search(cr, uid, [])
        titles = title_obj.browse(cr, suid, title_ids)
        if user.role not in ('client','venue'):
           partner = user.partner_id.parent_id
        if user.is_group:
           domain.append(('passen_type','=','group'))
        if not user.is_group:
           domain.append(('passen_type','=','fit')) 
        if path == 'operator': 
           domain.append(('partner_id','=',user.partner_id and user.partner_id.id or 0))    
           if user.role == 'client_mng':
              del domain[len(domain)-1] 
              domain.append(('partner_id','=',user.partner_id and user.partner_id.parent_id and user.partner_id.parent_id.id or 0))        
           if user.role in ('client_user','client_cust'):  
              del domain[len(domain)-1] 
              domain.append(('sales_person','=',user.id or 0 ))
           
        if not post.get('bking_status') and not post.get('inv_status'):
           domain.append('|') 
           domain.append(('state','in',['open','done']))
           domain.append(('is_cancelled','=',True))
             
        if post.get('from_which_path'):
           path =  post.get('from_which_path')                
         
        if path == 'restaurant':            
            if user.role == 'venue_user':                
               domain.append(('restaurant_id','in',[x.id for x in user.partner_id.contact_ids]))
            elif user.role == 'venue_mng':
               domain.append(('restaurant_id.parent_id','=',user.partner_id.parent_id and user.partner_id.parent_id.id or 0 ))
            else:
               domain.append(('restaurant_id.parent_id','=',user.partner_id and user.partner_id.id or 0))            
         
        if post.get('enq_no.'):
           domain.append(('lead_no','ilike',str(post.get('enq_no.'))))           
           
        if post.get('top_ref'):
           domain.append(('cust_ref','ilike',str(post.get('top_ref')))) 
         
        if post.get('start_date') and post.get('end_date'): 
           st_date = self.conv_to_utc(cr, uid, post.get('start_date'), 'st_date')
           ed_date = self.conv_to_utc(cr, uid, post.get('end_date'), 'ed_date')         
           domain.append(('date_requested','>=',st_date)) 
           domain.append(('date_requested','<=',ed_date))
        if post.get('guest_name'):
           domain.append(('partner_name','ilike',str(post.get('guest_name'))))           
        
        if post.get('guest_email'):
           domain.append(('email_from','ilike',str(post.get('guest_email'))))  
           
        if post.get('res_name'):
           domain.append(('restaurant_id.name','ilike',str(post.get('rest_name'))))       
        
        if post.get('bking_status') and path == 'restaurant':            
           domain.append(('state','in',eval(post.get('bking_status'))))
        
        if post.get('bking_status') and path == 'operator':
           domain.append(('stage_id.name','=',str(post.get('bking_status'))))
        
        if post.get('bookd_by'):
            domain.append(('sales_person','=',int(post.get('bookd_by'))))

        if post.get('reflinks'):
           domain.append(('referral_link','=',post.get('reflinks')))

        lead_ids = crmlead_obj.search(cr,uid,domain)
        
        if post.get('inv_status'):
           lead_dict =  crmlead_obj._get_inv_status(cr, suid, lead_ids, 'invoice_status', None, context=None)
           lead_ids = []
           for x,y in lead_dict.items():
               if y == post.get('inv_status'):
                  lead_ids.append(x) 
                  
        leads =  crmlead_obj.browse(cr, suid, lead_ids)
        upcoming = []
        past = []
        for l in leads:
            if l.conv_dob:
                if datetime.strptime(l.conv_dob,'%d-%b-%Y').strftime('%Y-%m-%d') < today:
                    past.append(l.id)
                else:
                    upcoming.append(l.id)
        lead_upcoming = crmlead_obj.browse(cr, suid, upcoming)
        lead_past     = crmlead_obj.browse(cr, suid, past)

         
        info_dtls = {}
        menus = []
         
        for ld in leads:
            for info in ld.info_ids:
                if info.is_completed == True:                    
                    for mdtls in info.menu_dt_ids:
                        menus.append(mdtls.id)
                info_dtls.update({ld.id : {'menus':info.menu_dt_ids and ', '.join(str(e.menu_id and e.menu_id.name or 'N/A') for e in info.menu_dt_ids) or 'N/A',
                                           'to_price' : "%.2f" % info.tot_top_price,
                                           'rest_price' :"%.2f" % info.tot_rest_price
                                          }})
             
        symbol = user.company_id.currency_id.symbol or ''
        
        cr.execute('select distinct(referral_link) from crm_lead where referral_link is not null and partner_id = %s',(partner.id,))
        ref_links = [x[0] for x in cr.fetchall()]
        cr.execute('select id from res_users where partner_id in (select id from res_partner where parent_id = %s or id = %s)'%(user.partner_id.parent_id and user.partner_id.parent_id.id or user.partner_id.id,user.partner_id.parent_id and user.partner_id.parent_id.id or user.partner_id.id))
        bookd_by = [x[0] for x in cr.fetchall()]

        values = {
                 'up_lead_ids'     : lead_upcoming,
                 'past_lead_ids'   : lead_past,
#                  'login_user': user,
                 'symbol'       : symbol,
                 'path'         : path,
                 'user'         : user,
                 'uid'          : request.registry.get('res.users').browse(cr,uid,uid) ,
                 'info_dtls'    : info_dtls,
                 'vals'         : post,
                 'bookdby_ids'  : request.registry.get('res.users').browse(cr,uid,bookd_by),
                 'ref_links'    : ref_links,
                 'url_path'     : 'bookings',
                 'title_ids'    : titles,
                 }
        return request.website.render("fit_website.bookings",values)
    
    
#My Cart link in TO Header
      @http.route(['/capital_centric/operator/my_cart'], type='http', auth="public", website=True, multilang=True)
      def my_cart(self,*arg, **post ):
        
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        loginuid = request.session.uid or request.uid
        user_obj = request.registry.get('res.users')
        user = user_obj.browse(cr,uid,loginuid)
        info_obj = request.registry.get('cc.send.rest.info')
        lead_obj = request.registry.get('crm.lead')
        
        if post is None:
           post = {}
        sql_str = ''
        #get the enquiries of public user
        if user.name == 'Public user':
           info_ids = []
           user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',user.cc_url)])
           user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
           operator = user.partner_id.id
           if user.role in ('client_user','client_mng','client_cust'):
              operator = user.partner_id and user.partner_id.parent_id and user.partner_id.parent_id.id or False
           lead_ids = lead_obj.search(cr, uid, [('state','=','draft'),('website_session_id','=',request.httprequest.session.get('website_session_id') or [])])
           request.httprequest.session['website_lead_id'] = lead_ids
           info_ids = info_obj.search(cr, uid, [('lead_id','in',lead_ids)])
           if post.get('empty_cart') == 'yes':
              request.httprequest.session['website_lead_id'] = []
           sql_str = """and website_session_id = '""" + str(request.httprequest.session.get('website_session_id')) + """'"""
        symbol = user.company_id.currency_id.symbol or ''
        operator = user.partner_id.id
        if user.role in ('client_user','client_mng','client_cust'):
           operator = user.partner_id and user.partner_id.parent_id and user.partner_id.parent_id.id or False

        title_obj = request.registry.get('res.partner.title')
        title_ids = title_obj.search(cr, uid, [])
        titles = title_obj.browse(cr, suid, title_ids)
        
        cr.execute("""select info.id 
                      from cc_send_rest_info info 
                      inner join crm_lead l on l.id = info.lead_id
                      where l.state = 'draft' and l.date_requested::date > '""" + str(time.strftime("%Y-%m-%d")) +"""'
                      and l.partner_id = """ + str(operator ) +""" 
                      and l.sales_person=""" + str(user.id) + """
                      and l.passen_type='""" + str(user.is_group and 'group' or 'fit') +"""' 
                      """ + sql_str + """
                      order by info.id asc""")

        info_ids = [i[0] for i in cr.fetchall()]

        if post.get('empty_cart') == 'yes':
           cr.execute("""update crm_lead set state='cancel',stage_id = (select id from crm_case_stage where name='Lost' and type='both') 
                         where id in (select lead_id from cc_send_rest_info where id in %s)""",(tuple(info_ids),)) 
           info_ids = [] 

        rest_info = info_obj.browse(cr, uid, info_ids)
        
        error = ''
        if post.get('error'):
            error = 'Incorrect Email or Password'
        if post.get('email_sent'):
            error = 'An email has been sent with credentials to reset your password'
        if post.get('wrong_email'):
            error = 'Wrong Email Address'   
        
        values = { 
                  'info_list':rest_info or [],
                  'user':user,
                  'uid':user_obj.browse(cr,uid, uid),
                  'info_ids':info_ids,
                  'path' : 'my_cart',                  
                  'title_ids' : titles,
                  'show_modal_val'  : 'show_modal' if post.get('modal') == 'True' else 'hide_modal',
                  'error'           : error,
                  #info id is required only to highlight the records
                  'info_id':post.get('info_id','') 
                 }
        
        subtotal = tax_amt = total = top_markup = 0.00 
        for info in rest_info:
            for m in info.menu_dt_ids:
                if m.food_type == 'meal':
                   subtotal += (m.top_service_charge +  ((m.top_menu_price / (100 + 20.00)) * 100)) * m.no_of_covers
                   tax_amt += (m.top_menu_price - ((m.top_menu_price / (100 + 20.00)) * 100)) * m.no_of_covers
                elif m.food_type == 'drink':
                    tax_amt += (m.top_drinks_price - ((m.top_drinks_price / (100 + 20.00)) * 100)) * m.no_of_covers
                    subtotal += (m.top_service_charge + ((m.top_drinks_price / (100 + 20.00)) * 100)) * m.no_of_covers
                top_markup += m.top_markup * m.no_of_covers
            total += info.tot_top_price
            
        h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
        values.update({'subtotal':subtotal,
                       'vat':tax_amt,
                       'total':total,
                       'symbol':user.company_id.currency_id.symbol,
                       'top_markup':top_markup,
                       'url' : h
                       })   
        
        return request.website.render("fit_website.booking_completion",values)
    
      #MARKUP link in Tour Operators
      @http.route(['/capital_centric/operator/markup'], type='http', auth="public", website=True, multilang=True)
      def markup(self, *arg, **post ):
          
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        loginuid = request.session.uid or request.uid
        user = request.registry.get('res.users').browse(cr,uid,loginuid)
        
        symbol = user.company_id.currency_id.symbol or ''
        
        user_obj = request.registry.get('res.users')
        user = user_obj.browse(cr,uid, uid)
        operator_id = user.partner_id.id or 0
        if user and user.role in ('client_user','client_mng'):
             operator_id = user.partner_id and user.partner_id.parent_id.id or 0
         
        partner_obj = request.registry.get('res.partner')
        menu_obj = request.registry.get('cc.menus')
        op_mrk_obj = request.registry.get('cc.operator.markup')
        
        markup_obj = request.registry.get('cc.operator.markup')
        markup_ids = markup_obj.search(cr,uid,[('partner_id','=', operator_id),('mrkup_lvl','=','menu_lvl')])
        markups = markup_obj.browse(cr, suid, markup_ids)
        
        venue_ids   = partner_obj.search(cr, openerp.SUPERUSER_ID, [('type','=','default'),('partner_type','=','venue')])
        venues      = partner_obj.browse(cr, openerp.SUPERUSER_ID, venue_ids)
        
        all_menus = {}
        sel_menus = {}
        for case in markup_obj.browse(cr, uid, markup_ids):
            mrk_menu_ids = menu_obj.search(cr,uid,[('partner_id','=', case.restaurant_id.id),('active','in',(True))])
            all_menus[case.id] = [x for x in menu_obj.browse(cr, uid,mrk_menu_ids)]
            sel_menus[case.id] = [x.id for x in case.menu_ids]        

        values = {
#                  'login_user' : user,
                 'symbol'     : symbol,
                 'user'       : user,
                 'uid'        : user_obj.browse(cr,uid, uid),
                 'venues'     : venues,
                 'all_menus'  : all_menus,
                 'sel_menus'  : sel_menus,
                 'url_path'   : 'markup'
                 }
          
        return request.website.render("fit_website.markup_template",values)


      #INVOICE link in Venues & Tour Operators with filter
      @http.route(['/capital_centric/<path>/invoice'], type='http', auth="public", website=True, multilang=True)
      def invoice(self,path,*arg, **post ):  
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        loginuid = request.session.uid or request.uid
        user = request.registry.get('res.users').browse(cr,uid,loginuid)        
        acc_inv_obj = request.registry.get('account.invoice') 
        operator = user.partner_id.id
        passen_type = 'fit'           
        if user.role in ('client_user','client_mng','client_cust'):
           operator = user.partner_id.parent_id and user.partner_id.parent_id.id           
        if user.is_group:
           passen_type = 'group'     
        acc_inv_ids = acc_inv_obj.search(cr,uid,[('partner_id','=',operator),('state','in',('open','paid')),('passen_type','=',passen_type)])
        acc_invs = acc_inv_obj.browse(cr, suid, acc_inv_ids)
             
        symbol = user.company_id.currency_id.symbol or ''
            
        values = {
                 'acc_inv_ids'  : acc_invs,
#                  'login_user'  : user,
                 'symbol'       : symbol,
                 'path'         : path,
                 'user'         : user,
                 'uid'          : user_obj.browse(cr,uid, uid), 
                 }
        return request.website.render("fit_website.invoice",values)
    
#PAYMENTS link in Tour Operators
      @http.route(['/capital_centric/operator/payments'], type='http', auth="public", website=True, multilang=True)
      def payments(self,*arg, **post ):  
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          
          voucher_obj = request.registry.get('account.voucher')
          loginuid = request.session.uid or request.uid
          user = user_obj.browse(cr,uid,loginuid)
          parent = user.partner_id
          if user.role not in ('venue','client'):
             parent = user.partner_id.parent_id 
          
          voucher_ids = voucher_obj.search(cr, uid, [('partner_id','=',parent.id),('state','=','posted')])
          vouchers = voucher_obj.browse(cr,uid,voucher_ids)
          symbol = user.company_id.currency_id.symbol or ''
          
          values = {
                     'user'         : user,
                     'voucher_ids'  : vouchers,
                     'symbol'       : symbol,
                     'uid'          : user_obj.browse(cr,uid, uid),
                     'url_path'     : 'payments'
                   } 
          return request.website.render("fit_website.payments",values)
 
#HELP link in Tour Operators
      @http.route(['/capital_centric/<path>/help'], type='http', auth="public", website=True, multilang=True)
      def help(self,path, *arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          
          loginuid = request.session.uid or request.uid
          user = user_obj.browse(cr,uid,loginuid)
          symbol = user.company_id.currency_id.symbol or ''
          
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
          
          values = {
#                      'login_user' : user,
                     'user' : user,
                     'symbol' : symbol,
                     'path' : path,
                     'uid'  : user_obj.browse(cr, uid, uid),
                     'url_path' : 'help'
                   }
          
          return request.website.render("fit_website.help_form",values)

#CONTACTS LINK in Venues & Tour Operators
      @http.route(['/capital_centric/contacts/<path>/'], type='http', auth="public", website=True, multilang=True)
      def contacts(self,path,*arg, **post ):
          request.context.update({'editable':False})
          
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          partner_obj = request.registry.get('res.partner')  
          user = user_obj.browse(cr,uid,loginuid)
          partner_id = user.partner_id.id
          
          values = {#'login_user'   : user,
                    'type'         : path,
                    'user'         : user,
                    'uid'          : user_obj.browse(cr, uid, uid),
                    'url_path'     : 'contacts'
                   }
        
          if user.role in ('venue_mng','client_mng'):
             partner_id =  user.partner_id.parent_id and user.partner_id.parent_id.id or 0
             
          domain = [('cc_fit','=',True)]
          if user.is_group:
              domain = [('cc_group','=',True)]
          child_ids_con = partner_obj.search(cr, uid, [('parent_id','=',partner_id),('active','in',(False,True, None)),('type','=','contact')]+domain)
          if user.is_wlabeling:
             child_ids_cust = user_obj.search_read(cr, uid, [('partner_id.parent_id','=',partner_id),('active','in',(False,True, None)),('role','=','client_cust')],['partner_id'])
             child_ids_cust = [x['partner_id'][0] for x in child_ids_cust]
             child_ids_con = list(set(child_ids_con) - set(child_ids_cust))             
             values['customer_ids'] = partner_obj.browse(cr,uid,child_ids_cust)
             
          child_con = partner_obj.browse(cr,uid,child_ids_con)         
          values['contact_ids'] = child_con
          return request.website.render("fit_website.con_info",values)
        
#RESTAURANTS LINK in Venues
      @http.route(['/capital_centric/restaurant'], type='http', auth="public", website=True, multilang=True)
      def restaurant(self,*arg, **post ):
         
          request.context.update({'editable':False})
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          partner_obj = request.registry.get('res.partner')
          user = user_obj.browse(cr,uid,loginuid)
          
          domain = [('active','in',(False,True, None)),('type','=','default')]    
          
                       
          if user.role == 'venue_user':
             domain.append(('id','in',[x.id for x in user.partner_id.contact_ids]))
          elif user.role == 'venue_mng':
             domain.append(('parent_id','=',user.partner_id.parent_id.id))
          else:
             domain.append(('parent_id','=',user.partner_id.id))
             
          if user.is_group:
                domain.append(('cc_group','=',True))
          else:
                domain.append(('cc_fit','=',True))
              
          child_ids_res = partner_obj.search(cr, uid,domain ,order='name')  
          child_res = partner_obj.browse(cr,uid,child_ids_res)
          
          values = {
#                     'login_user'   : user,
                    'child_res_id' : child_res,
                    'user'         : user,
                    'url_path'     :'restaurants'

                   }
         
          return request.website.render("fit_website.res_info",values)
      
      
#TC LINK in Venues
      @http.route(['/capital_centric/<path>/tc'], type='http', auth="public", website=True, multilang=True)
      def tc(self,path,*arg,**post ):
          request.context.update({'editable':False})

          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          
          if user.name == 'Public user':
            h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
            user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
            user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
          
          values = {
#                     'login_user' : user,
                    'user'       : user,
                    'path'       : path,
                    'uid'        : user_obj.browse(cr,uid, uid),
                    'url_path'   : 'tc'
                   }
         
          return request.website.render("fit_website.tc",values)


#Privacy LINK
      @http.route(['/capital_centric/privacy_policy'], type='http', auth="public", website=True, multilang=True)
      def privacy_policy(self,*arg, **post ):
          request.context.update({'editable':False})
          
          
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          
          values = {
#                     'login_user' : user,
                    'user'       : user,
                    'path'       : 'restaurant'
                   }
          
          return request.website.render("fit_website.home_privacy",values)

#TC LINK in Footer
      @http.route(['/capital_centric/terms_footer/<path>'], type='http', auth="public", website=True, multilang=True)
      def terms_footer(self,path,*arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr, uid, uid)  
          
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
             
          return request.website.render("fit_website.home_tc",{'user':user,'path':path})
      
#Privacy LINK in Footer 
      @http.route(['/capital_centric/privacy_policy_footer'], type='http', auth="public", website=True, multilang=True)
      def privacy_policy_footer(self,*arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr, uid, uid)  
          
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
             
          return request.website.render("fit_website.home_privacy",{'user':user,'path':'home_page'})
      
#Contact Us LINK in Footer
      @http.route(['/capital_centric/contact_us','/capital_centric/contact_us/<path>'], type='http', auth="public", website=True, multilang=True)
      def contact_us(self, path = None,*arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr, uid, uid)
          
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
               
          values = {'user' : user}
          if path == "submitted":
              values['error'] = "Thank you. We will get back to you shortly."
              
          return request.website.render("fit_website.contact_us",values)
      
      
#About Us LINK in Footer
      @http.route(['/capital_centric/about_us'], type='http', auth="public", website=True, multilang=True)
      def about_us(self,*arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr, uid, uid)  
          
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
             
          return request.website.render("fit_website.about_us",{'user':user})

#Contact Us Fetch Form
      @http.route(['/fit_website/contact_us_form/','/fit_website/contact_us_form/<path>'], type='http', auth="public", website=True, multilang=True)
      def contact_us_form(self, path=None, *arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          
          mail_obj = request.registry.get('mail.mail')
          email_from = email_to = 'fitforpurpose@capitalcentric.co.uk'
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr, uid, uid)
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
          operator = False
          if 'g-recaptcha-response' in post:
             url ='https://www.google.com/recaptcha/api/siteverify'
             params = {
                        'secret': '6Lcglw8TAAAAAKphTkfb2gb0MVMXrQW4X43Hj4G-',
                        'response': post.get('g-recaptcha-response'),
                      }
             verify_rs = requests.get(url, params=params, verify=True)
             verify_rs = verify_rs.json()
             if not verify_rs.get("success", False):
                 post.update({'captcha_error':'Please wait for the reCaptcha image to load and try again.',
                              'user':user})
                 return request.website.render("fit_website.contact_us",post)

          if user and user.is_wlabeling:
             email_from = email_to = user.partner_id.email
             operator = user.partner_id
             if user.role != 'client':
                email_from = email_to = user.partner_id.parent_id.email
                operator = user.partner_id.parent_id    
                     
          body = """<div style='font-family:Calibri; font-size: 12pt; color: rgb(34, 34, 34); background-color: rgb(255, 255, 255); '>
                    """ + str(not user.is_wlabeling and '<img src="https://fitforpurposeonline.com/fit_website/static/src/img/fitcclogo.jpg" height="156" width="245">' or '') + """
                    <br/><br/>Name: """ + post.get('name') +"""<br/>
                    Email: """ + post.get('email') + """<br/>
                    Phone: """ + post.get('phone') + """<br/>
                    Message: """+ post.get('message') + """<br/><br/>
                    <p>Thank you.</p>                    
                    <br/><br><div style="width: 375px; height: 20px; margin: 0px; padding: 0px; background-color:""" + str(operator and operator.wbsite_color or '#F2F2F2') + """; border-top-left-radius: 5px 5px; border-top-right-radius: 5px 5px; background-repeat: repeat no-repeat;">
        <h3 style="margin: 0px; padding: 2px 14px; font-size: 12px; color: """ + str(operator and operator.submenu_color or 'black') + """;">
            <strong style="text-transform:uppercase;">""" + str(operator and operator.name or 'The FIT For Purpose')+ """ Team </strong></h3>
    </div>
    <div style="width: 347px; margin: 0px; padding: 5px 14px; line-height: 16px; background-color: #F2F2F2;">
        <span style="color: #222; margin-bottom: 5px; display: block; ">
            """ + str(operator and operator.street or user.company_id.street) + """<br>
            """ + str(operator and operator.street2 or user.company_id.street2) + """<br>
            """ + str(operator and operator.city or user.company_id.city) +""" """ + str(operator and operator.zip or user.company_id.zip) + """<br>
            """ + str(operator and operator.country_id and operator.country_id.name or user.company_id.country_id and user.company_id.country_id.name) + """<br></span>
            <div style="margin-top: 0px; margin-right: 0px; margin-bottom: 0px; margin-left: 0px; padding-top: 0px; padding-right: 0px; padding-bottom: 0px; padding-left: 0px; ">
            </div>
        <p></p>
    </div>
</div>"""
                 
          mail_id = mail_obj.create(cr, SUPERUSER_ID, {'email_from'  : email_from,
                                                       'email_to'    : email_to, 
                                                       'reply_to'    : post.get('email'),
                                                       'subject'     : 'Enquiry generated from FIT For Purpose',
                                                       'body_html'   : body,
                                                       'auto_delete' : True,})
          if mail_id:
             res = mail_obj.send(cr, uid, [mail_id], False, False, None)
            
          if path != 'pop_up':                          
              return request.redirect('/capital_centric/contact_us/submitted')
          else:
              return
          
          
#TC SAVED(JSON)       
      @http.route(['/fit_website/tc_json/'], type='json', auth="public", website=True, multilang=True)
      def tc_json(self, partner_id, json=None):   
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          partner_obj = request.registry.get('res.partner')
          
          partner_vals = {
                            'accept_tc' : True,
                         }
          
          partner_obj.write(cr, uid, [partner_id], partner_vals)
          return 


      #Invoice Details Link in Venues & Operators
      @http.route(['/capital_centric/invoice_details/<path>'], type='http', auth="public", website=True, multilang=True)
      def profile(self,path,*arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          request.context.update({'editable':False})
          uid = request.session.uid
          if post is None: post = {}
          if post.get('inv_save'):
              inv_save = 'yes'
          else:
              inv_save = ''
          partner_obj = request.registry.get('res.partner')
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          country_id = user.partner_id and user.partner_id.country_id and user.partner_id.country_id.id or 0
          state_id = user.partner_id and user.partner_id.state_id and user.partner_id.state_id.id or 0
          city_id = user.partner_id and user.partner_id.city_id and user.partner_id.city_id.id or 0
          today = time.strftime("%Y-%m-%d")

          country_obj = request.registry.get('res.country')
          country_ids = country_obj.search(cr, uid, [])
          countries = country_obj.browse(cr, suid,country_ids)
          
          state_obj = request.registry.get('res.country.state')
          state_ids = state_obj.search(cr, uid,[('country_id','=',country_id)])
          states =  state_obj.browse(cr,uid,state_ids)
          
          city_obj = request.registry.get('cc.city')
          city_ids = city_obj.search(cr, uid,[('state_id','=', state_id)])
          cities =  city_obj.browse(cr,uid,city_ids)
          
          location_obj = request.registry.get('cc.location')
          location_ids = location_obj.search(cr, uid,[('city_id','=', city_id)])
          locations =  location_obj.browse(cr,uid,location_ids)
          
          acc_inv_obj = request.registry.get('account.invoice')
          
          operator = user.partner_id.id
          passen_type = 'fit'
          if user.is_group:
             passen_type = 'group' 
          if user.role in ('client_mng','client_usr'):
             operator = user.partner_id.parent_id.id 
          domain = [('partner_id','=',operator),('passen_type','=',passen_type)]
          if user.role == 'client_cust':
             domain = [('partner_id','=',operator),('lead_id.sales_person','=',user.id),('passen_type','=',passen_type)] 
          if post.get('inv_type'):
             domain.append((['type','=',post.get('inv_type')]))
          if post.get('start_date') and post.get('end_date'):
             st_date = self.conv_to_utc(cr, uid, post.get('start_date'), 'st_date')
             ed_date = self.conv_to_utc(cr, uid, post.get('end_date'), 'ed_date')         
             domain.append(('date_invoice','>=',st_date)) 
             domain.append(('date_invoice','<=',ed_date))
          if post.get('inv_status'):
             domain.append((['state','=',post.get('inv_status')]))
          if post.get('type'):
             path = post.get('type')
          if not post.get('inv_status'):
             domain.append((['state','in',('open','paid')]))     
              
          acc_inv_ids = acc_inv_obj.search(cr,uid,domain)     
          acc_browse = acc_inv_obj.browse(cr, suid, acc_inv_ids)
          # upcoming = []
          # past = []
          # for acc in acc_browse:
          #     print "acc.date_invoice",acc.date_invoice,today
          #     if acc.booking_date < today:
          #         past.append(acc.id)
          #     else:
          #         upcoming.append(acc.id)
          # print "upcoming",upcoming,past
          # acc_upcoming = acc_inv_obj.browse(cr, suid, upcoming)
          # acc_past     = acc_inv_obj.browse(cr, suid, past)
          symbol = user.company_id.currency_id.symbol or ''
          
          values = {
                   'userid'         : user,
#                    'login_user': user,
                   'country_ids'    : countries,
                   'state_ids'      : states,
                   'city_ids'       : cities,
                   'location_ids'   : locations,
                   'type'           : path,
                   'user'           : user,
                   'acc_inv_ids'    : acc_browse,
                   # 'acc_pastinv_ids'    : acc_past,
                   'inv_save'       : inv_save,
                   'symbol'         : symbol,
                   'vals'           : post,
                   'uid'            : user_obj.browse(cr,uid, uid),
                   'url_path'       : 'invoice'
                   }
          return request.website.render("fit_website.profile_form",values)

      @http.route(['/capital_centric/company/<path>'], type='http', auth="public", website=True, multilang=True)
      def company_profile(self,path,*arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          request.context.update({'editable':False})
          uid = request.session.uid
          if post is None: post = {}
          if post.get('inv_save'):
              inv_save = 'yes'
          else:
              inv_save = ''
          partner_obj = request.registry.get('res.partner')
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,loginuid)
          country_id = user.partner_id and user.partner_id.country_id and user.partner_id.country_id.id or 0
          state_id = user.partner_id and user.partner_id.state_id and user.partner_id.state_id.id or 0
          city_id = user.partner_id and user.partner_id.city_id and user.partner_id.city_id.id or 0

          country_obj = request.registry.get('res.country')
          country_ids = country_obj.search(cr, uid, [])
          countries = country_obj.browse(cr, suid,country_ids)

          state_obj = request.registry.get('res.country.state')
          state_ids = state_obj.search(cr, uid,[('country_id','=',country_id)])
          states =  state_obj.browse(cr,uid,state_ids)

          # city_obj = request.registry.get('cc.city')
          # city_ids = city_obj.search(cr, uid,[('state_id','=', state_id)])
          # cities =  city_obj.browse(cr,uid,city_ids)

          city_obj = request.registry.get('cc.city')
          city_ids = city_obj.search(cr, uid,[])
          cities =  city_obj.browse(cr,uid,city_ids)

          location_obj = request.registry.get('cc.location')
          location_ids = location_obj.search(cr, uid,[('city_id','=', city_id)])
          locations =  location_obj.browse(cr,uid,location_ids)

          acc_inv_obj = request.registry.get('account.invoice')

          # operator = user.partner_id.id
          # passen_type = 'fit'
          # if user.is_group:
          #    passen_type = 'group'
          # if user.role in ('client_mng','client_usr'):
          #    operator = user.partner_id.parent_id.id
          # domain = [('partner_id','=',operator),('passen_type','=',passen_type)]
          # if user.role == 'client_cust':
          #    domain = [('partner_id','=',operator),('lead_id.sales_person','=',user.id),('passen_type','=',passen_type)]
          # if post.get('inv_type'):
          #    domain.append((['type','=',post.get('inv_type')]))
          # if post.get('start_date') and post.get('end_date'):
          #    st_date = self.conv_to_utc(cr, uid, post.get('start_date'), 'st_date')
          #    ed_date = self.conv_to_utc(cr, uid, post.get('end_date'), 'ed_date')
          #    domain.append(('date_invoice','>=',st_date))
          #    domain.append(('date_invoice','<=',ed_date))
          # if post.get('inv_status'):
          #    domain.append((['state','=',post.get('inv_status')]))
          # if post.get('type'):
          #    path = post.get('type')
          # if not post.get('inv_status'):
          #    domain.append((['state','in',('open','paid')]))
          #
          # acc_inv_ids = acc_inv_obj.search(cr,uid,domain)
          # acc_invs = acc_inv_obj.browse(cr, suid, acc_inv_ids)
          #
          # symbol = user.company_id.currency_id.symbol or ''

          values = {
                   'userid'         : user,
#                    'login_user': user,
                   'country_ids'    : countries,
                   'state_ids'      : states,
                   'city_ids'       : cities,
                   'location_ids'   : locations,
                   'type'           : path,
                   'user'           : user,
                   # 'acc_inv_ids'    : acc_invs,
                   'inv_save'       : inv_save,
                   # 'symbol'         : symbol,
                   'vals'           : post,
                   'uid'            : user_obj.browse(cr,uid, uid),
                   'url_path'       : 'company'
                   }
          return request.website.render("fit_website.company_form",values)
      
       
#FETCHING THE STATE NAMES AND IDS(JSON)
      @http.route(['/fit_website/state_json/'], type='json', auth="public", website=True, multilang=True)
      def state_json(self,country, json=None):        
        cr, uid, = request.cr, request.uid
        state_obj = request.registry.get('res.country.state')        
        state_ids = state_obj.search(cr, openerp.SUPERUSER_ID, [("country_id","=",country)])
        states = state_obj.browse(cr, openerp.SUPERUSER_ID, state_ids)        
        state_names=[]
        for s in states:
           state_names.append(s.name)         
        return state_names,state_ids

#FETCHING THE Restaurants and Menus IDS(JSON) in Markup Operator
      @http.route(['/fit_website/markup_json/'], type='json', auth="public", website=True, multilang=True)
      def markup_json(self, from_which, restaurant_id, json=None):        
        cr, uid, = request.cr, request.uid
        
        partner_obj   = request.registry.get('res.partner')
        menu_obj   = request.registry.get('cc.menus')
        
        if from_which == 'restaurant':        
            partner_ids   = partner_obj.search(cr, openerp.SUPERUSER_ID, [('type','=','default'),('partner_type','=','venue')])
            partners      = partner_obj.browse(cr, openerp.SUPERUSER_ID, partner_ids)        
            partner_names =[]
            for p in partners:
               partner_names.append(p.name)         
            return partner_names,partner_ids
        
        if from_which == 'menu':        
            menu_ids   = menu_obj.search(cr, openerp.SUPERUSER_ID, [('partner_id','=',restaurant_id)])
            menus      = menu_obj.browse(cr, openerp.SUPERUSER_ID, menu_ids)        
            menu_names =[]
            for m in menus:
               menu_names.append(m.name)         
            return menu_names,menu_ids

      #Autocomplete JSON function
      @http.route('/autocomplete', type='json', auth="public")
      def autocomplete(self, location):
        cr, uid, suid, ctx, pool = request.cr, request.uid, openerp.SUPERUSER_ID, request.context, request.registry
        cr.execute(""" select distinct concat(s.name,', ', ct.name) as label, s.id
                           from res_partner p
                           inner join res_country_state s on s.id = p.state_id
                           inner join res_country ct on ct.id = s.country_id
                           where p.partner_type = 'venue' and p.is_company is False and p.active is True and s.name ilike '""" + location +"""%'"""
                    )
        res = cr.dictfetchall()
        return res

      #To get results form session
      @http.route('/FIT/GetData', type='http', auth="none")
      def GetService_Data(self, **post):
          cr, uid, suid, ctx, pool = request.cr, request.uid, openerp.SUPERUSER_ID, request.context, request.registry
          records = json.loads(request.httprequest.session.get('json_dict') or '[]')
          if post.get('offset') or post.get('limit'):
             jslimit = int(post.get('offset',0)) + int(post.get('limit',0))
             records = records[int(post.get('offset') or 0 ):jslimit]
          return json.dumps(records)

      #FETCHING THE LOCATION NAMES AND IDS(JSON)
      @http.route(['/fit_website/location_json/'], type='json', auth="public", website=True)
      def location_json(self,city, value, json=None):
        cr, uid, = request.cr, request.uid
        location_obj = request.registry.get('cc.location')
        if(value == 'city_clicked'):
            location_ids = location_obj.search(cr, openerp.SUPERUSER_ID, [("city_id","=",city)])
            locations = location_obj.browse(cr, openerp.SUPERUSER_ID, location_ids)        
            location_names=[]
            for l in locations:
               location_names.append(l.name) 
            return location_names,location_ids
        
        if(value == 'location_clicked'):
            location_ids = location_obj.search(cr, openerp.SUPERUSER_ID, [("id","=",city)])
            locations = location_obj.browse(cr, openerp.SUPERUSER_ID, location_ids)        
            code = locations[0].code
            return code
 
    
#FETCHING THE CITY NAMES AND IDS(JSON)
      @http.route(['/fit_website/city_json/'], type='json', auth="public", website=True)
      def city_json(self,state, json=None):
                  
        cr, uid, = request.cr, request.uid
        city_obj = request.registry.get('cc.city')        
        city_ids = city_obj.search(cr, openerp.SUPERUSER_ID, [("state_id","=",state)])
        cities = city_obj.browse(cr, openerp.SUPERUSER_ID, city_ids)
        city_names=[]
        for c in cities:
           city_names.append(c.name) 
        return city_names,city_ids
        
      @http.route(['/fit_website/address_json/'], type='json', auth="public", website=True)
      def address_json(self, json=None):
          
        cr, uid, = request.cr, request.uid
        loginuid = request.session.uid or request.uid
        user_obj = request.registry.get('res.users')
        user = user_obj.browse(cr,uid,loginuid)

        street = user.partner_id.street
        street1 = user.partner_id.street2
#         if not street1:
#             street1 = ' '
        country = user.partner_id.country_id.id
        state = user.partner_id.state_id.id
        city = user.partner_id.city_id.id
        if not city:
            city = ' '
        location = user.partner_id.location_id.id
        zip = user.partner_id.zip
        if not zip:
            zip = ' '
        
        return street,street1,country,state,city,location,zip
    
      @http.route(['/fit_website/existing_address_json/'], type='json', auth="public", website=True)
      def existing_address_json(self, partner_id,json=None):
          
        cr, uid, = request.cr, request.uid
        partner_obj = request.registry.get('res.partner')
        
        partner = partner_obj.browse(cr,uid,partner_id)
        
        street = partner.street
        street1 = partner.street2
        country = partner.country_id.id
        state = partner.state_id.id
        city = partner.city
        if not city:
            city = ' '
        location = partner.location_id.id
        zip = partner.zip
        if not zip:
            zip = ' '
            
        return street,street1,country,state,city,location,zip    

#Invoice Details Form Save Function              
      @http.route(['/capital_centric/contact_save'], type='http', auth='user', methods=['POST'], website=True)
      def contact_save(self,image_name = None, *args, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
        
          partner = user.partner_id.id          
          if user.role not in ('client','venue'):
             partner = user.partner_id.parent_id.id       

          partner_obj = request.registry.get('res.partner') 
          partner_vals = {
                          'name'        : post.get('name',''),
                          'street'      : post.get('street',''),
                          'street2'     : post.get('street2',''),
                          'phone'       : post.get('phone',''),
                          'mobile'      : post.get('mobile',''),
                          'zip'         : post.get('zip',''),
                          'cont_name'   : post.get('cont_name',''),
                          'city'        : post.get('city',''),
                          'email'       : user.login,
                          'country_id'  : post.get('Country',False),
                          'state_id'    : post.get('State',''),
                          'location_id' : post.get('Location',''),
                          'top_rmd_opt' : True if post.get('top_rmd_opt') else False, 
                          'customer'    : True,
                          'supplier'    : True,
                          'vat'         : post.get('vat',''),
                          'menu_sc'     : post.get('menu_sc',''),
                          'sc_included' : bool(post.get('sc_included')),
                          'acc_name'    : post.get('acc_name',''),
                          'acc_no'      : post.get('acc_no',''),
                          'chaps'       : post.get('chaps',''),
                          'bank_name'   : post.get('bank_name',''),
                          'iban'        : post.get('iban',''),
                          'swift'       : post.get('swift',''),
                          'sort_code'   : post.get('sort_code',''),
                          'branch_addrs': post.get('branch_addrs',''),
                          }
          img = image_name.read().encode('base64')
          if  img != "":
              partner_vals['image'] = img
          
          partner_obj.write(cr, uid, [partner], partner_vals)
          
          if img == "": 
              if(post.get('type') == 'restaurant'):
                   return request.redirect('/capital_centric/company/restaurant?inv_save=yes');
              if(post.get('type') == 'operator'):
                   return request.redirect('/capital_centric/company/operator?inv_save=yes');


#Request change in Price button in Pricing Menu page
      @http.route(['/capital_centric/request_change_in_price/<int:menu_id>'], type='http', auth="public", website=True, multilang=True)
      def request_change_in_price(self, menu_id=None, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          menu = request.registry.get('cc.menus').browse(cr,uid,menu_id)          
          mail_obj = request.registry.get('mail.mail')
          
          body = reply_to = ''
          if menu:
              for c in menu.partner_id.contact_ids:
                  reply_to = c.email
                  break
              
              body = """<div style="font-family:Calibri; font-size: 12pt; color: rgb(34, 34, 34); background-color: rgb(255, 255, 255); "> 
                        <img src="https://fitforpurposeonline.com/fit_website/static/src/img/fitcclogo.jpg" height="156" width="245">
                        <br/><br/>
                        REQUESTING CHANGE IN PRICE<br/><br/>
                         
                        Account Name: """ + str(menu.partner_id.parent_id and menu.partner_id.parent_id.name or '-') +"""<br/>
                        Restaurant Name: """ + str(menu.partner_id.name or '-') +"""<br/>
                        Menu Name: """ + str(menu.name or '')+"""
                        <br/>Contact Name: """ + str(user.partner_id.name or '-') + """<br/> 
                             Contact Phone: """ + str(user.partner_id.phone or '-') + """ <br/>                             
                             Contact Mobile: """ + str(user.partner_id.mobile or '-') + """<br/>
                             Contact Email: """ + str(user.partner_id.email or '-') + """<br/><br/>
                        <p>Thank you.</p>
                        <p>Regards,<br/>
                           FIT For Purpose Team</p>
                                            
                        <br/><br><div style="width: 375px; height: 20px; margin: 0px; padding: 0px; background-color: #CF7ED7; border-top-left-radius: 5px 5px; border-top-right-radius: 5px 5px; background-repeat: repeat no-repeat;">
            <h3 style="margin: 0px; padding: 2px 14px; font-size: 12px; color: black;">
                <strong style="text-transform:uppercase;">The FIT For Purpose Team</strong></h3>
        </div>
        <div style="width: 347px; margin: 0px; padding: 5px 14px; line-height: 16px; background-color: #F2F2F2;">
            <span style="color: #222; margin-bottom: 5px; display: block; ">
                47 Red Lion Street<br>
                Holborn <br>
                London WC1R 4PF <br>
                United Kingdom<br></span>
                <div style="margin-top: 0px; margin-right: 0px; margin-bottom: 0px; margin-left: 0px; padding-top: 0px; padding-right: 0px; padding-bottom: 0px; padding-left: 0px; ">
    
                </div>
            <p></p>
        </div>
    </div>"""
                 
          mail_id = mail_obj.create(cr, SUPERUSER_ID, {'email_from' : 'fitforpurpose@capitalcentric.co.uk',
                                    'email_to'   : 'fitforpurpose@capitalcentric.co.uk',
                                    'reply_to'   : reply_to,
                                    'subject'    : 'Request change in price',
                                    'body_html'  : body,
                                    'auto_delete': True,})
          if mail_id:
             res = mail_obj.send(cr, uid, [mail_id], False, False, None)    
                       
          return request.redirect("/capital_centric/profile/restaurant/edit_restaurant/"+ str(menu_id)) 
      
      @http.route(['/capital_centric/add_new_contact'], type='http', auth="public", website=True,multilang=True)
      def add_new_contact(self, *args, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          
          parent_id = user.partner_id.id          
          if user.role in ('client_mng','client_user','client_cust','venue_mng','venue_user'):
             parent_id = user.partner_id.parent_id.id 
          
          if post.get('use_parent_address') == 'on':
              use_parent_address = True
          else:
              use_parent_address = False
          
          partner_obj = request.registry.get('res.partner') 
          user_obj = request.registry.get('res.users') 
          
          partner_vals = {
                          'name' : post.get('name',''),
                          'street' : post.get('street',''), 
                          'street2' : post.get('street2',''),
                          'phone' : post.get('phone',''),
                          'mobile' : post.get('mobile',''),
                          'zip' : post.get('zip',''),
                          'cont_name' : post.get('cont_name',''),
                          'city_id' : post.get('city',''),
                          'email' : post.get('email',''),
                          'country_id' : post.get('Country',False),
                          'state_id' : post.get('State',''),
                          'location_id' : post.get('Location',''),
                          'customer':True,
                          'partner_type':'contact',
                          'work_dt_id' : post.get('work_detail'),
                          'type':'contact',
                          'parent_id':parent_id,
                          'cc_fit' : True,
                          'use_parent_address' : use_parent_address,
                          }
          
          if post.get('type') == 'restaurant':
               partner_vals.update({
                                    'supplier':True,
                                    'contact_ids' : post.get('res_cont_selected') and [(6,0,[int(x) for x in post.get('res_cont_selected').split(",")])] or [(6,0,[])],
                                  })          
          
          if post.get('save') == 'activate_user':  
             partner_vals['login'] = post.get('email')
             partner_vals['role']  = post.get('user_role') 
             partner_vals['password'] = post.get('password')
             
             try:
                 user_id = user_obj.create(cr, SUPERUSER_ID,partner_vals)
                 user = user_obj.browse(cr,SUPERUSER_ID ,user_id)
                 partner_id = user.partner_id.id                 
             except:                 
                    cr.rollback()
                    partner_id = partner_obj.create(cr, uid,partner_vals)
                    return request.redirect('/capital_centric/contacts/edit_contact/' + post.get('type')+ '/'+ str(partner_id) + '/?email_error=Someone already has this email.Please Try another!!')
          if post.get('save') in ('save','save_back'):
             if user.is_group:
                 partner_vals.update({
                                      'cc_fit':False,
                                      'cc_group':True,
                                    })
             partner_id = partner_obj.create(cr, uid,partner_vals)
          
          if post.get('save') in ('save','activate_user'):
            if post.get('type') == 'restaurant':
                return request.redirect('/capital_centric/contacts/edit_contact/restaurant/'+ str(partner_id))
            if post.get('type') == 'operator':
                return request.redirect('/capital_centric/contacts/edit_contact/operator/'+ str(partner_id)) 
          else:
            if post.get('type') == 'restaurant':
              return request.redirect('/capital_centric/contacts/restaurant')
            if post.get('type') == 'operator':
              return request.redirect('/capital_centric/contacts/operator')


          
      @http.route(['/capital_centric/edited_contact'], type='http', auth="public", website=True, multilang=True)
      def edited_contact(self, *args, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          partner_obj = request.registry.get('res.partner')
          if post.get('chnge_pswrd'):
             user_obj.write(cr, uid, [int(post.get('user'))],{'password':post.get('password')})
             user = user_obj.browse(cr, uid, int(post.get('user')))
             context = {'create_user':True}
             user_obj.action_reset_password(cr, uid, [user.id], context)
             return request.redirect('/capital_centric/contacts/edit_contact/' + post.get('type') + '/' + str(user.partner_id.id))
          
          if post.get('use_parent_address') == 'on':
              use_parent_address = True
          else:
              use_parent_address = False
          
          partner_vals = {
                          'name' : post.get('name',''),
                          'street' : post.get('street',''),
                          'street2' : post.get('street2',''),
                          'phone' : post.get('phone',''),
                          'mobile' : post.get('mobile',''),
                          'zip' : post.get('zip',''),
                          'cont_name' : post.get('cont_name',''),
                          'email' : post.get('email',''),
                          'country_id' : post.get('Country',False),
                          'state_id' : post.get('State',''),
                          'city_id' : post.get('city',''),
                          'location_id' : post.get('Location',''),
                          'work_dt_id' : post.get('work_detail',''),
                          'use_parent_address' : use_parent_address, 
                          }
            
          if post.get('type') == 'restaurant':
               partner_vals.update({
                                    'contact_ids' : post.get('res_cont_selected') and [(6,0,[int(x) for x in post.get('res_cont_selected').split(",")])] or [(6,0,[])],
                                   })
          if post.get('user_active') == 'checked':
              partner_vals.update({
                                    'role':post.get('user_role')
                                  })
               
          partner_obj.write(cr, uid, [int(post.get('partner_id'))], partner_vals)
          
          user_id = False
          if post.get('save') in ('activate_user','deactivate_user'): 
             user_ids = user_obj.search(cr,uid,['|',('active','=',True),('active','=',False),('partner_id','=',int(post.get('partner_id')))])
             try:
                 if user_ids:                
                    active = True 
                    if post.get('save') == 'deactivate_user':
                       active = False                     
                    user_id = user_obj.write(cr, SUPERUSER_ID, user_ids,{'active':active,'role':post.get('user_role'),'login' : post.get('email')})
                 else:
                    user_id = user_obj.create(cr,SUPERUSER_ID,{'name':post.get('name',''),
                                            'login' : post.get('email'),
                                            'partner_id':int(post.get('partner_id')),
                                            'role':post.get('user_role'),
                                            'password':post.get('password')})
             except:                 
                    cr.rollback()
                    return request.redirect('/capital_centric/contacts/edit_contact/' + post.get('type')+ '/'+ str(post.get('partner_id')) + '/?email_error=Someone already has this email.Please Try another!!')
                   
             
          if post.get('save') in ('save','activate_user','deactivate_user'):              
              return request.redirect('/capital_centric/contacts/edit_contact/' + post.get('type') + '/' + str(post.get('partner_id')))
          else:
              return request.redirect('/capital_centric/contacts/'+post.get('type'))
      
      @http.route(['/capital_centric/contacts/adding_new_contact/<path>'], type='http', auth="public", website=True, multilang=True)
      def adding_contact(self, path, *arg, **post ):
          request.context.update({'editable':False})
          
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          parent_id = user.partner_id.id          
          if user.role in ('client_mng','client_user','client_cust','venue_mng','venue_user'):
             parent_id = user.partner_id.parent_id.id 
          country_obj = request.registry.get('res.country')
          country_ids = country_obj.search(cr, uid, [])
          countries = country_obj.browse(cr, suid,country_ids)

          cc_city_obj = request.registry.get('cc.city')
          city_ids = cc_city_obj.search(cr, uid, [])
          cities   = cc_city_obj.browse(cr, suid, city_ids)
          
          work_obj = request.registry.get('work.detail')
          work_ids = work_obj.search(cr, uid, [])
          works = work_obj.browse(cr, suid,work_ids)
          
          partner_obj = request.registry.get('res.partner')
          venue_ids = partner_obj.search(cr, uid, ['|',('active','=',True),('active','=',False),('parent_id','=',parent_id),('type','=','default'),('partner_type','=','venue')])
          
          values = {'partner_id'    : user.partner_id.id,
                    'country_ids'   : countries,
                    'cities'        : cities,
                    'work_ids'      : works,
                    'type'          : path,
                    'user'          : user,
                    'uid'           : request.registry.get('res.users').browse(cr,uid, uid),
                    'venues'        : partner_obj.browse(cr, uid, venue_ids)
                    }    
      
          return request.website.render("fit_website.add_contact",values)
      
      @http.route(['/capital_centric/contacts/edit_contact/<path>/<int:child_id>/'], type='http', auth="public", website=True, multilang=True)
      def edit_contact(self, path, child_id=None, **post ):  
          request.context.update({'editable':False})
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          states = [] 
          
          loginuid = request.session.uid or request.uid
          user = request.registry.get('res.users').browse(cr,uid,loginuid)
          parent_id = user.partner_id.id          
          if user.role in ('client_mng','client_user','client_cust','venue_mng','venue_user'):
             parent_id = user.partner_id.parent_id.id 
          partner_obj = request.registry.get('res.partner')
          country_obj = request.registry.get('res.country')
          country_ids = country_obj.search(cr, uid, [])
          countries = country_obj.browse(cr, suid,country_ids)

          cc_city_obj = request.registry.get('cc.city')
          city_ids = cc_city_obj.search(cr, uid, [])
          cities   = cc_city_obj.browse(cr, suid, city_ids)
          
          partner = partner_obj.browse(cr, suid, child_id)
          
          state_obj = request.registry.get('res.country.state')
          city_obj = request.registry.get('cc.city')
          location_obj = request.registry.get('cc.location')
          work_obj = request.registry.get('work.detail')
          
          if partner:
              # state_ids = state_obj.search(cr, uid,[('country_id','=', partner.country_id.id)])
              # states =  state_obj.browse(cr,uid,state_ids)
              #
              # city_ids = city_obj.search(cr, uid,[('state_id','=', partner.state_id.id)])
              # cities =  city_obj.browse(cr,uid,city_ids)
              
              location_ids = location_obj.search(cr, uid,[('city_id','=', partner.city_id.id)])
              locations =  location_obj.browse(cr,uid,location_ids)
              
              work_ids = work_obj.search(cr, uid,[])
              works =  work_obj.browse(cr,uid,work_ids) 
              
              res_cont_ids = partner_obj.search(cr, uid,['|',('active','=',True),('active','=',False),('parent_id','=',parent_id),('type','=','default'),('partner_type','=','venue')])
              res_cont = partner_obj.browse(cr,uid,res_cont_ids)
              
              cont_user = request.registry.get('res.users').search(cr,uid,[('partner_id','=',partner.id),('active','in',(True,False,None))])
          
          values = {
                    'country_ids':countries,
                    'partner' : partner,
                    # 'state_ids' : states,
                    'city_ids' : cities,
                    'location_ids' : locations,
                    'work_ids' : works,
                    'record_id' : child_id, 
#                     'login_user' : user,
                    'parent_id' : user.partner_id.id,
                    'type' : path,
                    'user' : user,
                    'uid':request.registry.get('res.users').browse(cr,uid, uid),
                    'cont_user':cont_user and request.registry.get('res.users').browse(cr, uid, cont_user[0]) or False,
                    'res_contact_ids' : [x.id for x in partner.contact_ids],
                    'rest_cont_ids' : res_cont,
                    'res_contacts': ','.join(str(x.id) for x in partner.contact_ids),
                    'email_error':'email_error' in post and post.get('email_error') or ''
                    }
          
          return request.website.render("fit_website.edit_contact",values)
           
      
     
      @http.route(['/capital_centric/profile/restaurant/edit_restaurant/<int:child_id>/<path>'], type='http', auth="public", website=True, multilang=True)
      def edit_restaurant(self, path, child_id=None, **post ):
          request.context.update({'editable':True})
          import time
          start_date = (parser.parse(time.strftime("%Y-%m-%d"))+relativedelta(days=1))
          end_date = (parser.parse(time.strftime("%Y-%m-%d"))+relativedelta(days=90))
          if path == 'menu':
              chk_from_which = 'menu_go_back'
          elif path == 'events':
              chk_from_which = 'events'
          else:
              chk_from_which = 'res_details'
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          states = []
          cities = []
          locations = []
          dinings = []
          cuisines = []
          
          time = user.partner_id.id
                     
          partner_obj = request.registry.get('res.partner')
          partner = partner_obj.browse(cr, suid, child_id)
                    
          country_obj = request.registry.get('res.country')
          country_ids = country_obj.search(cr, uid, [])
          countries = country_obj.browse(cr, suid,country_ids)
          
          
          state_obj = request.registry.get('res.country.state')
          city_obj = request.registry.get('cc.city')
          location_obj = request.registry.get('cc.location')
          partner_obj = request.registry.get('res.partner')
          dining_obj = request.registry.get('cc.dining.style')
          cuisine_obj = request.registry.get('cc.cuisine')
          event_obj = request.registry.get('cc.events')
          
          if partner:
              state_ids = state_obj.search(cr, uid,[('country_id','=', partner.country_id.id)])
              states =  state_obj.browse(cr,uid,state_ids)
              
              partner_contact_ids = partner_obj.search(cr, uid,[('type','=','contact'),('partner_type','=','contact'),('parent_id','=',partner.parent_id.id)])
              partners_inv_contact = partners_contact =  partner_obj.browse(cr,uid,partner_contact_ids)
              
              city_ids = city_obj.search(cr, uid, [])
              cities = city_obj.browse(cr, uid, city_ids)
              
              location_ids = location_obj.search(cr, uid,[('city_id','=', partner.city_id.id)])
              locations =  location_obj.browse(cr,uid,location_ids)
              
              dining_ids = dining_obj.search(cr, uid,[])
              dinings =  dining_obj.browse(cr,uid,dining_ids)
             
              cuisine_ids = cuisine_obj.search(cr, uid,[])
              cuisines =  cuisine_obj.browse(cr,uid,cuisine_ids)
              
          m_domain = [('cc_fit', '=', True)]
          if user.is_group:
             m_domain = [('cc_group', '=', True)] 

          alloc_obj = request.registry.get('cc.time.allocations')
          alloc_ids = alloc_obj.search(cr,uid,[('partner_id','=', child_id)])
          alloc = alloc_obj.browse(cr, suid, alloc_ids)
          
          opening_hrs_obj = request.registry.get('cc.opening.hrs')
          opening_hrs_ids = opening_hrs_obj.search(cr,uid,[('partner_id','=', child_id)])
          opening_hrs     = opening_hrs_obj.browse(cr, suid, opening_hrs_ids)
          
          pvt_rooms_obj = request.registry.get('cc.private.rooms')
          pvt_rooms_ids = pvt_rooms_obj.search(cr,uid,[('partner_id','=', child_id)])
          pvt_rooms     = pvt_rooms_obj.browse(cr, suid, pvt_rooms_ids)
          
          time_obj = request.registry.get('cc.time')
          time_ids = time_obj.search(cr, uid, [])
          times    = time_obj.browse(cr, suid, time_ids)
          
          menu_obj = request.registry.get('cc.menus')
          menu_ids = menu_obj.search(cr,uid, [('partner_id', '=', child_id),('active', 'in', (False,True, None)),('food_type', '=', 'meal')] + m_domain)
          menu     = menu_obj.browse(cr, suid, menu_ids)
          
          black_obj = request.registry.get('cc.black.out.day')
          black_ids = black_obj.search(cr,uid,[('partner_id','=', child_id)])
          black = black_obj.browse(cr, suid, black_ids)
          
          drink_ids = menu_obj.search(cr,uid,[('partner_id','=', child_id),('active','in',(False,True, None)),('food_type','=','drink')] + m_domain)
          drink = menu_obj.browse(cr, suid, drink_ids)
          
          event_menu_ids = menu_obj.search(cr,uid,[('partner_id','=', child_id),('active','in',(False,True, None)),('food_type','=','events')])
          event_menus = menu_obj.browse(cr, suid, event_menu_ids)
          
          event_ids = event_obj.search(cr,uid,[('partner_id','=', child_id),('active','in',(False,True, None))])
          events = event_obj.browse(cr, suid, event_ids)
          sel_emenus = {}
          for e in events:
              sel_emenus[e.id] = [x.id for x in e.menu_ids]
          tstation_obj = request.registry.get('cc.tube.station')
          tstation_ids = tstation_obj.search(cr, uid, [])
          tstation = tstation_obj.browse(cr, suid, tstation_ids)
          
          values = { 'user'                 : user,
                     'child_id'             : child_id,
                     'partner'              : partner,
                     'country_ids'          : countries,
                     'state_ids'            : states,
                     'cities'               : cities,
                     'tstation_ids'         : tstation,
                     'dining_ids'           : dinings,
                     'dining_value_ids'     : [x.id for x in partner.dining_style_ids],
                     'dinings'              : ','.join(str(x.id) for x in partner.dining_style_ids),
                     'cuisine_ids'          : cuisines,
                     'cuisine_value_ids'    : [x.id for x in partner.cuisine_ids],
                     'cuisines'             : ','.join(str(x.id) for x in partner.cuisine_ids),
                     'location_ids'         : locations,
                     'allocations_ids'      : alloc,
                     'opening_hrs_ids'      : opening_hrs,
                     'pvt_rooms_ids'        : pvt_rooms,
                     'black_ids'            : black,
                     'drink_ids'            : drink,
                     'event_menu_ids'       : event_menus,
                     'event_ids'            : events,
                     'time_ids'             : times,
                     'menu_ids'             : menu,
                     'e_menu_ids'           : sel_emenus,
                     'partner_contact_ids'  : partners_contact,
                     'contact_ids'          : [x.id for x in partner.contact_ids],
                     'contacts'             : ','.join(str(x.id) for x in partner.contact_ids),
                     'inv_contacts'         : ','.join(str(x.id) for x in partner.inv_contact_ids),
                     'inv_contact_ids'      : [x.id for x in partner.inv_contact_ids],
                     'chk_from_which'       : chk_from_which,
                     'start_date'           : start_date,
                     'end_date'             : end_date,
                   }
          # if post.get('chk_wch','') == 'duplicate':
          #    values['error_msg'] = 'Menu Duplicated Successfully !!'
          # if post.get('chk_wch','') == 'save':
          #    values['error_msg'] = 'Menu Saved Successfully !!'
          # if post.get('chk_wch','') == 'events':
          #    values['error_msg'] = 'Events Saved Successfully !!'
     
          return request.website.render("fit_website.restaurant_details",values)
       
      
      @http.route(['/fit_website/pricing_json/'], type='json', auth="public", website=True)
      def pricing_json(self, dict_pricing, menu_id,chkwhich,sc_included,service_charge ,sc_disc, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          if chkwhich in ('apply_all','save'):
              pricing_obj = request.registry.get('cc.menu.pricing')
              pricing_ids = pricing_obj.search(cr,uid,[('menu_id','=',menu_id)])
              
              cr.execute("update cc_menus set sc_included =" + str(sc_included) + " ,service_charge =" + str(service_charge or 0) \
                         +" ,sc_disc=" + str(sc_disc) + " where id=" + str(menu_id))
    
          if chkwhich in ('m_apply_all','m_save'):
             pricing_obj = request.registry.get('cc.markup')
             pricing_ids = pricing_obj.search(cr,uid,[('op_markup_id','=',menu_id)])
             
          pricing_vals = context = {}
        
          for case in pricing_obj.browse(cr,uid,pricing_ids):
              if chkwhich == 'apply_all':
                 context['mu_update'] = False 
                 pricing_vals =  {'mon_price':float(dict_pricing[str(case.id)] or 0),
                                  'tue_price':float(dict_pricing[str(case.id)] or 0),
                                  'wed_price':float(dict_pricing[str(case.id)] or 0),
                                  'thu_price':float(dict_pricing[str(case.id)] or 0),
                                  'fri_price':float(dict_pricing[str(case.id)] or 0),
                                  'sat_price':float(dict_pricing[str(case.id)] or 0),
                                  'sun_price':float(dict_pricing[str(case.id)] or 0),                                  
                                  }
              elif chkwhich == 'save':
                  context['mu_update'] = False                   
                  p_dict = dict_pricing[str(case.id)]  
                  pricing_vals = {'mon_price':float(p_dict['monday'] or 0),
                                  'tue_price':float(p_dict['tuesday'] or 0),
                                  'wed_price':float(p_dict['wednesday'] or 0),
                                  'thu_price':float(p_dict['thursday'] or 0),
                                  'fri_price':float(p_dict['friday'] or 0),
                                  'sat_price':float(p_dict['saturday'] or 0),
                                  'sun_price':float(p_dict['sunday'] or 0)
                                  }
              elif chkwhich == 'm_save':
                   pricing_vals =  dict_pricing[str(case.id)]
              
              elif chkwhich == 'm_apply_all':
                   pricing_vals =  {'mon_to_mu':float(dict_pricing[str(case.id)] or 0),
                                    'tue_to_mu':float(dict_pricing[str(case.id)] or 0),
                                    'wed_to_mu':float(dict_pricing[str(case.id)] or 0),
                                    'thu_to_mu':float(dict_pricing[str(case.id)] or 0),
                                    'fri_to_mu':float(dict_pricing[str(case.id)] or 0),
                                    'sat_to_mu':float(dict_pricing[str(case.id)] or 0),
                                    'sun_to_mu':float(dict_pricing[str(case.id)] or 0)
                                   } 
              
              pricing_obj.write(cr,uid,[case.id],pricing_vals,context)    
              if chkwhich in ('apply_all','save'):
                 sc = case.menu_id.service_charge
                 sc_inc = case.menu_id.sc_included
                 sc_disc = case.menu_id.sc_disc
                 m_vals={'mon_ffp_mu':pricing_obj.onchange_pricing(cr, uid, [], 'mon', pricing_vals['mon_price'], case.mon_ffp_mu, sc, sc_inc, sc_disc, context)['value']['mon_ffp_mu'],
                         'tue_ffp_mu':pricing_obj.onchange_pricing(cr, uid, [], 'tue', pricing_vals['tue_price'], case.tue_ffp_mu, sc, sc_inc, sc_disc, context)['value']['tue_ffp_mu'],
                         'wed_ffp_mu':pricing_obj.onchange_pricing(cr, uid, [], 'wed', pricing_vals['wed_price'], case.wed_ffp_mu, sc, sc_inc, sc_disc, context)['value']['wed_ffp_mu'],
                         'thu_ffp_mu':pricing_obj.onchange_pricing(cr, uid, [], 'thu', pricing_vals['thu_price'], case.thu_ffp_mu, sc, sc_inc, sc_disc, context)['value']['thu_ffp_mu'],
                         'fri_ffp_mu':pricing_obj.onchange_pricing(cr, uid, [], 'fri', pricing_vals['fri_price'], case.fri_ffp_mu, sc, sc_inc, sc_disc, context)['value']['fri_ffp_mu'],
                         'sat_ffp_mu':pricing_obj.onchange_pricing(cr, uid, [], 'sat', pricing_vals['sat_price'], case.sat_ffp_mu, sc, sc_inc, sc_disc, context)['value']['sat_ffp_mu'],
                         'sun_ffp_mu':pricing_obj.onchange_pricing(cr, uid, [], 'sun', pricing_vals['sun_price'], case.sun_ffp_mu, sc, sc_inc, sc_disc, context)['value']['sun_ffp_mu'],} 
                 pricing_obj.write(cr,uid,[case.id],m_vals,context)
          return
      
      @http.route(['/capital_centric/edit_res'], type='http', auth="public", website=True, multilang=True)
      def edit_res(self, *arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context

          partner_obj = request.registry.get('res.partner')
             
          if post.get('active') == 'on':
              active = True
          else:
              active = False
              
          if post.get('use_parent_address') == 'on':
              use_parent_address = True
          else:
              use_parent_address = False
          partner_vals = {
                          'name'            : post.get('name'),
                          'street'          : post.get('street'),
                          'street2'         : post.get('street2'),
                          'city_id'         : post.get('city'),
                          'zip'             : post.get('zip'),
                          'country_id'      : post.get('Country',False),
                          'state_id'        : post.get('State',False),
                          'location_id'     : post.get('Location',False), 
                          'menu_sc'         : post.get('menu_sc',''),
                          'sc_included'     : bool(post.get('sc_included')),
                          'tstation_id'     : post.get('tstation',''),
                          'contact_ids'     : post.get('cont_selected') and [(6,0,[int(x) for x in post.get('cont_selected').split(",")])] or [(6,0,[])],
                          'inv_contact_ids' : post.get('inv_selected') and [(6,0,[int(x) for x in post.get('inv_selected').split(",")])] or [(6,0,[])],
                          'email'           : post.get('email',''),
                          'phone'           : post.get('phone',''),
                          'mobile'          : post.get('mobile',''),
                          'cuisine_ids'     : post.get('cuisine_selected') and [(6,0,[int(x) for x in post.get('cuisine_selected').split(",")])] or [(6,0,[])],
                          'descp_venue'     : post.get('descp_venue',''), 
                          'dining_style_ids': post.get('dining_selected') and [(6,0,[int(x) for x in post.get('dining_selected').split(",")])] or [(6,0,[])], 
                          'payment_opt'     : post.get('payment_opt',''),
                          'parking'         : post.get('parking',''),
                          'rest_directions' : post.get('rest_directions',''),
                          'features'        : post.get('features',''),
                          'main_covers'     : post.get('main_covers',''),
                          'room_covers'     : post.get('room_covers',''),
                          'semi_covers'     : post.get('semi_covers',''),
                          'private_rooms'   : post.get('private_rooms',''),
                          'cancel_policy'   : post.get('cancel_policy',''),
                          'terms_conditions': post.get('terms_conditions',''),
                          'dress_code'      : post.get('dress_code',''),
                          'latitude'        : post.get('latitude',''),
                          'longitude'       : post.get('longitude',''),
                          'additnal_details': post.get('additnal_details',''),
                          'max_covers'      : post.get('maximum_covers',''),
                          'no_of_covers'    : post.get('no_of_covers',''),
                          'use_parent_address' : use_parent_address,
                        }
          if post.get('use_menu'):
              partner_vals.update({'is_default' : True,'parent_res_id' : post.get('parent_res')})
          else:
              partner_vals.update({'is_default' : False,'parent_res_id' : False})

          if post.get('save')=='deactivate_restaurant':
              partner_vals.update({'active' : False})

          partner = partner_obj.write(cr, request.uid, [int(post.get('partner_id'))], partner_vals)
          if post.get('save') == 'save':
              return
          else:
              return request.redirect('/capital_centric/restaurant');
          

      @http.route(['/capital_centric/add_res'], type='http', auth="public", website=True, multilang=True)
      def add_res(self, *arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
           
          partner_obj = request.registry.get('res.partner')
          country_obj = request.registry.get('res.country')
          state_obj = request.registry.get('res.country.state')
          
          state_ids = state_obj.search(cr, uid, [('name','=', post.get('State')),('country_id.name','=', post.get('Country'))])         
          country_ids = country_obj.search(cr, uid, [('name','=', post.get('Country'))])          
          partner_contact_ids = partner_obj.search(cr, uid, [('name','=', post.get('cont_name'))])
          partner_inv_contact_ids = partner_obj.search(cr, uid, [('name','=', post.get('inv_cont_name'))])
          

          cc_fit = True
          if user.is_group:
              cc_fit = False
          
          if post.get('active') == 'on': 
              active = True
          else:
              active = False
              
          if post.get('use_parent_address') == 'on':
              use_parent_address = True
          else:
              use_parent_address = False
         
          partner_vals = {
                          'name'            : post.get('name',''),
                          'street'          : post.get('street',''),
                          'street2'         : post.get('street2',''),
                          'city_id'         : post.get('city',''),
                          'zip'             : post.get('zip',''),
                          'country_id'      : post.get('Country',''),
                          'state_id'        : post.get('State',''),
                          'tstation_id'     : post.get('tstation',''),
                          'contact_ids'     : post.get('cont_selected') and [(6,0,[int(x) for x in post.get('cont_selected').split(",")])] or [(6,0,[])],
                          'inv_contact_ids' : post.get('inv_selected') and [(6,0,[int(x) for x in post.get('inv_selected').split(",")])] or [(6,0,[])],
                          'email'           : post.get('email',''),
                          'phone'           : post.get('phone',''),
                          'mobile'          : post.get('mobile',''),
                          'menu_sc'         : post.get('menu_sc',''),
                          'sc_included'     : bool(post.get('sc_included')),
                          'active'          : False,    
                          'type'            : 'default',   
                          'cc_fit'          : cc_fit,
                          'cc_group'        : user.is_group,
                          'parent_id'       : post.get('partner_id'),      
                          'customer'        : True,  
                          'supplier'        : True,
                          'partner_type'    :'venue',
                          'cuisine_ids'     : post.get('cuisine_selected') and [(6,0,[int(x) for x in post.get('cuisine_selected').split(",")])] or [(6,0,[])],
                          'descp_venue'     : post.get('descp_venue',''), 
                          'dining_style_ids': post.get('dining_selected') and [(6,0,[int(x) for x in post.get('dining_selected').split(",")])] or [(6,0,[])], 
                          'payment_opt'     : post.get('payment_opt',''),
                          'parking'         : post.get('parking',''),
                          'rest_directions' : post.get('rest_directions',''),
                          'features'        : post.get('features',''),
                          'main_covers'     : post.get('main_covers',''),
                          'room_covers'     : post.get('room_covers',''),
                          'semi_covers'     : post.get('semi_covers',''),
                          'private_rooms'   : post.get('private_rooms',''),
                          'cancel_policy'   : post.get('cancel_policy',''),
                          'terms_conditions': post.get('terms_conditions',''),
                          'dress_code'      : post.get('dress_code',''),
                          'max_covers'      : post.get('maximum_covers',''),
                          'no_of_covers'    : post.get('no_of_covers',''),
                          'longitude'       : post.get('longitude',''),
                          'latitude'        : post.get('latitude',''),
                          'additnal_details': post.get('additnal_details',''),
                          'use_parent_address' : use_parent_address,
                        }
          if post.get('parent_res'):
              partner_vals.update({'is_default' : True,'parent_res_id' : post.get('parent_res')})
          
          partner_id = partner_obj.create(cr, uid,partner_vals,{'default_cc_fit':True,'default_partner_type':'venue'})
          
          if post.get('save') == 'save':
               return request.redirect('/capital_centric/profile/restaurant/edit_restaurant/'+str(partner_id)+'/res')
          else:              
               return request.redirect('/capital_centric/restaurant')
      
      @http.route(['/capital_centric/profile/restaurant/add_restaurant'], type='http', auth="public", website=True, multilang=True)
      def add_restaurant(self, *arg, **post ):
          request.context.update({'editable':False})
          
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          parent_id = user.partner_id.id
          if user.role != 'venue':
             parent_id = user.partner_id.parent_id.id

          city_obj = request.registry.get('cc.city')
          city_ids = city_obj.search(cr, uid, [])
          cities = city_obj.browse(cr, uid, city_ids)

          country_obj = request.registry.get('res.country')
          country_ids = country_obj.search(cr, uid, [])
          countries = country_obj.browse(cr, suid,country_ids)
          
          dining_obj = request.registry.get('cc.dining.style')
          dining_ids = dining_obj.search(cr, uid, [])
          dinings = dining_obj.browse(cr, suid, dining_ids)
          
          cuisine_obj = request.registry.get('cc.cuisine')
          cuisine_ids = cuisine_obj.search(cr, uid, [])
          cuisines = cuisine_obj.browse(cr, suid, cuisine_ids)
          
          tstation_obj = request.registry.get('cc.tube.station')
          tstation_ids = tstation_obj.search(cr, uid, [])
          tstation = tstation_obj.browse(cr, suid, tstation_ids)
          
          partner_obj = request.registry.get('res.partner')
          partner_contact_ids = partner_obj.search(cr, uid, [('type','=','contact'),('partner_type','=','contact'),('parent_id','=',parent_id)])
          partners_contact = partner_obj.browse(cr, suid,partner_contact_ids)
         
          values = {
                      'partner_id'          : parent_id,
                      'user'                : user,
                      'country_ids'         : countries,
                      'dining_ids'          : dinings,
                      'cuisine_ids'         : cuisines,
                      'tstation_ids'        : tstation,
                      'partner_contact_ids' : partners_contact,
                      'chk_from_which'      : 'res_details',
                      'cities'              : cities
                    }
      
          return request.website.render("fit_website.add_restaurant",values)
      
#For Time And Allocations Tab
      @http.route(['/fit_website/time/'], type='json', auth="public", website=True)
      def time(self, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          time_obj = request.registry.get('cc.time')
          time_ids = time_obj.search(cr, uid, [])
          times = time_obj.browse(cr, suid, time_ids)
          
          time = []
          for t in times:
            time.append(t.name) 
             
          return time,time_ids
      
#For Time And Allocations Tab Events Menu Sub tab
      @http.route(['/fit_website/events_menu/'], type='json', auth="public", website=True)
      def events_menu(self, partner_id, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          
          menu_obj = request.registry.get('cc.menus')
          event_menu_ids = menu_obj.search(cr,uid,[('partner_id','=',partner_id),('food_type','=','events')])
          event_menus = menu_obj.browse(cr, suid, event_menu_ids)
          
          event_menu = []
          for t in event_menus:
            event_menu.append(t.name) 
          
          return event_menu,event_menu_ids
      
#Apply all() for time&allocations
      @http.route(['/fit_website/existing_alloc_record/'], type='json', auth="public", website=True)
      def existing_alloc_record(self , value, type, db_id, partner_id, name, std_frm_id, std_to_id, covers, cap, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
         
          alloc_obj = request.registry.get('cc.time.allocations')
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          domain = [('partner_id','=',partner_id),('type','=',type)]
          alloc_vals = {
                        'name'          : name,
                        # 'non_frm_id'    : non_frm_id,
                        # 'non_to_id'     : non_to_id,
                        'std_frm_id'    : std_frm_id,
                        'std_to_id'     : std_to_id,
                        # 'pre_frm_id'    : pre_frm_id,
                        # 'pre_to_id'     : pre_to_id,
                        'covers'        : covers,
                        'cap'           : cap
                       }
          if user.is_group:
              alloc_obj = request.registry.get('cc.opening.hrs')
              domain = [('partner_id','=',partner_id)]
              alloc_vals = {
                            'name'          : name,
                            'bf_from'       : non_frm_id,
                            'bf_to'         : non_to_id,
                            'lunch_from'    : std_frm_id,
                            'lunch_to'      : std_to_id,
                            'dinner_from'   : pre_frm_id,
                            'dinner_to'     : pre_to_id,
                           }
          if value == 'existing':
             alloc_obj.write(cr, uid, [db_id], alloc_vals)
          
          if db_id  == 'false':
             alloc_vals.update({
                                'partner_id' : partner_id,
                                'type' : type                 
                                })
             db_id = alloc_obj.create(cr, uid, alloc_vals)
                 
          if value == 'apply':
              del alloc_vals['name']
              alloc_ids = alloc_obj.search(cr,uid,domain)
              alloc = alloc_obj.write(cr, uid, alloc_ids, alloc_vals)
              
          return db_id


#Save() for all one2many objects
      @http.route(['/fit_website/save_time_rec/'], type='json', auth="public", website=True)
      def save_time_rec(self , dict_time, type, venue_id,create_count, chkwhich, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid, uid)
          operator_id = user.partner_id.id or 0
          if user and user.role in ('client_user','client_mng'):
             operator_id = user.partner_id and user.partner_id.parent_id.id or 0
          
          domain=[]          
          
          if chkwhich == 'allocations':
             main_obj = request.registry.get('cc.time.allocations')
             domain = [('partner_id','=',venue_id),('type','=',type)]
             if user.is_group:
                 main_obj = request.registry.get('cc.opening.hrs')
                 domain = [('partner_id','=',venue_id)]
          elif chkwhich == 'private_room':
             main_obj = request.registry.get('cc.private.rooms')
             domain = [('partner_id','=',venue_id)]
          elif chkwhich == 'black_out':
             main_obj = request.registry.get('cc.black.out.day')
             domain = [('partner_id','=',venue_id)]
          elif chkwhich == 'drinks':
             main_obj = request.registry.get('cc.menus')
             domain = [('partner_id','=',venue_id),('food_type','=','drink'),('active','in',(False,True, None))]
          elif chkwhich == 'events_menu':
             main_obj = request.registry.get('cc.menus')
             domain = [('partner_id','=',venue_id),('food_type','=','events'),('active','in',(False,True, None))]
          elif chkwhich == 'events':
             main_obj = request.registry.get('cc.events')
             domain = [('partner_id','=',venue_id),('active','in',(False,True, None))]
          elif chkwhich == 'menu':
             main_obj = request.registry.get('cc.menus')
             domain = [('partner_id','=',venue_id),('active','in',(False,True, None)),('food_type','=','meal')]
          elif chkwhich == 'markup':
             main_obj = request.registry.get('cc.operator.markup')
             domain = [('partner_id','=',operator_id)]
             cr.execute("update res_partner set markup_perc =" + str(venue_id) + " where id=" + str(operator_id))
          
          main_ids = main_obj.search(cr,1,domain)
          
          for m in main_ids:
              vals = dict_time.get(str(m),{})
              if not vals:                 
                 continue
              del dict_time[str(m)]
              if chkwhich in ('menu','drinks','events_menu') or user.is_group:
                 context = {'mu_update':False}       
                 # if vals['sc_included'] == 'False':
                 #    vals['sc_included'] = False
                 #    vals['sc_disc'] = True
                 # else:
                 #    vals['sc_included'] = True
                 #    vals['sc_disc'] = False
                 vals['markup'] = main_obj.get_tourop_price(cr, uid, [], vals['food_type'],float(vals['rest_price']), 0, 0, False, vals.get('sc_disc',False), context)['value']['markup']
                 if user.is_group and chkwhich == 'meal':#Remove sc included, sc_disc, sc when its group menu 
                    del  vals['sc_included']
                    del  vals['sc_disc']
                    del  vals['service_charge']
              elif chkwhich in ('events','markup'):        
                   menu_ids  = vals.get('menu_ids','[]')
                   vals['menu_ids'] = [(6,0,eval(menu_ids))]               
              main_obj.write(cr,uid,[m],vals)
              
          if create_count > 1:
             for cnt in range(1,create_count):
                 vals = dict_time[str('create_'+str(cnt))]
                 vals.update({'partner_id':venue_id,
                              'cc_fit' : True})
                 if user.is_group:
                     vals.update({'cc_group' : True,
                                  'cc_fit' : False,})
                 if chkwhich in ('menu','drinks','events_menu') or user.is_group:
                    context = {'mu_update':False} 
                    # if vals['sc_included'] == 'False':
                    #    vals['sc_included'] = False
                    #    vals['sc_disc'] = True
                    # else:
                    #    vals['sc_included'] = True
                    #    vals['sc_disc'] = False
                    # if user.is_group and chkwhich == 'meal':#Remove sc included, sc_disc, sc when its group menu
                    #    del  vals['sc_included']
                    #    del  vals['sc_disc']
                    #    del  vals['service_charge']
                    vals['markup'] = main_obj.get_tourop_price(cr, uid, [], vals['food_type'],float(vals['rest_price']), 0, 0, False, False, context)['value']['markup']
                 elif chkwhich in ('events','markup'):  
                         menu_ids  = vals.get('menu_ids','[]')
                         vals['menu_ids'] = [(6,0,eval(menu_ids))]
                         if chkwhich == 'markup':
                             vals['partner_id'] = operator_id
                 main_id = main_obj.create(cr,uid,vals)
                 dict_time[str('create_'+str(cnt))] = main_id
                 
          return dict_time
      
             
      @http.route(['/fit_website/existing_menu_record/'], type='json', auth="public", website=True)
      def existing_menu_record(self , partner_id, db_id, dict_menu, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')  
          user = user_obj.browse(cr,uid,loginuid)
          menu_ids = {}
          menu_obj = request.registry.get('cc.menus')
          count=2
          if db_id != 'create_1':
             menu_obj.write(cr, uid, [int(db_id)], dict_menu)             
          else:
             count=3 

          for cnt in range(1,count):
             dict_menu.update({
                               'partner_id' : partner_id,
                               'cc_fit' : True,              
                               })
             if user.is_group:
                 dict_menu.update({
                               'partner_id' : partner_id,
                               'cc_fit' : False,
                               'cc_group' : True,
                               })
             menu_id = menu_obj.create(cr,uid, dict_menu)
             menu_ids[str('create_'+str(cnt))] = menu_id
           
          return menu_ids    
          
          
      @http.route(['/capital_centric/profile/restaurant/edit_restaurant/menu','/capital_centric/profile/restaurant/edit_restaurant/<path>'], type='http', auth="public", website=True, multilang=True)
      def menu(self, path=None,**post ):
          request.context.update({'editable':False})
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')
          partner_obj = request.registry.get('res.partner')
          user = user_obj.browse(cr,uid,loginuid)

          menu_pricing_obj = request.registry.get('cc.menu.pricing')
          menu_obj = request.registry.get('cc.menus')
          menus_id = menu_pricing = menu = False
          
          if post.get('active') == "True":
                 active = True
          else: 
                 active = False
                 
          cc_fit = True
          cc_group = False,
          if user.is_group:
                cc_group = True,
                cc_fit = False,
          if post.get('parent_res'):
              partner_obj.write(cr,uid,[int(post.get('partner_id'))],{'parent_res_id':post.get('parent_res')})

          if not post.get('menu_id') and not post.get('parent_res'):
             if path == None:
                 menus_id = menu_obj.create(cr,uid,{
                                                       'partner_id':post.get('partner_id'),
                                                       'name':post.get('menu_name'),
                                                       'description':post.get('menu_desc'),
                                                       'active': active,
                                                       'min_covers':post.get('min_covers'),
                                                       'break_fast':post.get('break_fast')=='on' and True or False,
                                                       'lunch':post.get('lunch')=='on' and True or False,
                                                       'afternoon_tea':post.get('afternoon_tea')=='on' and True or False,
                                                       'dinner':post.get('dinner')=='on' and True or False,
                                                       'course':post.get('course'),
                                                       'food_type':'meal',
                                                       'cc_group' : cc_group,
                                                       'cc_fit' : cc_fit,
                                                       'rest_price' : post.get('rest_price'),
                                                       'start_date' : post.get('start_date'),
                                                       'end_date' : post.get('end_date'),
                                                   })
          
          if post.get('menu_id'):
                menu_obj.write(cr,uid,[int(post.get('menu_id'))],{
                                                                   'partner_id':post.get('partner_id'),
                                                                   'name':post.get('menu_name'),
                                                                   'description':post.get('menu_desc'),
                                                                   'active': active,
                                                                   'min_covers':post.get('min_covers'),
                                                                   'break_fast':post.get('break_fast')=='on' and True or False,
                                                                   'lunch':post.get('lunch')=='on' and True or False,
                                                                   'afternoon_tea':post.get('afternoon_tea')=='on' and True or False,
                                                                   'dinner':post.get('dinner')=='on' and True or False,
                                                                   'course':post.get('course'),
                                                                   'rest_price' : post.get('rest_price'),
                                                                   'start_date' : post.get('start_date'),
                                                                   'end_date' : post.get('end_date')
                                                               })
          if menus_id or post.get('menu_id'):
              menu_id = menus_id or post.get('menu_id') or path
              menu = menu_obj.browse(cr,uid,int(menu_id))
              menu_pricing_ids = menu_pricing_obj.search(cr, uid, [('menu_id','=',int(menu_id))])
              menu_pricing =  menu_pricing_obj.browse(cr,uid,menu_pricing_ids)
          
          values = {
#                       'login_user' : user,
                      'menu_pricing_ids' : menu_pricing,
                      'menu' : menu,
                      'user':user
                   }
          if path != None:
              values['error'] = 'Your request has been sent'
          
          return request.website.render("fit_website.menu_individual",values)
      
#BLACKOUT TAB
      @http.route(['/fit_website/blackout_json/'], type='json', auth="public", website=True)
      def blackout_json(self ,value, partner_id, db_id, black_from_time,black_to_time, date, name, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          black_obj = request.registry.get('cc.black.out.day')
          
          black_vals = {
                             'name' : name,
                             'date' : date,
                             'from_time_id' : black_from_time,
                             'to_time_id' : black_to_time,
                        }
          if value == "existing":
              black_obj.write(cr, uid, [db_id], black_vals)
              
          if db_id == "false":
              black_vals.update({
                                'partner_id' : partner_id,
                                })
              db_id = black_obj.create(cr, uid, black_vals)
          return db_id    
      


#For Deletion Of records in Contacts & Restaurants,Time & Allocations,Menu,Black-Out
      @http.route(['/fit_website/delete_records/'], type='json', auth="public", website=True)
      def delete_records(self ,db_id, value, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          
          if(value == 'allocations_table'):
             allocations_obj = request.registry.get('cc.time.allocations')  
             allocations_obj.unlink(cr, uid, [db_id])
             
          if(value == 'opening_hrs_table'):
             opening_obj = request.registry.get('cc.opening.hrs')  
             opening_obj.unlink(cr, uid, [db_id])
             
          if(value == 'private_room_table'):
             private_room_obj = request.registry.get('cc.private.rooms')  
             private_room_obj.unlink(cr, uid, [db_id])
             
          if(value == 'menus_table'):
             menu_obj = request.registry.get('cc.menus') 
             pricing_obj = request.registry.get('cc.menu.pricing')
             pricing_ids = pricing_obj.search(cr, uid, [('menu_id','=',db_id)])
             pricing_obj.unlink(cr, uid, pricing_ids) 
             menu_obj.unlink(cr, uid, [db_id])
          
          if(value == 'black_out_table'):
             black_obj = request.registry.get('cc.black.out.day')  
             black_obj.unlink(cr, uid, [db_id])

          if(value == 'events_table'):
             events_obj = request.registry.get('cc.events')  
             events_obj.unlink(cr, uid, [db_id])
          
          if(value == 'markup_table'):
             markup_obj = request.registry.get('cc.operator.markup')  
             markup_obj.unlink(cr, uid, [db_id]) 
             
          if(value == 'partner_table'):
             partner_obj = request.registry.get('res.partner')
             user_obj = request.registry.get('res.users')
             info_obj = request.registry.get('cc.send.rest.info')
             partner = partner_obj.browse(cr, uid, [db_id])
             if partner[0].type == "contact": 
                 user_id = user_obj.search(cr,uid,['|',('active','=',True),('active','=',False),('partner_id','=',int(db_id))])
                 if user_id:
                     return "contact"
                 
                 cr.execute("""select (case when sum(a.count) > 0 then True else False end ) as  check                                
                               from 
                                  (select count(partner_id) as count from book_part_rel where booking_id = """ +str(db_id)+"""                                
                                   union all                                 
                                   select count(partner_id) as count from inv_part_rel where invoice_id = """ +str(db_id) +"""
                                  )a""")
                 
                 is_contacts = cr.fetchone()
                 
                 if is_contacts and is_contacts[0] : 
                     return "contact"
             elif partner[0].type == "default":
                 info_ids = info_obj.search(cr,uid,[('restaurant_id','=',db_id)])
                 if info_ids : 
                     return "restaurant"
                    
             partner_obj.unlink(cr, uid, [db_id],context=None)
             
          if(value == 'lead_table'):
             info_obj = request.registry.get('cc.send.rest.info')
             lead_obj = request.registry.get('crm.lead')  
             stage_obj = request.registry.get('crm.case.stage')
             stage_id = stage_obj.search(cr, uid, [('name','=','Lost'),('type','=','both')])
             info = info_obj.browse(cr, uid, db_id)
             if stage_id:
                lead_obj.write(cr, uid, [info.lead_id.id],{'stage_id':stage_id[0]})
             return "/capital_centric/operator/my_cart" 
             
          return

      
      
#       -------------------------------
#               TOUR OPERATORS    
#       -------------------------------

#Tour Operator Login Link
#       TO DO:Remove this function and point to page function
#       Action : onclick logo go to home page 
      @http.route(['/capital_centric/operator_login'], type='http', auth="public", website= True, multilang=True)
      def operator_login(self,*arg, **post ):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False}) 
        partner_obj = request.registry.get('res.partner')
        recent_venues_ids = partner_obj.search(cr, SUPERUSER_ID, [('type','=','default'),('partner_type','=','venue')])
        #this will 5 random venues
        recent_venues_ids = recent_venues_ids[shuffle(recent_venues_ids):6]
        recent_venues = partner_obj.browse(cr,SUPERUSER_ID,recent_venues_ids)
        
        values = {
                  'recent_venues' : recent_venues,
                 }
        
        return request.website.render("website.homepage",values)      

      #WestField Search 
      @http.route(['/capital_centric/fit/<path>'], type='http', auth="public", website=True, multilang=True)
      def westfield_search(self, path, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          request.context.update({'editable':False})
          loginuid = request.session.uid or request.uid
          if post is None:post={}  
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,loginuid)
          res_str = ''
          if user.role in ('venue','venue_user','venue_mng'):
              return request.redirect("/capital_centric/restaurant/bookings")

          cr.execute(""" select distinct (p.city_id) as id
                           , cc.name
                           , cc.sequence
                           from res_partner p
                           inner join cc_city cc on cc.id = p.city_id
                           where p.partner_type = 'venue' and p.is_company is False and p.active is True order by cc.sequence, cc.name"""
                    )
          city_obj = request.registry.get('cc.city')
          city_ids = [x[0] for x in cr.fetchall()]
          city_browse = city_obj.browse(cr, uid, city_ids)

          if post.get('res_id'):
              res_str = """ and rp.id = """+str(post.get('res_id'))
          if post.get('utm_source') and post.get('utm_campaign'):
             request.httprequest.session['referral_link'] = 'http://'+post.get('utm_source','')+'/'+post.get('utm_campaign','')

          _logger.error('Refferal Link: %s',request.httprequest.session.get('referral_link'))
          if user.name == 'Public user':
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',user.cc_url)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)

          print "user.id,uid",user.id,uid
          print "website_session_id",request.httprequest.session.get('website_session_id')
          if user.id != uid:   
             if not request.httprequest.session.get('website_session_id'):
                request.httprequest.session['website_session_id'] = str(uuid.uuid4())
          menu_obj = request.registry.get('cc.menus')
          operator = user.partner_id or False
          
          if user.role != 'client':
             operator = user.partner_id.parent_id or user.partner_id

          partner_ids = []
          markup_thr = []
          main_obj = request.registry.get('res.partner')
          selc_cuisine = selc_dining = category_ids = [] 
          min_p = float(post.get('min_p') or 0.00)
          max_p = float(post.get('max_p') or 0.00)
          
          categ_obj   = request.registry.get('res.partner.category')
          cuisine_obj = request.registry.get('cc.cuisine') 
          
          cr.execute("""select distinct(cc.id) ,cc.name
                        from cuisine_part_rel cr 
                        inner join res_partner rp on rp.id = cr.partner_id 
                        inner join cc_cuisine cc on cc.id = cr.cuisine_id 
                        where rp.active = True 
                        order by cc.name""")
          cuisine_rec = cuisine_obj.browse(cr, suid, [i[0] for i in cr.fetchall()])
        
          dining_obj = request.registry.get('cc.dining.style')
          cr.execute("""select distinct(dining_id),cd.name 
                        from dining_part_rel dr 
                        inner join res_partner rp on rp.id = dr.partner_id
                        inner join cc_dining_style cd on cd.id = dr.dining_id 
                        where rp.active = True order by cd.name""")
          dining_rec = dining_obj.browse(cr, suid, [j[0] for j in cr.fetchall()])
          
          tstation_obj = request.registry.get('cc.tube.station')
          cr.execute("select distinct(tstation_id), (select name from cc_tube_station where id = tstation_id) as tstation_name from res_partner where tstation_id is not null and active = True order by (select name from cc_tube_station where id = tstation_id)")
          tstation = tstation_obj.browse(cr, suid, [k['tstation_id'] for k in cr.dictfetchall()])
          sqlstr= ''
          
          if post.get('lead_id'):#Will get this key when it is directed from booking list page(Make a booking)
             request.registry.get('res.users').write(cr, suid, [uid], {'prev_booking_id':post.get('lead_id')})
               
          if post.get('post_code'):
             sqlstr += """ and lower(rp.zip) ilike '""" + str(post.get('post_code')) + """%'"""
         
          if post.get('cuisine_selected') or post.get('cuisine'):
             cuisine = post.get('cuisine_selected')
             if isinstance(eval(cuisine),int):
                sqlstr += """ and c.cuisine_id = """ + str(cuisine)
                selc_cuisine = [eval(cuisine)]                
             else:    
                sqlstr += """ and c.cuisine_id in """ + str(eval(cuisine))
                selc_cuisine = list(eval(cuisine))
       
       
          if post.get('dining_selected') or post.get('dining_style'):
             dining = post.get('dining_selected')
             if isinstance(eval(dining),int):
                sqlstr += """ and d.dining_id = """ + str(dining)
                selc_dining = [eval(dining)] 
             else:    
                sqlstr += """ and d.dining_id in """ + str(eval(dining))
                selc_dining = list(eval(dining))
          
          if post.get('tstation') or post.get('tube_station'):
             sqlstr += """ and rp.tstation_id = """ + str(post.get('tstation')) 
       
          if post.get('rest_name') or post.get('name'):
             restname = str(post.get('rest_name'))
             restname = restname.replace("'","''") 
             sqlstr += """ and rp.name ilike '%""" + restname + """%'""" 
          
          if post.get('table_size'):
             t_query = {'10 and under' : ' and rp.max_covers  <= 10',
                        '11 - 20' : ' and rp.max_covers between 11 and 20',
                        'Over 20' : ' and rp.max_covers > 20'}
             sqlstr += t_query[post.get('table_size')]  
          
          if post.get('rest_add') or post.get('address'):
             restadd = str(post.get('rest_add'))
             restadd = restadd.replace("'","''") 
             sqlstr += """ and (street ilike '%""" + restadd + """%' or 
                          street2 ilike '%""" + restadd + """%' or 
                          city ilike '%""" + restadd + """%' or
                          rp.state_id in (select id from res_country_state where name ilike '%""" + restadd + """%') or 
                          rp.country_id in (select id from res_country where name ilike '%""" + restadd + """%')) """
    
          if post.get('rest_letter') and post.get('rest_letter') != 'others' and path != 'events':
             sqlstr += """ and rp.name ilike '""" + chr(int(post.get('rest_letter'))) + """%'""" 
        
          if post.get('rest_letter','') == 'others' and path != 'events':
             sqlstr += """ and rp.name ~ '^[0-9]'"""
             
          if post.get('kids_menu'):
             sqlstr += """ and rp.id in (select partner_id from cc_menus where kids_menu = True) """ 
          
          if not user.is_group:
              sqlstr += """ and rp.max_covers > 0 and rp.cc_fit = True """ 
              cnt_str = """sum(cta.covers) > 0 and (select count(id) from cc_menus where cc_fit = True and partner_id = rp.id
                                                    and id not in (select menu_id from menu_top_hide_rel where top_id = """ + str(operator and operator.id or 0) + """)
                                                    and id not in (select menu_id from menu_top_show_rel where top_id != """ + str(operator and operator.id or 0) + """)) > 0"""
              
          if user.is_group:
             sqlstr += """ and rp.no_of_covers > 0 and rp.cc_group = True """ 
             cnt_str = '(select count(id) from cc_menus where cc_group = True and partner_id = rp.id) > 0'
             
          if user.role in ('client_user','client_cust'):
              sqlstr += """ and rp.id not in (select booking_id from book_part_rel where partner_id = """ + str(operator.id) + """)""" 

          search_str = case_str = avltime_str = ''
          if post.get('type') and post.get('type') != 'all':
              search_str = search_str + """ and cta.type    = '""" + post.get('type') + """'"""
              case_str   = case_str + """   and (case when '""" + post.get('type') + """' = 'break_fast' then cm.break_fast = True
                                            else case when '""" + post.get('type') + """' = 'lunch' then cm.lunch=True
                                            else case when '""" + post.get('type') + """' = 'at' then cm.afternoon_tea=True
                                            else case when '""" + post.get('type') + """' = 'dinner' then cm.dinner=True end end end end)"""
          if post.get('location_id') and post.get('location_id') != 'all':
              search_str = search_str + """ and rp.city_id = """ + str(post.get('location_id'))
          if post.get('resv_date') or post.get('booking_date'):
              search_str = search_str + """ and cta.name    = '""" + datetime.strptime((post.get('resv_date') or post.get('booking_date')),'%d/%m/%Y').strftime('%A').lower() + """'"""
          if post.get('restaurant_ID'):
              search_str = search_str + """ and rp.id = """ + post.get('restaurant_ID')
          if post.get('called_frm') == 'get_restaurants' and post.get('booking_time'):
             avltime_str = """ and name = '""" + post.get('booking_time') +"""' """

          #Get Active Restaurants based on Partner Tags
          if path in ('westfield_search','greenwich_search'):
             tags = {'westfield_search':[('parent_id.name','=','Westfield')],'greenwich_search':[('name','=','Greenwich')]}
             category_ids = categ_obj.search(cr,uid,tags[path])
             selc_categ = post.get('City_westfield') or category_ids
             if post.get('City_westfield') or len(category_ids) == 1 :
                sqlstr += """ and rpc.category_id = """ + str(post.get('City_westfield') or category_ids[0])
             elif len(category_ids) > 1:    
                sqlstr += """ and rpc.category_id in """ + str(tuple(category_ids))
             cr.execute("""select distinct(rp.id),rp.name from res_partner rp
                          inner join res_partner_res_partner_category_rel rpc on rp.id = rpc.partner_id 
                          inner join cc_time_allocations cta on cta.partner_id = rp.id 
                          left outer join cuisine_part_rel c on c.partner_id = rp.id
                          left outer join dining_part_rel d on d.partner_id = rp.id
                          where rp.active=True 
                          and rp.partner_type='venue'                           
                          and rp.type = 'default' """ + sqlstr + """ 
                          group by rp.id
                          having """ + cnt_str + """    
                          order by rp.name""")
             partner = cr.fetchall()
          
          #Get Active Restaurants
          else:
             cr.execute("""select distinct(rp.id),rp.name from res_partner rp  
                          left outer join cc_time_allocations cta on cta.partner_id = rp.id
                          left outer join cuisine_part_rel c on c.partner_id = rp.id
                          left outer join dining_part_rel d on d.partner_id = rp.id                         
                          where rp.active = True
                          and rp.partner_type='venue'
                          and rp.id not in (select partner_id from venue_top_hide_rel where top_id = """ + str(operator and operator.id or 0) + """)
                          and rp.id not in (select partner_id 
                                            from venue_top_show_rel 
                                            where top_id !=  """ + str(operator and operator.id or 0) + """ 
                                            and partner_id not in (select partner_id from venue_top_show_rel where top_id =  """ + str(operator and operator.id or 0) + """ ))
                          and rp.type = 'default'""" +sqlstr+ """
                          group by rp.id
                          having """ + cnt_str + """ order by rp.name""")
             partner = cr.fetchall()

             cr.execute("""	select i.*,j.*,k.*
                            from
                            (   select
                                  rp.id
                                , rp.type
                                , rp.name
                                , rp.sequence
                                , rp.descp_venue
                                , rp.street
                                , rp.street2
                                , cc.name as city
                                , rc.name as country
                                , rp.zip
                                , rp.max_covers
                                , cta.type
                                , cta.covers
                                , string_agg(distinct(cu.name), ',') as cuisine
                                , string_agg(distinct(cd.name), ',') as dining
                                , string_agg(distinct(rpc.name), ',') as category
                                , (case when (select id from cc_menus
                                      where kids_menu = true
                                      and partner_id = rp.id limit 1) is not null then true
                                   else false end) as kids_menu
                                , (select name from cc_time where id = cta.std_frm_id) as min_time
                                , (select name from cc_time where id = cta.std_to_id) as max_time
                                , (select string_agg(name,',') from cc_time where id between cta.std_frm_id and cta.std_to_id """ + avltime_str + """ and ('"""+ str(datetime.strptime((post.get('resv_date') or post.get('booking_date')),'%d/%m/%Y').strftime('%Y-%m-%d')) + """'|| ' ' || name::time)::timestamp  >  (select (now() + interval '1' day) AT TIME ZONE ('Europe/London'))) as avltimes
                                , (case when (select fav_rest_id from fav_part_rel
					                where user_id = """ + str(user.id)+ """ and fav_rest_id = rp.id) is null then false else true end) as fav
                            from res_partner rp
                            left outer join cc_time_allocations cta on cta.partner_id = rp.id
                            left outer join cuisine_part_rel c on c.partner_id = rp.id
                            left outer join cc_cuisine cu on cu.id = c.cuisine_id
                            left outer join dining_part_rel d on d.partner_id = rp.id
                            left outer join cc_dining_style cd on cd.id = d.dining_id
                            left outer join res_partner_res_partner_category_rel rpcl on rpcl.partner_id = rp.id
                            left outer join res_partner_category rpc on rpc.id = rpcl.category_id
                            left outer join cc_city cc on cc.id = rp.city_id
                            left outer join res_country rc on rc.id = rp.country_id
                            where rp.active = True
                            and (select count(id) from cc_black_out_day  where '"""+ str(datetime.strptime((post.get('resv_date') or post.get('booking_date')),'%d/%m/%Y').strftime('%Y-%m-%d')) + """' between date and date_to and partner_id = rp.id) = 0
                            and rp.partner_type='venue'
                            and rp.id not in (select partner_id from venue_top_hide_rel
                                      where top_id = """ + str(operator and operator.id or 0) + """)
                            and rp.id not in (select partner_id from venue_top_show_rel
                                      where top_id != """ + str(operator and operator.id or 0) + """
                                      and partner_id not in (select partner_id from venue_top_show_rel
                                                 where top_id =  """ + str(operator and operator.id or 0) + """ ))
                            and rp.type     = 'default' """+ res_str + search_str +"""
                            and cta.std_frm_id != 1 and cta.std_to_id != 1
                            group by rp.id, cta.covers, cta.type, cta.std_frm_id, cta.std_to_id, cc.name, rc.name
                            order by rp.name, rp.id
                            )i

                            inner join

                            (
                            select  x.rest_id
                                  , max(x.price) as max_price
                                  , min(x.price) as min_price
                            from
                            (
                                  select a.rest_id
                                   , (case when a.menu_mrkup is not null then round((a.price * a.menu_mrkup),1) + a.price
                                  else case when a.rest_mrkup is not null then round((a.price * a.rest_mrkup),1) + a.price
                                  else case when a.glb_mrkup is not null then round((a.price * a.glb_mrkup),1) + a.price
                                  else 0 end end end) as price

                                  from
                                  (
                                select  rp.id as rest_id
                                  , cm.id as menu_id
                                  , case when cm.to_price = 0 then 0 else cm.to_price end  as price
                                  , (select (case when 'markup' = 'markup' then (om.markup_perc/100) else 0 end) as menu_mrkup
                                     from rel_om_menu rom
                                     inner join cc_operator_markup om on om.id = rom.omarkup_id
                                     where om.partner_id = """ + str(operator and operator.id or 0) + """
                                     and restaurant_id = cm.partner_id and rom.menu_id = cm.id) as menu_mrkup
                                  , (select (case when 'markup' = 'markup' then (markup_perc/100) else 0 end)
                                     from cc_operator_markup where partner_id = """ + str(operator and operator.id or 0) + """
                                     and restaurant_id = cm.partner_id and mrkup_lvl = 'rest_lvl') as rest_mrkup
                                  , (select (case when 'markup' = 'markup' then (markup_perc/100) else 0 end)
                                     from res_partner where id = """ + str(operator and operator.id or 0) + """) as glb_mrkup
                                from cc_menus cm left outer join res_partner rp on case when rp.parent_res_id is not null then rp.parent_res_id = cm.partner_id else rp.id = cm.partner_id end
                                and case when cm.start_date is not null and cm.end_date is not null then '"""+str(datetime.strptime((post.get('resv_date')),'%d/%m/%Y').strftime('%Y-%m-%d'))+"""' BETWEEN cm.start_date AND cm.end_date  else true end
                                where cm.cc_fit = True and cm.active = True
                                and cm.kids_menu != True and cm.food_type ='meal'
                                and cm.to_price > 0
                                """ + case_str + """
                                order by rp.id,cm.id
                                  )a
                                  order by a.rest_id
                            )x
                            group by x.rest_id
                            )j
                            on i.id = j.rest_id

                            left outer join

                            (
                            select  distinct(a.restaurant_id)
                                  , True as is_markup
                            from
                            (
                                  select rp.id as restaurant_id
                                  from res_partner rp
                                  where type = 'default'
                                  and partner_type ='venue'
                                  and active = True and max_covers > 0
                                  group by rp.id
                                  having (select markup_perc from res_partner
                                      where id = """ + str(operator and operator.id or 0) + """) > 0

                                  union

                                  select restaurant_id from cc_operator_markup
                                  where partner_id = """ + str(operator and operator.id or 0) + """
                                  and markup_perc > 0
                            )a
                            )k
                            on k.restaurant_id = i.id
                            where i.avltimes is not null """)

             json_dict = cr.dictfetchall()
             json_dict = sorted(json_dict, key=itemgetter('sequence','name','min_price'))
             for i in json_dict:
                if i['street2'] not in ('', None):
                    i['street2'] = ' , '+ str(i['street2'])
                if i['zip'] != '':
                    i['zip'] = ' , '+ str(i['zip'])
                if i['city'] != None:
                    i['city'] = ' , '+ str(i['city'])
                if i['country'] != None:
                    i['country'] = ' , '+ str(i['country'])

                if i['cuisine'] != None:
                    cuisine = i['cuisine']
                    cuisine_split = cuisine.split(',')
                    i['cuisine']  = cuisine_split
                else:
                    i['cuisine'] = []

                if i['dining'] != None:
                    dining = i['dining']
                    dining_split = dining.split(',')
                    i['dining']  = dining_split
                else:
                    i['dining'] = []
                if i['category'] != None:
                    category = i['category']
                    category_split = category.split(',')
                    i['category']  = category_split
                else:
                    i['category'] = []
             if post.get('called_frm') == 'get_restaurants':
                 return json_dict
             request.httprequest.session['json_dict'] = json.dumps(json_dict)

          partner_ids = [x[0] for x in partner]
          # kd_dm = [('cc_fit','=',True)]
          # if user.is_group:
          #    kd_dm = [('cc_group','=',True)]
          # kids_menu = menu_obj.search_read(cr, uid, [('partner_id','in',partner_ids),('kids_menu','=',True)] + kd_dm,['partner_id'])
          # kids_menu = [x['partner_id'][0] for x in kids_menu]
          
          # Get Active Events based on Restaurnats
          if path == 'events':
             main_obj = request.registry.get('cc.events') 
             sqlstr = """select id from cc_events 
                         where active = True 
                         and date_to > '%s' 
                         and covers > 0 
                         and id not in (select event_id from event_top_hide_rel where top_id = %s)
                         and id not in (select event_id 
                                        from event_top_show_rel 
                                        where top_id != %s
                                        and event_id not in (select event_id from event_top_show_rel where top_id = %s))"""%(time.strftime("%Y-%m-%d"), str(operator.id), str(operator.id), str(operator.id))

             if len(partner_ids) == 1:
                sqlstr += """ and partner_id = """ + str((partner_ids[0]))
             elif partner_ids:
                sqlstr += """ and partner_id in """ + str((tuple(partner_ids)))                 
             if post.get('rest_letter') and post.get('rest_letter') != 'others':
                sqlstr += """ and name ilike '""" + (chr(int(post.get('rest_letter')))) + """%'""" 
        
             if post.get('rest_letter','') == 'others':
                sqlstr += """ and name ~ '^[0-9]'"""
                
             if post.get('event_name'):
                sqlstr += """ and name ilike '%""" + post.get('event_name') + """%'"""
            
             if post.get('event_date'):
                sqlstr += """ and '""" + post.get('event_date') + """' between date_from and date_to """ 

             cr.execute(sqlstr)   
             partner_ids = [x[0] for x in cr.fetchall()]
             kids_menu = set()
             for e in main_obj.browse(cr, uid, partner_ids):
                 for m in e.menu_ids:
                     if m .kids_menu:
                        kids_menu.add(e.id) 
             kids_menu = list(kids_menu)
          # if post.get('fav_rest','') == 'on':
          #    favrest_ids = []
          #    for f in user.fav_rest_ids:
          #        favrest_ids.append(f.id)
          #    partner_ids = list(set(partner_ids).intersection(favrest_ids))
             
          # cr.execute("""select distinct(restaurant_id)
          #               from (
          #                       select rp.id as restaurant_id
          #                       from res_partner rp where type = 'default' and partner_type ='venue' and active = True and max_covers > 0
          #                       group by rp.id
          #                       having (select markup_perc from res_partner where id = %s) > 0
          #
          #                       union
          #
          #                       select restaurant_id from cc_operator_markup where partner_id = %s and markup_perc > 0
          #                    )a"""%(operator and operator.id or 0,operator and operator.id or 0))
          # markup_thr = [x[0] for x in cr.fetchall()]
          #
          # if post.get('markup_added','') == 'on':
          #    partner_ids = list(set(partner_ids).intersection(markup_thr))
                 

          get_price={}
          rem_rest = set()          
          if path == 'events':
             cr.execute(""" select a.rest_id    
                                  ,min(case when a.menu_mrkup is not null then (a.min_price * a.menu_mrkup) + a.min_price 
                                   else case when a.rest_mrkup is not null then (a.min_price * a.rest_mrkup) + a.min_price
                                   else (a.min_price * a.glb_mrkup) + a.min_price end end) as min_price
                                  ,max(case when a.menu_mrkup is not null then (a.max_price * a.menu_mrkup) + a.max_price 
                                   else case when a.rest_mrkup is not null then (a.max_price * a.rest_mrkup) + a.max_price
                                   else (a.max_price * a.glb_mrkup) + a.max_price end end) as max_price          
                            from
                            (    
                                select  ce.id as rest_id
                                       ,cm.id as menu_id
                                       ,to_price as min_price
                                       ,to_price as max_price
                                       ,(select (om.markup_perc/100) as menu_mrkup
                                     from rel_om_menu rom
                                     inner join cc_operator_markup om on om.id = rom.omarkup_id
                                     where om.partner_id = """+str(operator.id)+""" and om.restaurant_id = ce.partner_id and rom.menu_id = cm.id) as menu_mrkup
                                       ,(select (markup_perc/100) from cc_operator_markup where partner_id = """+str(operator.id)+""" and restaurant_id = ce.partner_id and mrkup_lvl = 'rest_lvl') as rest_mrkup
                                       ,(select (markup_perc/100) from res_partner where id = """+str(operator.id)+""") as glb_mrkup
                                from cc_events ce 
                                inner join events_menu_rel emr on emr.events_id = ce.id
                                inner join cc_menus cm on cm.id = emr.menu_id
                                where to_price > 0 and ce.date_to >= '2014-08-14'
                                and ce.covers > 0 and ce.active = True    
                                group by cm.id,ce.id
                                order by ce.id
                            )a
                            group by a.rest_id""")
             
             price = cr.dictfetchall()
             
          elif user.is_group:
             cr.execute(""" select a.rest_id    
                                  ,min(a.min_price) as min_price
                                  ,max(a.max_price) as max_price          
                            from
                            (    
                                select  rp.id as rest_id
                                       ,cm.id as menu_id
                                       ,to_price as min_price
                                       ,to_price as max_price
                                from cc_menus cm 
                                inner join res_partner rp on rp.id = cm.partner_id
                                where cm.to_price > 0 
                                and rp.no_of_covers > 0 and cm.active = True 
                                and cm.cc_group = True and cm.kids_menu != True  
                                and cm.food_type = 'meal' 
                                group by cm.id,rp.id
                                order by rp.id
                            )a
                            group by a.rest_id""")
             
             price = cr.dictfetchall()
              
          else :
             price = []#main_obj.get_price(cr, user.id, False, context=None)
             
          fltr_partner_ids = []   
          for pr in price:                    
              if pr['min_price'] == '0.00' and pr['max_price'] == '0.00' or pr['min_price'] is None and pr['max_price'] is None:
                 rem_rest.add(pr['rest_id'])
                 continue 
              elif min_p > 0 and max_p > 0 and pr['min_price'] < min_p and pr['max_price'] > max_p:
                 rem_rest.add(pr['rest_id'])
                 continue
              elif min_p > 0 and pr['min_price'] < min_p:
                 rem_rest.add(pr['rest_id'])
                 continue
              elif max_p > 0 and pr['max_price'] > max_p:
                 rem_rest.add(pr['rest_id'])
                 continue              
              get_price[pr['rest_id']] = pr              
              fltr_partner_ids.append(pr['rest_id'])#collecting venue ids which has price 
              
          partner_ids = list(set(partner_ids).intersection(fltr_partner_ids))#Remove partner_ids which does not have menus or price
          sort = 'sequence,name'
          if path == 'events':
             sort = 'date_from,date_to' 
          partner_ids = main_obj.search(cr, suid, [('id','in',partner_ids)],order=sort)
          grp_size = {}
          if path != 'events' and partner_ids:
              cr.execute("select partner_id, max(covers) from cc_time_allocations where partner_id in %s group by partner_id",(tuple(partner_ids),))
              grp_rslt = cr.dictfetchall()
              grp_size = {grp_rslt[i]['partner_id']: grp_rslt[i]['max'] for i in range(0, len(grp_rslt))}   

          values = {
                     'partners'             : main_obj.browse(cr, suid, [x for x in partner_ids if x not in rem_rest]),
                     'price'                : get_price,
                     'user'                 : user,
                     'uid'                  : user_obj.browse(cr, uid, uid), 
                     'from_which'           : str(path),
                     'cuisine_ids'          : cuisine_rec,
                     'dining_ids'           : dining_rec,
                     'tstation_ids'         : tstation,
                     'min_p'                : min_p,
                     'max_p'                : max_p,
                     'selc_cuisine'         : selc_cuisine,
                     'selc_dining'          : selc_dining,
                     'partner_category_ids' : categ_obj.browse(cr, suid, category_ids),
                     'return_vals'          : post,
                     'markup_thr'           : user.role != 'client_cust' and not user.is_group and markup_thr or [],
                     'grp_size'             : grp_size,
                     'json_dict'            : len(json_dict),
                     'city_browse'          : city_browse,
                     'post'                 : post

                   }    
          return request.website.render("fit_website.westfield_search",values)

      def distance_on_unit_sphere(self, lat1, long1, lat2, long2):
        
            # Convert latitude and longitude to 
            # spherical coordinates in radians.
            degrees_to_radians = math.pi/180.0
            Earth_Radius = 6378137#in meters     
            # phi = 90 - latitude
            phi1 = (90.0 - lat1)*degrees_to_radians
            phi2 = (90.0 - lat2)*degrees_to_radians
                
            # theta = longitude
            theta1 = long1*degrees_to_radians
            theta2 = long2*degrees_to_radians
                
            # Compute spherical distance from spherical coordinates.
                
            # For two locations in spherical coordinates 
            # (1, theta, phi) and (1, theta, phi)
            # cosine( arc length ) = 
            #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
            # distance = rho * arc length
            
            cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
                   math.cos(phi1)*math.cos(phi2))
            arc = math.acos( cos )
        
            # Remember to multiply arc by the radius of the earth 
            # in your favorite set of units to get length.
            return arc * Earth_Radius
      
      # Google Maps Place Search
      @http.route(['/fit_website/json_maps_search'], type='json', auth="public", multilang=True, website=True)
      def json_maps_search(self,center_pt,cuisine,dining,min_p,max_p,fav_maps,json=None):

          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user = request.registry.get('res.users').browse(cr,uid,loginuid)
          request.context.update({'editable':False})
          partner_obj = request.registry.get("res.partner")
          places = {"html_attributions" : [],
                    "results" : []
                   }
          get_price = {}
          operator = user.partner_id
          adtinal_domain = []
          if user.role in ('client_cust','client_user'):
             operator = user.partner_id.parent_id                       
             adtinal_domain = [('id','not in',[x.id for x in operator.contact_ids])]
          p_ids = partner_obj.search(cr,uid,[('latitude','!=',''),('longitude','!=',''),('type','=','default'),('active','=', True),('max_covers','>',0)] + adtinal_domain,order='sequence,name')
          if fav_maps: 
                favrest_ids = []  
                for f in user.fav_rest_ids:
                    favrest_ids.append(f.id)
                p_ids = list(set(p_ids).intersection(favrest_ids))
                 
          price = partner_obj.get_price(cr, uid, False, context=None)
          for pr in price:
              get_price[pr['rest_id']] = pr
          for partner in partner_obj.browse(cr,uid,p_ids):
             d_ids = []
             c_ids = []
             pl = {} 
             try:
                 dist = self.distance_on_unit_sphere(float(center_pt['lat1']), float(center_pt['long1']), float(partner.latitude), float(partner.longitude)) 
                 if dist > center_pt['radius']:
                    continue
             except ValueError:
                # ignore if views are missing
                continue
             
             d_ids = [x.id for x in partner.dining_style_ids]
             c_ids = [x.id for x in partner.cuisine_ids]
             
             if (len(cuisine) > 0 and not [x for x in cuisine if x in c_ids]) and (len(dining)>0 and not [x for x in dining if x in d_ids]): 
                continue 
             elif (len(cuisine) > 0 and not [x for x in cuisine if x in c_ids]):
                 continue
             elif (len(dining) > 0 and  not [x for x in dining if x in d_ids]):
                 continue
             
             if partner.id not in get_price:
                continue
                    
             pl.update(get_price[partner.id])
             min_price = float(pl.get('min_price') or 0.00)
             max_price = float(pl.get('max_pice') or 0.00)
             
             if min_p > 0 and max_p > 0 and min_price < min_p and max_price > max_p:
                continue
             elif min_p > 0 and min_price < min_p:
                continue
             elif max_p > 0 and max_price > max_p:
                continue

             menu_names = ''                 
             for m in partner.menus_ids:
                 menu_names += m.name + '<b> | </b>'

             cr.execute("select (case when fav_rest_id is not null then True else False end) as fav from fav_part_rel where user_id=%s and fav_rest_id = %s",(uid, partner.id))
             is_fav = cr.fetchone()
                              
             pl.update({'name' : partner.name,
                        'image':partner.image_medium or '',
                        'description': partner.descp_venue or '',
                        'menu_name': menu_names or '',
                        'dining_style': partner.dining_style_ids and ', '.join(str(e.name) for e in partner.dining_style_ids) or 'N/A',
                        'cuisine': partner.cuisine_ids and ', '.join(str(e.name) for e in partner.cuisine_ids) or 'N/A',
                        'partner': partner.id,
                        'symbol' : partner.company_id.currency_id.symbol,
                        'geometry':{'location':{'lat':float(partner.latitude),'lng':float(partner.longitude)}},
                        'is_fav'  : is_fav and is_fav[0] or False
                        })
             places['results'].append(pl)                  
          return places
      #Google Map Search      
      @http.route(['/capital_centric/fit/search'], type='http', auth="public", website=True, multilang=True)
      def search(self,*arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          request.context.update({'editable':False})
          loginuid = request.session.uid or request.uid
                   
          cuisine_obj = request.registry.get('cc.cuisine')          
          param_obj = request.registry.get("ir.config_parameter")
          venue_obj = request.registry.get("res.partner")
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,loginuid)
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
          
          cr.execute("""select distinct(cc.id) ,cc.name
                        from cuisine_part_rel cr 
                        inner join res_partner rp on rp.id = cr.partner_id 
                        inner join cc_cuisine cc on cc.id = cr.cuisine_id 
                        where rp.active = True 
                        order by cc.name""")
          cuisine_ids = [i[0] for i in cr.fetchall()]
          cuisines = cuisine_obj.browse(cr, suid,cuisine_ids)
        
          dining_obj = request.registry.get('cc.dining.style')
          cr.execute("""select distinct(dining_id),cd.name 
                        from dining_part_rel dr 
                        inner join res_partner rp on rp.id = dr.partner_id
                        inner join cc_dining_style cd on cd.id = dr.dining_id 
                        where rp.active = True order by cd.name""")
          dining_ids = [j[0] for j in cr.fetchall()]
          dinings = dining_obj.browse(cr, suid,dining_ids)
          
          tstation_obj = request.registry.get('cc.tube.station')
          tstation_ids = tstation_obj.search(cr, uid, [])
          tstation = tstation_obj.browse(cr, suid, tstation_ids)
          values = {  
                      'cuisine_ids' : cuisines,
                      'dining_ids' : dinings,
                      'tstation_ids':tstation,
                      'user' : user,
                      'api_key' : param_obj.get_param(cr, uid, "mapsapi_key"),
                      'uid': user_obj.browse(cr, uid, uid)
                   }
                        
          return request.website.render("fit_website.google_maps",values)
     
      @http.route(['/capital_centric/fit/search/result'], type='http', auth="public", website=True, multilang=True)
      def result(self,*arg, **post ):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False})
        min_price = 0 
        max_price = 0   
        loginuid = request.session.uid or request.uid
        user = request.registry.get('res.users').browse(cr,uid,loginuid)
       
        city_obj = request.registry.get('cc.city')
        location_obj = request.registry.get('cc.location')
        cuisine_obj = request.registry.get('cc.cuisine')
        
        city_ids = city_obj.search(cr, uid, [])
        cities = city_obj.browse(cr, uid, city_ids)
        
        location_ids = location_obj.search(cr, uid, [('city_id','=',int(post.get('City')))])
        locations = location_obj.browse(cr, uid, location_ids)
        
        cuisine_ids = cuisine_obj.search(cr, uid, [])
        cuisines = cuisine_obj.browse(cr, uid, cuisine_ids)
        
        partner_obj = request.registry.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [('partner_type','=','venue'),('cc_fit','=',True),('city_id','=',int(post.get('City'))),('location_id','=',int(post.get('Location')))])
        partners = partner_obj.browse(cr, suid, partner_ids)
        
        menu_obj = request.registry.get('cc.menus')
        menu_ids = menu_obj.search(cr, uid, [('partner_id','in',partner_ids),('cc_fit','=',True)])
        menus = menu_obj.browse(cr, suid, menu_ids)
        
        time_obj = request.registry.get('cc.time')
        time_ids = time_obj.search(cr, uid, [])
        times = time_obj.browse(cr, suid, time_ids)
        
        symbol = user.company_id.currency_id.symbol
        
        a = {}
        for part in partners:
            menu_price = {}
            all_prices = []
                    
            for price in menus:
                if price.partner_id.id == part.id:    
                   all_prices.append(price.rest_price)
            if all_prices:
                menu_price={'min_price': min(all_prices),
                            'max_price' :max(all_prices)}
            if menu_price:
               a.update({part.id:menu_price})
        
        values = {
#                    'login_user' : user,
                   'partners' : partners,
                   'total' : len(partners),
                   'menu_ids' : menus,
                   'price':a,
                   'min_price' : int(min_price),
                   'max_price' : int(max_price),
                   'time_ids' : times,
                   'symbol' : symbol,
                   'city_id' : int(post.get('City')),
                   'city_ids' : cities,
                   'location_id' : int(post.get('Location')),
                   'location_ids' : locations,
                   'cuisine_id' : int(post.get('Cuisine')),
                   'cuisine_ids' : cuisines,
                   'time_id' : int(post.get('Time')),
                   'date' : post.get('Date'),                   
                 }
        return request.website.render("fit_website.result",values)
 
          
      #On Click Of "Select" Button on the marker
      @http.route(['/capital_centric/fit/<path>/result/<int:venue_id>'], type='http', auth="public", website=True, multilang=True)
      def result_menu(self,path, venue_id=None, **post ):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False})
        loginuid = request.session.uid or request.uid
        partner_obj = request.registry.get('res.partner')
        alloc_obj = request.registry.get('cc.time.allocations')
        event_obj = request.registry.get('cc.events')
        time_obj = request.registry.get('cc.time')
        menutable_obj = request.registry.get('cc.menus.table')
        user_obj = request.registry.get('res.users')
        lead_obj = request.registry.get("crm.lead")
        product_obj = request.registry.get('product.product')
        user = user_obj.browse(cr,uid,loginuid)
        session_id = request.httprequest.session.get('website_session_id')
        menutbl_dict = {}
        if user.name == 'Public user':
           h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
           user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
           user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)

        avltimes = []
        menutbl_ids = []
        tx_perc = 0
        event = False
        amend_error = False
        lead_browse = False
        type_list = set()
        if post.get('lead_id'):
            lead_browse = lead_obj.browse(cr, suid, int(post.get('lead_id')))
            today = (parser.parse(time.strftime("%Y-%m-%d %H:%M"))+relativedelta(hours=+36)).strftime("%Y-%m-%d %H:%M")
            post['type'] = lead_browse.lead_res_type
            post['resv_date'] = datetime.strptime(lead_browse.conv_dob, '%d-%b-%Y').strftime('%d/%m/%Y')
            post['time_selected'] =lead_browse.conv_tob
            post['no_persons'] =lead_browse.covers
            post['location_id'] = lead_browse.restaurant_id.city_id.id
            post['parent_res_id'] = lead_browse.restaurant_id.parent_res_id and lead_browse.restaurant_id.parent_res_id.id or False
            post['called_frm'] = 'get_restaurants'
            post['res_id'] = lead_browse.restaurant_id.id
            product_ids = product_obj.search(cr,uid,[('name_template','=','FIT for Purpose')])
            product = product_obj.browse(cr,uid,product_ids[0])
            for tx in product.taxes_id:
                 tx_perc += tx.amount * 100
            for menu in lead_browse.info_ids[0].menu_dt_ids:
                # cr.execute(""" select id from cc_menus_table where menu_id = """+str(menu.menu_id.id))
                # cc_menus = cr.fetchone()
                # cc_menus = cc_menus and cc_menus[0] or False
                # if cc_menus:
                #     menutbl_ids.append(cc_menus)
                # else:
                price = menu.top_tot_top_price + menu.no_of_covers * menu.top_markup
                p_price = menu.menu_id.to_price + menu.menu_id.markup
                tx_amt = (p_price - ((p_price / (100 + tx_perc)) * 100)) * int(lead_browse.covers)
                total_price = (menu.menu_id.service_charge + ((p_price / (100 + tx_perc)) * 100)) * int(lead_browse.covers)
                menutbl_ids.append(menutable_obj.create(cr,uid,{'venue_id'       :  menu.restaurant_id and menu.restaurant_id.id,
                                                          'operator_id'    :  user.partner_id.id,
                                                          'ffp_mu'         :  menu.menu_id.markup,
                                                          'ffp_co'         :  menu.menu_id.commission,
                                                          # 'to_mu'          :  menu.to_mu,
                                                          'pp_person'      :  menu.menu_id.rest_price,
                                                          'menu_id'        :  menu.menu_id.id,
                                                          # 'service_charge' :  price - (menu.menu_id.to_price + menu.menu_id.to_mu),
                                                          'price_type'     :  '',
                                                          'food_type'      :  menu.menu_id.food_type,
                                                          'website_session_id' : session_id,
                                                          'vat'            : round(tx_amt, 2),
                                                          'total_price'    : round(total_price,2),
                                                          'guest'          : lead_browse.covers}))
            for m in menutable_obj.browse(cr, uid, menutbl_ids):
                menutbl_dict.update({m.menu_id.id:m.id})
            json_dict = self.westfield_search(path='', **post)
            for avl in json_dict[0]['avltimes'].split(','):
              avltimes.append(avl)
            if lead_browse and lead_browse.date_requested < today:
                amend_error = True

        operator = user.partner_id
        if user.role != 'client':
           operator = user.partner_id.parent_id or False
        if path == 'events':
           event = event_obj.browse(cr, suid, venue_id)  
           venue_id = event.partner_id.id  
           
        venue = partner_obj.browse(cr, suid, venue_id)
        symbol = user.company_id.currency_id.symbol
        #Clear the dummy table before proceeding
        cr.execute("delete from cc_menus_table \
                    where operator_id = %s \
                    and venue_id = %s and website_session_id = %s",(user.partner_id.id, venue.id, session_id))
        
        values = {
                  'partner_id' : venue,
                  'symbol'     : user.company_id.currency_id.symbol,
                  'cuisine_names' : venue.cuisine_ids and ', '.join(str(e.name) for e in venue.cuisine_ids) or 'N/A',
                  'dining_names':venue.dining_style_ids and ', '.join(str(e.name) for e in venue.dining_style_ids) or 'N/A',
                  'path'       : path,
                  'user'       : user,
                  'uid'        : user_obj.browse(cr,uid,uid),
                  'post'       : post,
                  'lead_browse': lead_browse,
                  'amend_error': amend_error,
                  'avltimes'   : avltimes,
                  'menutbl_dict' : menutbl_dict
                 }

        day = datetime.strptime(datetime.strptime((post.get('resv_date')),'%d/%m/%Y').strftime('%Y-%m-%d'), "%Y-%m-%d").strftime("%A").lower()
        print "day",day
        if path != 'events' and not user.is_group:
            if venue.parent_res_id and venue.parent_res_id.id:
                venue = partner_obj.browse(cr, suid, venue.parent_res_id.id)
            cr.execute(""" select   a.menu_id
                                 , (case when a.menu_mrkup is not null then round((a.price * a.menu_mrkup),1) + a.price
                                    else case when a.rest_mrkup is not null then round((a.price * a.rest_mrkup),1) + a.price
                                    else case when a.glb_mrkup is not null then round((a.price * a.glb_mrkup),1) + a.price
                                    else 0 end end end) as price
                                 , (case when a.menu_mrkup is not null then round((a.price * a.menu_mrkup),1)
                                    else case when a.rest_mrkup is not null then round((a.price * a.rest_mrkup),1)
                                    else case when a.glb_mrkup is not null then round((a.price * a.glb_mrkup),1)
                                    else 0 end end end) as to_mu
                           from
                           (
                                select  cm.partner_id as rest_id
                                  , cm.id as menu_id
                                  , case when cm.to_price = 0 then 0 else cm.to_price end  as price
                                  , (select (case when 'markup' = 'markup' then (om.markup_perc/100) else 0 end) as menu_mrkup
                                     from rel_om_menu rom
                                     inner join cc_operator_markup om on om.id = rom.omarkup_id
                                     where om.partner_id = """ + str(operator and operator.id or 0) + """
                                     and restaurant_id = cm.partner_id and rom.menu_id = cm.id) as menu_mrkup
                                  , (select (case when 'markup' = 'markup' then (markup_perc/100) else 0 end)
                                     from cc_operator_markup where partner_id = """ + str(operator and operator.id or 0) + """
                                     and restaurant_id = cm.partner_id and mrkup_lvl = 'rest_lvl') as rest_mrkup
                                  , (select (case when 'markup' = 'markup' then (markup_perc/100) else 0 end)
                                     from res_partner where id = """ + str(operator and operator.id or 0) + """) as glb_mrkup
                                from cc_menus cm
                                where cm.cc_fit = True and cm.active = True
                                and cm.food_type  in ('meal','drink')
                                and cm.to_price > 0 and cm.partner_id = """ + str(venue and venue.id) + """
                                and (case when '""" + post.get('type') + """' = 'break_fast' then cm.break_fast = True
                                else case when '""" + post.get('type') + """' = 'lunch' then cm.lunch=True
                                else case when '""" + post.get('type') + """' = 'at' then cm.afternoon_tea=True
                                else case when '""" + post.get('type') + """' = 'dinner' then cm.dinner=True end end end end)
                                and (case when '""" + day + """' = 'sunday' then cm.is_sun = True
                                else case when '""" + day + """' = 'monday' then cm.is_mon=True
                                else case when '""" + day + """' = 'tuesday' then cm.is_tue=True
                                else case when '""" + day + """' = 'wednesday' then cm.is_wed=True
                                else case when '""" + day + """' = 'thursday' then cm.is_thu=True
                                else case when '""" + day + """' = 'friday' then cm.is_fri=True
                                else case when '""" + day + """' = 'saturday' then cm.is_sat=True end end end end end end end)
                                and case when cm.start_date is not null and cm.end_date is not null then '"""+str(datetime.strptime((post.get('resv_date')),'%d/%m/%Y').strftime('%Y-%m-%d'))+"""' BETWEEN cm.start_date AND cm.end_date  else true end
                                and cm.id not in (select menu_id from menu_top_hide_rel
                                      where top_id = """ + str(operator and operator.id or 0) + """)
				                and cm.id not in (select menu_id from menu_top_show_rel
                                      where top_id != """ + str(operator and operator.id or 0) + """
                                      and menu_id not in (select menu_id from menu_top_show_rel
                                                 where top_id =  """ + str(operator and operator.id or 0) + """))
                                order by cm.partner_id,cm.id
                           )a
                           order by a.rest_id """)
            to_mu = cr.dictfetchall()
            values.update({'menu_price': to_mu and dict((m.get('menu_id'),m.get('price')) for m in to_mu),
                           'to_markup' : to_mu and dict((m.get('menu_id'),m.get('to_mu')) for m in to_mu)})
        #for Events and Groups Data regarding Menus,time,date is sent from here. Its different from normal process
        if path == 'events' or user.is_group:                  
           date_list = []
           emenus = []
           to_mu = {}
           if path == 'events':     
              dt_start = datetime.strptime(event.date_from, '%Y-%m-%d')
              dt_end = datetime.strptime(event.date_to, '%Y-%m-%d')
              no = dt_end - dt_start           
              [date_list.append((dt_start + relativedelta(days=x)).strftime('%d-%b-%Y')) for x in range(int(no.days + 1))]
              menu_ids = event.menu_ids              
              if event.covers <= 0:
                 return request.website.render("fit_website.single_record",values)
           else:
              menu_ids = venue.menus_ids + venue.grp_drink_ids
               
           for m in menu_ids:
              if m.break_fast:
                 type_list.add('1bf')
              if m.lunch:
                 type_list.add('2lunch')           
              if m.afternoon_tea:
                 type_list.add('3at')
              if m.dinner:
                 type_list.add('4dinner')                 
              
              if user.is_group and '3at' in type_list:#Afternoon tea option is not there for group menus so had to be removed if present in list
                 type_list.remove('3at') 
              if path == 'events':
                 cr.execute(""" select 
                                    (select (om.markup_perc/100) as menu_mrkup
                                     from rel_om_menu rom
                                     inner join cc_operator_markup om on om.id = rom.omarkup_id
                                     where om.partner_id = """+str(operator.id)+""" and om.restaurant_id = """+str(m.partner_id.id)+""" and rom.menu_id = """+str(m.id)+"""
                                    ) as menu_mrkup
                                   ,(select (markup_perc/100) from cc_operator_markup where partner_id = """+str(operator.id)+""" and restaurant_id = """+str(m.partner_id.id)+""" and mrkup_lvl = 'rest_lvl') as rest_mrkup
                                   ,(select (markup_perc/100) from res_partner where id = """+str(operator.id)+""") as glb_mrkup""")
                 to_mu = cr.dictfetchone() 

              emenus.append(menutable_obj.create(cr,uid,{'venue_id'         : venue.id,
                                                         'operator_id'      : user.partner_id.id,
                                                         'pp_person'        : m.rest_price,
                                                         'menu_id'          : m.id,
                                                         'ffp_mu'           : m.markup,
                                                         'food_type'        : m.food_type ,
                                                         'to_mu'            : round(m.to_price * (to_mu.get('menu_mrkup') or to_mu.get('rest_mrkup') or to_mu.get('glb_mrkup') or 0),1),  
                                                         'service_charge'   : m.to_price - (m.rest_price + m.markup),
                                                         'website_session_id':session_id
                                                        }))
           type_list = list(type_list)
           type_list.sort()
           values.update({'events':event,
                          'event_dates' : date_list,
                          'meal_tp'     : type_list,
                          'lead_browse' : lead_browse})
        return request.website.render("fit_website.single_record",values)

 #Check for Blackout Day
      @http.route(['/fit_website/blackout_validation/'], type='json', auth="public", website=True, multilang=True)
      def blackout_validation(self, partner_id, time, date, type, chkwhich, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user = request.registry.get('res.users').browse(cr,uid,loginuid)
          partner_obj = request.registry.get('res.partner') 
          time_obj =  request.registry.get('cc.time')         
          partner = partner_obj.browse(cr, suid, partner_id)
          date = datetime.strptime(date, "%Y-%m-%d")
          day = date.strftime("%A").lower()
          
          if chkwhich == 'time':
             time = request.registry.get('cc.time').browse(cr,uid,time)
             blackout_ids = request.registry.get('cc.black.out.day').search(cr,uid,[('partner_id','=',partner.id),
                                                                           ('date','=',date),
                                                                           ('from_time_id.name','<=',time.name),
                                                                           ('to_time_id.name','>=',time.name)])
             if blackout_ids:
                return False
             else:
                 return True
          
          else:
              cr.execute(""" select id from cc_time where id between 
                                    (select min(a.min_time)
                                    from
                                    (select least(non_frm_id,non_to_id,std_frm_id,std_to_id,std_frm_id,pre_frm_id,pre_to_id) as min_time
                                    from cc_time_allocations where partner_id ="""+ str(partner_id)+""" and type='"""+ str(type)+"""' and name='"""+str(day)+"""')a)
                                    
                                    and 
                                    
                                    (select max(a.max_time)
                                    from
                                    (select greatest(non_frm_id,non_to_id,std_frm_id,std_to_id,std_frm_id,pre_frm_id,pre_to_id) as max_time
                                    from cc_time_allocations where partner_id ="""+ str(partner_id)+""" and type='"""+ str(type)+"""' and name='"""+str(day)+"""')a)
                                    """)
              time_ids = cr.fetchall()
              time_ids = [x[0] for x in time_ids]
              time = [] 
              for t in time_obj.browse(cr,uid,time_ids):
                  time.append(t.name)
              return time,time_ids
              
      # Onchange of  guests  
      @http.route(['/fit_website/cc_menus_table/'], type='json', auth="public", website=True, multilang=True)
      def cc_menus_table(self, guest, db_id, price, menu_ids, frmwch=None, e_date=None, json=None, to_mu=None):
          
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user = request.registry.get('res.users').browse(cr,uid,loginuid)  
          menus_obj = request.registry.get('cc.menus.table')
          ccmenu_obj = request.registry.get('cc.menus')
          event_obj = request.registry.get('cc.events')
          venue_obj = request.registry.get('res.partner')
          time_obj = request.registry.get('cc.time')
          product_obj = request.registry.get('product.product')
          tx_perc = 0
          etimes = []
          product_ids = product_obj.search(cr,uid,[('name_template','=','FIT for Purpose')])
          session_id = request.httprequest.session.get('website_session_id')
          menu_filter = {'1bf'     : [('menu_id.break_fast','=',True)],
                         '2lunch'  : [('menu_id.lunch','=',True)],
                         '3at'     : [('menu_id.at','=',True)],
                         '4dinner' : [('menu_id.dinner','=',True)]}
          
          if frmwch in ('1bf','2lunch','3at','4dinner','events') and not user.is_group:      
             menus = []   
             event = False
             etimes = []                      
             if frmwch != 'events':
                event = event_obj.browse(cr, uid, int(db_id))  
                time_filter = {'1bf'     : [('id','>=',event.bt_from and event.bt_from.id or 0),('id','<',event.bt_to and event.bt_to.id or 0)],   
                               '2lunch'  : [('id','>=',event.lt_from and event.lt_from.id or 0),('id','<',event.lt_to and event.lt_to.id or 0)],
                               '3at'     : [('id','>=',event.att_from and event.att_from.id or 0),('id','<',event.att_to and event.att_to.id or 0)],
                               '4dinner' : [('id','>=',event.dt_from and event.dt_from.id or 0),('id','<',event.dt_to and event.dt_to.id or 0)],}
               
                etimes = time_obj.search_read(cr, suid, time_filter[frmwch], ['name'])                     
                menus_obj.write(cr, uid, menu_ids, {'guest':0})
                menu_ids = menus_obj.search(cr, uid, menu_filter[frmwch] + [('food_type','=','events'),('operator_id','=',user.partner_id.id),('venue_id', '=', event.partner_id.id),('website_session_id','=', session_id)],order='pp_person')
                menus = menus_obj.browse(cr, uid, menu_ids)
             if e_date : 
                menus_obj.write(cr, uid, menu_ids, {'booking_date':datetime.strptime(e_date, '%d-%b-%Y')})
                if frmwch == 'events':
                   return 

             return request.website._render("fit_website.events_table",{'event_menus' : menus,
                                                                                      'max_covers':event.partner_id.max_covers,
                                                                                      'user':user}),etimes
                                                                                      
          elif frmwch in ('1bf','2lunch','3at','4dinner') and user.is_group:  
              if e_date:
                 m_vals = {'booking_date':datetime.strptime(e_date, '%d-%b-%Y')}
                 for mt in menus_obj.browse(cr, uid, menu_ids):
                     if mt.menu_id.break_fast and frmwch != '1bf':
                        m_vals.update({'guest':0})
                     elif mt.menu_id.lunch and frmwch != '2lunch':
                        m_vals.update({'guest':0})
                     elif mt.menu_id.afternoon_tea and frmwch != '3at':
                        m_vals.update({'guest':0})
                     elif mt.menu_id.dinner and frmwch != '4dinner':
                        m_vals.update({'guest':0})
                        
                     if (mt.menu_id.break_fast and frmwch == '1bf') or (mt.menu_id.lunch and frmwch == '2lunch') or (mt.menu_id.afternoon_tea and frmwch == '3at') or (mt.menu_id.dinner and frmwch == '4dinner'):
                         del m_vals['guest'] 
                                                                        
                 tm_domain = {'1bf'     :['bf_from','bf_to'],
                              '2lunch'  :['lunch_from','lunch_to'],
                              '3at'     :['at_from','at_to'],
                              '4dinner' :['dinner_from','dinner_to']
                              } 
                 day = datetime.strptime(e_date, '%d-%b-%Y').strftime("%A").lower()
                 menus_obj.write(cr, uid, menu_ids, m_vals)
                 opening_hrs_obj = request.registry.get('cc.opening.hrs')
                 opening_hrs = opening_hrs_obj.search_read(cr, uid, [('name','=',day),('partner_id','=',int(db_id))],tm_domain[frmwch])
                 for o in opening_hrs:
                     etimes += time_obj.search_read(cr, suid, [('id','>=',o[tm_domain[frmwch][0]][0]),('id','<',o[tm_domain[frmwch][1]][0])], ['name'])
                     
              venue = venue_obj.browse(cr,uid,int(db_id))
              operator = user.partner_id
#               if user.role != 'client':
#                  operator = user.partner_id.parent_id or False
              menu_ids = menus_obj.search(cr, uid, [('venue_id','=', int(db_id)),('operator_id','=',operator.id),('food_type', '=', 'meal'),('website_session_id','=',session_id)] + menu_filter[frmwch],order='pp_person')
              drink_ids = menus_obj.search(cr, uid, [('venue_id','=', int(db_id)),('operator_id','=',operator.id),('food_type', '=', 'drink'),('website_session_id','=',session_id)],order='pp_person')
              drinks = request.website._render("fit_website.drinks_table_template",{'drinks' : menus_obj.browse(cr, uid, drink_ids),
                                                                                      'max_covers':venue.max_covers,
                                                                                      'user':user})
              return request.website._render("fit_website.events_table",{'event_menus' : menus_obj.browse(cr, uid, menu_ids),
                                                                                      'max_covers':venue.no_of_covers,
                                                                                      'user':user}),etimes,drinks
                                
          else:
              if product_ids:
                 product = product_obj.browse(cr,uid,product_ids[0])
                 for tx in product.taxes_id:
                     tx_perc += tx.amount * 100
              menutbl_id = 0
              menu = db_id and ccmenu_obj.browse(cr,uid,int(db_id)) or False
              menutbl_ids = menus_obj.search(cr, uid, [('menu_id','=', int(db_id)),('operator_id','=',user.partner_id.id),('food_type', '=', menu.food_type),('id','in',menu_ids)])
              if frmwch == 'create' and not menutbl_ids:
                 p_price = menu.to_price + menu.markup
                 tx_amt = (p_price - ((p_price / (100 + tx_perc)) * 100)) * int(guest)
                 total_price = (menu.service_charge + ((p_price / (100 + tx_perc)) * 100)) * int(guest)
                 menutbl_id = menus_obj.create(cr,uid,{'venue_id'       :  menu.partner_id and menu.partner_id.id,
                                                          'operator_id'    :  user.partner_id.id,
                                                          'ffp_mu'         :  menu.markup,
                                                          'ffp_co'         :  menu.commission,
                                                          'to_mu'          :  to_mu,
                                                          'pp_person'      :  menu.rest_price,
                                                          'menu_id'        :  menu.id,
                                                          'service_charge' :  price and price - (menu.to_price + float(to_mu)),
                                                          'price_type'     :  '',
                                                          'food_type'      :  menu.food_type,
                                                          'website_session_id' : session_id,
                                                          'vat'            : round(tx_amt, 2),
                                                          'total_price'    : round(total_price,2),
                                                          'guest'          : guest})
              elif frmwch == 'edit' and menutbl_ids:
                   menus_vals = {'guest' : guest}
                   menus_obj.write(cr, uid, menutbl_ids, menus_vals)

              elif frmwch == 'delete' and menutbl_ids:
                   menus_obj.unlink(cr, uid, menutbl_ids)

              return menutbl_id
              
          return          

# 5 Image Saving functions in Venues...      
      @http.route(['/fit_website/image/'], type='http', auth='user', methods=['POST'], website=True)
      def image(self ,partner_id, image_name,image):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          partner_obj = request.registry.get("res.partner")
          
          img = image_name.read().encode('base64')
          
          if(image == '1'):
              partner_vals = {
                               'image' : img,
                             }
          if(image == '2'):
              partner_vals = {
                               'cc_image1' : img,
                             }
          if(image == '3'):
              partner_vals = { 
                               'cc_image2' : img,
                             }
          if(image == '4'):
              partner_vals = {
                               'cc_image3' : img,
                             }
          if(image == '5'):
              partner_vals = {
                               'cc_image4' : img,
                             }
          partner = partner_obj.write(cr, uid, [int(partner_id)], partner_vals)
          
          return      
            
      # Save the Image Description JSON      
      @http.route(['/fit_website/image_desc/'], type='json', auth="public", multilang=True, website=True)
      def image_desc(self,dict,partner_id,json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          partner_obj = request.registry.get("res.partner")
          
          partner_obj.write(cr, uid, [partner_id], dict)
          return   

      @http.route(['/fit_website/on_change_type/'], type='json', auth="public", website=True, multilang=True)
      def on_change_type(self ,partner_id, type, date,json=None):
          """ To fetch data based on meal_type selected and to populate on calendar view """
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          
          lead_obj = request.registry.get("crm.lead") 
          parse_date =  (parser.parse(''.join((re.compile('\d')).findall(date)))).strftime('%Y-%m-%d 13:00')
          date = datetime.strptime(parse_date, "%Y-%m-%d %H:%M")     
          curr_day = date.day
          today = time.strftime("%Y-%m-%d %H:%M")
          cd = lead_obj.onchange_DOB(cr, uid, [], today, context={'from_web':True})['value']
          if int(cd['conv_tob'][3:]) < 30 :
             cd['conv_tob'] = cd['conv_tob'].replace(cd['conv_tob'][3:],'30')
          else:
             cd['conv_tob'] = str(int(cd['conv_tob'][:2]) + 1) + ':'+'00'           
          last_day = calendar.monthrange(date.year,date.month)[1]          
          allocation_obj = request.registry.get("cc.time.allocations")
          time_obj = request.registry.get("cc.time")
          event = []      
          cal_data = [] 
 
          for i in range(0,180):
              blackout_ids = []
              date = date + relativedelta(days=1)
              runing_date = date.strftime('%Y-%m-%d')              
              alloc_ids = allocation_obj.search(cr,uid,[('partner_id','=',partner_id),('type','=',type),('name','=',date.strftime("%A").lower()),('covers','>',0)])
              
              if alloc_ids:
                  cr.execute("""select (select name from cc_time where id = min(non_frm_id)) as non_frm_id,
                                       (select name from cc_time where id = max(non_to_id)) as non_to_id,
                                       (select name from cc_time where id = min(std_frm_id)) as std_frm_id,
                                       (select name from cc_time where id = max(std_to_id)) as std_to_id,
                                       (select name from cc_time where id = max(pre_frm_id)) as pre_frm_id,
                                       (select name from cc_time where id = min(pre_to_id)) as pre_to_id
                                from cc_time_allocations where id in %s""" ,(tuple(alloc_ids),))  
                  alloc_time = cr.dictfetchall()                  
                  alloc_time = alloc_time[0]
                  for t in range(0,3):
                    title = ''  
                    cal_vals = {}
                    min_time = max_time = ''
                    if t == 0 :                           
                       if 'non_frm_id' in alloc_time and 'non_to_id' and alloc_time['non_frm_id'] not in ('N/A',None):                           
                           min_time = alloc_time['non_frm_id']
                           max_time = alloc_time['non_to_id']
                           min_time_id = time_obj.search(cr, uid, [('name','=',min_time)])[0]
                           max_time_id = time_obj.search(cr, uid, [('name','=',max_time)])[0] 
                           blackout_ids = request.registry.get('cc.black.out.day').search(cr,uid,[('partner_id','=',partner_id),
                                                                                                  ('date','<=',runing_date),('date_to','>=',runing_date),
                                                                                                  ('from_time_id.name','<=',min_time),
                                                                                                  ('to_time_id.name','>=',max_time)]) 
                           cr.execute("select extract( EPOCH from age(%s,%s))",(runing_date+' ' +min_time,cd['conv_dob'] + ' '+ cd['conv_tob']))
                           time_diff = cr.fetchone()
                           
                           if time_diff and time_diff[0] < 86400:
                              min_time = cd['conv_tob'] 
                              if  cd['conv_tob'] >= max_time:
                                  continue
                           title = min_time + ' - ' + max_time
                           if   type == 'break_fast' :price_type = 'bf_non_premium'
                           elif type == 'lunch'      :price_type = 'l_non_premium'
                           elif type == 'at'         :price_type = 'at_non_premium'
                           elif type == 'dinner'     :price_type = 'd_non_premium'                       
                           color = '#c00000'
                    elif t == 1 :
                       if 'std_frm_id' in alloc_time and 'std_to_id' in alloc_time and alloc_time['std_frm_id'] not in ('N/A',None):
                           min_time = alloc_time['std_frm_id']
                           max_time = alloc_time['std_to_id']        
                           blackout_ids = request.registry.get('cc.black.out.day').search(cr,uid,[('partner_id','=',partner_id),
                                                                                                  ('date','<=',runing_date),('date_to','>=',runing_date),
                                                                                                  ('from_time_id.name','<=',min_time),
                                                                                                  ('to_time_id.name','>=',max_time)])               
                           cr.execute("select extract( EPOCH from age(%s,%s))",(runing_date+' ' +min_time,cd['conv_dob'] + ' '+ cd['conv_tob']))
                           time_diff = cr.fetchone()
                           if time_diff and time_diff[0] < 86400:
                              min_time = cd['conv_tob'] 
                              if  cd['conv_tob'] >= max_time:
                                  continue  
                           title = min_time + ' - ' + max_time                           
                           if   type == 'break_fast' :price_type = 'bf_standard'
                           elif type == 'lunch'      :price_type = 'l_standard'
                           elif type == 'at'         :price_type = 'at_standard'
                           elif type == 'dinner'     :price_type = 'd_standard'
                           color = '#26466D'
                    elif t == 2 :
                       if 'pre_frm_id' in alloc_time and 'pre_to_id' in alloc_time and alloc_time['pre_frm_id'] not in ('N/A',None):
                           min_time = alloc_time['pre_frm_id']
                           max_time = alloc_time['pre_to_id']
                           blackout_ids = request.registry.get('cc.black.out.day').search(cr,uid,[('partner_id','=',partner_id),
                                                                                                  ('date','<=',runing_date),('date_to','>=',runing_date),
                                                                                                  ('from_time_id.name','<=',min_time),
                                                                                                  ('to_time_id.name','>=',max_time)]) 
                           cr.execute("select extract( EPOCH from age(%s,%s))",(runing_date+' ' +min_time,cd['conv_dob'] + ' '+ cd['conv_tob']))
                           time_diff = cr.fetchone()
                           if time_diff and time_diff[0] < 86400:
                              min_time = cd['conv_tob']
                              if  cd['conv_tob'] >= max_time:
                                  continue   
                           title = min_time + ' - ' + max_time                           
                           if   type == 'break_fast' :price_type = 'bf_premium'
                           elif type == 'lunch'      :price_type = 'l_premium'
                           elif type == 'at'         :price_type = 'at_premium'
                           elif type == 'dinner'     :price_type = 'd_premium'
                           color = '#004c00'
                    if title and not blackout_ids:
                        cal_data.append({'title':title,
                                         'start': str(date),
                                         'allday':'true',
                                         'price_type':price_type,
                                         'color':color,
                                         'textColor':'white',
                                         'min_time' : min_time,
                                         'max_time' : max_time, 
                                         'day':date.strftime("%A").lower()
                                         })

          return cal_data 
            
      @http.route(['/fit_website/onclick_date/'], type='json', auth="public", website=True, multilang=True)
      def date_selected_on_calview(self, price_type, type, partner_id, date, min_time, max_time, menu_ids, json=None):
          
            """ Function to populate menus along with price of the restaurant for the day and meal type selected on
            calendar view of website"""
            
            cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context            
            loginuid = request.session.uid or request.uid
            
            partner_obj = request.registry.get('res.partner')        
            menu_obj = request.registry.get('cc.menus')
            time_obj = request.registry.get('cc.time')
            allocation_obj = request.registry.get('cc.time.allocations')
            menutable_obj = request.registry.get('cc.menus.table')
            pricing_obj = request.registry.get('cc.menu.pricing')
            lead_obj = request.registry.get('crm.lead')
            user_obj = request.registry.get('res.users')
            user = user_obj.browse(cr,uid,loginuid)
            session_id = request.httprequest.session.get('website_session_id')

            symbol = user.company_id.currency_id.symbol   
            today = time.strftime("%Y-%m-%d %H:%M")
            cd = lead_obj.onchange_DOB(cr, uid, [], today, context={'from_web':True})['value']
            date = datetime.strptime((parser.parse(''.join((re.compile('\d')).findall(date)))).strftime('%Y-%m-%d'), "%Y-%m-%d")
            sel_date = date.strftime('%Y-%m-%d')

            if user.name == 'Public user':
               user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',user.cc_url)])
               user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)

            operator_id = user.partner_id and user.partner_id.id
            if user and user.role in ('client_user','client_mng','client_cust'):
               operator_id = user.partner_id and user.partner_id.parent_id.id or 0

               
            cr.execute("select extract( EPOCH from age(%s,%s))",(sel_date+' ' +min_time,cd['conv_dob']+ ' ' + cd['conv_tob']))
            time_diff = cr.fetchone()
            if time_diff and time_diff[0] < 86400:
               min_time = cd['conv_tob']                   
            venue = partner_obj.browse(cr, suid, partner_id)             
            
            day = date.strftime("%A").lower()
            course ={'c1':'1','c2':'2','c3':'3','c4':'4','c5':'5','c6':'6'} 
            cr.execute("delete from cc_menus_table where venue_id=" + str(venue.id)+ " and operator_id = " + str(user.partner_id.id) + " and website_session_id = '" + str(session_id) + "'")
            time_ids = time_obj.search(cr, uid, [('name','>=',min_time),('name','<',max_time)])
            
            time_rec = []
            avlblty_dict = {}
            for t in time_obj.browse(cr,uid,time_ids):
                blackout_ids = request.registry.get('cc.black.out.day').search(cr,uid,[('partner_id','=',partner_id),
                                                                           ('date','<=',date),('date_to','>=',date),
                                                                           ('from_time_id.name','<=',t.name),
                                                                           ('to_time_id.name','>=',t.name)])
                if blackout_ids:
                    continue
                #to show availability
                if price_type in ('bf_non_premium', 'l_non_premium', 'at_non_premium', 'd_non_premium'):
                   sqlstr = " and '" + str(t.name) + "' between (select name from cc_time where id = non_frm_id)  and (select name from cc_time where id = non_to_id)" 
                elif price_type in ('bf_standard', 'l_standard', 'at_standard', 'd_standard'):
                     sqlstr = " and '" + str(t.name) + "' between (select name from cc_time where id = std_frm_id)  and (select name from cc_time where id = std_to_id)"
                elif price_type in ('bf_premium', 'l_premium', 'at_premium', 'd_premium'):
                     sqlstr = " and '" + str(t.name) + "' between (select name from cc_time where id = pre_frm_id)  and (select name from cc_time where id = pre_to_id)"
                
                cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) as alloc_cvoers , id from cc_time_allocations 
                    where partner_id = """ + str(venue.id) +""" 
                    and type = '""" + str(type) + """'
                    and name = '""" + str(day) + """'"""+ str(sqlstr)+
                    """ group by id """)
                
                alloc_covers = cr.fetchone()
                
                cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) 
                              from crm_lead 
                              where state in ('open','done')
                              and conv_dob = '""" + str(date.strftime("%d-%b-%Y")) + """'
                              and conv_tob = '""" + str(t.name) + """'
                              and restaurant_id = '""" + str(venue.id) + """'
                          """) 
                tot_covers = cr.fetchone()
                avlblty_dict[t.name] = (alloc_covers and alloc_covers[0] or 0) - (tot_covers and tot_covers[0] or 0)      
                time_rec.append(t.name)
             
            if type == 'break_fast':
               domain=[('break_fast','=',True),('partner_id','=',venue.id),('food_type','=','meal')]
            elif type == 'lunch':
               domain=[('lunch','=',True),('partner_id','=',venue.id),('food_type','=','meal')]
            elif type == 'at':
               domain=[('afternoon_tea','=',True),('partner_id','=',venue.id),('food_type','=','meal')]
            elif type == 'dinner':
               domain=[('dinner','=',True),('partner_id','=',venue.id),('food_type','=','meal')]
               
            cr.execute(""" select id from cc_menus 
                           where id in (select menu_id from menu_top_hide_rel where top_id = """ + str(operator_id)+ """) 
                           or id in (select menu_id 
                                     from menu_top_show_rel 
                                     where top_id != """ + str(operator_id)+ """ 
                                     and menu_id not in (select menu_id from menu_top_show_rel where top_id = """ + str(operator_id)+ """)) """)
            hide_menus = [i[0] for i in cr.fetchall()]
            domain.append(('id','not in',hide_menus))
            menu_ids = menu_obj.search(cr,uid,domain)
                          
            menus = []            
            for m in menu_obj.browse(cr,uid,menu_ids):
                for pr in m.pricing_ids:
                    if price_type == pr.meal_type:
                       price,ffp_mu,ffp_co,to_mu,sc = get_price(cr,day,pr,operator_id)                        
                       if price > 0:
                          menus.append(menutable_obj.create(cr,uid,{'venue_id'       :  venue.id,
                                                                    'operator_id'    :  user.partner_id.id,
                                                                    'ffp_mu'         :  ffp_mu,
                                                                    'ffp_co'         :  ffp_co,
                                                                    'to_mu'          :  to_mu,
                                                                    'pp_person'      :  price,
                                                                    'menu_id'        :  m.id,
                                                                    'booking_date'   :  date,
                                                                    'service_charge' :  sc,
                                                                    'price_type'     :  price_type,
                                                                    'food_type'      :  'meal',
                                                                    'website_session_id' : session_id })) 
                          
            drinks = []            
            for d in venue.drink_ids:
                if d.rest_price > 0:
                  cr.execute(""" select 
                        (select (om.markup_perc/100) as menu_mrkup
                         from rel_om_menu rom
                         inner join cc_operator_markup om on om.id = rom.omarkup_id
                         where om.partner_id = """+str(operator_id)+""" and om.restaurant_id = """+str(d.partner_id.id)+""" and rom.menu_id = """+str(d.id)+"""
                        ) as menu_mrkup
                       ,(select (markup_perc/100) from cc_operator_markup where partner_id = """+str(operator_id)+""" and restaurant_id = """+str(d.partner_id.id)+""" and mrkup_lvl = 'rest_lvl') as rest_mrkup
                       ,(select (markup_perc/100) from res_partner where id = """+str(operator_id)+""") as glb_mrkup""")
                  to_mu = cr.dictfetchone()
                  drinks.append(menutable_obj.create(cr,uid,{'venue_id'        :  venue.id,
                                                            'operator_id'      :  user.partner_id.id,
                                                            'pp_person'        :  d.rest_price,
                                                            'menu_id'          :  d.id,
                                                            'booking_date'     :  date,
                                                            'ffp_mu'           :  d.markup,
                                                            'to_mu'            :  round(d.to_price * (to_mu['menu_mrkup'] or to_mu['rest_mrkup'] or to_mu['glb_mrkup'] or 0),1),
                                                            'food_type'        :  'drink' ,
                                                            'service_charge'   :  d.to_price - (d.rest_price + d.markup),
                                                            'website_session_id' : session_id
                                                            }))
            drinks = menutable_obj.search(cr, uid, [('id','in',drinks)],order='pp_person')
                  
            menu_data = []              
            for m in menutable_obj.browse(cr,uid,menus):
                type_list = []
                if price_type in ('bf_non_premium','bf_standard','bf_premium'):
                   type_list = ['bf_non_premium','bf_standard','bf_premium']
                elif price_type in ('l_non_premium','l_standard','l_premium'):
                   type_list = ['l_non_premium','l_standard','l_premium']
                elif price_type in ('at_non_premium','at_standard','at_premium'):
                   type_list = ['at_non_premium','at_standard','at_premium']
                elif price_type in ('d_non_premium','d_standard','d_premium'):
                   type_list = ['d_non_premium','d_standard','d_premium']
                type_list.remove(price_type)
                pricing_ids = pricing_obj.search(cr,uid,[('menu_id','=',m.menu_id.id),('meal_type','in',type_list)])
                non_price = p_price = std_price = non_mu = p_mu = std_mu = non_co = p_co = std_co = non_to_mu = p_to_mu = std_to_mu = 0.00
                non_sc = p_sc = std_sc = 0.00
                
                #getting the other 2 meal type price to show on website 
                for p in pricing_obj.browse(cr,uid,pricing_ids):
                       if p.meal_type in ('bf_non_premium', 'l_non_premium', 'at_non_premium','d_non_premium'):
                          non_price,non_mu,non_co,non_to_mu,non_sc = get_price(cr,day,p,operator_id)
                       elif p.meal_type in ('bf_premium', 'l_premium', 'at_premium','d_premium'):
                          p_price,p_mu,p_co,p_to_mu,p_sc = get_price(cr,day,p,operator_id)
                       elif p.meal_type in ('bf_standard', 'l_standard', 'at_standard','d_standard'):
                          std_price,std_mu,std_co,std_to_mu,std_sc = get_price(cr,day,p,operator_id)     
                    
                menu_data.append({'m_name':m.menu_id.name + (m.menu_id.course and ' (' + course[m.menu_id.course] + ' course)' or ''),
                                  'm_desc':m.menu_id.description,
                                  'm_id':m.id,
                                  'symbol':symbol,
                                  'pp_person':(m.pp_person + m.ffp_mu + m.to_mu + m.service_charge),
                                  'non_price' : non_price + non_mu + non_to_mu + non_sc,
                                  'p_price' : p_price + p_mu + p_to_mu + p_sc ,
                                  'std_price':std_price + std_mu + std_to_mu + std_sc,
                                  'to_mu' : m.to_mu,
                                  'kids_menu' : m.menu_id.kids_menu,
                                  'min_covers' : m.menu_id.min_covers,
                                  'sc_incl'    : not m.menu_id.sc_included and m.menu_id.service_charge and True or False})
            
            #sorting menus based on price 
            menu_data = sorted(menu_data, key=itemgetter('pp_person'))     
            #Getting website color based on weather incoming is white labeled or not. To highlight to markup added menus     
            wcolor = '#793487'
            if user.role == 'client_cust':
               wcolor = '' 
            elif user.is_wlabeling:
               wcolor = user.partner_id.wbsite_color or user.partner_id.parent_id and user.partner_id.parent_id.wbsite_color or ''     
              
            return menu_data, time_rec, request.website._render("fit_website.drinks_table_template", {'drinks': drinks and menutable_obj.browse(cr, suid, drinks) or False,'user':user}), venue.max_covers, wcolor,request.website._render("fit_website.popover_content", {'times_list': time_rec,'avlblty_dict':avlblty_dict})
            
      @http.route(['/onmouseover_availabilty'], type='json', auth="public", website=True, multilang=True)
      def onmouseover_availabilty(self, res_id = '', booking_date='', booking_type='', booking_time='', booking_covers='', min_time='', max_time='', json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          time_obj = request.registry.get('cc.time')
          time_rec = []
          avlblty_dict = {}
          covers = booking_covers
          booking_date = datetime.strptime(booking_date, "%d/%m/%Y").strftime("%Y-%m-%d")
          day = datetime.strptime(booking_date, "%Y-%m-%d").strftime("%A").lower()
          time_ids = time_obj.search(cr, uid, [('name','>=',min_time),('name','<',max_time)])
          for t in time_obj.browse(cr,uid,time_ids):
                blackout_ids = request.registry.get('cc.black.out.day').search(cr,uid,[('partner_id','=',res_id),
                                                                           ('date','<=',booking_date),('date_to','>=',booking_date),
                                                                           ('from_time_id.name','<=',t.name),
                                                                           ('to_time_id.name','>=',t.name)])
                if blackout_ids:
                    continue
                cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) as alloc_cvoers , id from cc_time_allocations
                        where partner_id = """ + str(res_id) +"""
                        and type = '""" + str(booking_type) + """'
                        and name = '""" + str(day) + """'"""
                        """ group by id """)

                alloc_covers = cr.fetchone()

                cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end)
                      from crm_lead
                      where state in ('open','done')
                      and conv_dob = '""" + str(datetime.strptime(booking_date, "%Y-%m-%d").strftime("%d-%b-%Y")) + """'
                      and conv_tob = '""" + str(t.name) + """'
                      and restaurant_id = '""" + str(res_id) + """'
                  """)
                tot_covers = cr.fetchone()
                avlblty_dict[t.name] = (alloc_covers and alloc_covers[0] or 0) - (tot_covers and tot_covers[0] or 0)
                time_rec.append(t.name)
          return request.website._render("fit_website.popover_content", {'times_list': time_rec,'avlblty_dict':avlblty_dict})

      # Function for "PROCEED" Button..
      @http.route(['/capital_centric/fit/search/result/booking_done/'], type='json', auth="public", website=True, multilang=True)
      def menu_select_proceed(self, venue_id, req_time, menu_ids, type=None, event_id=None, json=None):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False})
        loginuid = request.session.uid or request.uid       
        partner_obj = request.registry.get('res.partner')
        menu_obj = request.registry.get('cc.menus')
        time_obj = request.registry.get('cc.time')
        allocation_obj = request.registry.get('cc.time.allocations')
        menutable_obj = request.registry.get('cc.menus.table')
        mdetails_obj = request.registry.get("cc.menu.details")          
        lead_obj     = request.registry.get("crm.lead")
        info_obj     = request.registry.get("cc.send.rest.info")
        user_obj     = request.registry.get('res.users')
        user = user_obj.browse(cr,uid,loginuid)
        session_id = request.httprequest.session.get('website_session_id')
        if user.name == 'Public user':
           user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',user.cc_url)])
           user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)

        product_ids  = request.registry.get("product.product").search(cr,uid,[('name_template','=','FIT for Purpose')])
        
        title_obj = request.registry.get('res.partner.title')
        title_ids = title_obj.search(cr, uid, [])
        titles = title_obj.browse(cr, suid, title_ids)
        
        operator = user.partner_id
        if user.role in ('client_user','client_mng','client_cust'):
             operator = user.partner_id and user.partner_id.parent_id or False
        #Restaurant
        venue = partner_obj.browse(cr, suid, venue_id)
           
        covers = 0
        subtotal = vat_total = 0.00     
        price_type = ''
        day = ''
        sqlstr = ''
        frm_tm = ''
        to_tm = ''
        booking_date=''
        event = False
        alloc_covers = False
        day = datetime.strptime(json.get('resv_date'), "%d/%m/%Y").strftime("%A").lower()
        for m in  menutable_obj.browse(cr,uid,menu_ids):
            booking_date = datetime.strptime(json.get('resv_date'), "%d/%m/%Y").strftime("%Y-%m-%d")
            if m.food_type != 'drink':covers += m.guest 
            if req_time:
               sqlstr = ''

            subtotal += m.total_price
            vat_total += m.vat 
        
        booking_date = (parser.parse(''.join((re.compile('\d')).findall(booking_date)))).strftime('%d-%b-%Y')
        if not user.is_group:
            if m.food_type == 'events':# Food type Events will be changed to meal while creating lead
               event = request.registry.get('cc.events').browse(cr, uid, int(event_id))

               cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end)
                             from crm_lead
                             where state in ('open','done')
                             and conv_dob = '""" + str(booking_date) + """'
                             and conv_tob = '""" + str(req_time) + """'
                             and restaurant_id = '""" + str(venue.id) + """'
                              """)
               tot_covers = cr.fetchone()
               if (int(tot_covers[0]) +  covers) > event.covers:
                  return 'unavilability',req_time,booking_date
            else:
                #Checking Availability
                cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) as covers
                                  , id
                                  , (case when sum(cap) is null then 0 else sum(cap) end) as shift_covers
                                  , min(std_frm_id) as from_id
                                  , max(std_to_id) as to_id
                                    from cc_time_allocations
                                    where partner_id = """ + str(venue.id) +"""
                                    and type = '""" + str(type) + """'
                                    and name = '""" + str(day) + """'"""+ str(sqlstr)+
                                    """ group by id """)

                alloc_covers = cr.dictfetchone()
                if alloc_covers:
                   cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) from crm_lead
                                 where state in ('open','done') and conv_dob = '""" + str(booking_date) +"""'
                                 and conv_tob='"""+ str(req_time) + """'
                                 and restaurant_id = """ + str(venue.id))
                   tot_covers = cr.fetchone()
                   if int(tot_covers[0]) + covers > int(alloc_covers['covers']):
                      return 'unavilability',req_time,booking_date

                   cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) from crm_lead
                                 where state in ('open','done') and conv_dob = '""" + str(booking_date) +"""'
                                 and conv_tob in (select name from cc_time where id between """ +str(alloc_covers['from_id'])+""" and """ +str(alloc_covers['to_id'])+ """)
                                 and restaurant_id = """ + str(venue.id))
                   totbkd_covers = cr.fetchone()
                   if (int(alloc_covers.get('shift_covers',0)) > 0) and (int(totbkd_covers and totbkd_covers[0] or 0) + covers) > int(alloc_covers.get('shift_covers')):
                      return 'shift_unavailable',req_time,booking_date
                   
            #Balance Validation 
            limit = operator.booking_limit or 0.00
            acc_bal = -(operator.credit + limit)
            if operator.payment_type == 'prepaid' and acc_bal < (subtotal + vat_total):
                return 'low_balance'
                                  
        menu_dtls=[]
        total_covers = 0          
        Invoice_Type = 'to_client'
        bking_date = ''
        contact_id = False
        cont_email = ''
        price_type = ''
        now = time.strftime("%Y-%m-%d")
                              
        for m in menutable_obj.browse(cr, suid, menu_ids):
            menus = [0,False]
            bking_date = m.booking_date or datetime.strptime(json.get('resv_date'), "%d/%m/%Y").strftime("%Y-%m-%d")
            
            if not price_type:price_type = m.price_type
            if m.guest > 0:
               menus.append(mdetails_obj.onchange_menu_option(cr, user.id, [] , m.id,'',m.guest, False, '', {'fit_purpose':True})['value'])
               menus[2].update({'top_markup':m.to_mu})
               if user.is_wlabeling:
                  if operator.comision_type == 'fixed_amt':
                     menus[2].update({'top_markup':operator.commission})
                  if operator.comision_type == 'fixed_perc':
                     menus[2].update({'top_markup':m.ffp_mu * ((operator.commissiom or 0 )/100)})  
               menu_dtls.append(menus)   
               if m.food_type in ('meal','events'):
                  total_covers += m.guest
               if m.ffp_co > 0:        
                  Invoice_Type = 'to_both'
                            
        dob_frmt = bking_date + ' ' + (req_time or '00:00') 
        local = pytz.timezone (user.tz or 'Europe/London') 
        naive = datetime.strptime (dob_frmt, "%Y-%m-%d %H:%M")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone (pytz.utc)           
    
        for c in venue.contact_ids:
            if not contact_id:
               contact_id = c.id
            cont_email += c.email + ','          
        cont_email = cont_email[0:(len(cont_email) - 1)]                                      
          
        info_vals = {'restaurant_id'   : venue.id,
                     'inv_address_id'  : venue.parent_id.id,
                     'cont_address_id' : contact_id,
                     'menu_dt_ids'     : menu_dtls,
                     'invoice_type'    : Invoice_Type,
                     'product_id'      : product_ids[0],
                     'contact_email'   : cont_email, 
                     'tax_srvc_chrg'   : False,
                     'price_type'      : price_type 
                    }
        description = 'Complete booking for ' + (venue.name) + (event and ' - ' + event.name or '')
        if user.is_group:
           description = 'Booking request for ' + (venue.name) + (event and ' - ' + event.name or '')
        lead_vals = {'covers'          : total_covers,    
                     'name'            : description,
                     'partner_id'      : operator.id,
                     'service_type'    : 'venue',
                     'passen_type'     : user.is_group and 'group' or 'fit',
                     'type'            : 'opportunity',
                     'info_ids'        : [[0,False, info_vals]],
                     'date_requested'  : utc_dt,
                     'conv_dob'        : (parser.parse(''.join((re.compile('\d')).findall(bking_date)))).strftime('%d-%b-%Y'),
                     'conv_tob'        : req_time,
                     'user_id'         : 1, 
                     'sales_person'    : user.id,
                     'send_confirmation' : user.role == 'client_cust' and True or False,
                     'event_id'         : event and event.id or False,
                     'alloc_id'         : alloc_covers and alloc_covers['id'] or False,
                     'website_session_id' : session_id,
                     'referral_link'   : request.httprequest.session.get('referral_link'),
                     'lead_res_type'   : type,
                     'lead_day'        : day,
                    }
        
        if user.prev_booking_id:
           lead_vals.update({'cust_ref'     : user.prev_booking_id.cust_ref or '',
                             'partner_name' : user.prev_booking_id.partner_name or '',
                             'contact_name' : user.prev_booking_id.contact_name or '',
                             'email_from'   : user.prev_booking_id.email_from or '',
                             'mobile'       : user.prev_booking_id.mobile or '',
                             'title'        : user.prev_booking_id.title and user.prev_booking_id.title.id  or False,
                             'send_confirmation' : user.prev_booking_id.send_confirmation or False}) 
           request.registry.get('res.users').write(cr, suid, [uid], {'prev_booking_id':False})
        if json.get('lead_id') and json.get('type_change') == 'no':
            lead_browse = lead_obj.browse(cr, suid, int(json.get('lead_id')))
            stage_ids = request.registry.get("crm.case.stage").search(cr,uid,[('name','=','Confirmed')])[0]
            if lead_browse.state in ('open','draft'):
                lead_obj.write(cr, suid, [int(json.get('lead_id'))], {'state':'draft','stage_id': stage_ids})
            # info_obj.cc_create_invoices(cr, user.id, [int(json.get('lead_id'))])
            cr.execute(""" delete from cc_send_rest_info where lead_id = """+str(json.get('lead_id')))
            lead = lead_obj.write(cr, suid, [int(json.get('lead_id'))], lead_vals)
        else:
            lead = lead_obj.create(cr, suid, lead_vals)
        if lead:
            menutable_obj.unlink(cr,suid,menu_ids)
            if uid != user.id:
               if not request.httprequest.session.get('website_lead_id'):
                  request.httprequest.session['website_lead_id'] = [lead]
               else:
                  request.httprequest.session['website_lead_id'].append(lead)

        cr.execute("""select info.id 
                      from cc_send_rest_info info 
                      inner join crm_lead l on l.id = info.lead_id
                      where l.state = 'draft' and l.date_requested::date > '""" + now+"""'
                      and l.partner_id = """ + str(operator.id ) +
                      """ and l.sales_person = """ + str(user.id) +
                      """ order by info.id asc""")
        info = cr.fetchall()
        info_ids = []
        for i in info:
            info_ids.append(i[0])
        
        if user.id != uid:
           lead_ids = lead_obj.search(cr, uid, [('state','=','draft'),('website_session_id','=',request.httprequest.session.get('website_session_id') or [])])
           # lead_ids = request.httprequest.session.get('website_lead_id',[])
           info_ids = info_obj.search(cr, uid, [('lead_id','in',lead_ids)])
        rest_info = info_obj.browse(cr, uid, info_ids)
        
        h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
        values = {'info_list':rest_info or [],
                  'user':user,
                  'info_ids':info_ids,
                  'title_ids' : titles,
                  'url' : h, 
                  'uid' : user_obj.browse(cr, uid, uid) 
                  }
        
        subtotal = tax_amt = total = top_markup = 0.00 
        for info in rest_info:
            for m in info.menu_dt_ids:
                if m.food_type == 'meal':
                   subtotal += (m.top_service_charge +  ((m.top_menu_price / (100 + 20.00)) * 100)) * m.no_of_covers
                   tax_amt += (m.top_menu_price - ((m.top_menu_price / (100 + 20.00)) * 100)) * m.no_of_covers
                elif m.food_type == 'drink':
                    tax_amt += (m.top_drinks_price - ((m.top_drinks_price / (100 + 20.00)) * 100)) * m.no_of_covers
                    subtotal += (m.top_service_charge +((m.top_drinks_price / (100 + 20.00)) * 100)) * m.no_of_covers
                                                      
                top_markup += m.top_markup * m.no_of_covers
            total += info.tot_top_price
        values.update({'subtotal':subtotal,
                       'vat':tax_amt,
                       'total':total,
                       'symbol':user.company_id.currency_id.symbol,
                        'top_markup':top_markup,
                        'type_change':json and json.get('type_change') or 'yes',
                       'session_id' : session_id
                       })    
        return request.website._render("fit_website.booking_completion",values)
  
#On Click Of "Complete Booking" Button creation of lead,invoice and proceed to payments  
      @http.route(['/fit_website/guest_details/'], type='http', auth="public", website=True ,multilang=True)
      def complete_booking(self , *args, **post):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context

          loginuid = request.session.uid or request.uid
          if post is None:
             post = {} 
          user = request.registry.get('res.users').browse(cr,uid,loginuid)          
          mtable_obj = request.registry.get("cc.menus.table")
          mdetails_obj = request.registry.get("cc.menu.details")          
          lead_obj     = request.registry.get("crm.lead")
          info_obj     = request.registry.get("cc.send.rest.info")           
          invoice_obj  = request.registry.get('account.invoice')
          user_obj     = request.registry.get('res.users')
          if user.name == 'Public user':
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',user.cc_url)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)

          h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
          payment_type = user.partner_id.payment_type
          operator = user.partner_id
          if user.role in ('client_user','client_mng','client_cust'):
             post['partner_id'] = user.partner_id and user.partner_id.parent_id and user.partner_id.parent_id.id or False
             operator = user.partner_id.parent_id 
             payment_type = user.partner_id and user.partner_id.parent_id and user.partner_id.parent_id.payment_type or ''

          now = time.strftime("%Y-%m-%d") 
          info_ids = []
          lead_ids = [] 
          wrldpay_typ = post.get('paymentType','')
          inv_date = False
          due_date = False
          
          if post.get('from_wch') == 'continue' or user.is_group:
             if user.is_group:
                if post.get('info_ids','[]'):
                 info_ids = list(eval(post.get('info_ids')))  
                 stage_ids = request.registry.get("crm.case.stage").search(cr,uid,[('name','=','Requested')])[0]
                 for info in info_obj.browse(cr, uid, info_ids):
                     lead_obj.write(cr, uid, [info.lead_id.id], {'stage_id':stage_ids})
             return request.redirect("/")
                  
          if post.get('from_wch') == 'complete':
             if post.get('info_ids','[]'):
                 info_ids = list(eval(post.get('info_ids')))
                 prev_rec = False
                 covers = 0
                 r_dict={}
                 t_dict={}
                 for info in info_obj.browse(cr,uid,info_ids):#To check Bookings made is in same month or different month
                     t_dict={}
                     # meal_type = ''
                     # if   info.price_type   in ('bf_non_premium','bf_standard','bf_premium'):meal_type = 'break_fast'
                     # elif info.price_type   in ('l_non_premium','l_standard','l_premium'):meal_type = 'lunch'
                     # elif info.price_type   in ('at_non_premium','at_standard','at_premium'):meal_type = 'at'
                     # elif info.price_type   in ('d_non_premium','d_standard','d_premium'):meal_type = 'dinner'
                     day = datetime.strptime(info.lead_id.date_requested, "%Y-%m-%d %H:%M:%S").strftime("%A").lower()
                     covers = info.lead_id.covers
                     stime = info.lead_id.conv_tob
                     rest = info.restaurant_id.id
                     
                     if rest not in r_dict:
                        r_dict.update({rest:t_dict}) 
                        
                     if stime not in r_dict[rest]:
                        t_dict.update({stime:covers})
                     else:
                        r_dict[rest][stime] = r_dict[rest][stime]+covers

                     if info.lead_id.event_id:
                        cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end)
                                      from cc_events where id = """+ str(info.lead_id.event_id and info.lead_id.event_id.id))
                     else:
                        cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) from cc_time_allocations
                                      where partner_id = """ + str(info.restaurant_id.id) +"""
                                      and type = '""" + str(info.lead_id.lead_res_type) + """'
                                      and name = '""" + str(day) + """'""")
                     alloc_covers = cr.fetchone()
                     
                     if alloc_covers:
                        booking_date = (parser.parse(''.join((re.compile('\d')).findall(info.lead_id.date_requested)))).strftime('%Y-%m-%d')
                        cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) from crm_lead
                                      where state in ('open','done') and date_requested::date ='""" + str(booking_date) +"""'
                                      and conv_tob='"""+ str(info.lead_id.conv_tob or '') + """'
                                      and restaurant_id = """ + str(info.restaurant_id.id))
                        tot_covers = cr.fetchone()
                        if int(tot_covers[0]) + r_dict[rest][stime] > int(alloc_covers[0]) :
                           return request.redirect("/capital_centric/operator/my_cart?info_id="+str(info.id))

                     blackout_ids = request.registry.get('cc.black.out.day').search(cr,uid,[('partner_id','=',info.restaurant_id.id),
                                                                           ('date','<=',booking_date),('date_to','>=',booking_date),
                                                                           ('from_time_id.name','<=',info.lead_id.conv_tob),
                                                                           ('to_time_id.name','>=',info.lead_id.conv_tob)])
                     if blackout_ids:
                        return request.redirect("/capital_centric/operator/my_cart?info_id="+str(info.id))
                       
                     if payment_type == 'pay_adv':
                        payment_type = 'monthly'      
                        bk_date = (parser.parse(''.join((re.compile('\d')).findall(info.lead_id.date_requested)))).strftime('%Y-%m-20')              
                        bk_date = datetime.strptime(bk_date, "%Y-%m-%d") - relativedelta(months=1)                         
                        today = datetime.strptime(now, "%Y-%m-%d")
                        if bk_date < today:
                           inv_date = bk_date + relativedelta(months=1)
                        else:
                           inv_date = bk_date                            
                        due_date = inv_date + relativedelta(days=10)
                 if payment_type == 'on_purchase': 
                    card_chrgs = 0.00  
                    if wrldpay_typ in ('MAES','DMC','VIED','VISD'):
                       card_chrgs = operator.debit_charges and (operator.debit_charges/100) or 0.00
                    elif wrldpay_typ in ('VISA','MSCD'):
                       card_chrgs = operator.credit_charges and (operator.credit_charges/100) or 0.00                     
                    return request.redirect("https://secure.worldpay.com/wcc/purchase?instId=1000460&cartId=" +str(user.partner_id.name) +"&amount=" + str(post.get('total',0.00)) + "&currency=GBP&paymentType=" +str(wrldpay_typ)+"&desc=Restaurant+Booking+on+FIT+for+Purpose&CM_acc_type="+str(payment_type)+"&CM_loginid="+str(user.id)+"&CM_infoids="+str(info_ids)+"&CM_URL="+str(h)+"&CM_Card_Chrgs="+str(card_chrgs))
                                  
                 for info in info_obj.browse(cr,uid,info_ids):
                     info_obj.cc_create_invoices(cr, uid, [info.id], context=None)
                     lead_ids.append(info.lead_id.id)
                     
                 invoice_ids = invoice_obj.search(cr,uid,[('lead_id','in',lead_ids),('type','=','out_invoice')])
                 invoice = invoice_obj.browse(cr, uid, invoice_ids or False)
                 for inv in invoice:
                     if payment_type == 'prepaid':
                          invoice_obj.write(cr,uid,[inv.id],{'date_due':time.strftime("%Y-%m-%d")}) 
                          lead_obj.create_payment_rec(cr, uid, inv, post=None, context=None)
                      
                     elif payment_type == 'monthly':
                         if not inv_date and not due_date:
                           inv_date =  datetime.strptime((parser.parse(''.join((re.compile('\d')).findall(inv.booking_date)))).strftime('%Y-%m-01'), "%Y-%m-%d") + relativedelta(months=1)
                           day = '30'
                           if inv.booking_date and ((datetime.strptime(inv.booking_date,'%Y-%m-%d %H:%M:%S') + relativedelta(months=1)).month == 2):
                              day = '28' 
                           due_date =  (datetime.strptime(inv.booking_date, "%Y-%m-%d %H:%M:%S") + relativedelta(months=1)).strftime('%Y-%m-'+day)
                         invoice_obj.write(cr,uid,[inv.id],{'date_invoice':inv_date,'date_due':due_date})  
                                    
             for info in info_obj.browse(cr,uid,info_ids):        
                 toptemplate_id = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Booking Confirmation To Customer')])
                 vtemplate_id   = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Booking Confirmation To Venue1')])
                 gutemplate_id  = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Booking Confirmation To Guest')])
                 if post.get('type_change') == 'no':
                    toptemplate_id = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Customer')])
                    vtemplate_id = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Venue')])
                    gutemplate_id  = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Guest')])
                    if toptemplate_id:
                       request.registry.get("email.template").send_mail(cr, uid, toptemplate_id[0], info.id, force_send=True, context=None)
                    if vtemplate_id:
                       request.registry.get("email.template").send_mail(cr, uid, vtemplate_id[0], info.id, force_send=True, context= {'tmp_name':'Enquiry - Amendment Confirmation To Venue'})
                    if gutemplate_id and info.lead_id.send_confirmation:
                       context = {}
                       request.registry.get("email.template").send_mail(cr, uid, gutemplate_id[0], info.id, force_send=True, context=None)
                 else:
                     if toptemplate_id:
                        request.registry.get('email.template').send_mail(cr, uid, toptemplate_id[0], info.id, force_send=True, context=None)
                        context = {}
                     if vtemplate_id:
                        request.registry.get('email.template').send_mail(cr, uid, vtemplate_id[0], info.id, force_send=True, context={'tmp_name':'Enquiry - Booking Confirmation To Venue1'})
                     if gutemplate_id and info.lead_id.send_confirmation:
                        context = {}
                        request.registry.get('email.template').send_mail(cr, uid, gutemplate_id[0], info.id, force_send=True, context=None)
                            
             return request.website.render("fit_website.thnk_u_pg",{'response':'for_booking','user':user,'uid':False})
     
      @http.route(['/fit_website/payment_status/'], type='http', auth="public", website=True ,multilang=True)
      def worldpay_response(self , *args, **post):
          cr, uid, suid, context = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          _logger.error('WORLD PAY POST: %s',post)
          h = post.get('CM_URL')
          _logger.error('WORLD PAY FORM: %s %s',h,uid)  
          red_url = 'http://' + h
          red2_url= 'http://' + h +'/capital_centric/operator/bookings'
          img_url = 'http://' + h
          if context is None: context = {}
            
          is_wlabel = False 
          if h not in ('bookamenu.com','fitforpurposeonline.com','cc.trabacus.com'):
             is_wlabel = True
               
          if post is None:
             post = {}
          values ={}   
          uid = post.get('CM_loginid') and int(post.get('CM_loginid')) or SUPERUSER_ID
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,uid)

#           _logger.error('WORLD PAY USWER: %s',user)
          invoice_obj = request.registry.get('account.invoice')
          invoiceln_obj = request.registry.get('account.invoice.line')          
          lead_obj    = request.registry.get('crm.lead')
          info_obj    = request.registry.get('cc.send.rest.info')
          templ_obj   = request.registry.get('email.template')
          stage_obj   = request.registry.get('crm.case.stage')
          prod_obj    = request.registry.get('product.product')
          
          info_ids = list(eval(post.get('CM_infoids','[]')))
          stage_ids =  stage_obj.search(cr,uid,[('name','=','Lost')])

          lead_ids = []
          inv_ids  = []
          prod_ids = prod_obj.search(cr,uid, [('name','=','Credit/Debit Card Charges')])
          if prod_ids:prod = prod_obj.browse(cr, uid, prod_ids[0])
          
          if post.get('rawAuthMessage') == 'cardbe.msg.authorised': 
             if post.get('CM_acc_type','') in ('prepaid','monthly','pay_adv'):
                inv_ids = post.get('CM_Inv_Ids') and '[' + post.get('CM_Inv_Ids') + ']' 
                inv_ids = inv_ids and eval(inv_ids)                  
                     
             for info in info_obj.browse(cr,uid,info_ids):
                 info_obj.cc_create_invoices(cr, uid, [info.id], context=None)
                 if post.get('CM_Card_Chrgs'):
                    invids = invoice_obj.search(cr, uid, [('lead_id','=', info.lead_id.id),('type','=','out_invoice')])
                    inv = invoice_obj.browse(cr,uid,invids and invids[0])
                    cardchrgs = round(inv.amount_total * (post.get('CM_Card_Chrgs') and float(post.get('CM_Card_Chrgs')) or 0.00),2)                     
                    invln_vals = {'origin': info.lead_id.name,
                                  'account_id' : prod.property_account_income and prod.property_account_income.id,
                                  'quantity': 1,
                                  'discount': 0,
                                  'uos_id': 1,
                                  'product_id': prod.id or False,
                                  'invoice_line_tax_id': [(6, 0, [x.id for x in prod.taxes_id])],
                                  'name':  prod.name_template + ' (' + str(post.get('cardType')) + ')' ,  
                                  'price_unit': cardchrgs,                                 
                                  'enq_dob' :info.lead_id.date_requested or False,
                                  'invoice_id': inv and inv.id
                                  } 
                    invoiceln_obj.create(cr, SUPERUSER_ID, invln_vals)
                    invoice_obj.button_compute(cr, uid, [inv.id])
                    inv_ids.append(inv.id)
                    
             _logger.error('Invoice_ids: %s',inv_ids)      
             lead_obj.create_payment_rec(cr, SUPERUSER_ID, inv_ids, post,context=None)
             
             #Send Confirmation Mails if payment type is "Payment on Purchase"        
             for info in info_obj.browse(cr,uid,info_ids):
                 toptemplate_id = templ_obj.search(cr,uid,[('name','=','Enquiry - Booking Confirmation To Customer')])
                 vtemplate_id   = templ_obj.search(cr,uid,[('name','=','Enquiry - Booking Confirmation To Venue1')])
                 gutemplate_id  = templ_obj.search(cr,uid,[('name','=','Enquiry - Booking Confirmation To Guest')])
                  
                 if toptemplate_id:
                    templ_obj.send_mail(cr, uid, toptemplate_id[0], info.id, force_send=True, context=None)
                 if vtemplate_id:
                    templ_obj.send_mail(cr, uid, vtemplate_id[0], info.id, force_send=True, context=None)
                 if gutemplate_id and info.lead_id.send_confirmation:
                    templ_obj.send_mail(cr, uid, gutemplate_id[0], info.id, force_send=True, context=None)
                                  
             values = {'response' : 'success',
                       'transId'  : post.get('transId'),
                       'red_url'  : red_url,
                       'red2_url' : red2_url,
                       'img_url'  : img_url,  
                       'user'     : user,
                       'uid'      :False,
                       'is_wlabel': is_wlabel}
             
          elif post.get('rawAuthMessage') == 'trans.cancelled':
              for i in info_obj.browse(cr,uid,info_ids):
                  if stage_ids:                 
                     lead_obj.write(cr,uid,[i.lead_id.id],{'stage_id':stage_ids[0]})
              values = {'response' : 'failure',
                        'red_url'  : red_url,
                        'red2_url'  : red2_url,
                        'img_url'  : img_url,
                        'user'     : user,
                        'uid'      : False,
                        'is_wlabel': is_wlabel}
                    
          return request.website.render("fit_website.thank_you_page",values)
      
      @http.route(['/fit_website/Thankyou/'], type='http', auth="public", website=True ,multilang=True)
      def Thank_you(self ,*args, **post):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user = request.registry.get('res.users').browse(cr,SUPERUSER_ID,SUPERUSER_ID)
#           _logger.error('I AM CALLED')        
#           _logger.error('WORLD PAY FORM: %s', request.website._render("fit_website.thank_you_page",{}))
          return request.website.render("fit_website.thank_you_page",{'user':user})

      @http.route(['/capital_centric/color/'], type='http', auth="public", website=True ,multilang=True)
      def website_color(self ,*args, **post):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user = request.registry.get('res.users').browse(cr,uid,loginuid)
          operator = user.partner_id
          if user.role == 'client_mng':
             operator = user.partner_id.parent_id and user.partner_id.parent_id or False
              
          request.registry.get('res.partner').write(cr,uid,[operator.id],{
                                                                                 'wbsite_color'     : post.get('wbsite_color'),
                                                                                 'header_color'     : post.get('header_color'),
                                                                                 'submenu_color'    : post.get('submenu_color'),
                                                                                 'font_website'     : post.get('font_website'),
                                                                                 'terms_conditions' : post.get('terms_conditions'),
                                                                                 'privacy_policy'   : post.get('privacy_policy'),
                                                                                 'about_us'         : post.get('about_us'),
                                                                          }) 
          return 

            
# Function to add Transaction Charge to total
      @http.route(['/capital_centric/add_transactionchrg/'], type='json', auth="public", website=True, multilang=True)
      def transaction_charge(self, info_ids, payment, json=None):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False}) 
        loginuid = request.session.uid or request.uid
        user = request.registry.get('res.users').browse(cr,uid,loginuid)
        info_obj = request.registry.get('cc.send.rest.info')
        symbol = user.company_id.currency_id.symbol
        total = 0
        info_ids = list(eval(info_ids))
        
        operator = user.partner_id
        if user.role != 'client':
           operator = user.partner_id.parent_id
            
        debit = operator.debit_charges and (operator.debit_charges/100) or 0.00
        credit = operator.credit_charges and (operator.credit_charges/100) or 0.00
         
        for i in info_obj.browse(cr, uid, info_ids):
            total += i.tot_top_price
        
        if payment in ('MAES','DMC','VIED','VISD'):
           debit_amt = round((total * debit),2)             
           return (total + debit_amt), debit_amt,symbol  
        elif payment in ('VISA','MSCD'):
           credit_amt =  round((total * credit),2)
           return (total + credit_amt), credit_amt,symbol
        return total,0,symbol
      
#Send Venue Unavailability Request mail To Capital Centric      
      @http.route(['/capital_centric/request/availability'], type='json', auth="public", website=True)
      def request_availability(self , message, time, date, rest_name, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user = request.registry.get('res.users').browse(cr,uid,loginuid)
          email_from = email_to = 'fitforpurpose@capitalcentric.co.uk'
          operator = False
          if user and user.is_wlabeling:
             email_from = email_to = user.partner_id.email
             operator = user.partner_id
             if user.role != 'client':
                email_from = email_to = user.partner_id.parent_id.email
                operator = user.partner_id.parent_id  
          mail_obj = request.registry.get('mail.mail')
          
          
          body = """<div style="font-family:Calibri; font-size: 12pt; color: rgb(34, 34, 34); background-color: rgb(255, 255, 255); "> 
        """ + str(not user.is_wlabeling and '<img src="https://fitforpurposeonline.com/fit_website/static/src/img/fitcclogo.jpg" height="156" width="245">' or '') + """
        <br/><br/>
        Dear Team,<br/><br/>

        Name: """ + str(user.partner_id.display_name) + """<br/>
        Restaurant Name: """ + str(rest_name or '') + """<br/>
        Date: """  + str(date or '') +  """<br/>
        Time: """ + str(time or '') + """<br/>
        Message: """+ str(message or '' ) + """<br/>
        Email: """ + str(user.partner_id.email or '-') + """<br/>
        phone: """ + str(user.partner_id.phone or '-') + """<br/>
        
        
        <p>Thank you.</p>
        <p>Regards,<br/>
           """ + str(operator and operator.name or 'FIT For Purpose') + """ Team.</p>
                            
        <br/><br><div style="width: 375px; height: 20px; margin: 0px; padding: 0px; background-color:""" + str(operator and operator.wbsite_color or '#F2F2F2') + """; border-top-left-radius: 5px 5px; border-top-right-radius: 5px 5px; background-repeat: repeat no-repeat;">
<h3 style="margin: 0px; padding: 2px 14px; font-size: 12px; color: """ + str(operator and operator.submenu_color or 'black') + """;">
            <strong style="text-transform:uppercase;">""" + str(operator and operator.name or 'The FIT For Purpose')+ """ Team </strong></h3>
</div>
<div style="width: 347px; margin: 0px; padding: 5px 14px; line-height: 16px; background-color: #F2F2F2;">
<span style="color: #222; margin-bottom: 5px; display: block; ">
            """ + str(operator and operator.street or user.company_id.street) + """<br>
            """ + str(operator and operator.street2 or user.company_id.street2) + """<br>
            """ + str(operator and operator.city or user.company_id.city) +""" """ + str(operator and operator.zip or user.company_id.zip) + """<br>
            """ + str(operator and operator.country_id and operator.country_id.name or user.company_id.country_id and user.company_id.country_id.name) + """<br></span>
<div style="margin-top: 0px; margin-right: 0px; margin-bottom: 0px; margin-left: 0px; padding-top: 0px; padding-right: 0px; padding-bottom: 0px; padding-left: 0px; ">
</div>
<p></p>
</div>
</div>"""

                 
          mail_id = mail_obj.create(cr, SUPERUSER_ID, {'email_from' : email_from,
                                    'email_to'   : email_to or '',
                                    'reply_to'   : user.partner_id.email or '',
                                    'subject'    : 'Request for availability from Tour Operator',
                                    'body_html'  : body,
                                    'auto_delete': False,})
          if mail_id:
             res = mail_obj.send(cr, uid, [mail_id], False, False, None)
                              
          return 
          
          
      # MarkUp Pricing dialog Box    
      @http.route(['/fit_website/markup_pricing/'], type='json', auth="public", website=True)
      def markup_pricing(self,db_id,restaurant_id,menu_id,partner_id, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          markup_obj = request.registry.get('cc.operator.markup')
          
          markup_id = db_id
          if db_id == None:
             try: 
                 markup_id = markup_obj.create(cr,uid,{ 'partner_id':partner_id,
                                                        'restaurant_id':restaurant_id,
                                                        'menu_id':menu_id})
                           
                 markup_obj.populate_pricing(cr, uid, [markup_id],context=None)
             except:                 
                 cr.rollback()
                 return request.website._render("fit_website.markup_pricing_template", {'error':"You Cannot select same Menu twice."})
                    
          return request.website._render("fit_website.markup_pricing_template", {'markup': markup_id and markup_obj.browse(cr, uid, markup_id) or False,})


#Cancel button in my_cart page...
      @http.route(['/capital_centric/remove_menu/<db_id>'], type='http', auth="public", website=True, multilang=True)
      def remove_sc_disc(self, db_id=None, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          menu_details_obj = request.registry.get('cc.menu.details')
          menud_ids = menu_details_obj.search(cr,uid,[('info_id','=',int(db_id)),('menu_id.sc_disc','=',True)])       
          info_obj = request.registry.get('cc.send.rest.info')
          tosc_mu = 0 
          for menu in  menu_details_obj.browse(cr, uid, menud_ids):
              tosc_mu = round((menu.top_service_charge *(menu.top_markup/menu.top_tot_top_price)),1)
              menu_details_obj.write(cr, uid, [menu.id], {'rp_service_charge': 0.00, 'top_service_charge' : 0.00, 'top_markup' : (menu.top_markup -  tosc_mu)})          
          info_obj.write(cr,uid,[int(db_id)],{})
          #Updating the Flag
          cr.execute("update crm_lead set is_servccharge = True where id = (select lead_id from cc_send_rest_info where id = " + db_id +" limit 1)")
          
          return request.redirect('/capital_centric/operator/my_cart')

# Saving Guest details entered on cart view      
      @http.route(['/fit_website/save_input_my_cart/'], type='json', auth="public", website=True)
      def save_input_my_cart(self, db_id, value, json=None):  
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          info_obj = request.registry.get('cc.send.rest.info')
          lead_obj = request.registry.get('crm.lead')
          info = info_obj.browse(cr,uid,db_id)
          if 'spcl_req' in value.keys():
              info_obj.write(cr, suid, [db_id], value)
              del value['spcl_req']              
              
          if 'spcl_req' not in value.keys():
              lead_obj.write(cr, suid, [info.lead_id.id], value)
          
          return
      
#Star Click on Search Page...
      @http.route(['/capital_centric/<path>/<int:rest_id>'], type='http', auth="public", website=True, multilang=True)
      def star(self, path, rest_id=None, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')
          partner_obj = request.registry.get('res.partner')
          user = user_obj.browse(cr,uid,loginuid)
          if path == 'star':
              for u in user.fav_rest_ids:
                  if u.id == rest_id:
                     user_obj.write(cr,SUPERUSER_ID,[loginuid],{'fav_rest_ids':[(3,rest_id)]})
                     rest_id = False
              if rest_id:
                 user_obj.write(cr,SUPERUSER_ID,[loginuid],{'fav_rest_ids':[(4,rest_id)]})
          elif path == 'checkbox':
              operator = user.partner_id
              if user.role == 'client_mng':
                 operator = user.partner_id.parent_id
              for r in  operator.contact_ids:
                  if r.id == rest_id:
                     partner_obj.write(cr,SUPERUSER_ID,[operator.id],{'contact_ids':[(3,rest_id)]})
                     rest_id = False
              if rest_id:
                 partner_obj.write(cr,SUPERUSER_ID,[operator.id],{'contact_ids':[(4,rest_id)]})
                           
          return
      
      POLLING_DELAY = 0.25
      TYPES_MAPPING = {'doc': 'application/vnd.ms-word',
                       'html': 'text/html',
                       'odt': 'application/vnd.oasis.opendocument.text',
                       'pdf': 'application/pdf',
                       'sxw': 'application/vnd.sun.xml.writer',
                       'xls': 'application/vnd.ms-excel',
                      }

      @http.route('/capital_centric/report/<int:id>', type='http', auth="public")
      def get_confirmationreport(self, id=None, token=None):
            cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
            user_obj = request.registry.get('res.users')
            info_obj = request.registry.get('cc.send.rest.info')
            
            user = user_obj.browse(cr, uid, uid)
            type = ''
            if user.role in ('client','clinet_mng','client_user','client_cust'):
               type ='top'
            if user.role in ('venue','venue_user','venue_mng','client_cust'):
               type ='rp'
            
            info_ids = info_obj.search(cr, uid, [('lead_id', '=', id)])
            info_id = info_ids and info_ids[0]
                                        
            rep_obj = request.registry.get('ir.actions.report.xml')
            report_name = 'to_bookingconfirm'            
            rep_data = rep_obj.pentaho_report_action(cr, uid, report_name, info_id, None, None)
            if type:
               rep_data['datas']={'variables':{'cc_type' : type}}             
            report_instance = openerp.addons.pentaho_reports.core.Report('report.' + report_name, cr, uid, info_id, rep_data['datas'], request.context)                                
            result, output_type = report_instance.execute()

            return request.make_response(result,headers=[('Content-Disposition', content_disposition('Booking_Voucher.pdf')),
                                                         ('Content-Type', 'application/pdf'),
                                                         ('Content-Length', len(result))])
      #Logout       
      @http.route('/capital_centric/logout', type='http' ,auth="public" ,website=True ,multilang=True)
      def logout_redirect(self, *args, **post):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          tracking_obj = request.registry.get('login.time.tracking')
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr, uid, uid)
          tracking_ids = tracking_obj.search(cr, uid, [('name','=',uid),('logout','=',False)])
          session_id = request.httprequest.session.get('website_session_id')
          if tracking_ids:
             cr.execute("update login_time_tracking set logout=%s where id in %s",(time.strftime("%Y-%m-%d %H:%M:%S"),tuple(tracking_ids),))
          cr.execute("delete from cc_menus_table where operator_id = %s and website_session_id = %s",(user.partner_id.id,session_id))  

          request.httprequest.session['website_session_id'] = False
          request.httprequest.session['website_previous_uid'] = False
          return request.redirect("/web/session/logout?redirect=/")
      
      # Saving Guest details entered on cart view      
      @http.route(['/fit_website/session_info/'], type='json', auth="public", website=True)
      def check_session(self, current_url, previous_url, json=None):  
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
#           user_obj = request.registry.get('res.users')
#           user = user_obj.browse(cr,uid,loginuid)
#           if user.prev_booking_id:
#               cr.execute("update res_users set prev_booking_id = False where id = %s",(user.id))
#           h = 'http://' + request.httprequest.environ['HTTP_HOST']+'/'
#           if not user.is_login and current_url not in (h) and previous_url:
#              return  h 
          return

      @http.route(['/get_availability'], type='json', auth="public", website=True)
      def get_availability(self, res_id = '', lead_id='', booking_date='', booking_type='', booking_time='', booking_covers='',json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          lead_obj = request.registry.get("crm.lead")
          if lead_id:
            lead_browse = lead_obj.browse(cr, uid, lead_id)
            covers = lead_browse.covers
          else:
            covers = booking_covers
          booking_date = datetime.strptime(booking_date, "%d/%m/%Y").strftime("%Y-%m-%d")
          day = datetime.strptime(booking_date, "%Y-%m-%d").strftime("%A").lower()
          #Checking Availability
          cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) as covers
                              , id
                              , (case when sum(cap) is null then 0 else sum(cap) end) as shift_covers
                              , min(std_frm_id) as from_id
                              , max(std_to_id) as to_id
                                from cc_time_allocations
                                where partner_id = """ + str(res_id) +"""
                                and type = '""" + str(booking_type) + """'
                                and name = '""" + str(day) +
                                """' group by id """)

          alloc_covers = cr.dictfetchone()
          if alloc_covers:
              cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) from crm_lead
                             where state in ('open','done') and conv_dob = '""" + str(booking_date) +"""'
                             and conv_tob='"""+ str(booking_time) + """'
                             and restaurant_id = """ + str(res_id))
              tot_covers = cr.fetchone()
              if int(tot_covers[0]) + covers > int(alloc_covers['covers']):
                  return False

              cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) from crm_lead
                             where state in ('open','done') and conv_dob = '""" + str(booking_date) +"""'
                             and conv_tob in (select name from cc_time where id between """ +str(alloc_covers['from_id'])+""" and """ +str(alloc_covers['to_id'])+ """)
                             and restaurant_id = """ + str(res_id))
              totbkd_covers = cr.fetchone()
              if (int(alloc_covers.get('shift_covers',0)) > 0) and (int(totbkd_covers and totbkd_covers[0] or 0) + covers) > int(alloc_covers.get('shift_covers')):
                  return False

          return True

      @http.route(['/get_time_slots'], type='json', auth="public", website=True)
      def get_time_slots(self, res_id = '', booking_date='', booking_type='', post=None, json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          avltimes = []
          symbol = '£'
          menu_str = drink_str = ''
          partner_obj = request.registry.get("res.partner")
          user_obj = request.registry.get('res.users')
          loginuid = request.session.uid or request.uid
          user = user_obj.browse(cr,uid,loginuid)
          operator = user.partner_id
          if post.get('parent_res_id'):
              res_id = post.get('parent_res_id')
          post['type'] = booking_type
          post['resv_date'] = booking_date
          post['location_id'] = post.get('location_id')
          post['called_frm'] = 'get_restaurants'
          post['res_id'] = res_id
          json_dict = self.westfield_search(path='', **post)
          if json_dict and json_dict[0]['avltimes']:
              for avl in json_dict[0]['avltimes'].split(','):
                  avltimes.append(avl)
          print "booking_date",booking_date
          day = datetime.strptime(datetime.strptime((booking_date),'%d/%m/%Y').strftime('%Y-%m-%d'), "%Y-%m-%d").strftime("%A").lower()
          print "day",day
          cr.execute(""" select   a.menu_id
                                 , (case when a.menu_mrkup is not null then round((a.price * a.menu_mrkup),1) + a.price
                                    else case when a.rest_mrkup is not null then round((a.price * a.rest_mrkup),1) + a.price
                                    else case when a.glb_mrkup is not null then round((a.price * a.glb_mrkup),1) + a.price
                                    else 0 end end end) as price
                                 , (case when a.menu_mrkup is not null then round((a.price * a.menu_mrkup),1)
                                    else case when a.rest_mrkup is not null then round((a.price * a.rest_mrkup),1)
                                    else case when a.glb_mrkup is not null then round((a.price * a.glb_mrkup),1)
                                    else 0 end end end) as to_mu
                           from
                           (
                                select  cm.partner_id as rest_id
                                  , cm.id as menu_id
                                  , case when cm.to_price = 0 then 0 else cm.to_price end  as price
                                  , (select (case when 'markup' = 'markup' then (om.markup_perc/100) else 0 end) as menu_mrkup
                                     from rel_om_menu rom
                                     inner join cc_operator_markup om on om.id = rom.omarkup_id
                                     where om.partner_id = """ + str(operator and operator.id or 0) + """
                                     and restaurant_id = cm.partner_id and rom.menu_id = cm.id) as menu_mrkup
                                  , (select (case when 'markup' = 'markup' then (markup_perc/100) else 0 end)
                                     from cc_operator_markup where partner_id = """ + str(operator and operator.id or 0) + """
                                     and restaurant_id = cm.partner_id and mrkup_lvl = 'rest_lvl') as rest_mrkup
                                  , (select (case when 'markup' = 'markup' then (markup_perc/100) else 0 end)
                                     from res_partner where id = """ + str(operator and operator.id or 0) + """) as glb_mrkup
                                from cc_menus cm
                                where cm.cc_fit = True and cm.active = True
                                and cm.food_type  in ('meal','drink')
                                and cm.to_price > 0 and cm.partner_id = """ + str(res_id) + """
                                and (case when '""" + post.get('type') + """' = 'break_fast' then cm.break_fast = True
                                else case when '""" + post.get('type') + """' = 'lunch' then cm.lunch=True
                                else case when '""" + post.get('type') + """' = 'at' then cm.afternoon_tea=True
                                else case when '""" + post.get('type') + """' = 'dinner' then cm.dinner=True end end end end)
                                and (case when '""" + day + """' = 'sunday' then cm.is_sun = True
                                else case when '""" + day + """' = 'monday' then cm.is_mon=True
                                else case when '""" + day + """' = 'tuesday' then cm.is_tue=True
                                else case when '""" + day + """' = 'wednesday' then cm.is_wed=True
                                else case when '""" + day + """' = 'thursday' then cm.is_thu=True
                                else case when '""" + day + """' = 'friday' then cm.is_fri=True
                                else case when '""" + day + """' = 'saturday' then cm.is_sat=True end end end end end end end)
                                and case when cm.start_date is not null and cm.end_date is not null then '"""+str(datetime.strptime((booking_date),'%d/%m/%Y').strftime('%Y-%m-%d'))+"""' BETWEEN cm.start_date AND cm.end_date  else true end
                                and cm.id not in (select menu_id from menu_top_hide_rel
                                      where top_id = """ + str(operator and operator.id or 0) + """)
				                and cm.id not in (select menu_id from menu_top_show_rel
                                      where top_id != """ + str(operator and operator.id or 0) + """
                                      and menu_id not in (select menu_id from menu_top_show_rel
                                                 where top_id =  """ + str(operator and operator.id or 0) + """))
                                order by cm.partner_id,cm.id
                           )a
                           order by a.rest_id """)
          to_mu = cr.dictfetchall()
          menu_price = to_mu and dict((m.get('menu_id'),m.get('price')) for m in to_mu)
          to_markup = to_mu and dict((m.get('menu_id'),m.get('to_mu')) for m in to_mu)
          for menu in partner_obj.browse(cr, uid, res_id).fit_menu_ids:
            course_str = ''
            if menu_price and menu_price.get(menu.id,0) > 0:
                if menu.course:
                    course_str = course_str + """("""+str(menu.course)+""" course )"""
                if menu.include_srvchrg == 'yes':
                    course_str = course_str + """<i class="fa fa-check-square-o" title="Service Charge Included" aria-hidden="true" style="padding-left: 5px;color: #ED1E6B;"></i>"""
                menu_str = menu_str + """<div class="order-menu-item clearfix"><div class="pull-left col-sm-9">
                            <h4 class="menu-name" data-id="""+str(menu.id)+""" data-food-type="""+str(menu.food_type)+""">
                            """+str(menu.name)+str(course_str)+"""</h4>
                            </div><div class="pull-right"><a class="btn btn-primary animation add_menu" onclick="add_menu($(this))">
                            <span class="price-new" data-price="""+str("%.2f" %menu_price.get(menu.id,0))+""" data-to-mu="""+str(to_markup and to_markup.get(menu.id,0))+"""
                            data-symbol="""+str(symbol)+""">"""+str(symbol)+str("%.2f" %menu_price.get(menu.id,0))+"""
                            </span><i class="fa fa-plus-circle"></i></a></div>
                            <div class="panel-group bootstarp-accordion pull-left col-sm-12" id="faq-accordion" role="tablist" aria-multiselectable="true">
                            <div class="panel"><div class="panel-heading" role="tab"><a role="button" data-toggle="collapse" data-parent="#faq-accordion"
                            href="#faq-accordion-one-"""+str(menu.id)+"""" aria-expanded="true" aria-controls="faq-accordion-one-1">Click here to see the menu</a>
                            </div><div id="faq-accordion-one-"""+str(menu.id)+"""" class="panel-collapse collapse" role="tabpanel">
                            <div class="panel-body"><div class="faq-thread"><textarea disabled="disabled" style="width: 100%;height: 50%;resize: none;background: white;border: none;overflow: auto;">
                            """+str(menu.description)+"""</textarea></div></div></div></div></div></div>"""

          for drink in partner_obj.browse(cr, uid, res_id).drink_ids:
            course_str = ''
            if menu_price and menu_price.get(drink.id,0) > 0:
                # if menu.course:
                #     course_str = course_str + """("""+str(menu.course)+""" course )"""
                if drink.include_srvchrg == 'yes':
                    course_str = course_str + """<i class="fa fa-check-square-o" title="Service Charge Included" aria-hidden="true" style="padding-left: 5px;color: #ED1E6B;"></i>"""
                drink_str = drink_str + """<div class="order-menu-item clearfix"><div class="pull-left col-sm-9">
                            <h4 class="menu-name" data-id="""+str(drink.id)+""" data-food-type="""+str(drink.food_type)+""">
                            """+str(drink.name)+str(course_str)+"""</h4>
                            </div><div class="pull-right"><a class="btn btn-primary animation add_menu" onclick="add_menu($(this))">
                            <span class="price-new" data-price="""+str("%.2f" %menu_price.get(drink.id,0))+""" data-to-mu="""+str(to_markup and to_markup.get(drink.id,0))+"""
                            data-symbol="""+str(symbol)+""">"""+str(symbol)+str("%.2f" %menu_price.get(drink.id,0))+"""
                            </span><i class="fa fa-plus-circle"></i></a></div>
                            <div class="panel-group bootstarp-accordion pull-left col-sm-12" id="faq-accordion" role="tablist" aria-multiselectable="true">
                            <div class="panel"><div class="panel-heading" role="tab"><a role="button" data-toggle="collapse" data-parent="#faq-accordion"
                            href="#faq-accordion-one-"""+str(drink.id)+"""" aria-expanded="true" aria-controls="faq-accordion-one-1">Click here to see the menu</a>
                            </div><div id="faq-accordion-one-"""+str(drink.id)+"""" class="panel-collapse collapse" role="tabpanel">
                            <div class="panel-body"><div class="faq-thread"><textarea disabled="disabled" style="width: 100%;height: 50%;resize: none;background: white;border: none;overflow: auto;">
                            """+str(drink.description)+"""</textarea></div></div></div></div></div></div>"""
          return avltimes,menu_str,drink_str

      @http.route(['/get_restaurant_list'], type='json', auth="public", website=True)
      def get_restaurant_list(self, res_id='', json=None):
          request.context.update({'editable':False})
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')
          partner_obj = request.registry.get('res.partner')
          user = user_obj.browse(cr,uid,loginuid)

          domain = [('active','in',(False,True, None)),('type','=','default'),('id','!=',res_id)]


          if user.role == 'venue_user':
             domain.append(('id','in',[x.id for x in user.partner_id.contact_ids]))
          elif user.role == 'venue_mng':
             domain.append(('parent_id','=',user.partner_id.parent_id.id))
          else:
             domain.append(('parent_id','=',user.partner_id.id))

          if user.is_group:
                domain.append(('cc_group','=',True))
          else:
                domain.append(('cc_fit','=',True))
          domain.append(('is_default','=',False))
          child_ids_res = partner_obj.search_read(cr, uid,domain,['name'],order='name')
          return child_ids_res

      
      # Choice Dining Banner
      @http.route(['/capital_centric/choice_dining'], type='http', auth="public", website=True ,multilang=True)
      def choicedining_banner(self ,*args, **post):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,loginuid)
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
             
          values = {
                        'user'  : user,
                        'uid'   : user_obj.browse(cr, uid, uid)
                   }
          
          return request.website.render("fit_website.choicedining_banner",values)
      
      # Choice Dining Standard, VIP, Filters Links
      @http.route(['/choice_dinning/groups/<path>'], type='http', auth='public', website=True)
      def choicedining_groups_menu(self, path, *arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          grps_obj      = request.registry.get('cc.group.details')
          category_obj  = request.registry.get('res.partner.category')
          user_obj = request.registry.get('res.users')
          user = user_obj.browse(cr,uid,loginuid)
          if user.name == 'Public user':
             h = request.httprequest.environ['HTTP_HOST'].split(':')[0]
             user_ids = user_obj.search(cr, SUPERUSER_ID, [('wlabel_url','=',h)])
             user = user_obj.browse(cr, SUPERUSER_ID, user_ids and user_ids[0] or suid)
          
          operator = user.partner_id
          if user != 'client':
             operator = user.partner_id.parent_id or user.partner_id

          selc_categ = []
          sqlstr= ''
          
          domain = [('st_price','>',0),('type','=',path == 'standard' and 'std' or 'vip')]
          
          cr.execute("""
                    select distinct(cc.id) ,cc.name
                        from cc_group_details_res_partner_category_rel cr 
                        inner join cc_group_details rp on rp.id = cr.cdgroups_id 
                        inner join res_partner_category cc on cc.id = cr.category_id 
                        where rp.active = True 
                        order by cc.name
                     """)
          categories    = category_obj.browse(cr,suid,[i and i[0] for i in cr.fetchall()])

          if post.get('max_p'):
             domain = [('ed_price','<',post.get('max_p')),('type','=',path == 'standard' and 'std' or 'vip')]

          if post.get('min_p'):
             domain = [('st_price','>',post.get('min_p')),('type','=',path == 'standard' and 'std' or 'vip')]

          if post.get('max_p') and post.get('min_p'):
             domain = [('st_price','>',post.get('min_p')),('ed_price','<',post.get('max_p')),('type','=',path == 'standard' and 'std' or 'vip')]
          
          if post.get('rest_name'):
             domain.append(('name','ilike',post.get('rest_name')))
             
          if post.get('category_selected'):
             categ = post.get('category_selected')
             grps_ids = []
             if isinstance(eval(categ),int):
                cr.execute("select cdgroups_id from cc_group_details_res_partner_category_rel where category_id = %s",(categ,))
                grps_ids = [j and j[0] for j in cr.fetchall()]
                selc_categ = [eval(categ)]
             else:   
                cr.execute("select cdgroups_id from cc_group_details_res_partner_category_rel where category_id in %s",(tuple(eval(categ)),))
                grps_ids = [j and j[0] for j in cr.fetchall()]
                selc_categ = list(eval(categ))
             if grps_ids:
                domain.append(('id','in',grps_ids)) 
          grps_ids = grps_obj.search(cr, uid, domain)

          if grps_ids: 
              cr.execute("""select cdtoperator_ids from cc_group_details_res_partner_rel where cdtoperator_ids in %s 
                              and toperator_id = %s""",(tuple(grps_ids), str(operator.id))
                        )
              grps_ids = [x[0] for x in cr.fetchall()]
              
          values = {
                        'user'          : user,
                        'uid'           : user_obj.browse(cr, uid, uid),
                        'cd_groups'     : grps_obj.browse(cr, uid, grps_ids),
                        'categories'    : categories,
                        'post'          : post,
                        'path'          : path,
                        'selc_categ'    : selc_categ,
                        'email_sent'    : 'email_sent' if post.get('email_sent') == 'True' else ''
                   }
          
          return request.website.render("fit_website.groups_menu",values)
      
      
      # 'Enquiry' Button in Choice Dining    
      @http.route(['/fit_website/choice_dining_enquiry/'], type='json', auth="public", website=True)
      def choice_dining_enquiry(self,id,json=None):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          cc_grp_details_obj = request.registry.get('cc.group.details')
          hotel =  cc_grp_details_obj.browse(cr, suid, id)
          title_obj = request.registry.get('res.partner.title')
          title_ids = title_obj.search(cr, uid, [])
          titles    = title_obj.browse(cr, suid, title_ids)
          
          values = {
                        'hotel'     : hotel,
                        'title_ids' : titles,
                   }
          
          return request.website._render("fit_website.choice_dining_details", values)
      
      # 'Enquiry' Button in Choice Dining    
      @http.route(['/post-enquiry'], type='http', auth="public", website=True)
      def choice_dining_post_enquiry(self, *arg, **post ):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          loginuid = request.session.uid or request.uid
          user = request.registry.get('res.users').browse(cr,uid,loginuid)
          grp_obj = request.registry.get('cc.group.details')
          if post is None: post = {}
          hotel = post.get('db_id') and grp_obj.browse(cr, uid, int(post.get('db_id'))) or False
          
          if user:
             email_from = email_to = user.partner_id.email
             operator = user.partner_id
             if user.role != 'client':
                email_from = email_to = user.partner_id.parent_id.email
                operator = user.partner_id.parent_id  
          mail_obj = request.registry.get('mail.mail')
 
           
          body = """ 
                    Venue: """ + str(hotel and hotel.name or post.get('pref_venue')) + """<br/>
                    Name: """ + str(post.get('first_name','')) + """<br/>                    
                    Title: """ + str(post.get('title')) + """<br/>
                    Contact Name: """ + str(post.get('sec_name')) + """<br/>
                    Email: """  + str(post.get('email','')) +  """<br/>
                    Tel: """ + str(post.get('phone','')) + """<br/>
                    Mobile: """ + str(post.get('mobile','')) +"""<br/>
                    Reason for event: """ + str(post.get('special_request','')) +"""<br/>
                    Event Type: """ + str(post.get('event_type','')) + """<br/>
                    Number of people: """ + str(post.get('covers',0))+ """<br/>
                    Private room: """ + str(post.get('dining_room', '')) + """<br/>
                    Budget per head: """ + str(post.get('budget_per_head',0)) + """<br/>
                    Preferred Date: """ + str(post.get('preferred_date','')) + """<br/>
                    Preferred Time: """ + str(post.get('preferred_time','')) + """<br/>
                    Alternative hotel or restaurant: """ + str(post.get('alt_hotel','')) + """<br/>
                    Alternative date: """ + str(post.get('alt_date','')) + """<br/>
                    Additional Information: """ + str(post.get('add_info','')) + """<br/>
                    Group Reference: """ + str(post.get('cust_ref','')) + """<br/>               
          """
          mail_id = mail_obj.create(cr, SUPERUSER_ID, {'email_from' : 'fitforpurpose@capitalcentric.co.uk', 
                                  'email_to'   : 'info@capitalcentric.co.uk' or '',
                                  'reply_to'   : 'fitforpurpose@capitalcentric.co.uk' or '',
                                  'subject'    : 'Group Booking Enquiry - ' + str(post.get('first_name')) + ' ' + str(post.get('sec_name')),
                                  'body_html'  : body,
                                  'auto_delete': False,})
          if mail_id:
            res = mail_obj.send(cr, uid, [mail_id], False, False, None)

          
          values = {
                    'user': user,
                    'uid'  :False,   
                   }
          
          return request.redirect('/choice_dinning/groups/'+post.get('path','')+'?email_sent=True')

      @http.route(['/onclick_sign_in'], type='json', auth="public", website=True)
      def onclick_sign_in(self, login, password):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          user_obj = request.registry.get('res.users')
          partner_obj = request.registry.get('res.partner')
          user_agent_env = {'base_location': 'http://localhost:8069', 'HTTP_HOST': 'localhost:8069', 'REMOTE_ADDR': '127.0.0.1'} # TODO: send http information
          loginuid = user_obj.authenticate(cr, login, password, user_agent_env)
          uid = request.session.authenticate(request.db, login, password)
          if loginuid:
              user = user_obj.browse(cr, uid, loginuid) or False
              if user.partner_id.parent_id and user.partner_id.parent_id.partner_type == 'venue' or user.partner_id.partner_type == 'venue':
                  return False
              else:
                  return True
          else:
            return False

      @http.route(['/save_parent_restaurant'], type='json', auth="public", website=True)
      def save_parent_restaurant(self, parent_id, res_id):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          partner_obj = request.registry.get('res.partner')
          partner_obj.write(cr, uid, [int(res_id)], {'is_default' : True,'parent_res_id' : parent_id})
          return True


      @http.route(['/amend_paid_booking'], type='json', auth="public", website=True)
      def amend_paid_booking(self, post):
          cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
          lead_obj     = request.registry.get("crm.lead")
          info_obj     = request.registry.get("cc.send.rest.info")
          lead_browse  = lead_obj.browse(cr, uid, int(post.get('lead_id')))
          amend_error  = False
          send_confirmation = False
          today = (parser.parse(time.strftime("%Y-%m-%d %H:%M"))+relativedelta(hours=+36)).strftime("%Y-%m-%d %H:%M")
          if lead_browse and lead_browse.date_requested < today:
                amend_error = True
          if post.get('send_confirmation') == 'on':
              send_confirmation = True
          if not amend_error:
              lead_vals = {
                        'cust_ref'        : post.get('cust_ref'),
                        'title'           : post.get('title'),
                        'partner_name'    : post.get('f_name'),
                        'contact_name'    : post.get('s_name'),
                        'mobile'          : post.get('mobile'),
                        'email_from'      : post.get('email'),
                        'send_confirmation': send_confirmation,
                        'booker_name'      : post.get('booker_name'),
                        }
              lead_obj.write(cr, uid, [lead_browse.id], lead_vals)
              for case in lead_browse.info_ids:
                 cr.execute("""update cc_send_rest_info
                               set spcl_req = '""" + str(post.get('spcl_req')) + """' where id = """+ str(case.id))
                 toptemplate_id = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Customer')])
                 vtemplate_id = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Venue')])
                 gutemplate_id  = request.registry.get("email.template").search(cr,uid,[('name','=','Enquiry - Amendment Confirmation To Guest')])
                 if toptemplate_id:
                    request.registry.get("email.template").send_mail(cr, uid, toptemplate_id[0], case.id, force_send=True, context=None)
                 if vtemplate_id:
                    request.registry.get("email.template").send_mail(cr, uid, vtemplate_id[0], case.id, force_send=True, context= {'tmp_name':'Enquiry - Amendment Confirmation To Venue'})
                 if gutemplate_id and send_confirmation:
                    context = {}
                    request.registry.get("email.template").send_mail(cr, uid, gutemplate_id[0], case.id, force_send=True, context=None)
          return amend_error

          
        
      
import jwt
class Api(http.Controller):
     
    headers = [('Content-Type', 'application/json')]
    fitOBJ = login()
    def handle_ffp_Exception(self,chk,res = None):
        ffp_status = {'bad_request'  : '400 Bad Request' ,
                      'unauthorized' : '401 Unauthorized' ,
                      'server_error' : '500 Internal Server Error',
                      'auth_timeout' : '419 Authentication Timeout',
                      'no_content'   : '204 No Content',
                      'not_found'    : '404 Not Found',
                      'reset_content': '210 Reset Content'
                      }        
        
        if chk == 'bad_request' and not res:
           res = { 'error': 'Required Parameters are missing.', 'results':[]}
        elif chk == 'unauthorized' and not res:
            res ={'error': 'The token provided is invalid.','results':[]}
        elif chk == 'server_error' and not res:
            res ={'error': 'The server encountered an unexpected condition which prevented it from fulfilling the request.','results':[]}
        elif chk == 'auth_timeout' and not res:
            res ={'error': 'The provided token is expired.Please authenticate again.','results':[]}
        elif chk == 'no_content' and not res:
            res ={'error': 'Zero Results.','results':[]}
        response = request.make_response(simplejson.dumps(res), self.headers)
        response.status = ffp_status.get(chk,'200 OK')        
        request.session.logout(keep_db=True)  
        return response
    
    @http.route('/ffp/api/authenticate', type='http', auth="public")
    def api_login(self, *args, **post):   
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        try:
           post['db'] = request.db  
           post['exp'] = datetime.utcnow() + relativedelta(seconds=86400)           
           user_obj = request.registry.get('res.users')
           user_ids = user_obj.search(cr, suid, [('api_key','=',str(post['api_key']))])
           if not user_ids :
              return self.handle_ffp_Exception('unauthorized',{'error':'Incorrect API Key','results':[]})
           user = user_obj.browse(cr, suid, user_ids[0])
           login_id = request.session.authenticate(post.get('db'), user.login, user.password)
           token_dict = {'login' : user.login,
                    'password' : user.password,
                    'db' : post.get('db')}
           if not login_id: 
              return self.handle_ffp_Exception('unauthorized',{'error':'Wrong Login Id / Password','results':[]})           
          
           token = jwt.encode(token_dict,'token')            
           res = {'token':token, 'results' : []}          
           return self.handle_ffp_Exception('', res)
       
        except KeyError:
            return self.handle_ffp_Exception('bad_request')

        except:
            return self.handle_ffp_Exception('server_error')
             
    @http.route(['/ffp/api/masters/<path>'], type='http', auth="none")    
    def get_masters(self , path,*args, **post):
         
        try:            
            post.update(jwt.decode(post['token'],'token'))            
            request.session.authenticate(post.get('db'), post.get('login'), post.get('password'))        

            master_allowed = {'country':'res.country','state':'res.country.state','title':'res.partner.title',
                              'dinning_style':'cc.dining.style','cuisine':'cc.cuisine','tube_station':'cc.tube.station', 
                              'work_detail':'work.detail','restaurants':'res.partner','location':'cc.city'}

            res = {}
            user_obj = request.session.model('res.users')
            if path not in master_allowed:
               return self.handle_ffp_Exception('not_found',{'error':'Invalid Path','results':[]}) 
            master_obj = request.session.model(master_allowed[path])
            user = user_obj.browse(request.session.uid)
            fields_access = ['id','name']
            if path == 'restaurants':
               fields_access = ['id','name', 'street' , 'street2', 'country_id', 'state_id', 'city',
                                'zip', 'phone', 'mobile', 'email', 'descp_venue', 'dining_style_ids', 'cuisine_ids',
                                'payment_opt', 'dress_code', 'cancellation_hrs', 'booking_hrs']
            domain = []
            
            if post.get('sync_date'):                
               sync_date = datetime.strptime(post.get('sync_date'), "%d-%m-%Y")
               domain = [('write_date','>=',sync_date.strftime("%Y-%m-%d"))]  
            master_ids = master_obj.search_read(domain,fields_access)            
            
            if not master_ids:
               return self.handle_ffp_Exception('no_content') 
               
            return self.handle_ffp_Exception('', {'results':master_ids,'status':'OK'})
        
        except KeyError:
            return self.handle_ffp_Exception('bad_request')
        except ValueError:    
            return self.handle_ffp_Exception('bad_request',{'error':'Date format not correctly set.','results':[]})
        except jwt.ExpiredSignature:
            return self.handle_ffp_Exception('auth_timeout')
        except jwt.DecodeError:
            return self.handle_ffp_Exception('unauthorized')            
        except:         
            return self.handle_ffp_Exception('server_error')
      
    @http.route(['/ffp/api/restaurant/<path>'], type='http', auth="public")
    def get_available_restaurants(self, path, *args, **post):
        if post is None:
           post = {}           
        res = {}
        mdr_dict = {}
        covers = 0
        sqlstr = ''
        fitOBJ = login()
        if path == 'search':
           _logger.info('API Search Restaurant Request: %s',json.dumps(post))
        elif path == 'confirm':
           _logger.info('API Confirm Restaurant Request: %s',json.dumps(post))

        try:
            if 'restaurant_ID' not in post and post['token'] and post['booking_date'] and post['location_id'] and post['no_persons'] and post['type']:
               post.update({'called_frm':'get_restaurants'})

            if path == 'confirm' and post['restaurant_ID']:
              post.update({'called_frm':'get_restaurants'})
              post.update({'menus':eval(post['menus'])})
              [x.update({'food_type':'meal'}) for x in post.get('menus',[])]

              if post.get('drinks'):
                 post.update({'drinks':eval(post['drinks'])})
                 [y.update({'food_type':'drink'}) for y in post.get('drinks',[])]

              covers = sum([x['covers'] for x in post.get('menus',[])])
              for m in post.get('menus',[]) + post.get('drinks',[]):
                  if m['food_type'] == 'meal':
                     isinstance(m['menu_id'],int)
                     mdr_dict.update({m['menu_id'] : m})
                  else:
                     isinstance(m['drink_id'],int)
                     mdr_dict.update({m['drink_id'] : m})
                  isinstance(m['covers'],int)
                  isinstance(m['price'],float)
                  
        except KeyError:
            return self.handle_ffp_Exception('bad_request')
        except ValueError:
            return self.handle_ffp_Exception('bad_request', {'error_message': 'Booking Date/Time format not correctly set.','results':[]})
        except:
            return self.handle_ffp_Exception('server_error')

        try:
            post.update(jwt.decode(post.get('token') or '','token'))
            request.session.authenticate(post.get('db'), post.get('login'), post.get('password'))
            cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        except jwt.ExpiredSignature:
            return self.handle_ffp_Exception('auth_timeout')
        except jwt.DecodeError:
            return self.handle_ffp_Exception('unauthorized')

        try: 
            user_obj = request.registry.get('res.users')
            time_obj = request.registry.get('cc.time')
            menu_obj = request.session.model('cc.menus')
            alloc_obj = request.session.model('cc.time.allocations')
            black_obj = request.session.model('cc.black.out.day')
              
            user = user_obj.browse(cr, uid, uid)
            time_id = time_obj.search(cr, uid, [('name','=',post.get('booking_time','N/A'))],limit=1)[0]
            date = datetime.strptime(post.get('booking_date'), "%d/%m/%Y")
            day = date.strftime("%A").lower()
            bking_date = date.strftime("%d-%b-%Y")
            operator = user.partner_id
            if user.role != 'client':
               operator = user.partner_id.parent_id or False

            result = fitOBJ.westfield_search('grid_view',**post)
            if not result:
               if path == 'search': 
                  return self.handle_ffp_Exception('no_content')
               else:
                  return self.handle_ffp_Exception('',{'error_message':'Requested restaurant is not found/ not available ','result':[]})  
              
            for r in result:
                type = {'break_fast':('break_fast','=',True),'lunch':('lunch','=',True),'at':('afternoon_tea','=',True),'dinner':('dinner','=',True)}
                meal_type = ''
                black_out = black_obj.search_read([('partner_id','=',r['restaurant_id']),('date','<=',date.strftime('%Y-%m-%d'))
                                                  ,('date_to','>=',date.strftime('%Y-%m-%d'))],['from_time_id','to_time_id'],limit=1)
                
                if black_out:
                   black_time = time_obj.search_read(cr, uid, [('id','>=',black_out[0]['from_time_id'][0]),('id','<=',black_out[0]['to_time_id'][0])],['name'])                   
                   for b in black_time:
                       r.update({'available_times' :r['available_times'].replace(b['name']+',','')})

                if mdr_dict and mdr_dict.keys():
                   sqlstr = """ and cm.id in (""" + ', '.join(str(e) for e in mdr_dict.keys()) + """) """

                cr.execute(""" select   a.menu_id
                                 , a.name
                                 , a.description
                                 , a.food_type
                                 , (case when a.menu_mrkup is not null then round((a.price * a.menu_mrkup),1) + a.price
                                    else case when a.rest_mrkup is not null then round((a.price * a.rest_mrkup),1) + a.price
                                    else case when a.glb_mrkup is not null then round((a.price * a.glb_mrkup),1) + a.price
                                    else 0 end end end) as price
                                 , (case when a.menu_mrkup is not null then round((a.price * a.menu_mrkup),1)
                                    else case when a.rest_mrkup is not null then round((a.price * a.rest_mrkup),1)
                                    else case when a.glb_mrkup is not null then round((a.price * a.glb_mrkup),1)
                                    else 0 end end end) as to_mu
                           from
                           (
                                select  cm.partner_id as rest_id
                                  , cm.id as menu_id
                                  , cm.name
                                  , cm.description
                                  , cm.food_type
                                  , case when cm.to_price = 0 then 0 else cm.to_price end  as price
                                  , (select (case when 'markup' = 'markup' then (om.markup_perc/100) else 0 end) as menu_mrkup
                                     from rel_om_menu rom
                                     inner join cc_operator_markup om on om.id = rom.omarkup_id
                                     where om.partner_id = """ + str(operator and operator.id or 0) + """
                                     and restaurant_id = cm.partner_id and rom.menu_id = cm.id) as menu_mrkup
                                  , (select (case when 'markup' = 'markup' then (markup_perc/100) else 0 end)
                                     from cc_operator_markup where partner_id = """ + str(operator and operator.id or 0) + """
                                     and restaurant_id = cm.partner_id and mrkup_lvl = 'rest_lvl') as rest_mrkup
                                  , (select (case when 'markup' = 'markup' then (markup_perc/100) else 0 end)
                                     from res_partner where id = """ + str(operator and operator.id or 0) + """) as glb_mrkup
                                from cc_menus cm
                                where cm.cc_fit = True and cm.active = True
                                and cm.food_type  in ('meal','drink')
                                """ + str(sqlstr) + """
                                and cm.to_price > 0 and cm.partner_id = """ + str(r and r.get('id')) + """
                                and (case when '""" + post.get('type') + """' = 'break_fast' then cm.break_fast = True
                                else case when '""" + post.get('type') + """' = 'lunch' then cm.lunch=True
                                else case when '""" + post.get('type') + """' = 'at' then cm.afternoon_tea=True
                                else case when '""" + post.get('type') + """' = 'dinner' then cm.dinner=True end end end end)
                                and case when cm.start_date is not null and cm.end_date is not null then '"""+str(time.strftime('%Y-%m-%d'))+"""' BETWEEN cm.start_date AND cm.end_date  else true end
                                order by cm.partner_id,cm.id
                           )a
                           order by a.rest_id """)

                menus = cr.dictfetchall()
                menu_lst, drink_lst = [], []

                for m in menus:
                    if m.get('food_type') == 'meal':
                       menu_lst.append(m)
                    else:
                       m['drink_id'] = m.pop('menu_id')
                       drink_lst.append(m)

                    if path == 'confirm' and m.get('food_type') == 'meal':
                       menu = menu_obj.browse(m.get('menu_id'))
                       if not menu or menu.partner_id.id != r['id']:
                          return self.handle_ffp_Exception('not_found',{'error':'Invalid menu ID','results':[]})

                       if m['price'] != mdr_dict.get(m.get('menu_id')).get('price'):
                          return self.handle_ffp_Exception('reset_content',{'error':'There is change in Menu price.Please update menu with new price and Try Again',
                                                                            'result':[{'menu_id':menu.id,
                                                                                       'old_price':mdr_dict.get(m.get('menu_id')).get('price'),
                                                                                       'new_price':m['price']}]})
                       m.update(mdr_dict.get(m.get('menu_id')))
                       m.update({'rp_menu':menu.rest_price,
                                 'top_mp_markup': menu.markup,
                                 'rp_service_charge' : menu.to_price - (menu.rest_price + menu.markup),
                                 'top_service_charge' : menu.to_price - (menu.rest_price + menu.markup),
                                 'comsion_pprsn' : menu.commission,
                                 'menu_desc':menu.description
                                })

                    if path == 'confirm' and m.get('food_type') == 'drink':
                       menu = menu_obj.browse(m.get('drink_id'))
                       m.update(mdr_dict.get(m.get('drink_id')))
                       m.update({'rp_drinks':menu.rest_price,
                                 'menu_id'  : menu.id,
                                 'top_drinks_markup': menu.markup,
                                 'rp_service_charge': menu.to_price - (menu.rest_price + menu.markup),
                                 'top_service_charge' : menu.to_price - (menu.rest_price + menu.markup)})
                       if mdr_dict.get(m.get('drink_id')).get('price') != menu.to_price:
                          return self.handle_ffp_Exception('reset_content',{'error':'There is change in Drink price.Please update drinks with new price and Try Again',
                                                                            'result':[{'drinks_id':menu.id,
                                                                                       'old_price':mdr_dict.get(m.get('menu_id')).get('price'),
                                                                                       'new_price':menu.to_price}]})
                r.update({'menus':menu_lst,'drinks':drink_lst})
             
            if path == 'confirm' and result:
               crtemp = pooler.get_db(cr.dbname).cursor() # Creating new cursor to prevent TransactionRollbackError

               booking = self.confirm_booking(crtemp, user, date, post, covers, result[0])
               result = [{'booking_no':booking.lead_no}]
               crtemp.commit()  # It means database operation will be taken place if error occurs
               crtemp.close()
            return self.handle_ffp_Exception('',{'result':result,'status':'OK'})
        except KeyError:
            return self.handle_ffp_Exception('bad_request')
        except:
            return self.handle_ffp_Exception('server_error')
     
    def confirm_booking(self, cr ,user, date, post, covers, result):
        uid = request.uid
        menu_dtls=[]
        total_covers = 0          
        Invoice_Type = 'to_client'
        bking_date = ''
        contact_id = False
        cont_email = ''
        now = time.strftime("%Y-%m-%d")
        rest_obj = request.session.model('res.partner')
        mdetails_obj = request.registry.get("cc.menu.details")
        info_obj = request.registry.get("cc.send.rest.info")
        lead_obj = request.registry.get("crm.lead")
        invoice_obj = request.registry.get("account.invoice") 
        venue = rest_obj.browse(result.get('id'))
        product_ids  = request.session.model("product.product").search([('name_template','=','FIT for Purpose')])
        operator = user.partner_id
        if user.role in ('client_user','client_mng','client_cust'):
             operator = user.partner_id and user.partner_id.parent_id or False
        # day = datetime.strptime(json.get('resv_date'), "%d/%m/%Y").strftime("%A").lower()
        # #Checking Availability
        # cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) as covers
        #                   , id
        #                   , (case when sum(cap) is null then 0 else sum(cap) end) as shift_covers
        #                   , min(std_frm_id) as from_id
        #                   , max(std_to_id) as to_id
        #                     from cc_time_allocations
        #                     where partner_id = """ + str(venue.id) +"""
        #                     and type = '""" + str(type) + """'
        #                     and name = '""" + str(day) + """'
        #                     group by id """)
        #
        # alloc_covers = cr.dictfetchone()
        # print 'alloc_covers',alloc_covers
        # if alloc_covers:
        #    cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) from crm_lead
        #                  where state in ('open','done') and conv_dob = '""" + str(booking_date) +"""'
        #                  and conv_tob='"""+ str(req_time) + """'
        #                  and restaurant_id = """ + str(venue.id))
        #    tot_covers = cr.fetchone()
        #    if int(tot_covers[0]) + covers > int(alloc_covers['covers']):
        #       return 'unavilability',req_time,booking_date
        #
        #    cr.execute("""select (case when sum(covers) is null then 0 else sum(covers) end) from crm_lead
        #                  where state in ('open','done') and conv_dob = '""" + str(booking_date) +"""'
        #                  and conv_tob in (select name from cc_time where id between """ +str(alloc_covers['from_id'])+""" and """ +str(alloc_covers['to_id'])+ """)
        #                  and restaurant_id = """ + str(venue.id))
        #    totbkd_covers = cr.fetchone()
        #    print 'totbkd_covers',totbkd_covers
        #    if (int(alloc_covers.get('shift_covers',0)) > 0) and (int(totbkd_covers and totbkd_covers[0] or 0) + covers) > int(alloc_covers.get('shift_covers')):
        #       return 'shift_unavailable',req_time,booking_date

        for m in result.get('menus',[]) + result.get('drinks'):
            menus = [0,False]            
            if m['covers'] > 0:
               m['no_of_covers'] = m.pop('covers')
               m['previous_covers'] = m['no_of_covers']
               menus.append(m) 
               menus[2].update(mdetails_obj.get_pricing(cr, user.id, [], m.get('no_of_covers',0), m.get('rp_menu',0.00), m.get('rp_service_charge',0.00), 
                                             m.get('rp_drinks',0.00), 0.00, 0.00, 0.00, m.get('top_mp_markup',0.00), m.get('top_service_charge',0.00), 
                                             m.get('top_drinks_markup',0.00), m.get('comsion_pprsn',0.00), 0.00, 0.00, 0.00, 0.00)['value'])
                
               menu_dtls.append(menus)   
               if m.get('comsion_pprsn',0) > 0:        
                  Invoice_Type = 'to_both'
                             
        dob_frmt =  date.strftime("%Y-%m-%d")+ ' ' + (post.get('booking_time') or '00:00') 
        local = pytz.timezone (user.tz or 'Europe/London') 
        naive = datetime.strptime (dob_frmt, "%Y-%m-%d %H:%M")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone (pytz.utc)           
     
        for c in venue.contact_ids:
            if not contact_id:
               contact_id = c.id
            cont_email += c.email + ','          
        cont_email = cont_email[0:(len(cont_email) - 1)]                                      
           
        info_vals = {
                    'restaurant_id'   : venue.id,
                    'inv_address_id'  : venue.parent_id.id,
                    'cont_address_id' : contact_id,
                    'menu_dt_ids'     : menu_dtls,
                    'invoice_type'    : Invoice_Type,
                    'product_id'      : product_ids[0],
                    'contact_email'   : cont_email, 
                    'tax_srvc_chrg'   : False,
                    'special_requirement' : post.get('dietary_req','')
                    }
        
        lead_vals = {
                    'covers'          : covers,    
                    'name'            : 'Complete booking for ' + (venue.name),
                    'partner_id'      : operator.id,
                    'service_type'    : 'venue',
                    'passen_type'     : 'fit',
                    'type'            : 'opportunity',
                    'info_ids'        : [[0,False, info_vals]],
                    'date_requested'  : utc_dt,
                    'conv_dob'        : date.strftime('%d-%b-%Y'),
                    'conv_tob'        : post.get('booking_time','00:00'),
                    'sales_person'    : user.id,
                    'cust_ref'        : post['opt_ref'],
                    'title'           : post['title'],
                    'partner_name'    : post['f_name'],
                    'contact_name'    : post['l_name'],
                    'mobile'          : post['mobile'], 
                    'email_from'      : post['email'],
                    'send_confirmation': post.get('mail_to_guest',False),                     
                    }
           
        lead_id = request.registry.get("crm.lead") .create(cr, user.id, lead_vals)
        lead = lead_obj.browse(cr, user.id, lead_id)
        for l in lead.info_ids:
            info_obj.cc_create_invoices(cr, user.id, [l.id])
        invoice_ids = invoice_obj.search(cr,user.id,[('lead_id','=',lead.id),('type','=','out_invoice')])
        import calendar
        last_day = calendar.monthrange(int(date.strftime('%Y')), int(date.strftime('%m')))
        inv_date =  datetime.strptime((parser.parse(''.join((re.compile('\d')).findall(date.strftime('%Y-%m-%d'))))).strftime('%Y-%m-01'), "%Y-%m-%d") + relativedelta(months=1)
        due_date =  datetime.strptime((parser.parse(''.join((re.compile('\d')).findall(date.strftime('%Y-%m-%d'))))).strftime('%Y-%m-'+str(last_day[-1])), "%Y-%m-%d") + relativedelta(months=1)
        invoice_obj.write(cr,user.id,invoice_ids,{'date_invoice':inv_date,'date_due':due_date})
        toptemplate_id = request.registry.get("email.template").search(cr, uid, [('name','=','Enquiry - Booking Confirmation To Customer')])
        vtemplate_id   = request.registry.get("email.template").search(cr, uid, [('name','=','Enquiry - Booking Confirmation To Venue1')])
        for info in lead.info_ids:
            if toptemplate_id:
                request.registry.get('email.template').send_mail(cr, uid, toptemplate_id[0], info.id, force_send=True, context=None)
            if vtemplate_id:
                request.registry.get('email.template').send_mail(cr, uid, vtemplate_id[0], info.id, force_send=True, context=None)
        return lead
    
    #Fetching Covers from dialog box in Bookings of Tour Operators    
    @http.route(['/ffp/api/restaurant/cancellation'], type='http', auth="public")
    def cancel_booking(self, *args, **post):  
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        
        if post is None:
           post = {}           
        res = {}
        covers = 0
        try:       
           if not post.get('menus'):
              isinstance(post['drinks'],str)
               
           if post.get('menus'):   
              post.update({'menus':eval(post['menus'])})                    
              [x.update({'food_type':'meal'}) for x in post.get('menus',[])]               
           if post.get('drinks'):
              post.update({'drinks':eval(post['drinks'])})
              [y.update({'food_type':'drink'}) for y in post.get('drinks',[])] 
              covers = sum([x['covers'] for x in post.get('menus',[])]) 
           for m in post.get('menus',[]) + post.get('drinks',[]):
               if m['food_type'] == 'meal':
                 isinstance(m['menu_id'],int)
               else:
                 isinstance(m['drink_id'],int) 
               isinstance(m['covers'],int)   
                                   
           post.update(jwt.decode(post['token'],'token'))            
           request.session.authenticate(post.get('db'), post.get('login'), post.get('password'))
           cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        except jwt.ExpiredSignature:
            return self.handle_ffp_Exception('auth_timeout')
        except jwt.DecodeError:
            return self.handle_ffp_Exception('unauthorized')
        except KeyError:
            return self.handle_ffp_Exception('bad_request')
        except ValueError:
            return self.handle_ffp_Exception('bad_request')
        except:
            return self.handle_ffp_Exception('server_error')
            
        mdetails_obj = request.registry.get('cc.menu.details')
        info_obj = request.registry.get('cc.send.rest.info')
        user_obj = request.registry.get('res.users')
        invoice_obj = request.registry.get('account.invoice')
        lead_obj = request.registry.get('crm.lead') 
        tmpl_obj = request.registry.get("email.template")
        today = (parser.parse(time.strftime("%Y-%m-%d %H:%M"))+relativedelta(hours=+36)).strftime("%Y-%m-%d %H:%M")
        user = user_obj.browse(cr, uid, uid)
        payment_type = user.partner_id and user.partner_id.payment_type or ''
        
        lead_id = lead_obj.search(cr,uid,[('lead_no','=',post['booking_no']),('state','!=','cancel')])        
        if not lead_id:
           return self.handle_ffp_Exception('not_found',{'error':'Booking Not Found','results':[]}) 
        lead = lead_obj.browse(cr,uid,lead_id[0])
        if lead.date_requested < today:           
           return self.handle_ffp_Exception('',{'error':'Cancellation can be done before 36hrs of booking date','results':[]})        
        crtemp = pooler.get_db(cr.dbname).cursor()
        for i in lead.info_ids:    
            for j in post.get('menus',[]) + post.get('drinks',[]):                
                is_menu = False       
                for k in i.menu_dt_ids:
                    if k.menu_id.id == j['menu_id']:
                       is_menu = True 
                       if k.no_of_covers < j['covers']:                         
                          return self.handle_ffp_Exception('',{'error':'The provided Covers for cancellation is more than booked covers','results':[]})
                          
                       mdetails_obj.write(crtemp, uid, [k.id], {'no_of_covers':j['covers']})
        
        if not is_menu:
           self.handle_ffp_Exception('not_found',{'error':'Invalid menu ID / drink ID','results':[]}) 
                               
        try:
          info_obj.write(crtemp,uid, [i.id],{})
          res = info_obj.update_invoice(crtemp, uid, [i.id],context=None)
          crtemp.commit()  # It means database operation will be taken place if error occurs
          crtemp.close() 
        except except_orm:
            return self.handle_ffp_Exception('bad_request',{'error':'Please enter revised no. of covers to proceed.'})
        except:
          cr.rollback()    
          return self.handle_ffp_Exception('server_error')
          
        return self.handle_ffp_Exception('',{'message':'Booking has been cancelled for given no of covers'})
    
    
#   Session Info    
    @http.route(['/fit_website/session_info/'], type='json', auth="public", website=True)
    def session_info(self, current_url, json=None):
        previous_url = ''
        
        return previous_url
    
#   Video Template
    @http.route(['/capital_centric/video'], type='http', auth="public", multilang=True, website=True)
    def video_template(self,*arg, **post ):
        cr, uid, suid, ctx = request.cr, request.uid, openerp.SUPERUSER_ID, request.context
        request.context.update({'editable':False})
        user_obj = request.registry.get('res.users')
        user = user_obj.browse(cr,uid,uid)
        return request.website.render("fit_website.video_template",{'user':user})
    
  
