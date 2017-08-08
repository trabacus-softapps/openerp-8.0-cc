$(document).ready(function()
{
	var stGlobals = {};
    stGlobals.isMobile = (/(Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|windows phone)/.test(navigator.userAgent));
	$('[data-toggle="popover"]').popover("show");
	var today = new Date();
	var tomorrow = new Date();
	var yrRange = (today.getFullYear() - 100) + ":" + today.getFullYear();
	tomorrow.setDate(today.getDate() + 2);
	$('.black_to_date').datepicker
	({
		minDate: tomorrow,
		changeMonth: true,
		changeYear: true,
		dateFormat: "dd-M-yy",
		//yearRange : yrRange
		//defaultDate: tomorrow
	});
	$('.black_from_date').datepicker
	({
		minDate: tomorrow,
		changeMonth: true,
		changeYear: true,
		dateFormat: "dd-M-yy",
		//yearRange : yrRange
		//defaultDate: tomorrow
	});

	$('.start_date').datepicker
	({
		minDate: tomorrow,
		changeMonth: true,
		changeYear: true,
		dateFormat: "yy-mm-dd",
		yearRange : yrRange
		//defaultDate: tomorrow
	});

	$('.end_date').datepicker
	({
		minDate: tomorrow,
		changeMonth: true,
		changeYear: true,
		dateFormat: "yy-mm-dd",
		yearRange : yrRange
		//defaultDate: tomorrow
	});

	$('.filter_date').datepicker
	({
		//minDate: tomorrow,
		changeMonth: true,
		changeYear: true,
		dateFormat: "dd/mm/yy",
		yearRange : yrRange
		//defaultDate: tomorrow
	});
	tomorrow.setDate(today.getDate() + 1);
    //Initiating Datepicker
    if($('.datepicker').length)
    {
		$('.datepicker').datepicker
		({
			minDate: tomorrow,
			changeMonth: true,
			changeYear: true,
			dateFormat: "dd/mm/yy",
			defaultDate: tomorrow
		});
    }


	<!--  Get Emulation Function Call -->
	openerp.jsonRpc("/capital_centric/get/emulation", 'call', {})
   .then(function (data)
   {
	   if(data != false)
	   {
		   $('#emulation_form').removeClass('hidden');

	   }
	   else
	   {
		   if(stGlobals.isMobile)
    		{
		   		$('.navbar.navbar-default').css('height','100px');
				$('main').css('padding-top','0px');
    		}
	   }

   });

	//Make Tab Active
	var url = window.location.href;
	if((url.indexOf("#")+1) > 0) {
		var activeTab = url.substring(url.indexOf("#") + 1);
		if (activeTab) {
			$("ul.nav-tabs").find('li').removeClass('active');
			$("ul.nav-tabs li").each(function () {
				if ($(this).find('a').attr('href') == '#' + activeTab) {
					$(this).addClass('active');
					$('.tab-content').find('.tab-pane').removeClass('active in');
					$('#' + activeTab).addClass('active in');
				}
			});
		}
	}

    $('.login-radio').change(function()
    {
        if ($(this).attr('id') == 'restaurant')
        {
            $("input[name='login_type']").val('venue');
        }
        else
        {
            $("input[name='login_type']").val('client');
        }
    });

	$('.sign-up-radio').change(function()
    {
        if ($(this).attr('id') == 'restaurant_type')
        {
            $("input[name='type']").val('venue');
			$('#type_label').text('Name of the Restaurant/Company');
        }
        else
        {
            $("input[name='type']").val('operator');
			$('#type_label').text('Name of the Tour Operator/Company');
        }
    });
	$('.search_btn').click(function()
	{
		$('.loader').css('display','block');
	});
	$('.clear_filters').click(function()
	{
		$('#modify_search').find('.search_btn').click();
	});

	// Contact us Slide Event
	$("#button").click(function()
	{
		 $('#contact_us_pop_up').toggle('slow');
		 document.getElementById("pop_up_contact_form").reset();
		 $(".contact_us_msg").hide();
	});

	$('#menu_drink_save').click(function()
	{
		if($('#menu_restaurant_list').val() == 'Select Restaurant')
		{
			$("html, body").animate({
            			scrollTop: 0
			}, 600);
			document.getElementById('save_prompt').innerHTML="Please Select a Restaurant!!";
			$("#save_prompt").stop(true,true).show().fadeOut(5000);
		}
		else
		{
			openerp.jsonRpc("/save_parent_restaurant", 'call',{'parent_id' : $('#menu_restaurant_list').val(), 'res_id' : $('#main_button').find('input[name=partner_id]').val()})
	  		.then(function (data)
			{
				if (data == true)
				{
					$("html, body").animate({
            			scrollTop: 0
					}, 600);
					document.getElementById('save_prompt').innerHTML="Saved Successfully!!";
					$("#save_prompt").stop(true,true).show().fadeOut(5000);
				}
			});
		}
	});

	//Calling Auto Complete
	auto_complete();
	//Calling color change function onload
	color_change('undefined');


});

