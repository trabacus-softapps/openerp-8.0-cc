
// function for change in guest in menus table and on change of quantity in drinks table
function change_guest(e)
{    
 	  $('#no_guest').hide();
 	  var table;
 	  if(e.name == 'guest')
 	  {
 	      table = "restaurant_table";
 	  } 
	  else if (e.name == 'eguest')
	  {
	  	  table = "events_table";
	  }
 	  else
 	  {
 	  	  table = "drinks_table";
 	  }
      var id = $(e).closest("tr");
      var db_id = id.find("#db_id").text(); 
      var name = id.find(".menu_name").text();
      var guest = id.find("select").val();
      var price = id.find("#single_price").text();  
      var new_value = guest * price ;
      var partner_id = $("input[name='Id']").val(); 
      if(e.name == 'guest' || e.name == 'eguest') 
      {
      	id.find("#total_price").text(parseFloat(new_value).toFixed(2));
      } 
      else
      {
      	id.find("#total_price_drinks").text(parseFloat(new_value).toFixed(2));
      }
      var menu = [];
	  $('table#'+table+' tr#menu_serial').each(function()
	  { 
	    	var x = $(this).find("#db_id").text();
		    if (x != undefined)
		   	{	
		   		menu.push(parseInt(x));
		   	}
	  });
      openerp.jsonRpc("/website_capitalcentric/cc_menus_table/", 'call', {'db_id':parseInt(db_id), 'price': new_value, 'guest': guest,'menu_ids':menu})
      .then(function (data) 
      {	
      		if(e.name == 'guest' || e.name == 'eguest')
      		{
      			$('.grand_total_value').text(parseFloat(data).toFixed(2));
      		}
      		else
      		{
      			$('.drinks_grand_total_value').text(parseFloat(data).toFixed(2));
      		}
      		if(e.name == 'eguest')
      		{
      			$('.main_gtotal_value').text(parseFloat(data).toFixed(2));
      		}
      		else
      		{
      			var add_menu_drink = parseFloat($('.grand_total_value').text()) + parseFloat($('.drinks_grand_total_value').text());
      			$('.main_gtotal_value').text(add_menu_drink.toFixed(2));
      		}
      });
}

function onchange_meal_date(e)
{
	var menu = [];	
	var frmwch = 'events';
	var event_id = 0;
	var edate = e.value; 
	
	$(".alert-danger").hide();
	if (e.id == 'e_date')
	{
		var today = new Date();
		var date_selec = new Date(edate);
		if (date_selec <= today)
		{
			e.value = "";
			alert("Please select date prior to today");			
			document.getElementById('e_date').focus();	
            return false;
		}
	}
	
    $('table#events_table tr#menu_serial').each(function()
	{	
	    var x = $(this).find("#db_id").text();
	    if (x != undefined)
	   	{
	   		menu.push(parseInt(x));
	   	}
    });
    
    $('table#drinks_table tr#menu_serial').each(function()
	{	
	    var x = $(this).find("#db_id").text();
	    if (x != undefined)
	   	{
	   		menu.push(parseInt(x));
	   	}
    });
    
    if (e.name == 'type')
    {	
    	frmwch = e.value;
    	if (frmwch == '')
    	{
    	   document.getElementById('show_emenus').innerHTML="";
      	   $('#e_time').empty();
      	   $('.main_gtotal_value').text('0.00');
      	   var etime = '<option value=""> Select Time </option>';
      	   $(etime).appendTo($("#e_time"));
      	   return true;
      	}    	
    	var event_id = $("#event_id").val();
    	var edate = $("#e_date").val();
    }
    
    if(document.getElementById('is_group').innerHTML == 'Group')
    {	frmwch = $('#type').val();
    	event_id = $(".single_id").val();
    }
    openerp.jsonRpc("/website_capitalcentric/cc_menus_table/", 'call', {'db_id':event_id, 'price': 0, 'guest': 0, 'menu_ids':menu, 'frmwch': frmwch, 'e_date':edate})
      .then(function (data) 
      {
	      	if (data && data[1])
	      	{
	      	$('#e_time').empty();
	  		var etime = '<option value=""> Select Time </option>';
	  		for (i=0; i < data[1].length; i++)
	  		{	
	  			etime += '<option>'+ data[1][i]['name'] +'</option>';
	  		}
	  		$(etime).appendTo($("#e_time"));
	  		}
	      	if (e.name == 'type')
	      	{	
	      		document.getElementById('show_emenus').innerHTML = "";
	      		document.getElementById('show_emenus').innerHTML = data[0];
	      		if(data[2])
	      		{
	      			document.getElementById('show_emenus').innerHTML += data[2];	
	      		}		
	      	} 
	  		if (document.getElementById('is_group').innerHTML == 'Group')
	  		{	
	  			// document.getElementById('show_emenus').innerHTML += data[2];  		
	  			$('#events_div').css({'width':'48%','float':'left'});
	  			$('#drinks_div').css({'width':'48%','float':'right'});
	  			$('#drinks_table_div').css({'overflow-y':'auto','height':'200px'});
	  			$('#grand_total_table').css('display','block');
	  			$("table#drinks_table tr#menu_serial").addClass('alternative_record');
	  			$("table#drinks_table tr#menu_serial").css('border-bottom','0px solid transparent');
	  			$("table#drinks_table tr#menu_serial td span.menu_name").css('font-size','11pt');
	  			$(".show_emenus").css('overflow-y','initial');
	  			
	  			if($("table#drinks_table tr").length == 0)
	  			{
	  				$('#events_div').css({'width':'100%'});
	  				$('#drinks_div').addClass('hidden');
	  				$('#drink_heading').addClass('hidden');
	  				$('#grand_total_drink_div').addClass('hidden');
	  				$('#menu_total_drink_div').addClass('hidden');
	  				$('#events_div').css({'width':'100%'});
	  			}
	  		}	
      });    
} 

