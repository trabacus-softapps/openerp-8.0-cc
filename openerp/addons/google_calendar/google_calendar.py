##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 OpenERP SA (<http://www.openerp.com>).
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

import operator
import simplejson
import re
import urllib
import warnings

from openerp import tools
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

from openerp.addons.web.http import request
import werkzeug.utils

from datetime import datetime, timedelta, date
from dateutil import parser
import pytz
from openerp.osv import fields, osv
from openerp.osv import osv


class google_calendar(osv.AbstractModel):
    STR_SERVICE = 'calendar'
    _name = 'google.%s' % STR_SERVICE

    def generate_data(self, cr, uid, event, context=None):
        if event.allday:
            start_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.date, tools.DEFAULT_SERVER_DATETIME_FORMAT) , context=context).isoformat('T').split('T')[0]
            end_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.date, tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=event.duration), context=context).isoformat('T').split('T')[0]
            type = 'date'
        else:
            start_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.date, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context).isoformat('T')
            end_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.date_deadline, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context).isoformat('T')
            type = 'dateTime'
        attendee_list = []

        for attendee in event.attendee_ids:
            attendee_list.append({
                'email':attendee.email or 'NoEmail@mail.com',
                'displayName':attendee.partner_id.name,
                'responseStatus':attendee.state or 'needsAction',
            })
        data = {
            "summary": event.name or '',
            "description": event.description or '',
            "start":{
                 type:start_date,
                 'timeZone':'UTC'
             },
            "end":{
                 type:end_date,
                 'timeZone':'UTC'
             },
            "attendees":attendee_list,
            "location":event.location or '',
            "visibility":event['class'] or 'public',
        }
        if event.recurrency and event.rrule:
            data["recurrence"]=["RRULE:"+event.rrule]

        if not event.active:
            data["state"] = "cancelled"

        return data

    def create_an_event(self, cr, uid,event, context=None):
        gs_pool = self.pool.get('google.service')

        data = self.generate_data(cr, uid,event, context=context)

        url = "/calendar/v3/calendars/%s/events?fields=%s&access_token=%s" % ('primary',urllib.quote('id,updated'),self.get_token(cr,uid,context))
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data_json = simplejson.dumps(data)

        return gs_pool._do_request(cr, uid, url, data_json, headers, type='POST', context=context)

    def delete_an_event(self, cr, uid,event_id, context=None):
        gs_pool = self.pool.get('google.service')

        params = {
                 'access_token' : self.get_token(cr,uid,context)
                }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        url = "/calendar/v3/calendars/%s/events/%s" % ('primary',event_id)

        return gs_pool._do_request(cr, uid, url, params, headers, type='DELETE', context=context)

    def get_event_dict(self,cr,uid,token=False,nextPageToken=False,context=None):
        if not token:
            token = self.get_token(cr,uid,context)

        gs_pool = self.pool.get('google.service')

        params = {
                 'fields': 'items,nextPageToken',
                 'access_token' : token,
                 'maxResults':1000
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        url = "/calendar/v3/calendars/%s/events" % 'primary'
        if nextPageToken:
            params['pageToken'] = nextPageToken

        content = gs_pool._do_request(cr, uid, url, params, headers, type='GET', context=context)

        google_events_dict = {}

        for google_event in content['items']:
            google_events_dict[google_event['id']] = google_event

        if content.get('nextPageToken', False):
            google_events_dict.update(self.get_event_dict(cr,uid,token,content['nextPageToken'],context=context))
        return google_events_dict    

    def update_to_google(self, cr, uid, oe_event, google_event, context):
        calendar_event = self.pool['calendar.event']
        gs_pool = self.pool.get('google.service')

        url = "/calendar/v3/calendars/%s/events/%s?fields=%s&access_token=%s" % ('primary', google_event['id'],'id,updated', self.get_token(cr,uid,context))
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data = self.generate_data(cr,uid ,oe_event, context)
        data['sequence'] = google_event.get('sequence', 0)
        data_json = simplejson.dumps(data)

        content = gs_pool._do_request(cr, uid, url, data_json, headers, type='PATCH', context=context)

        update_date = datetime.strptime(content['updated'],"%Y-%m-%dT%H:%M:%S.%fz")
        calendar_event.write(cr, uid, [oe_event.id], {'oe_update_date':update_date})

        if context['curr_attendee']:
            self.pool.get('calendar.attendee').write(cr,uid,[context['curr_attendee']], {'oe_synchro_date':update_date},context)

    def update_an_event(self, cr, uid,event, context=None):
        gs_pool = self.pool.get('google.service')

        data = self.generate_data(cr, uid,event, context=context)

        url = "/calendar/v3/calendars/%s/events/%s" % ('primary', event.google_internal_event_id)
        headers = {}
        data['access_token'] = self.get_token(cr,uid,context)

        response = gs_pool._do_request(cr, uid, url, data, headers, type='GET', context=context)
        #TO_CHECK : , if http fail, no event, do DELETE ?
        return response

    def update_recurrent_event_exclu(self, cr, uid,instance_id,event_ori_google_id,event_new, context=None):
        gs_pool = self.pool.get('google.service')

        data = self.generate_data(cr, uid,event_new, context=context)

        data['recurringEventId'] = event_ori_google_id
        data['originalStartTime'] = event_new.recurrent_id_date

        url = "/calendar/v3/calendars/%s/events/%s?access_token=%s" % ('primary', instance_id,self.get_token(cr,uid,context))
        headers = { 'Content-type': 'application/json'}

        data['sequence'] = self.get_sequence(cr, uid, instance_id, context)

        data_json = simplejson.dumps(data)
        return gs_pool._do_request(cr, uid, url, data_json, headers, type='PUT', context=context)

    def update_from_google(self, cr, uid, event, single_event_dict, type, context):
        if context is None:
            context= []

        calendar_event = self.pool['calendar.event']
        res_partner_obj = self.pool['res.partner']
        calendar_attendee_obj = self.pool['calendar.attendee']
        user_obj = self.pool.get('res.users')
        myPartnerID = user_obj.browse(cr,uid,uid,context).partner_id.id
        attendee_record = []
        partner_record = [(4,myPartnerID)]
        result = {}

        if single_event_dict.get('attendees',False):
            for google_attendee in single_event_dict['attendees']:
                if type == "write":
                    for oe_attendee in event['attendee_ids']:
                        if oe_attendee.email == google_attendee['email']:
                            calendar_attendee_obj.write(cr, uid,[oe_attendee.id] ,{'state' : google_attendee['responseStatus']},context=context)
                            google_attendee['found'] = True
                            continue

                if google_attendee.get('found',False):
                    continue
                attendee_id = res_partner_obj.search(cr, uid,[('email', '=', google_attendee['email'])], context=context)
                if not attendee_id:
                    attendee_id = [res_partner_obj.create(cr, uid,{'email': google_attendee['email'],'Customer': False, 'name': google_attendee.get("displayName",False) or google_attendee['email'] }, context=context)]
                attendee = res_partner_obj.read(cr, uid, attendee_id[0], ['email'], context=context)
                partner_record.append((4, attendee.get('id')))
                attendee['partner_id'] = attendee.pop('id')
                attendee['state'] = google_attendee['responseStatus']
                attendee_record.append((0, 0, attendee))
        UTC = pytz.timezone('UTC')
        if single_event_dict.get('start') and single_event_dict.get('end'): # If not cancelled   
            if single_event_dict['start'].get('dateTime',False) and single_event_dict['end'].get('dateTime',False):
                date = parser.parse(single_event_dict['start']['dateTime'])
                date_deadline = parser.parse(single_event_dict['end']['dateTime'])
                delta = date_deadline.astimezone(UTC) - date.astimezone(UTC)
                date = str(date.astimezone(UTC))[:-6]
                date_deadline = str(date_deadline.astimezone(UTC))[:-6]
                allday = False
            else:
                date = (single_event_dict['start']['date'] + ' 00:00:00')
                date_deadline = (single_event_dict['end']['date'] + ' 00:00:00')
                d_start = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                d_end = datetime.strptime(date_deadline, "%Y-%m-%d %H:%M:%S")
                delta = (d_end - d_start)
                allday = True

            result['duration'] = (delta.seconds / 60) / 60.0 + delta.days *24
            update_date = datetime.strptime(single_event_dict['updated'],"%Y-%m-%dT%H:%M:%S.%fz")
            result.update({
                'date': date,
                'date_deadline': date_deadline,
                'allday': allday
            })
        result.update({
            'attendee_ids': attendee_record,
            'partner_ids': list(set(partner_record)),

            'name': single_event_dict.get('summary','Event'),
            'description': single_event_dict.get('description',False),
            'location':single_event_dict.get('location',False),
            'class':single_event_dict.get('visibility','public'),
            'oe_update_date':update_date, 
#            'google_internal_event_id': single_event_dict.get('id',False),
        })

        if single_event_dict.get("recurrence",False):
            rrule = [rule for rule in single_event_dict["recurrence"] if rule.startswith("RRULE:")][0][6:]
            result['rrule']=rrule

        if type == "write":
            res = calendar_event.write(cr, uid, event['id'], result, context=context)
        elif type == "copy":
            result['recurrence'] = True
            res = calendar_event.write(cr, uid, [event['id']], result, context=context)

        elif type == "create":
            res = calendar_event.create(cr, uid, result, context=context)

        if context['curr_attendee']:
            self.pool.get('calendar.attendee').write(cr,uid,[context['curr_attendee']], {'oe_synchro_date':update_date,'google_internal_event_id': single_event_dict.get('id',False)},context)
        return res

    def synchronize_events(self, cr, uid, ids, context=None):
        gc_obj = self.pool.get('google.calendar')

        self.create_new_events(cr, uid, context=context)

        self.bind_recurring_events_to_google(cr, uid, context)
        cr.commit()

        res = self.update_events(cr, uid, context)

        return {
                "status" :  res and "need_refresh" or "no_new_event_form_google",
                "url" : ''
                }

    def create_new_events(self, cr, uid, context):
        gc_pool = self.pool.get('google.calendar')

        calendar_event = self.pool['calendar.event']
        att_obj = self.pool['calendar.attendee']
        user_obj = self.pool['res.users']
        myPartnerID = user_obj.browse(cr,uid,uid,context=context).partner_id.id

        context_norecurrent = context.copy()
        context_norecurrent['virtual_id'] = False

        my_att_ids = att_obj.search(cr, uid,[('partner_id', '=', myPartnerID),('google_internal_event_id', '=', False)], context=context_norecurrent)
        for att in att_obj.browse(cr,uid,my_att_ids,context=context):
            if not att.event_id.recurrent_id or att.event_id.recurrent_id == 0:
                response = self.create_an_event(cr,uid,att.event_id,context=context)
                update_date = datetime.strptime(response['updated'],"%Y-%m-%dT%H:%M:%S.%fz")
                calendar_event.write(cr, uid, att.event_id.id, {'oe_update_date':update_date})
                att_obj.write(cr, uid, [att.id], {'google_internal_event_id': response['id'], 'oe_synchro_date':update_date})
                cr.commit()
        return True

    def get_empty_synchro_summarize(self) :
        return {
                #OPENERP
                'OE_event' : False,
                'OE_found' : False,
                'OE_event_id' : False,
                'OE_isRecurrence':False,
                'OE_isInstance':False,
                'OE_update':False,
                'OE_status':False,
                'OE_attendee_id': False,
                'OE_synchro':False,

                #GOOGLE
                'GG_event' : False,
                'GG_found' : False,
                'GG_isRecurrence':False,
                'GG_isInstance':False,
                'GG_update':False,
                'GG_status':False,

                #TO_DO_IN_GOOGLE
                'td_action':'',  #  create, update, delete, None
                #If 'td_action' in (create , update), 
                #    If td_source == OE
                #            We create in google the event based on OpenERP
                #    If td_source == GG
                #            We create in OpenERP the event based on Gmail
                #
                #If 'td_action' in (delete),
                #    If td_source == OE
                #            We delete in OpenERP the event 
                #    If td_source == GG
                #            We delete in Gmail the event 
                #    If td_source == ALL
                #            We delete in openERP AND in Gmail the event 
                'td_source': '', #  OE, GG, ALL
                'td_comment':''

        }

    def update_events(self, cr, uid, context):
        if context is None:
            context = {}

        calendar_event = self.pool['calendar.event']
        user_obj = self.pool['res.users']
        att_obj = self.pool['calendar.attendee']
        myPartnerID = user_obj.browse(cr,uid,uid,context=context).partner_id.id

        context_novirtual = context.copy()
        context_novirtual['virtual_id'] = False
        context_novirtual['active_test'] = False

        all_event_from_google = self.get_event_dict(cr,uid,context=context)
        all_new_event_from_google = all_event_from_google.copy()

        # Select all events from OpenERP which have been already synchronized in gmail
        my_att_ids = att_obj.search(cr, uid,[('partner_id', '=', myPartnerID),('google_internal_event_id', '!=', False)], context=context_novirtual)
        event_to_synchronize = {}
        for att in att_obj.browse(cr,uid,my_att_ids,context=context):
            event = att.event_id

            base_event_id = att.google_internal_event_id.split('_')[0]

            if base_event_id not in event_to_synchronize:
                event_to_synchronize[base_event_id] = {}

            if att.google_internal_event_id not in event_to_synchronize[base_event_id]:
                event_to_synchronize[base_event_id][att.google_internal_event_id] = self.get_empty_synchro_summarize()

            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_attendee_id'] = att.id
            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_event'] = event
            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_found'] = True
            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_event_id'] = event.id
            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_isRecurrence'] = event.recurrency
            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_isInstance'] = bool(event.recurrent_id and event.recurrent_id > 0)
            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_update'] = event.oe_update_date
            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_status'] = event.active
            event_to_synchronize[base_event_id][att.google_internal_event_id]['OE_synchro'] = att.oe_synchro_date


        for event in all_event_from_google.values():
            event_id = event.get('id')
            base_event_id = event_id.split('_')[0]

            if base_event_id not in event_to_synchronize:
                event_to_synchronize[base_event_id] = {}

            if event_id not in event_to_synchronize[base_event_id]:
                event_to_synchronize[base_event_id][event_id] = self.get_empty_synchro_summarize()

            event_to_synchronize[base_event_id][event_id]['GG_event'] = event
            event_to_synchronize[base_event_id][event_id]['GG_found'] = True
            event_to_synchronize[base_event_id][event_id]['GG_isRecurrence'] = bool(event.get('recurrence',''))
            event_to_synchronize[base_event_id][event_id]['GG_isInstance'] = bool(event.get('recurringEventId',0))  
            event_to_synchronize[base_event_id][event_id]['GG_update'] = event.get('updated',None) # if deleted, no date without browse event
            if event_to_synchronize[base_event_id][event_id]['GG_update']:
                event_to_synchronize[base_event_id][event_id]['GG_update'] =event_to_synchronize[base_event_id][event_id]['GG_update'].replace('T',' ').replace('Z','')
            event_to_synchronize[base_event_id][event_id]['GG_status'] = (event.get('status') != 'cancelled')


        ######################  
        #   PRE-PROCESSING   #
        ######################

        for base_event in event_to_synchronize:
            for current_event in event_to_synchronize[base_event]:
                event = event_to_synchronize[base_event][current_event]

                #If event are already in Gmail and in OpenERP 
                if event['OE_found'] and event['GG_found']:
                    #If the event has been deleted from one side, we delete on other side !
                    if event['OE_status'] != event['GG_status']:
                        event['td_action'] = "DELETE"
                        event['td_source'] = (event['OE_status'] and "OE") or (event['GG_status'] and "GG")
                    #If event is not deleted !     
                    elif event['OE_status'] and event['GG_status']:
                        if event['OE_update'].split('.')[0] != event['GG_update'].split('.')[0]:
                            if event['OE_update'] < event['GG_update']:
                                event['td_source'] = 'GG'
                            elif event['OE_update'] > event['GG_update']:
                                event['td_source'] = 'OE'


                            if event['td_action'] != "None":
                                if event['%s_isRecurrence' % event['td_source']]:
                                    if event['%s_status' % event['td_source']]:
                                         event['td_action'] = "UPDATE"
                                         event['td_comment'] = 'Only need to update, because i\'m active'
                                    else:
                                        event['td_action'] = "EXCLUDE"
                                        event['td_comment'] = 'Need to Exclude (Me = First event from recurrence) from recurrence'

                                elif event['%s_isInstance' % event['td_source']]:
                                    event['td_action'] = "UPDATE"
                                    event['td_comment'] = 'Only need to update, because already an exclu'
                                else:
                                    event['td_action'] = "UPDATE"
                                    event['td_comment'] = 'Simply Update... I\'m a single event'

                        else:
                            if not event['OE_synchro'] or event['OE_synchro'].split('.')[0] < event['OE_update'].split('.')[0]:
                                event['td_source'] = 'OE'
                                event['td_action'] = "UPDATE"
                                event['td_comment'] = 'Event already updated by another user, but not synchro with my google calendar'

                            else:
                                event['td_action'] = "None"
                                event['td_comment'] = 'Not update needed'
                    else:
                        event['td_action'] = "None"
                        event['td_comment'] = "Both are already deleted"  
                # New in openERP...  Create on create_events of synchronize function
                elif event['OE_found'] and not event['GG_found']:
                    #Has been deleted from gmail
                    if event['OE_status']:
                        event['td_source'] = 'OE'
                        event['td_action'] = 'DELETE'
                        event['td_comment'] = 'Removed from GOOGLE ?'
                    else:
                        event['td_action'] = "None"  
                        event['td_comment'] = "Already Deleted in gmail and unlinked in OpenERP"  
                elif event['GG_found'] and not event['OE_found']:
                    event['td_source'] = 'GG'
                    if not event['GG_status'] and not event['GG_isInstance']:
                            # don't need to make something... because event has been created and deleted before the synchronization
                            event['td_action'] = 'None'
                            event['td_comment'] = 'Nothing to do... Create and Delete directly'

                    else:
                          if event['GG_isInstance']:
                               if event['%s_status' % event['td_source']]:
                                    event['td_action'] = "EXCLUDE"     
                                    event['td_comment'] = 'Need to create the new exclu'
                               else:
                                    event['td_action'] = "EXCLUDE"
                                    event['td_comment'] = 'Need to copy and Exclude'    
                          else:
                              event['td_action'] = "CREATE"
                              event['td_comment'] = 'New EVENT CREATE from GMAIL'

        ######################
        #      DO ACTION     #
        ###################### 
        for base_event in event_to_synchronize:
            event_to_synchronize[base_event] = sorted(event_to_synchronize[base_event].iteritems(),key=operator.itemgetter(0))
            for current_event in event_to_synchronize[base_event]:
                cr.commit()
                event = current_event[1] 
                #############
                ### DEBUG ###   
                ############# 
#                 if event['td_action'] and event['td_action'] != 'None':               
#                     print "  Real Event  %s (%s)" %  (current_event[0],event['OE_event_id'])
#                     print "    Found       OE:%5s vs GG: %5s" % (event['OE_found'],event['GG_found'])
#                     print "    Recurrence  OE:%5s vs GG: %5s" % (event['OE_isRecurrence'],event['GG_isRecurrence'])
#                     print "    Instance    OE:%5s vs GG: %5s" % (event['OE_isInstance'],event['GG_isInstance'])
#                     print "    Synchro     OE: %10s " % (event['OE_synchro']) 
#                     print "    Update      OE: %10s " % (event['OE_update'])  
#                     print "    Update      GG: %10s " % (event['GG_update'])
#                     print "    Status      OE:%5s vs GG: %5s" % (event['OE_status'],event['GG_status'])
#                     print "    Action      %s" % (event['td_action'])
#                     print "    Source      %s" % (event['td_source'])
#                     print "    comment     %s" % (event['td_comment'])

                context['curr_attendee'] = event.get('OE_attendee_id',False)

                actToDo = event['td_action']
                actSrc = event['td_source']
                if not actToDo:
                    raise ("#!? WHAT I NEED TO DO ????")
                else:
                    if actToDo == 'None':
                        continue
                    elif actToDo == 'CREATE':
                        context_tmp = context.copy()
                        context_tmp['NewMeeting'] = True
                        if actSrc == 'GG':
                            res = self.update_from_google(cr, uid, False, event['GG_event'], "create", context=context_tmp)
                            event['OE_event_id'] = res
                            meeting = calendar_event.browse(cr,uid,res,context=context)
                            attendee_record_id = att_obj.search(cr, uid, [('partner_id','=', myPartnerID), ('event_id','=',res)], context=context)
                            self.pool.get('calendar.attendee').write(cr,uid,attendee_record_id, {'oe_synchro_date':meeting.oe_update_date,'google_internal_event_id': event['GG_event']['id']},context=context_tmp)
                        elif  actSrc == 'OE':
                            raise "Should be never here, creation for OE is done before update !"
                        #TODO Add to batch
                    elif actToDo == 'UPDATE':
                        if actSrc == 'GG':
                            self.update_from_google(cr, uid, event['OE_event'], event['GG_event'], 'write', context)
                        elif  actSrc == 'OE':
                            self.update_to_google(cr, uid, event['OE_event'], event['GG_event'], context)
                    elif actToDo == 'EXCLUDE' :
                        if actSrc == 'OE':
                            self.delete_an_event(cr,uid,current_event[0],context=context)
                        elif  actSrc == 'GG':
                                new_google_event_id = event['GG_event']['id'].split('_')[1]
                                if 'T' in new_google_event_id:
                                    new_google_event_id = new_google_event_id.replace('T','')[:-1]
                                else:
                                    new_google_event_id = new_google_event_id + "000000"
    
                                    if event['GG_status']:
                                        parent_event = {}
                                        parent_event['id'] = "%s-%s" % (event_to_synchronize[base_event][0][1].get('OE_event_id') ,  new_google_event_id)
                                        res = self.update_from_google(cr, uid, parent_event, event['GG_event'], "copy", context)
                                    else:
                                        if event_to_synchronize[base_event][0][1].get('OE_event_id'):
                                            parent_oe_id =  event_to_synchronize[base_event][0][1].get('OE_event_id')
                                            calendar_event.unlink(cr,uid,"%s-%s" % (parent_oe_id,new_google_event_id),unlink_level=1,context=context)

                    elif actToDo == 'DELETE':
                        if actSrc == 'GG':
                            self.delete_an_event(cr,uid,current_event[0],context=context)
                        elif  actSrc == 'OE':
                            calendar_event.unlink(cr,uid,event['OE_event_id'],unlink_level=0,context=context)
        return True

    def bind_recurring_events_to_google(self, cr, uid,  context):
        calendar_event = self.pool['calendar.event']
        att_obj = self.pool.get('calendar.attendee')
        user_obj = self.pool['res.users']
        myPartnerID = user_obj.browse(cr,uid,uid,context=context).partner_id.id

        context_norecurrent = context.copy()
        context_norecurrent['virtual_id'] = False
        context_norecurrent['active_test'] = False

        my_att_ids = att_obj.search(cr, uid,[('partner_id', '=', myPartnerID),('google_internal_event_id', '=', False)], context=context_norecurrent)
        for att in att_obj.browse(cr,uid,my_att_ids,context=context):
            if att.event_id.recurrent_id and att.event_id.recurrent_id > 0:
                new_google_internal_event_id = False
                source_event_record = calendar_event.browse(cr, uid, att.event_id.recurrent_id, context)
                source_attendee_record_id = att_obj.search(cr, uid, [('partner_id','=', myPartnerID), ('event_id','=',source_event_record.id)], context=context)
                source_attendee_record = att_obj.browse(cr, uid, source_attendee_record_id, context)
                if source_attendee_record:
                    source_attendee_record = source_attendee_record[0]

                if att.event_id.recurrent_id_date and source_event_record.allday and source_attendee_record.google_internal_event_id:
                    new_google_internal_event_id = source_attendee_record.google_internal_event_id +'_'+ att.event_id.recurrent_id_date.split(' ')[0].replace('-','')
                elif event.recurrent_id_date and source_attendee_record.google_internal_event_id:
                    new_google_internal_event_id = source_attendee_record.google_internal_event_id +'_'+ att.event_id.recurrent_id_date.replace('-','').replace(' ','T').replace(':','') + 'Z'

                if new_google_internal_event_id:
                    #TODO WARNING, NEED TO CHECK THAT EVENT and ALL instance NOT DELETE IN GMAIL BEFORE !
                    res = self.update_recurrent_event_exclu(cr,uid,new_google_internal_event_id,source_attendee_record.google_internal_event_id,att.event_id,context=context)
                    att_obj.write(cr, uid, [att.event_id.id], {'google_internal_event_id': new_google_internal_event_id})

    def check_and_sync(self, cr, uid, oe_event, google_event, context):
        if datetime.strptime(oe_event.oe_update_date,"%Y-%m-%d %H:%M:%S.%f") > datetime.strptime(google_event['updated'],"%Y-%m-%dT%H:%M:%S.%fz"):
            self.update_to_google(cr, uid, oe_event, google_event, context)
        elif datetime.strptime(oe_event.oe_update_date,"%Y-%m-%d %H:%M:%S.%f") < datetime.strptime(google_event['updated'],"%Y-%m-%dT%H:%M:%S.%fz"):
            self.update_from_google(cr, uid, oe_event, google_event, 'write', context)

    def get_sequence(self,cr,uid,instance_id,context=None):
        gs_pool = self.pool.get('google.service')

        params = {
                 'fields': 'sequence',
                 'access_token' : self.get_token(cr,uid,context)
                }

        headers = {'Content-type': 'application/json'}

        url = "/calendar/v3/calendars/%s/events/%s" % ('primary',instance_id) 

        content = gs_pool._do_request(cr, uid, url, params, headers, type='GET', context=context)
        return content.get('sequence',0)
#################################        
##  MANAGE CONNEXION TO GMAIL  ##
#################################

    def get_token(self,cr,uid,context=None):
        current_user = self.pool.get('res.users').browse(cr,uid,uid,context=context)

        if datetime.strptime(current_user.google_calendar_token_validity.split('.')[0], "%Y-%m-%d %H:%M:%S") < (datetime.now() + timedelta(minutes=1)):
            self.do_refresh_token(cr,uid,context=context)
            current_user.refresh()

        return current_user.google_calendar_token

    def do_refresh_token(self,cr,uid,context=None):
        current_user = self.pool.get('res.users').browse(cr,uid,uid,context=context)
        gs_pool = self.pool.get('google.service')

        refresh = current_user.google_calendar_rtoken
        all_token = gs_pool._refresh_google_token_json(cr, uid, current_user.google_calendar_rtoken,self.STR_SERVICE,context=context)

        vals = {}
        vals['google_%s_token_validity' % self.STR_SERVICE] = datetime.now() + timedelta(seconds=all_token.get('expires_in'))
        vals['google_%s_token' % self.STR_SERVICE] = all_token.get('access_token')

        self.pool.get('res.users').write(cr,SUPERUSER_ID,uid,vals,context=context)

    def need_authorize(self,cr,uid,context=None):
        current_user = self.pool.get('res.users').browse(cr,uid,uid,context=context)
        return current_user.google_calendar_rtoken == False

    def get_calendar_scope(self,RO=False):
        readonly = RO and '.readonly' or ''
        return 'https://www.googleapis.com/auth/calendar%s' % (readonly)

    def authorize_google_uri(self,cr,uid,from_url='http://www.openerp.com',context=None):
        url = self.pool.get('google.service')._get_authorize_uri(cr,uid,from_url,self.STR_SERVICE,scope=self.get_calendar_scope(),context=context)
        return url

    def can_authorize_google(self,cr,uid,context=None):
        return self.pool['res.users'].has_group(cr, uid, 'base.group_erp_manager')

    def set_all_tokens(self,cr,uid,authorization_code,context=None):
        gs_pool = self.pool.get('google.service')
        all_token = gs_pool._get_google_token_json(cr, uid, authorization_code,self.STR_SERVICE,context=context)

        vals = {}
        vals['google_%s_rtoken' % self.STR_SERVICE] = all_token.get('refresh_token')
        vals['google_%s_token_validity' % self.STR_SERVICE] = datetime.now() + timedelta(seconds=all_token.get('expires_in'))
        vals['google_%s_token' % self.STR_SERVICE] = all_token.get('access_token')
        self.pool.get('res.users').write(cr,SUPERUSER_ID,uid,vals,context=context)


class res_users(osv.Model): 
    _inherit = 'res.users'

    _columns = {
        'google_calendar_rtoken': fields.char('Refresh Token'),
        'google_calendar_token': fields.char('User token'), 
        'google_calendar_token_validity': fields.datetime('Token Validity'),
     }


class calendar_event(osv.Model):
    _inherit = "calendar.event"

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context= {}
        sync_fields = set(['name', 'description', 'date', 'date_closed', 'date_deadline', 'attendee_ids', 'location', 'class'])
        if (set(vals.keys()) & sync_fields) and 'oe_update_date' not in vals.keys() and 'NewMeeting' not in context:
            vals['oe_update_date'] = datetime.now()

        return super(calendar_event, self).write(cr, uid, ids, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default['attendee_ids'] = False
        if default.get('write_type', False):
            del default['write_type']
        elif default.get('recurrent_id', False):
            default['oe_update_date'] = datetime.now()
        else:
            default['oe_update_date'] = False
        return super(calendar_event, self).copy(cr, uid, id, default, context)

    _columns = {
        'oe_update_date': fields.datetime('OpenERP Update Date'),
    }


class calendar_attendee(osv.Model):
    _inherit = 'calendar.attendee'

    _columns = {
        'google_internal_event_id': fields.char('Google Calendar Event Id', size=256),
        'oe_synchro_date': fields.datetime('OpenERP Synchro Date'),
    }

    _sql_constraints = [('google_id_uniq','unique(google_internal_event_id,partner_id,event_id)', 'Google ID should be unique!')]

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        for id in ids:
            ref = vals.get('event_id',self.browse(cr,uid,id,context=context).event_id.id)

            # If attendees are updated, we need to specify that next synchro need an action
            # Except if it come from an update_from_google
            if not context.get('curr_attendee', False) and not context.get('NewMeeting', False):
                self.pool.get('calendar.event').write(cr, uid, ref, {'oe_update_date':datetime.now()},context)

        return super(calendar_attendee, self).write(cr, uid, ids, vals, context=context)