// AutoComplete Function Common
function auto_complete()
{
    $( ".location" ).autocomplete({
		minLength: 3,
		source: function (request, response) {
			openerp.jsonRpc("/autocomplete", 'call', {
				'location': request["term"]
			})
				.then(function (data) {response(data);});
		},
		messages:{
		  noResults:'Entered location not found.',
		  results:function(){}
	  	},
		select: function(event, ui){
                var item = ui.item;
                if (item.id) {
					$(".location").val(item.value);
					$("input[name=location_id]").val(item.id);
				}
		},
		change: function( event, ui ){
		   var item = ui.item;
	  	},
	});
}

function add_menu(e)
{
	$('#your_orders h6').addClass('hidden');
	var frmwch ='edit';
	var menu_ids = [];
	var to_mu = 0;
	var no_covers = parseInt(e.closest('.order-menu-item').find('.price-new').data('no-covers'));
	if (e.attr('class') == 'minus-prod'){
		menuli = e.closest('li');
		menu_id = menuli.data('id');
		price  = parseFloat((menuli.find('.cart-product-price').data('price') == '') ? 0 : menuli.find('.cart-product-price').data('price'));
		symbol  = menuli.find('.cart-product-price').data('symbol');
		qty = parseFloat((menuli.find('.cart-product-qty').text() == '') ? 0 : menuli.find('.cart-product-qty').text()) - 1;
		console.log("your_orders",price,qty);
		if (qty == 0){
			menuli.remove();
		}
		else {
			tot_price = (parseFloat(price) * qty);
			console.log("your_orders",tot_price);
			menuli.find('.cart-product-qty').text(qty);
			menuli.find('.cart-product-price').text(symbol + tot_price.toFixed(2));
			menuli.find('.cart-product-price').data('tot-price', tot_price);
		}
	}
	else if(e.attr('class') == 'remove-prod'){
		menuli = e.closest('li');
		menu_id = menuli.data('id');
		menu_ids.push(menuli.data('mtable-id'));
		qty = 0;
		price = 0;
		symbol  = menuli.find('.cart-product-price').data('symbol');
		menuli.remove();
		frmwch = 'delete';
	}
	else {
		var menu_name = e.closest('.order-menu-item').find('.menu-name').text();
		var menu_id = e.closest('.order-menu-item').find('.menu-name').data('id');
		var menu_foodtype = e.closest('.order-menu-item').find('.menu-name').data('food-type');
		var price = parseFloat(e.closest('.order-menu-item').find('.price-new').data('price'));
		var symbol = e.closest('.order-menu-item').find('.price-new').data('symbol');
		var to_mu = (e.closest('.order-menu-item').find('.price-new').data('to-mu') == undefined ) ? 0 : e.closest('.order-menu-item').find('.price-new').data('to-mu');
		var qty = 1;
		var quantity = parseInt(($('#menu_' + menu_id).find('.cart-product-qty').text() == '') ? 0 : $('#menu_' + menu_id).find('.cart-product-qty').text()) + 1;
		if((quantity <= no_covers && menu_foodtype=='meal') || (menu_foodtype=='drink'))
		{
			if ($('#menu_' + menu_id).length)
			{
				menuli = $('#menu_' + menu_id);
				qty = parseFloat((menuli.find('.cart-product-qty').text() == '') ? 0 : menuli.find('.cart-product-qty').text()) + 1;
				tot_price = (parseFloat(price) * qty);
				menuli.find('.cart-product-qty').text(qty);
				menuli.find('.cart-product-price').text(symbol + tot_price.toFixed(2));
				menuli.find('.cart-product-price').data('tot-price', tot_price);
			}
			else
			{
				var ord_li = '<li class="clearfix" data-id="' + menu_id + '" data-food-type="' + menu_foodtype + '" id="menu_' + menu_id + '">' +
					'<div class="pull-left" style="margin-top:6px;">' +
					'<div class="update-product">' +
					'<a title="Minus a product" 	class="minus-prod" onclick="add_menu($(this))"><i class="fa fa-minus-circle"></i></a>' +
					'</div>' +
					'</div>' +
					'<div class="cart-product-name pull-left">' + menu_name + '</div>' +
					'<div style="margin-left:20px;" class="cart-product-sign pull-left text-spl-color"><b>X</b></div>' +
					'<div style="margin-left:20px;" class="cart-product-qty pull-left text-spl-color">1</div>' +
					'<div class="cart-product-price pull-right text-spl-color" data-symbol="' + symbol + '" data-price="' + price + '" data-tot-price="' + price + '">' + symbol + price.toFixed(2) + '</div>' +
					'<div class="cart-product-remove" style="margin-top:5px;"><a title="Remove a product" class="remove-prod" onclick="add_menu($(this))"><i class="fa fa-trash"></i></a></div>' +
					'</li>';
				$('#your_orders').append(ord_li);
				frmwch ='create';
			}
		}
		else
		{
			return;
		}
	}

	var amt_total = menu_total = drink_total = 0;

	$('#your_orders li').each(function()
	  {
		menu_ids.push($(this).data('mtable-id'));

		amt_total += parseFloat($(this).find('.cart-product-price').data('tot-price')== undefined ? 0 : $(this).find('.cart-product-price').data('tot-price'));
		if ($(this).data('food-type') == 'meal'){
			menu_total += parseFloat($(this).find('.cart-product-price').data('tot-price')== undefined ? 0 : $(this).find('.cart-product-price').data('tot-price'));
		}
	    if ($(this).data('food-type') == 'drink'){
			drink_total += parseFloat($(this).find('.cart-product-price').data('tot-price')== undefined ? 0 : $(this).find('.cart-product-price').data('tot-price'));
		}

	  });

	if (!$('#your_orders li').length){
		$('#your_orders h6').removeClass('hidden');
	}
	$('.amt-total').text(symbol+amt_total.toFixed(2));
	$('.menu-total').text(symbol+menu_total.toFixed(2));
	$('.drink-total').text(symbol+drink_total.toFixed(2));

	openerp.jsonRpc("/fit_website/cc_menus_table/", 'call', {'db_id':parseInt(menu_id), 'price': price , 'guest': qty,'menu_ids':menu_ids,'frmwch': frmwch, 'to_mu':to_mu})
      .then(function (data)
      {
		  if (frmwch == 'create'){
			  console.log("22222data",data);
			  $('#menu_' + menu_id).data('mtable-id',data);
		  }
		  console.log('menu_table id',$('#menu_' + menu_id).data('mtable-id'));

      });
}