// function for going to the booking completion page on click of available time buttons
function time_selected(e) 
{	
	if($('#wchpage').text().replace(/\s+/g, " ") == ' events ' || (document.getElementById('is_group') && document.getElementById('is_group').innerHTML == 'Group'))
	{
		var time = e;
	}
	else
	{
		var time = e.innerHTML;
	}
	var partner_id = $("#partner_id").val();
	var event_id = $("#event_id").val();
	var type = $("#type").val();
	var menu = [];
	$('table#restaurant_table tr#menu_serial').each(function()
	{	
	    var x = $(this).find("#db_id").text();
	    if (x != undefined)
	   	{
	   		menu.push(parseInt(x));
	   	}
    });
    $('table#drinks_table tr#menu_serial').each(function()
	{	
	    var x = $(this).find("#db_id").text();
	    if (x != undefined)
	   	{
	   		menu.push(parseInt(x));
	   	}
    });
    
    $('table#events_table tr#menu_serial').each(function()
	{	
	    var x = $(this).find("#db_id").text();
	    if (x != undefined)
	   	{
	   		menu.push(parseInt(x));
	   	}
    });
	openerp.jsonRpc("/capital_centric/fit/search/result/booking_done/", 'call', {'venue_id':parseInt(partner_id), 'req_time':time, 'type':type, 'menu_ids':menu, 'event_id':event_id})
	.then(function (data) 
    {  	
      	if (data[0] == 'unavilability')
      	{
      		fader = document.getElementById('login_fader');
          	login_box = document.getElementById('div1');
          	$('#selc_time').val(data[1]);
          	$('#selc_date').val(data[2]);
          	fader.style.display = "block";
			$("#div2").find("#alert_msg").text("Sorry! There seems to be no "+
                                               "availability for the time selected. Please click "+
                                               "on 'Back To Booking' to select an alternative time "+
                                               "or click on 'Send Email' to request "+
                                               "availability");
            $("#div2").show();
            return;
      	}
		if (data[0] == 'shift_unavailable')
      	{
      		fader = document.getElementById('login_fader');
          	login_box = document.getElementById('div1');
          	$('#selc_time').val(data[1]);
          	$('#selc_date').val(data[2]);
          	fader.style.display = "block";
			$("#div2").find("#alert_msg").text("Sorry! Maximum booking for the shift has been achieved. " +
											   "Please click on 'Back To Booking' to select an alternative date or " +
											   "click on 'Send Email' to request");
            $("#div2").show();
            return;
      	}
        if (data == 'low_balance')
      	{
      		fader = document.getElementById('login_fader');
          	login_box = document.getElementById('div1');
          	fader.style.display = "block";
            $("#div4").show();
            return;
      	}
      	else
      	{	
      		$('#wchpage').val('westfield_search'); 
      		document.open();
      	 	document.write(data);
        	document.close();
        }
    });
}

//function for menu description pop-up
function menu_popup(m)
{
      var id = $(m).closest("tr");
      var desc = id.find(".menu_desc").text();
      var name = id.find(".menu_name").text();
	  var new_name = (name.split('Also')[0]);
      fader = document.getElementById('login_fader');
  	  var login_box = document.getElementById('div1');
  	  document.getElementById('alert_msg_name').innerHTML=new_name;
	  document.getElementById('alert_msg_menu').innerHTML=desc;
	  fader.style.display = "block";
	  $("#div5").show();
}

//function for showing "NO AVAILABILTY" pop-up and request the same with a message
function get_value()
{   
    openerp.jsonRpc("/capital_centric/request/availability", 'call', {'message':$("#message").val(), 'time':$("#selc_time").val(),'date':$("#selc_date").val(),'rest_name':$(".hotelcolor").text()})
	.then(function (data)
	{
		fader = document.getElementById('login_fader');	
	    $("#div2").hide();
	    fader.style.display = "none";
	    $('#no_availability').show();
	    return;
 	});
}

function onchange_payment(e)
{
	var payment = e.value;
	var info = [];
	// $('table#info_table tr').each(function() 
	// {		
       // var x = $(this).find("#info_db_id").val();
       // if (x != undefined)
       	// {
       		// info.push(parseInt(x));
       	// }
       	// console.log(info);
	// });
	var id = $(this).closest("tr");
	var info = $("input[name='info_ids']").val();
	openerp.jsonRpc("/capital_centric/add_transactionchrg/", 'call', {'info_ids':info,'payment':payment})
	.then(function (data) 
	{
		$('#tr_charge').text(data[2] + parseFloat(data[1]).toFixed(2)); 
		$('#sumry_total').text(data[2] + parseFloat(data[0]).toFixed(2));
		$('#payment_total').val(parseFloat(data[0]).toFixed(2));			
	});
}


