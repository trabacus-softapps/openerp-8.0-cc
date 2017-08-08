$(document).ready(function () 
{     
	  $('div[id="tcbutton"]').addClass('color');
	  var accept_tc = $(".accept_tc").val();
	  // $('.hidden').hide();
	  $('#second_bookingline').hide();
	  // $('.alert').hide();
	  var wch_path = document.getElementById('path').value;
	
	  if(accept_tc == '')
	  {
		  $('div[id="search_button"]').hide();
		  $('div[id="partnerbutton"]').hide();
		  $('div[id="paymentsbutton"]').hide();
		  $('div[id="bookingsbutton"]').hide();
		  $('div[id="fitbutton"]').hide();
		  $('div[id="eventsbutton"]').hide();
		  $('div[id="restaurantbutton"]').hide();
		  $('div[id="contactbutton"]').hide();
          $('div[id="invoicebutton"]').hide();
          $('div[id="markupbutton"]').hide(); 
          $('div[id="groupsbutton"]').hide();
	      $('.button_tc').hide();
	      $("input[name='accept_tc']").on("click", function()
		  {
		  	  var value_accept_checkbox = $("#accept_tc").is(':checked');
		  	  console.log(value_accept_checkbox);
		  	  if(value_accept_checkbox == true)
		  	  {
		  	  	$('.button_tc').show();
	  	  	  } 
	  	  	  else
	  	  	  {
	  	  	  	$('.button_tc').hide();
	  	  	  }
		  });
		  
		  $(".button_tc").on("click", function()
		  {
		  	// cancellation_hrs = $(".input_hrs").val();
		  	
		  	var partner_id = $(".partner_id").val();
		  	console.log(partner_id);
		  	
		  	openerp.jsonRpc("/fit_website/tc_json/", 'call', {'partner_id':parseInt(partner_id)})
		   .then(function (data) 
		    {
			   	 $("input[name='accept_tc']").prop('disabled', true);
			   	 $('.button_tc').hide();
		   	 	 if( document.getElementById('path').value == 'restaurant')
	  	  		 {
					  $('div[id="fitbutton"]').show();
					  $('div[id="restaurantbutton"]').show();
		      	 }
		         if( document.getElementById('path').value == 'operator')
		  	     {
					  $('div[id="search_button"]').show();
					  $('div[id="eventsbutton"]').show();
					  $('div[id="fitbutton"]').show();
					  $('div[id="partnerbutton"]').show();
					  $('div[id="paymentsbutton"]').show();
					  $('div[id="markupbutton"]').show();
					  $('div[id="groupsbutton"]').show();
		          }
			      $('div[id="contactbutton"]').show();
			      $('div[id="invoicebutton"]').show();
				  document.getElementById('accept_tc').title="Accepted the Terms & Conditions";
				  // document.getElementById('save_prompt').innerHTML="Submitted Successfully!!";
			      // $("#save_prompt").stop(true,true).show().fadeOut(5000);
			      // $('.alert').show();
			      $("html, body").animate({
            		scrollTop: 0
        	  	}, 600);
	         	document.getElementById('prompt_msg').innerHTML="Submitted Successfully !!";
				$("#prompt_msg").stop(true,true).show().fadeOut(5000);
		     });
		 });
	  }
	  
	  if(accept_tc == 'True')
	  {
	  	  $('.button_tc').hide();
		  $("input[name='accept_tc']").prop('disabled', true);
		  document.getElementById("accept_tc").checked = true;	
		  
		  $(".button_tc").on("click", function()
		  {
		  	cancellation_hrs = $(".input_hrs").val();
		  	var partner_id = $(".partner_id").val();
		  	console.log(partner_id);
		  	
		  	openerp.jsonRpc("/fit_website/tc_json/", 'call', {'cancellation_hrs':cancellation_hrs,'partner_id':parseInt(partner_id)})
		    .then(function (data) 
		    {
			   	 $("input[name='accept_tc']").prop('disabled', true);
	   	  	 	 if( document.getElementById('path').value == 'restaurant')
	  	  		 {
					  $('button[id="restaurantbutton"]').show();
		      	 }
		         if( document.getElementById('path').value == 'operator')
		  	     {
					  $('div[id="search_button"]').show();
					  $('div[id="events_button"]').show();
					  $('div[id="partnerbutton"]').show();
				 	  $('div[id="paymentsbutton"]').show();
					  $('div[id="markupbutton"]').show();
					  $('div[id="groupsbutton"]').show();
		         }
		         $('div[id="fitbutton"]').show();
		         $('div[id="contactbutton"]').show();
		         $('div[id="invoicebutton"]').show();
				 $("html, body").animate({
            		scrollTop: 0
        	  	 }, 600);
	         	 document.getElementById('prompt_msg').innerHTML="Submitted Successfully !!";
				 $("#prompt_msg").stop(true,true).show().fadeOut(5000);
			     // $('.alert').show();
		    });
		 });
	   }
	  
});