// function for going to the booking completion page on click of available time buttons
function time_selected(e)
{
	var venu_id = $("input[name=venu_id]").val();
	var post = JSON.parse($("input[name=post]").val());
	if(post['lead_id'])
	{
		post['type']=$('#booking_type').val();
		post['resv_date']=$('#booking_date').val();
		post['time_selected']=$('#booking_time').val();
		post['type_change']=$('#type_change').val();
	}
	console.log("post",post);
	var type = post['type'];
	var menu = [];
	var time_selected;
	var event_id = 0;
	$('#your_orders li').each(function()
	{
		console.log('menu lis',$(this));
	    menu.push($(this).data('mtable-id'));
    });
	console.log('menus',menu,$('#your_orders li').length);
	console.log('venue_id',parseInt(venu_id),post['time_selected'],menu,type,0,post);
	if($('#your_orders li').length > 0)
	{
		openerp.jsonRpc("/capital_centric/fit/search/result/booking_done/", 'call', {'venue_id':parseInt(venu_id), 'req_time':post['time_selected'], 'menu_ids':menu, 'type':type, 'event_id':0, 'json':post})
		.then(function (data)
		{

			if (data[0] == 'unavilability')
			{
				alert('Sorry! There seems to be no availability for the time selected. Please search again.');
			}
			else if (data[0] == 'shift_unavailable')
			{
				alert('Sorry! Maximum booking for the shift has been achieved. Please search again.');
			}
			else
			{
				document.open();
				document.write(data);
				document.close();
			}
			//if (data[0] == 'unavilability')
			//{
			//	fader = document.getElementById('login_fader');
			//  	login_box = document.getElementById('div1');
			//  	$('#selc_time').val(data[1]);
			//  	$('#selc_date').val(data[2]);
			//  	fader.style.display = "block";
				//$("#div2").find("#alert_msg").text("Sorry! There seems to be no "+
			//                                       "availability for the time selected. Please click "+
			//                                       "on 'Back To Booking' to select an alternative time "+
			//                                       "or click on 'Send Email' to request "+
			//                                       "availability");
			//    $("#div2").show();
			//    return;
			//}
			//if (data[0] == 'shift_unavailable')
			//{
			//	fader = document.getElementById('login_fader');
			//  	login_box = document.getElementById('div1');
			//  	$('#selc_time').val(data[1]);
			//  	$('#selc_date').val(data[2]);
			//  	fader.style.display = "block";
				//$("#div2").find("#alert_msg").text("Sorry! Maximum booking for the shift has been achieved. " +
				//								   "Please click on 'Back To Booking' to select an alternative date or " +
				//								   "click on 'Send Email' to request");
			//    $("#div2").show();
			//    return;
			//}
			//if (data == 'low_balance')
			//{
			//	fader = document.getElementById('login_fader');
			//  	login_box = document.getElementById('div1');
			//  	fader.style.display = "block";
			//    $("#div4").show();
			//    return;
			//}
			//else
			//{
			//	$('#wchpage').val('westfield_search');
			//	document.open();
			// 	document.write(data);
			//	document.close();
			//}
		});
	}

}

