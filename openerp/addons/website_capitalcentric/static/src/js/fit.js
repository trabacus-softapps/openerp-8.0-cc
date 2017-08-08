if($.browser.mozilla) 
{
   HTMLElement.prototype.click = function() {
	   var evt = this.ownerDocument.createEvent('MouseEvents');
	   evt.initMouseEvent('click', true, true, this.ownerDocument.defaultView, 1, 0, 0, 0, 0, false, false, false, false, 0, null);
	   this.dispatchEvent(evt);
   };
};

$(document).ready(function () 
{
	
	 // var SelectedDates = {};
	    // SelectedDates[new Date('10/11/2014')] = new Date('10/11/2014');
	    // SelectedDates[new Date('10/09/2014')] = new Date('10/09/2014');
	    // SelectedDates[new Date('10/10/2014')] = new Date('10/10/2014');
// 	 
	    // $('#end_date').datepicker({
	        // beforeShowDay: function(date) {
	        	// console.log('highlight',SelectedDates);
	        	// console.log('date',date);
	            // var Highlight = SelectedDates[date];
	            // if (Highlight) {
	                // return [true, "Highlighted", toString(date)];
	            // }
	            // else {
	                // return [true, '', ''];
	            // }
	        // }
	    // });
	var fader;
	$("#btnExport").click(function(e) 
	{
        //getting values of current time for generating the file name
        var dt = new Date();
        var day = dt.getDate();
        var month = dt.getMonth() + 1;
        var year = dt.getFullYear();
        var hour = dt.getHours();
        var mins = dt.getMinutes();
        var postfix = day + "." + month + "." + year + "_" + hour + "." + mins;
        //creating a temporary HTML link element (they support setting file names)
        var a = document.createElement('a');
        var data_type = 'data:application/vnd.ms-excel';
        var no_of_rows = $('#lead_table tr').length;
        if(no_of_rows > 1)
        {
	        //getting data from our div that contains the HTML table
	        var table_div = $('#lead_table').clone();
			//remove the unwanted columns
	 		table_div.find('td#lead_id').remove();
	 		table_div.find('td#amend_td').remove();
	 		table_div.find('td#cancel_icon_td').remove();
	 		table_div.find('td#print_voucher').remove(); 
	 		   
	        var table_html = table_div['0'].outerHTML.replace(/ /g, '%20');
	        // window.open('data:application/vnd.ms-excel,' + table_html);
	        a.href = data_type + ', ' + table_html;
	        //setting the file name
	        a.download = 'exported_table.xls';
	        //triggering the function
	        a.click();
	        console.log(a);
	        //just in case, prevent default behaviour
	        e.preventDefault();
	     }
	     else
	     {
	     	alert("No data to export");
	     }
    });
   
    // $("#log_out").click(function()
    // {	
    	// console.log("Logg out Entered");
    	// window.location.href="/capital_centric/restaurant_login?log_out=logout";
    	// // history.back();
    	// // window.history.forward();
    // });

	//Dynamic Table Creation in JS 
    // var table = $('<table id="create_table"></table>').addClass('table table-condensed table-bordered');
    // for (i = 0; i < 10; i++) 
    // {
        // row = $('<tr></tr>');
        // for (j = 0; j <= i; j++) 
        // {
            // var row1 = $('<td></td>').addClass('text-center').text('result ' + j);
            // table.append(row);
            // row.append(row1);
        // }
    // }
    // $('#bookinglayout').append(table);
    
	$('div#menus_btn').addClass("button_common");
 	$('div[id="fitbutton"]').addClass('color');
 	$('#second_bookingline').hide();
 	$("#div3").hide();
 	$("#div3").draggable();
 	$("#path_for_js").hide();
 	$(".alert-danger").hide();
 	
 	if($("#path_for_js").val() == 'operator')
 	{
 		var op_venue_filter = ($('#enq_no').val() != '') || ($('#start_date').val() != '') || ($('#end_date').val() != '') || ($('#res_name').val() != '') || ($('#guest_name').val() != '') || ($('#guest_email').val() != '') || ($('#bking_status').val() != '');
 		console.log("op_venue_filter",op_venue_filter);
 	} 
 	else
 	{
 		var op_venue_filter = ($('#enq_no').val() != '') || ($('#start_date').val() != '') || ($('#end_date').val() != '') ||($('#guest_name').val() != '') || ($('#guest_email').val() != '') || ($('#bking_status').val() != '') || ($('#inv_status').val() != '');
 	}
 	if(op_venue_filter)
 	{
 		$("#filter_form").show();	
 	}	
 	else
 	{
 		$("#filter_form").hide();	
 	}
 	
 	$("#filter_search").click(function()
 	{
 		if($('#start_date').val() != '')
 		{
 			$('#end_date').attr('required', true);
 		}	
 		if($('#end_date').val() != '')
 		{
 			$('#start_date').attr('required', true);
 		}	
 	});
 	
 	
 	
// Add Filters Button Toggle
 	jQuery('#add_filters_button').on('click', function(event) 
    {        
         jQuery('#filter_form').slideToggle('show');
    }); 
 	
 	
// Amend link in bookings Table
 	$('.cancel_booking_request').on('click',function()
 	{
  		console.log($(this).attr('id'));
  		if($(this).attr('id') == 'amend')
  		{
  			amend_and_cancel($(this).attr('id'),$(this));	
  		}
  		else
  		{
  			var confirm_value = confirm('Do you want to Cancel?');
      		if(confirm_value == true)
      		{	
      			amend_and_cancel($(this).attr('id'),$(this));
      		}
      		else
      		{
      			return false;
      		}
  		}
 	});
 	

// Cancel Button in Dialog Box  	
 	$('#cancel_button_menu_covers').on('click',function()
	{
		fader = document.getElementById('login_fader');
		$("#div3").hide();
		fader.style.display = "none";
		window.location.href= "/capital_centric/operator/bookings";
	});
	

// Continue Button in Dialog Box
	$(".continue_button").on('click',function()
	{		
		continue_button();
	});

});