$(function()
{ 
    $("#div2").hide();
    $("#div2").draggable();
    $("#div4").hide();
    $("#div4").draggable();  
    $("#div5").hide();
    $("#div5").draggable();
    //$("#div6").hide();
    //$("#div6").draggable();
});

function low_bal_continue()
{
    $("#div4").hide();
    $("#div1").show();
}

$(document).ready(function() 
{
	


	// $("tr#alert_message").hide();
	if ($("#tr_alert")[0])
	{
 		$("body").scrollTop($("#tr_alert").offset().top - $("#alert_div").outerHeight(true));
		// $('#alert_div')[0].scrollIntoView(true);
	}
	
	
	
	
	$("tr#sc_tr a.sc_link").hide();
	$('table#booking_menu_table tr#menu_ids_tr').each(function()
	{
		var x = $(this).find('.sc_value').val();
		if(x == 'true')
		{
			var table = $(this).closest("table#booking_menu_table");
			table.find('tr#sc_tr a.sc_link').show();
		}
	});
	
// On click of cancel button pop up
	$('.cancel_button').on('click',function()
	{
			$("#div2").hide();
			$("#div4").hide();
			$("#div5").hide();
			//$("#div6").hide();
			$("#empty_cart_dialog").hide();
			fader.style.display = "none";
    });
    
   	if($.browser.webkit) 
    {
        $('table#info_table tr#info_table_tr').css({"display":"table","width":"100%"}); 
    };

// On click of "Make Another Booking" & "Complete Booking" on mycart page	
	$('.from_wch_button').on('click',function()
	{	
	    var button_id = $(this).attr('id');
	    $("input[name='from_wch']").val(button_id);
	    var vals = {};
     	$('table#guest_details_table').each(function()
        {   var dict = {};
		    dict['cust_ref']          = $(this).find(".cust_ref").val();
	        dict['title']   		  = $(this).find(".title").val();
            dict['partner_name']      = $(this).find(".partner_name").val();
            dict['contact_name']      = $(this).find(".contact_name").val();
            dict['mobile']            = $(this).find(".mobile").val();
            dict['email_from']        = $(this).find(".email_from").val();
            dict['spcl_req']		  = $(this).find(".spcl_req").val();
        	dict['send_confirmation'] = $(this).find("#send_confirmation").is(':checked');
        	dict['terms'] 			  = $(this).find("#terms").is(':checked');
            var db_id  				  = $(this).find(".db_id_info").val();
           	vals[db_id] = dict;
           	
           	if(dict['cust_ref'] == '')
	  		{	
	  			$(this).find(".cust_ref").focus();
	  			// $(this).find("tr#alert_message").show();
	  			// $(this).find("#to_ref_alert").innerHTML = "Please Enter ";
	  			// $(this).document.getElementById('to_ref_alert').innerHTML="Please Enter an Email!!";
	  			document.getElementById("check_value").value = 1;
	  			return false;
	  		}
	  		if(dict['title'] == '')
	  		{	
	  			$(this).find(".title").focus();
	  			// $(this).find("tr#alert_message").show();
	  			document.getElementById("check_value").value = 1;
	  			return false;
	  		}
	  		if(dict['partner_name'] == '')
	  		{	
	  			$(this).find(".partner_name").focus();
	  			// $(this).find("tr#alert_message").show();
	  			document.getElementById("check_value").value = 1;
	  			return false;
	  		}
	  		if(dict['contact_name'] == '')
	  		{	
	  			$(this).find(".contact_name").focus();
	  			// $(this).find("tr#alert_message").show();
	  			document.getElementById("check_value").value = 1;
	  			return false;
	  		}
	  		if(dict['mobile'] == '' && dict['send_confirmation'] == true)
	  		{	
	  			$(this).find(".mobile").focus();
	  			// $(this).find("tr#alert_message").show();
	  			document.getElementById("check_value").value = 1;
	  			return false;
	  		}
	  		if(dict['email_from'] == '' && dict['send_confirmation'] == true)
	  		{	
	  			$(this).find(".email_from").focus();
	  			// $(this).find("tr#alert_message").show();
	  			document.getElementById("check_value").value = 1;
	  			return false;
	  		}
	  		if(dict['terms'] == false)
	  		{	
	  			$(this).find("#terms").focus();
	  			// $(this).find("tr#alert_message").show();
	  			document.getElementById("check_value").value = 1;
	  			return false;
	  		}
	  		// if(dict['send_confirmation'] == false)
	  		// {	
	  			// $(this).find("#send_confirmation").focus();
	  			// document.getElementById("check_value").value = 1;
	  			// return false;
	  		// }
        });
        var check_value = document.getElementById('check_value').value;
		if(check_value == 1)
		{
			$("#check_value").val('');
			return false;
		}
		else
		{
			if(button_id == 'complete')
			{
				if($('.paymentType').val() == '')
	    		{
	    			$(".paymentType").focus();
		  			// document.getElementById("check_value").value = 1;
		  			return false;
	    		}
	    		if($('.payment_type').text().trim() == 'Payment On Purchase')
	    		{
	    			var payment_confirm = confirm("You are now being directed to the payment site. Please note that your payment will be processed in favour of ‘Season & Vine Limited’");
	    			if (payment_confirm == false)
			        {	
					    return false;
			        }
	    		}
	    		if($('#session_or_nt').length > 0)
	    		{
	    			fader = document.getElementById('login_fader');
	    			var login_box = document.getElementById('sign_in_modal');
	    			fader.style.display = "block";
			        $("#sign_in_modal").show();
			        return false;
	    		}
	    		
			}
			$("#guest_details_form").submit();
		}
	});
	
// On blur of input fields in mycart page
   $('.guest_input').on('change',function()
   {	
   		var dict = {};
		var frm_wch_field_id = $(this).attr('id');
		var value = this.value;
	 	var db_id = $(this).closest("table#guest_details_table");
	 	// db_id.find("tr#alert_message").hide();
		if(frm_wch_field_id == 'send_confirmation' || frm_wch_field_id == 'terms')
		{
			if($(this).attr('checked'))
			{
				value = true;
			}
			else
			{
				value = false;
			}
		}		
		dict[frm_wch_field_id] =  value;
		openerp.jsonRpc("/website_capitalcentric/save_input_my_cart/", 'call', {'value' : dict, 'db_id' : parseInt(db_id.find(".db_id_info").val())});
   });

// On click of "Remove from Cart" in mycart page	
	$('.remove_from_cart').on('click',function()
	{
		var id = $(this).closest("tr");
  		var db_id = id.find("#db_id").text();
  		var r=confirm("Are you sure you want to remove this from your cart ?");
        if (r==true)
        {	
		    openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value' : 'lead_table', 'db_id' : parseInt(db_id)})
	        .then(function (data) 
	        {	
	         	id.remove();
	         	window.location.href = "/capital_centric/operator/my_cart/";
	        });
        }
	});
	
	// $('.fc-day-header').css('width','14.3%');
	
    $('#wchpage').hide();
    $('#second_bookingline').hide();
    $('#no_guest').hide();
    $('#no_availability').hide();
    console.log("Hello",$('#wchpage').text().replace(/\s+/g, " "));
	if($('#wchpage').text().replace(/\s+/g, " ") == ' grid_view ' || $('#wchpage').text().replace(/\s+/g, " ") == ' search ')
	{
		$('div[id="search_button"]').addClass('color'); 
		$('#wchpage').val('search');
    }
    else if($('#wchpage').text().replace(/\s+/g, " ") == ' westfield_search ' || $('#wchpage').text().replace(/\s+/g, " ") == ' greenwich_search ')
    {
    	$('div[id="partnerbutton"]').addClass('color'); 
    	$('#wchpage').val('westfield_search'); 
    }	
    else if($('#wchpage').text().replace(/\s+/g, " ") == ' events ')
    {
    	$('div[id="eventsbutton"]').addClass('color'); 
    	$('#wchpage').val('events'); 
    }	
    else
    {
    	$('div[id="partnerbutton"]').removeClass('color'); 
    	$('div[id="search_button"]').removeClass('color'); 
    	$('div[id="eventsbutton"]').removeClass('color');
    }
	
    $('.single_id').hide();
    $('.test').hide();
   	$("#select_time_div").hide(); 
    $("#booking_text").hide();
    $("#drink_gtotal_div").hide();

    if($('#wchpage').text().replace(/\s+/g, " ") == ' events ')
    {
    	$("#grand_total_table").css('border-top','1px solid #f2f2f2');
    	$("#grand_total_table").show();
    }
    else
    {
    	// $("#grand_total_table").css('width','48%');
    	$("#grand_total_table").hide();
    }
    $("#upper_right_div").hide();
    $('#inner_res_button_block').hide();
    $('#button_menus_content').hide();
    $('#button_drinks_content').hide();
    
    $(".button_common_res").click(function()
     {
     	var wch_id = $(this).attr('id');
     	if(wch_id == 'forget_password')
     	{
     		$('.password_res').removeAttr('required');
			$('#from_wch_button').val('forget_password');
     		var get_email = $('#email_res').val();
     		if(get_email == '')
     		{	
     			return;
     		}
     		else
     		{
	     		var confirm_value = confirm('Do you want to reset your password?');
	      		console.log(confirm_value);
	      		if(confirm_value==true)
	      		{
	      			console.log("submitted");	
	      			if($("input[name='login_type']").val() == 'venue')
	      				$('#rloginformblock').submit();
      				if($("input[name='login_type']").val() == 'client')
	      				$('#operator_form').submit();
	      		}
	      		else
	      		{	
	      			$('.password_res').attr('required', true);
	      			console.log("not submitted");
	      			$('#from_wch_button').val('');
	      			return false;
	      		}
	      	}
     	}
     	if(wch_id == 'submit')
     	{
     		$('#from_wch_button').val('submit');
     	}
     });
    
    $(".common_button").click(function() 
    { 	          
      	  var wch_button   =   $(this).attr('id');
	      $(this).addClass('button_common');
	      if(wch_button == 'menus')
	      {
		      	$('#drinks').removeClass("button_common");      	
		      	$('#button_drinks_content').hide();
		 		$('#button_menus_content').show();
		 		$("#menu_gtotal_div").show();
		 		$("#drink_gtotal_div").hide();
	      }
	      if(wch_button == 'drinks')
	      {
		      	$('#menus').removeClass("button_common");
		      	$('#button_menus_content').hide();
		 		$('#button_drinks_content').show();
		 		$("#drink_gtotal_div").show();
		 		$("#menu_gtotal_div").hide();
	      }
     });
     
     if($('#wchpage').text().replace(/\s+/g, " ") == ' events ')
     	var slicepoint = 300;
     else
     	var slicepoint = 750;
    
    $('#hotelinfo').expander({
		    slicePoint : slicepoint,
		    preserveWords: true,
		    userCollapsePrefix : '... '
  	});
  	
  	$('#eventinfo').expander({
		    slicePoint : slicepoint,
		    preserveWords: true,
		    userCollapsePrefix : '... '
  	});

// On click of Continue Button 
    $('.continue_button').on('click',function()
    {
    	var count = 0;
    	var table;
    	// var count_drinks = 0;
    	if($('#wchpage').text().replace(/\s+/g, " ") == ' events ' || (document.getElementById('is_group') && document.getElementById('is_group').innerHTML == 'Group'))
    	{
    		table="events_table";
    	}
    	else
    	{
    		table="restaurant_table";
    	}
    	$('table#'+table+' tr#menu_serial').each(function()
		{	console.log($(this).find(".guest").value);
		   	count += parseInt($(this).find(".guest").val());
    	});
    	
    	// $('table#drinks_table tr#menu_serial').each(function()
		// {	
		   	// count_drinks += parseInt($(this).find(".quantity").val());
    	// });
    	if (count <= 0)
	    {	
	 		$('#no_availability').hide();
	 		$('#no_guest').show();
	 		// $("body").scrollTop($("#no_guest").offset().top);
	 		$("html, body").animate({
            	scrollTop: $("#no_guest").offset().top
        	}, 600);
	 		return false;
	    }
	    else
	    {	
	    	if($('#wchpage').text().replace(/\s+/g, " ") == ' events ' || (document.getElementById('is_group') && document.getElementById('is_group').innerHTML == 'Group'))
	    	{	
	    		if($('#wchpage').text().replace(/\s+/g, " ") == ' events ' && document.getElementById('e_date').options[document.getElementById('e_date').selectedIndex].text == 'Select Date')
	    		{
	    			alert("Please select an Event date");
	    			document.getElementById('e_date').focus();		
	    			return false;
	    		}
	    		else if(document.getElementById('is_group').innerHTML == 'Group' && $('#e_date').val()== '')
	    		{
	    			alert("Please select an Event date");
	    			document.getElementById('e_date').focus();		
	    			return false;
	    		}
	    		else if(document.getElementById('e_time').options[document.getElementById('e_time').selectedIndex].text == 'Select Time')
	    		{
	    			alert("Please select an Event Time");
	    			document.getElementById('e_time').focus();
	    			return false;
	    		}
	    		else
	    		{
	    			var r=confirm("Do you want to continue ?");
			        if (r == false)
					{
					 	return false;
					}
					else
					{
						time_selected(document.getElementById('e_time').options[document.getElementById('e_time').selectedIndex].text);	
					}
	    		}
	    	}
	    	else
	    	{
	    		
	    		$('.continue_button').hide();
    			$("#select_time_div").show();	
	    	}
	    	
    	}
	    // else
	    // {	
	    	// if(count_drinks <= 0)
		    // {
		    	// $('#no_availability').hide();
		 		// var confirm_drinks = confirm('Do you want to proceed without selecting the drinks ?');
	      		// console.log(confirm_drinks);
	      		// if(confirm_drinks == false)
	      		// {
	      			// $("body").scrollTop($("#drinks").offset().top);
	      			// $('#menus').removeClass("button_common");
		      		// $('#drinks').addClass("button_common");
		      		// $('#button_menus_content').hide();
		 			// $('#button_drinks_content').show();
		 			// $("#drink_gtotal_div").show();
		 			// $("#menu_gtotal_div").hide();
	      			// // return false;
	  			// }
		    // }
		    // else
	  			// {
	  				// $('.continue_button').hide();
    				// $("#select_time_div").show();
	  			// }
    	// }
    });
    
// On click of Empty Cart Button 
    $('.empty_cart').on('click',function()
    {
    	var r=confirm("This will clear all items in your cart. Do you want to continue ?");
        if (r== false)
		{
		 	return false;
		}
    });
    

// On click of close icon in "Select Time" Block
    $('.select_time_div_close').on('click',function()
    {
    	$('.continue_button').show();
    	$("#select_time_div").hide();
    });
    
    $('#calendar').fullCalendar({
    weekMode: 'liquid',
    url:'#',
    firstDay:1,
    eventClick :function(calEvent, jsEvent, view)
                {	
					var selectedContainer = findContainerForDate(calEvent.start);

    				$(".fc-state-highlight").removeClass("fc-state-highlight");
    				$(selectedContainer).addClass("fc-state-highlight");
                	$("#main_result_div").show();
                	$('#inner_res_button_block').show();
                	$('#menus').addClass('button_common');
                	$('#drinks').removeClass('button_common');
                	$('#button_menus_content').show();
                	$('#button_drinks_content').hide();
                	if(calEvent.start.getDate()<10) 
  					{
						date = '0' + calEvent.start.getDate();
					} 
					else
					{
						date = calEvent.start.getDate();
					}
					var month_nms = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
					month = month_nms[calEvent.start.getMonth()];
  					var date_selected = date+ '-'+month+'-'+calEvent.start.getFullYear();
	 			    var type = $('#type').val();
     				var partner_id = $("#partner_id").val();
 					var menu = [];
					$('table#restaurant_table tr:gt(0)').each(function()
					{	
						$(this).find('td').each(function()
					            {	
					               var x = $(this).find("#db_id").text();
					               if (x != undefined)
					               	{
					               		menu.push(parseInt(x));
					               	}
					            });
					});
                	openerp.jsonRpc("/website_capitalcentric/onclick_date/", 'call', {'price_type':calEvent.price_type, 'type':type, 'partner_id':parseInt(partner_id), 'date':calEvent.start, 'min_time':calEvent.min_time, 'max_time':calEvent.max_time,'menu_ids':menu})
      				.then(function (data)
      				{	
      					$('#restaurant_table').empty();
      					$('#drinks_table').empty();
      					$('#header_desc').text("Menu(s) and Drinks(s) Available for "+date_selected+" ("+calEvent.title+")");
      					$("#upper_right_div").show();
  						$("#grand_total_table").show();
      					$('.grand_total_value').text('0.00');
      					$('.drinks_grand_total_value').text('0.00');
      					$('.main_gtotal_value').text('0.00');
      					$('#d_table_div').replaceWith(data[2]);
      					document.getElementById('display_avlblty').innerHTML = data[5];
      					document.getElementById('avlblty_popup').innerHTML = "Availablity for "+date_selected+" ("+calEvent.title+")";
      					var kids_menu_td = '';
      					
      					
						// if(data[0].length != 0)
						// {      		
								
	      					for (i = 0; i < data[0].length;i++)
	      					{
	      						var count=0;
	      						var guest_opt = '';
	      						
                            	for(j = data[0][i]['min_covers'] ; j <= data[3]; j++ )
                            	{ 
                              		guest_opt += '<option>'+ j +'</option>';
                            	}	
	      						var otherPrice ='<span class="" style="margin-left:1%;font-weight:bold;font-size:11px;color:#c00000;">Also available for : </span>';
	      						if (data[0][i]['non_price'] > 0)
	      						{
	      							otherPrice += '<span class="" style="color:#c00000;font-weight:bold;font-size:11px">Non-Premium Price : '+ data[0][i]['symbol'] + (data[0][i]['non_price']).toFixed(2) +'</span>';
	      							count = 1;
	      						}
	      						if (data[0][i]['std_price'] > 0)
	      						{
	      							if (count== 1)
	      								otherPrice +='<span class="" style="margin-left:1%;margin-right:1%;color:black;font-weight:bold;font-size:10px">,</span>'; 
	      							otherPrice += '<span class="" style="color:#26466D;font-weight:bold;font-size:11px">Standard Price : '+ data[0][i]['symbol'] + (data[0][i]['std_price']).toFixed(2) +'</span>';
									count = 1;
								}      							
	      						if (data[0][i]['p_price'] > 0)
	      						{
		      						if (count== 1)
		      							otherPrice +='<span class="" style="margin-left:1%;margin-right:1%;color:black;font-weight:bold;font-size:10px">,</span>';
	      							otherPrice += '<span class="" style="color:#004c00;font-weight:bold;font-size:11px">Premium Price : '+ data[0][i]['symbol'] + (data[0][i]['p_price']).toFixed(2) +'</span>';
	      						};	
	      						
								if(otherPrice == '<span class="" style="margin-left:1%;font-weight:bold;font-size:11px;color:#c00000;">Also available for : </span>')
								{
									otherPrice = '';
								    // $("tr.menu_serial").css('border-bottom','1px solid #CCC');
								} 
								if(data[0][i]['kids_menu'] == true)
								{
									kids_menu_td = '<td style="width:5%;"><img id="" class="" src="/website_capitalcentric/static/src/img/kidsmenu.png" alt="Kids Menu Icon" style="height:20px;" title="Kids Menu"/></td>';
								}
								
								tr_style = '';
								if (data[0][i]['to_mu'] > 0)
									tr_style = 'border-left:5px solid ' + data[4] + ';';


	      					    var new_grid_row  = '<tr id="menu_serial" class="menu_serial" style="' + tr_style + '">'+
	                                                '<td id="db_id" class="test" style="display:none;">'+ data[0][i]['m_id'] +'</td>'+
	                                                '<td style="width:50%;" class="descp">'+
	                                                    '<p></p>'+
	                                                    '<div class="menu_name">'+ data[0][i]['m_name'] +'</div>'+
	                                                    '<span class="menu_desc" style="display:none;">'+ data[0][i]['m_desc'] +'</span>'+
	                                                    '<p></p>'+
	                                                    '<a class="main_color menu_descp" style="cursor:pointer;" onclick="javascript:menu_popup(this)">Click here to see the menu</a>'+
	                                                '</td>'+
	                                                '<td class="price">'+
	                                                    '<p class="text_span_9"> Per Person </p>'+ 
	                                                    '<p class="spacing"></p>'+
	                                                    '<span style="color:#C00000;font-size:12pt;">'+data[0][i]['symbol']+'<span id="single_price">'+ parseFloat(data[0][i]['pp_person']).toFixed(2)+'</span></span>'+
	                                                '</td>'+
	                                                '<td class="select_guest">'+
	                                                    '<p class="text_span_9"> Guests </p>'+
	                                                    '<p class="guestspacing"></p>'+
	                                                    '<select id="menu" name="guest" title="Min. covers for this menu: '+data[0][i]['min_covers']+'" class="input-control guest" onchange="javascript:change_guest(this)" style="color:black;"><option value="0"></option>'+
	                     								guest_opt
	                                                    +'</select>'+
	                                                '</td>'+
	                                                '<td class="total_price">'+
	                                                    '<p class="text_span_9"> Total </p>'+
	                                                    '<p class="spacing"></p>'+
	                                                    '<span style="color:#C00000;font-size:12pt;">'+data[0][i]['symbol']+'<span id="total_price">0.00</span></span>'+
	                                                '</td>'+
	                                                ''+kids_menu_td+''+
	                                                '</tr>';
	                            $(new_grid_row).appendTo($("#restaurant_table"));  
	                            
	                            var new_grid_row_price = "<tr style='" + tr_style + "'><td colspan='5'>"+otherPrice+"</td></tr>"
	                                                     +"<tr style='border-bottom:1px solid #CCC'><td colspan='5'></td></tr>";
	                            $(new_grid_row_price).appendTo($("#restaurant_table"));
	      					}
	      					
	      					$("#select_time").empty();      					
	      					// $("#select_time").show();
	      					var booking_text = '<span id="booking_text" style="font-weight:bold;font-size:9pt;color:#c00000;font-style:italic">  Click on the time slot to check availability and complete booking for '+ date_selected +' </span><p style="margin:3px;"></p>';
	  					 	$(booking_text).appendTo($("#select_time")); 
	      					for (i = 0; i < data[1].length;i++)
	      					{      					 	       
	      						var new_grid_row = '<button class="button proceedbutton" onclick="javascript:time_selected(this)">'+ data[1][i] +'</button>';
	      						$(new_grid_row).appendTo($("#select_time"));         
	      					} 

	      					if(document.getElementById('restaurant_table').clientHeight > 400)
	      					{
	      						$("#g_total_menu").css('width','96.5%');
	      						if(kids_menu_td != '')
		      					{
		      						$("#g_total_menu").css('width','92.5%');
		      					}
	      					}
	      					else
	      					{
	      						if(kids_menu_td != '')
		      					{
		      						$("#g_total_menu").css('width','95%');
		      					}
	      					}
	      					if(document.getElementById('drinks_table').clientHeight > 400)
	      					{
	      						$("#g_total_drink").css('width','96.5%');
	      					}
      				});
            	},
     events: []
        });
         
    var webmain_color = $("#wbsite_color").val();
	if (webmain_color == '')
	{
		webmain_color = '#793487';
	}

    $('#special').addClass('button_common');
    $('#button_restaurant_content').hide();
    $('#button_map_content').hide();
	$('#type').popover('show');
	$('#mealtype_id').find('.popover-title').attr('id','bookingline');
	$('#mealtype_id').find('.popover').addClass('border_main');
	$('#mealtype_id').find(".arrow").attr("style", "border-right-color:"+ webmain_color+";");
	$("#calendar").addClass('col-md-12');
	//$('#mealtype_id').find('.popover').css('top','573px');
	$( "#type" ).focus(function()
	{
		$('#type').popover('destroy');
	});
// Popover Hover
    $('.popover-markup > .trigger').popover({
    	html : true,
    	trigger : "hover",
	    title: function() {
	      return $(this).parent().find('.head').html();
	    },
	    content: function() {
	      return $(this).parent().find('.content').html();
	    },
	    container: 'body',
	    placement: 'left'
	});

    $(".restaurant_page").click(function() 
    { 	        
	      var wch_button = $(this).attr('id');
	      $(this).addClass('button_common');
	      if(wch_button == 'special')
	      {
	      		$('#restaurant').removeClass("button_common");
	      		$('#cancel').removeClass("button_common");
		 		$('#button_restaurant_content').hide();
		 		$('#button_cancel_content').hide();
		 		$('#button_special_content').show();
	      }
	      if(wch_button == 'restaurant')
	      {
	      		$('#special').removeClass("button_common");
	      		$('#cancel').removeClass("button_common");
	      		$('#button_special_content').hide();
	      		$('#button_cancel_content').hide();
		 		$('#button_restaurant_content').show();
	      }
	      if(wch_button == 'cancel')
	      {
	      		$('#special').removeClass("button_common");
	      		$('#restaurant').removeClass("button_common");
	      		$('#button_special_content').hide();
	      		$('#button_restaurant_content').hide();
		 		$('#button_cancel_content').show();
	      }
    });
    
    // Toggle Menus Plus
    $('.toggle-plus').click(function()
	{
		var x = $(this).attr('class');
		if(x.indexOf("fa-minus") > -1)
		{
			$(this).attr('class','main_color toggle-plus fa fa-plus');
			$(this).closest('tr').next().addClass('hidden');
		}
		else
		{
			$(this).attr('class','main_color toggle-plus fa fa-minus');
			$(this).closest('tr').next().removeClass('hidden');
		}
	}); 
	
	// Toggle Total Plus
    $('.tot_plus').click(function()
	{
		var x = $(this).attr('class');
		if(x.indexOf("fa-minus") > -1)
		{
			$("#plus_tot_div").removeClass('hidden');
			$("#minus_tot_div").addClass("hidden");
		}
		else
		{
			$("#plus_tot_div").addClass('hidden');
			$("#minus_tot_div").removeClass("hidden");
		}
	});
	
     
	//Image Slider 	  
	var triggers = $('ul.triggers li');
	var images = $('ul.images li');
	var lastElem = triggers.length-1;
	var target;

	triggers.first().addClass('selected');
	images.hide().first().show();

	function sliderResponse(target)
	{
	    images.fadeOut(300).eq(target).fadeIn(300);
	    triggers.removeClass('selected').eq(target).addClass('selected');
	} 

	triggers.click(function() 
	{
	    if ( !$(this).hasClass('selected') ) 
	    {
	        target = $(this).index();
	        sliderResponse(target);
	        resetTiming();
	    }
	});
	$('.next').click(function() 
	{
	    target = $('ul.triggers li.selected').index();
	    target === lastElem ? target = 0 : target = target+1;
	    sliderResponse(target);
	    resetTiming();
	});
	$('.prev').click(function() 
	{
	    target = $('ul.triggers li.selected').index();
	    lastElem = triggers.length-1;
	    target === 0 ? target = lastElem : target = target-1;
	    sliderResponse(target);
	    resetTiming();
	});
	function sliderTiming() 
	{
	    target = $('ul.triggers li.selected').index();
	    target === lastElem ? target = 0 : target = target+1;
	    sliderResponse(target);
	}
	var timingRun = setInterval(function() { sliderTiming(); },5000);
	function resetTiming() 
	{
	    clearInterval(timingRun);
	    timingRun = setInterval(function() { sliderTiming(); },5000);
	}
});