//Onchange of date and time populate restaurant name
function type_onchange(e)
{
	var confirm_msg = true;
	if (e.attr('id') == 'booking_type')
	{
		var confirm_msg = confirm("This action will reload all menus for the selected meal type and time. Your booking will be amended only when you click on UPDATE BOOKING and complete the amendment process.");
	}
	if (confirm_msg == true)
	{
		$('.cfo-checkoutarea').css('display','none');
		$('#type_change').val('yes');
		var booking_date = $('#booking_date').val();
		var booking_type = $('#booking_type').val();
		var res_id       = parseInt($('#booking_res').val());
		var post = JSON.parse($("input[name=post]").val());
		console.log("post",post);
		var option_str = '';
		$('.loader').css('display','block');
		option_str = '<option>Select Time<option>';
		openerp.jsonRpc("/get_time_slots", 'call', {'res_id': res_id, 'booking_date' : booking_date, 'booking_type' : booking_type, 'post' : post})
		  .then(function (data)
		  {
			  if (data[0].length > 0 && data[1].length > 0)
			  {
				  console.log("data[0]",data[1].length);
				  for(var i=0;i<data[0].length;i++)
				  {
					  option_str = option_str + '<option value="'+data[0][i]+'">'+data[0][i]+'</option>';
				  }
				  $('#booking_time').html(option_str);
				  $('#time_div').removeClass('hidden');
				  $('.side-block-order').removeClass('hidden');
				  $('.menu-tabs-wrap').removeClass('hidden');
				  $('#no_timeslot').css( 'display','none');
				  if (e.attr('id') == 'booking_type')
				  {
					  $('#your_orders').html('<h6 class="text-center">Please select the menus to proceed.</h6>');
					  $('#menu_list').html(data[1]);
					  $('#drink_list').html(data[2]);
					  $('.menu-total').text('£0.00');
					  $('.drink-total').text('£0.00');
				  	  $('.amt-total').text('£')
				  }


			  }
			  else
			  {
				  $('#time_div').addClass('hidden');
				  $('.side-block-order').addClass('hidden');
				  $('.menu-tabs-wrap').addClass('hidden');
				  $('#no_timeslot').css( 'display','block');
			  }
			  $('.loader').css('display','none');
		  });

	}
}

