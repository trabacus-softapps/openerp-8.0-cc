openerp.Trabacus_Capitalcentric = function(session) 
{
	var mail = session.mail;
	
	//Inherited : mail.compose_message Widget
	mail.ThreadComposeMessage = mail.ThreadComposeMessage.extend({
				
        on_compose_fullmail: function (default_composition_mode) {
            var self = this;
            if(!this.do_check_attachment_upload()) {
                return false;
            }
            var recipient_done = $.Deferred();
            if (this.is_log) {
                recipient_done.resolve([]);
            }
            else {
                recipient_done = this.check_recipient_partners();
            }
            $.when(recipient_done).done(function (partner_ids) {
                var context = {
                    'default_composition_mode': default_composition_mode,
                    'default_parent_id': self.id,
                    //'default_body': mail.ChatterUtils.get_text2html(self.$el ? (self.$el.find('textarea:not(.oe_compact)').val() || '') : ''),
                    //'default_attachment_ids': self.attachment_ids,
                    'default_partner_ids': partner_ids,
                    'mail_post_autofollow': false, 
                    'mail_post_autofollow_partner_ids': partner_ids,
                    'mail_foward':true,
                };
                if (self.is_log) {
                    _.extend(context, {'mail_compose_log': true});
                }
                if (default_composition_mode != 'reply' && self.context.default_model && self.context.default_res_id) {
                    context.default_model = self.context.default_model;
                    context.default_res_id = self.context.default_res_id;
                }

                var action = {
                    type: 'ir.actions.act_window',
                    res_model: 'mail.compose.message',
                    view_mode: 'form',
                    view_type: 'form',
                    views: [[false, 'form']],
                    target: 'new',
                    context: context,
                };

                self.do_action(action);
                self.on_cancel();
            });

        },
	});
	
	//Inherited : mail.thread.message Widget
	mail.ThreadMessage = mail.ThreadMessage.extend({
	 	
        init: function (parent, datasets, options) {
        	this._super(parent, datasets, options);
            this.ccaction_id = datasets.ccaction_id || false;
        },
	 });
	 
	
	//Inherited : mail.thread Widget
	mail.Thread = mail.Thread.extend({
		
      on_compose_message: function (event) {
            this.instantiate_compose_message();            
            this.compose_message.on_compose_fullmail('reply');
            return false;
        },
	});
	
	//Inherited : mail.record_thread Widget
	mail.RecordThread = mail.RecordThread.extend({
		
		init: function (parent, node) {	 
            this._super(parent, node);            
            this.node.params = _.extend({},this.node.params);     
        },	            
        
        render_value: function () {
            var self = this;
        	this.node.params = _.extend(this.node.params, {
           				     'show_reply_button': true,
           	});            
            this._super();
          },
        
		});
};