function findContainerForDate(date) {
    var firstDayFound = false;
    var lastDayFound = false;
    var calDate = $('#calendar').fullCalendar('getDate');

    var allDates = $('td[class*="fc-day"]')
    for (var index = 0; index < allDates.length; index++) {
        var container = allDates[index];
        var month = calDate.getMonth();
        var dayNumber = $(container).find(".fc-day-number").html();
        if (dayNumber == 1 && ! firstDayFound) {
            firstDayFound = true;
        }
        else if (dayNumber == 1) {
            lastDayFound = true;
        }

        if (! firstDayFound) {
            month--;
        }
        if (lastDayFound) {
            month++;
        }

        if (month == date.getMonth() && dayNumber == date.getDate()) {
            return container;
        }
    }
}


var website = openerp.website;

function onchange_time(e)  
 {  
	 var id = e.id;
	 var date = $('.datepicker').val();
	 $("#selected_date").val(date);
 	 var type = $('#type').val();
     var time = $('#time').val();
     var partner_id = $("#partner_id").val();
     
     
     if(type != '')
     {
     	
 		openerp.jsonRpc("/website_capitalcentric/on_change_type/", 'call', {'partner_id':parseInt(partner_id),'type':type,'date':new Date()})
	     .then(function (data)
	     {	
	     	$('#calendar').fullCalendar('removeEvents');
            $('#main_result_div').hide(); 
            $('#calendar').fullCalendar('addEventSource', data);
            $('#calendar').fullCalendar('refetchEvents');
            // for(i = 0;i<data.length;i++)
	     	// {
	     		// if(data[i].is_blackout == true)
	     		// {
	     			// $('#calendar').fullCalendar('removeEvents'); 
	     		// }
	     	// }
        	$('#grand_total_table').hide();
        	$('#no_guest').hide();
    		$('#no_availability').hide();
            // window.scrollTo(0, document.body.scrollHeight);
            $("html, body").animate({
            	scrollTop: $("#main_calendar_div").offset().top
        	}, 600);
            
	     });
     }
	 if (id == 'time')
	 {	
		 openerp.jsonRpc("/website_capitalcentric/blackout_validation/", 'call', {'partner_id':parseInt(partner_id), 'time':parseInt(time),'date':date,'type':type,'chkwhich':'time'})
	     .then(function (data) 
		  {
		    if (data == false)
		    {	
		       var dict = {};
	     	   var data = {};
	     	   var arguments = [];
	     	   arguments[0]="Warning";
	     	   arguments[1] = 'There is no availability for this day';
		       data['arguments'] = arguments;
	     	   dict['data'] = data;
	     	   website.error(dict,'');
	     	}
	  	  }); 
	 }
	 
	 else if ((id == 'type') || (id == 'date'))
	 {	 	
	 	if (date && type)
	 	{
	 	   $('#time').empty();
	 	   openerp.jsonRpc("/website_capitalcentric/blackout_validation/", 'call', {'partner_id':parseInt(partner_id), 'time':parseInt(time),'date':date, 'type': type,'chkwhich':'all'})
	 	   .then(function (data) 
		  {
		  	for(var i=0; i<data[0].length; i++)
		    {	
	       		 $('#time').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
		    }
		  });
	 	}
	 }
 }
function close_dialog()
{
	$("#sign_in_modal").hide();
	fader.style.display = "none";
}

function wch_btn(btn)
{
	console.log(btn);
	console.log(btn.id);
	if(btn.id == 'forget_password')
 	{
 		$('.password_res').removeAttr('required');
		$('#from_wch_button').val('forget_password');
 		var get_email = $('#email_res').val();
 		if(get_email == '')
 		{	
 			return;
 		}
 		else
 		{
     		var confirm_value = confirm('Do you want to reset your password?');
      		console.log(confirm_value);
      		if(confirm_value==true)
      		{
      			console.log("submitted");	
  				if($("input[name='login_type']").val() == 'client')
      				$('#operator_form').submit();
      		}
      		else
      		{	
      			$('.password_res').attr('required', true);
      			console.log("not submitted");
      			$('#from_wch_button').val('');
      			return false;
      		}
      	}
 	}
}