// Reset Form Button for Bookings Filter Table
function resetForm()
{           
    $('input[name="enq_no."]').val('');
    $('input[name="start_date"]').val('');
    $('input[name="end_date"]').val('');
    $('input[name="res_name"]').val('');
    $('input[name="guest_name"]').val('');
    $('input[name="guest_email"]').val('');
    $('select[name="bking_status"]').val('');
    $('select[name="inv_status"]').val('');
    $('select[name="bookd_by"]').val('');
}

function covers_onfocus()
{
	if($("#alert_text").text() != '') 
    {
        $(".continue_button").show();
        $(".alert-danger").hide();
    }
}

//Common Button for fetching Covers info
function amend_and_cancel(chk_wch,p)
{
	var id = p.closest("tr");
	var lead_id = id.find("#lead_id").text();
	if (id.find("#lead_stage").text().trim() == 'Cancelled')
		{
			fader = document.getElementById('login_fader');
    		var login_box = document.getElementById('div3');
    		fader.style.display = "block";
    		$("#div3").show();
    		$(".modal-title").text("Warning");
    		$(".modal-body").empty().text("Booking is already cancelled");
    		$(".continue_button").hide();
    		return false;
		}
	openerp.jsonRpc("/website_capitalcentric/menu_and_covers_for_bookings/", 'call', {'lead_id' : parseInt(lead_id)})    	
	.then(function (data)
	{	
		fader = document.getElementById('login_fader');
	    var login_box = document.getElementById('div3');
	    fader.style.display = "block";
		
        $('.replaced_div').replaceWith(data);
        $("#div3").show();
	    $('#cust_info_tab').hide();
	    if(chk_wch == 'amend')
	    {
	    	
		    if($('#error_msg').val() == "not_allowed")
		    {
		    	$(".continue_button").hide();
		    	$(".modal-title").text("Amend Booking");
		    	$(".alert-danger").text("Amendments are possible only before 36 hours of the booking date/time");
		    	$(".alert-danger").show();
		    	$("#info_tr").css('display','none');
		    	$("#send_confirmation_fit").prop("disabled",true);
		    	$("input.guest_input,select").prop("disabled",true);
		    	$(".guest_input").prop("disabled",true);
		    	$(".covers_class").prop("disabled",true);
		    }
		    else
		    {
		    	$(".continue_button").show();
		    	$(".modal-title").text("Amend Booking");
		    }
		}
		else
		{
			if($('#error_msg').val() == "not_allowed")
			{
				$(".modal-title").text("Warning");
				$('.modal-body').empty().text("Amendments are possible only before 36 hours of the booking date/time");
				$(".continue_button").hide();
			}
			else
			{
				$("#div3").hide();
				fader.style.display = "none";
				continue_button("cancel_icon");
			}
		}
	});
}