////Onchange of restaurant name get time slots
//function onchange_restaurants(e)
//{
//	var booking_date = $('#booking_date').val();
//	var booking_type = $('#booking_type').val();
//	var res_id       = parseInt($('#booking_res').val());
//	var option_str = '';
//	option_str = '<option>Select<option>'
//	openerp.jsonRpc("/get_time_slots", 'call', {'res_id': res_id, 'booking_date' : booking_date, 'booking_type' : booking_type})
//      .then(function (data)
//      {
//		  if (data)
//		  {
//			  for(var i=0;i<data.length;i++)
//			  {
//				  option_str = option_str + '<option value="'+data[i]+'">'+data[i]+'</option>';
//			  }
//			$('#booking_time').html(option_str);
//		  }
//      });
//	//$('#amend_res_btn').removeClass('hidden');
//	//$('#amend_res_btn').attr('href','/capital_centric/fit/grid_view/result/'+res_id+'?lead_id='+$('#res_lead_id').val()+'&booking_date='+booking_date+'&type='+booking_type+'&restaurant_id='+res_id+'&res_name='+$('#booking_res').text().replace(' ','-')+'&frm_whch=amend');
//}

//Onchange of time slots
function onchange_time_slots(e)
{
	var booking_date = $('#booking_date').val();
	var booking_type = $('#booking_type').val();
	var res_id       = parseInt($('#booking_res').val());
	var lead_id      = parseInt($('#res_lead_id').val());
	var booking_time = e.val();
	openerp.jsonRpc("/get_availability", 'call', {'res_id' : res_id, 'lead_id' : lead_id, 'booking_date' : booking_date, 'booking_type' : booking_type, 'booking_time' : booking_time, 'booking_covers' : ''})
      .then(function (data)
      {
		  if (data == true)
		  {
			$('.cfo-checkoutarea').css('display','block');
		  }
		  else
		  {
			$('#available_msg').show().fadeOut(5000);
		  }
      });
}