//Continue Button Common function
function continue_button(chk_wch)
{
	console.log(chk_wch);
	var menu_list = [];
	var info_dict = {};
	$('#dvLoading').show();
	$('table#menu_covers_table tr').each(function()
	{
		var dict={}; 
		$(this).find("td:eq(0)").each(function()
        {           
	        dict['menu_id'] = $(this).find("#menu_id").val();
	 	});
	 	$(this).find("td:eq(2)").each(function()
	 	{
	 		 dict['covers'] = $(this).find("#covers").val();
	 		 if(chk_wch == 'cancel_icon')
	 		 {
	 		 	dict['covers'] = '0';
	 		 }
	 	});
	 	console.log(dict);
	 	menu_list.push(dict);
	});
	
	if($("#cust_ref").val() != $("#prev_cust_ref").val())	
		info_dict['cust_ref'] = $("#cust_ref").val();
		
	if($("#title").val() != $("#prev_title").val())
		info_dict['title'] = $("#title").val();
		
	if($("#partner_name").val() != $("#prev_partner_name").val())
		info_dict['partner_name'] = $("#partner_name").val();
			
	if($(".contact_name").val() != $("#prev_contact_name").val())
		info_dict['contact_name'] = $(".contact_name").val();
		
	if($("#mobile").val() != $("#prev_mobile").val())
		info_dict['mobile'] = $("#mobile").val();
		
	if($("#email_from").val() != $("#prev_email_from").val())
		info_dict['email_from'] = $("#email_from").val();
		
	if($("#spcl_req").val() != $("#prev_spcl_req").val())
		info_dict['spcl_req'] = $("#spcl_req").val();
		
	openerp.jsonRpc("/website_capitalcentric/menu_covers_save/", 'call', {'menu_list' : menu_list,'send_confirmation' : $("#send_confirmation_fit").is(':checked'),'info_dict' : info_dict})
    .then(function (data) 
    {
	    if(data == 'false' || data == 'exception' || data == 'unavailability')
	    {
	    	if(chk_wch == 'cancel_icon')
	    	{
	    		fader = document.getElementById('login_fader');
	    		var login_box = document.getElementById('div3');
	    		fader.style.display = "block";
	    		$("#div3").show();
	    		$(".modal-title").text("Warning");
	    		$(".modal-body").empty().text("Booking is already cancelled");
	    		$(".continue_button").hide();
	    	}
	    	else
	    	{
	    		$(".continue_button").hide();
	    		$(".modal-title").text("Amend Booking");
		    	if(data == 'false')
		    	{
		    		$(".alert-danger").text("You cannot increase the no. of covers");
	    		}
	    		else if(data == 'unavailability')
	    		{
	    			$(".alert-danger").empty();
	    			$(".alert-danger").text("There is no availability for the number of covers entered.");
	    		}
	    		else
	    		{
	    			$(".alert-danger").empty();
	    			$(".alert-danger").css('width','500px');
	    			$(".alert-danger").text("Please revise the number of covers or change the customer information to amend the booking.");
	    			
	    		}
		    	$(".alert-danger").show();
		    	$('#dvLoading').hide();	
	    	}
	    	return false;
	    }
	    else if(chk_wch == 'cancel_icon')
	    	 {
	    		fader = document.getElementById('login_fader');
	    		var login_box = document.getElementById('div3');
	    		fader.style.display = "block";
	    		$("#div3").show();
	    		$(".modal-title").text("Warning");
	    		$(".modal-body").empty().text("Booking is cancelled");
	    		$(".continue_button").hide();
	    	 }
    	location.reload();
    });
}

function save_customerinfo(e)
{	dict = {};
	i = 0;
	if (e.id == 'edit_btn')
	{
		$(".guest_input").prop("disabled",false);
		$("#save_btn").css('display','block');
		$("#edit_btn").css('display','none');
	}	
	if (e.id == 'save_btn')
	{	
		var info_id = $("#info_id").text();
		dict['custref'] 	 = $("#cust_ref").val();
		dict['title']  		 = $("#title").val();
		dict['partner_name'] = $("#partner_name").val();
		dict['contact_name'] = $(".contact_name").val();
		dict['mobile']       = $("#mobile").val();
		dict['email_from']   = $("#email_from").val();
		dict['spcl_req']     = $("#spcl_req").val();
     	i++;		
     	console.log(dict);
     	openerp.jsonRpc("/website_capitalcentric/save_input_my_cart/", 'call', {'value' : dict, 'db_id' : parseInt(info_id)});
     	$(".guest_input").prop("disabled",true);
     	$("#save_btn").css('display','none');
		$("#edit_btn").css('display','block');
	}
     	
}

function click_tab(e)
{ 	  
  if(e.id == 'menus_btn') 
  {
  	$('#menus_tab').show();
	$('#cust_info_tab').hide();
	$('#menus_btn').addClass("button_common");
	$('#custinfo_btn').removeClass("button_common");
  }
  if(e.id == 'custinfo_btn') 
  {
  	$('#menus_tab').hide();
	$('#cust_info_tab').show();
	$('#custinfo_btn').addClass("button_common");
	$('#menus_btn').removeClass("button_common");
  }
}