//Onclick of sign button inside modal
function onclick_sign_in(e)
{
	var modalBody = e.closest('.modal-dialog');
	var login = modalBody.find('#email_res').val();
	var password = modalBody.find('#password_res').val();
	console.log("login",login,password);
	if (login == '')
	{
		modalBody.find('#email_error').show().fadeOut(5000);
		return false;
	}
	else if (password == '')
	{
		modalBody.find('#password_error').show().fadeOut(5000);
		return fasle;
	}
	else
	{
		openerp.jsonRpc("/onclick_sign_in", 'call', {'login': login, 'password' : password})
		  .then(function (data)
		  {
		    console.log("data",data);
			if (data == true)
			{

				$('#modify_search').find('.search_btn').click();
			}
			else
			{
				modalBody.find('#login_error').show().fadeOut(5000);
			}
		  });
	}
}
function onclick_mybookings(e)
{
	var ahref = e.attr('href');
	var formact = $('#filter_form').attr('action').split('#')+ahref;
	$('#filter_form').attr('action',formact);
}
function onchange_menu_drink(e)
{
	var option_str = '';
	if (e.prop("checked") == true)
	{
			$('#menu_tab').addClass('hidden');
			$('#drink_tab').addClass('hidden');

		openerp.jsonRpc("/get_restaurant_list", 'call',{'res_id':$('#main_button').find('input[name=partner_id]').val()})
	  	.then(function (data)
	  	{
			if (data)
			{
				  for(var i=0;i<data.length;i++)
				  {
					  option_str = option_str + '<option value="'+data[i]['id']+'">'+data[i]['name']+'</option>';
				  }
						$('#menu_restaurant_list').html(option_str);
				        $('#menu_select_restaurant').css('display','block');
					    //$('#menu_drink_save').css('display','block');

			}
	  	});
	}
	else
	{
		    //$('#menu_restaurant_list').html(option_str);
		    $('#menu_select_restaurant').css('display','none');
			$('#menu_tab').removeClass('hidden');
			$('#drink_tab').removeClass('hidden');

	}

}

function color_change(e)
{
	var wbsite_color;
	var submenu_color;
	var header_color;
	var font_website;
	$("#d_"+e.id+"").val(e.value);

	if(e.value != undefined)
	{
		wbsite_color     = $("#d_wbsite_color").val();
		submenu_color    = $("#d_submenu_color").val();
		header_color     = $("#d_header_color").val();
		font_website     = $("#d_font_website").val();
		$("#"+e.id+"").val(e.value);
	}
	else
	{
		wbsite_color     = $("#wbsite_color").val();
		submenu_color    = $("#submenu_color").val();
		header_color     = $("#header_color").val();
		font_website     = $("#font_website").val();
	}


	$.when($.get("/fit_website/static/src/css/main.css"))
	.done(function(response)
	{

		if(wbsite_color == '')
		{
			var m_color       = response.replace(/\#ED1E6B/g,'#ED1E6B');
			//var d_m_color     = m_color.replace(/\#793487/g,'#793487');  // dark Color 30%
		}
		else
		{
			var m_color       = response.replace(/\#ED1E6B/g,wbsite_color);
			//var d_m_color     = m_color.replace(/\#793487/g,ColorLuminance(wbsite_color, -0.3));  // dark Color 30%
		}



		if(submenu_color == '')
		{
			var s_color       = m_color.replace(/\#E64D64/g,'#E64D64');
			//var d_s_color     = s_color.replace(/\#bfafce/g,'#bfafce');
		}
		else
		{
			var s_color       = m_color.replace(/\#E64D64/g,submenu_color);
			//var d_s_color     = s_color.replace(/\#bfafce/g,ColorLuminance(submenu_color, -0.3));
		}
		if(header_color != '')
		{
			$('.navbar-sticky').css('background-color',header_color);
			$('.not-transparent-header .navbar-default').css('background-color',header_color);
			$('.footer-area-content').css('background-color',header_color);
		}
		//var h_color       = m_color.replace(/\rgba(0, 0, 0, 0.8)/g,header_color);

		//$('<style id="new_css"/>').text(h_color).appendTo($('head'));
		if(font_website != '')
		{
			var font = s_color.replace(/\'Open Sans', sans-serif/g,font_website);
			$('<style id="new_css"/>').text(font).appendTo($('head'));
			if ($("#google_font_link").length > 0)
			{
				$("#google_font_link").remove();
			}
			$('head').append('<link id="google_font_link" rel="stylesheet" href="https://fonts.googleapis.com/css?family='+font_website+'" type="text/css"></link>');
		 }
		 else
		 {
			$('<style id="new_css"/>').text(s_color).appendTo($('head'));
		 }
	 });
}
function onclick_view_availabilty(e)
{
	var link = e;
	var id = e.closest('form');
	var res_id = parseInt(id.find('input[name=restaurant_id]').val());
	var booking_date = id.find('input[name=resv_date]').val();
	var booking_type = id.find('input[name=type]').val();
	var booking_time = e.text().trim();
	var booking_covers = parseInt(id.find('input[name=no_persons]').val());
	var min_time = id.find('input[name=min_time]').val();
	var max_time = id.find('input[name=max_time]').val();
	openerp.jsonRpc("/onmouseover_availabilty", 'call', {'res_id' : res_id, 'booking_date' : booking_date, 'booking_type' : booking_type, 'booking_time' : booking_time,  'booking_covers' : booking_covers, 'min_time' : min_time, 'max_time' : max_time})
	.then(function (data)
	{
		$('#view_'+res_id).find('.modal-body').html(data);
		$('#view_'+res_id).find('.modal-title').html('Availablity for '+booking_date+' ('+min_time+'-'+max_time+')');
	});

}
function onclick_paid_amend(e)
{
	var bookingvals = {};
	var fElements = e.closest('.modal-content').find('.modal-body input');
	var selectname = e.closest('.modal-content').find('.modal-body select').attr('name');
	for(var i=0; i < fElements.length; i++)
	{
		bookingvals[fElements[i].name] = fElements[i].value;
	}
	bookingvals[selectname] = e.closest('.modal-content').find('.modal-body select').val();
	openerp.jsonRpc("/amend_paid_booking", 'call', {'post': bookingvals})
		.then(function (data)
	{
		if(data == true)
		{
			e.closest('.modal-content').find('p.alert-danger').removeClass('hidden');
			e.closest('.modal-content').find('p.alert-danger span').text('Amendments are possible only before 36 hours of the booking date/time.');
			e.closest('.modal-content').find('p.alert-danger').fadeOut(5000);
		}
		else
		{
			e.closest('.modal-content').find('p.alert-danger').removeClass('hidden');
			e.closest('.modal-content').find('p.alert-danger span').text('Your amend has been done succesfully.');
			e.closest('.modal-content').find('p.alert-danger').fadeOut(5000);
		}
	});
}

//function ColorLuminance(hex, lum)
//{
//	// validate hex string
//	hex = String(hex).replace(/[^0-9a-f]/gi, '');
//	if (hex.length  &lt; 6)
//	{
//		hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
//	}
//	lum = lum || 0;
//
//	// convert to decimal and change luminosity
//	var rgb = "#", c, i;
//	for (i = 0; i  &lt; 3; i++)
//	{
//		c = parseInt(hex.substr(i*2,2), 16);
//		c = Math.round(Math.min(Math.max(0, c + (c * lum)), 255)).toString(16);
//		rgb += ("00"+c).substr(c.length);
//	}
//	return rgb;
//}
function showcuisine()
{
	var opt = document.getElementById("cuisine");
	var no_of_opt = opt.length;
	var selValue = new Array
	var j = 0;
	for (i=0; i < no_of_opt;i++)
	{
	if (opt[i].selected === true)
	{
	selValue[j] = parseInt(opt[i].value);
	j++
	}
	}
	console.log('selValue',selValue);

	selValue = selValue.join(",");

	console.log('selValue',selValue);
	document.getElementById("cuisine_ids").innerHTML = selValue
}

function showdining()
{
	var opt = document.getElementById("dining_style");
	var no_of_opt = opt.length;
	var selValue = new Array;
	var j = 0;
	for (i=0; i < no_of_opt;i++)
	{
	if (opt[i].selected === true)
	{
	selValue[j] = parseInt(opt[i].value);
	j++
	}
	}
	console.log('selValue',selValue);

	selValue = selValue.join(",");

	console.log('selValue',selValue);
	document.getElementById("dining_ids").innerHTML = selValue
}