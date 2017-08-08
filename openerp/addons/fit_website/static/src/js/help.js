$(document).ready(function ()
{
  	$('div[id="helpbutton"]').addClass('color');
  	$('#second_bookingline').hide();
	var accept_tc = $(".accept_tc").val();
	if(accept_tc == '')
	{
		$('div[id="search_button"]').hide();
		$('div[id="partnerbutton"]').hide();
		$('div[id="fitbutton"]').hide();
		$('div[id="paymentsbutton"]').hide();
		$('div[id="contactbutton"]').hide();
		$('div[id="restaurantbutton"]').hide();
		$('div[id="invoicebutton"]').hide();
		$('div[id="invbutton"]').hide();
		$('div[id="markupbutton"]').hide();
		$('div[id="eventsbutton"]').hide();
		$('div[id="groupsbutton"]').hide();
	}
	else
	{
		$('div[id="search_button"]').show();
		$('div[id="partnerbutton"]').show();
		$('div[id="fitbutton"]').show();
		$('div[id="paymentsbutton"]').show();
		$('div[id="contactbutton"]').show();
		$('div[id="restaurantbutton"]').show();
		$('div[id="invoicebutton"]').show();
		$('div[id="invbutton"]').show();
		$('div[id="markupbutton"]').show();
		$('div[id="eventsbutton"]').show();
		$('div[id="groupsbutton"]').show();
	}
	
	$("#terms_ul").hide();
	$("#invoice_details_ul").hide();
	$("#contacts_ul").hide(); 
	$("#markup_ul").hide(); 
	$("#search_book_ul").hide(); 
	$("#bookings_payments_ul").hide(); 
	$("#events_ul").hide(); 
	
	
	$('#terms').toggle(function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_down.png');
        $("#terms_ul").show();
    }, function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_right.png');
        $("#terms_ul").hide();
    });
    
    
    $('#invoice_details').toggle(
    function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_down.png');
        $("#invoice_details_ul").show();
    }, function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_right.png');
        $("#invoice_details_ul").hide();
    });
    
    
    $('#contacts').toggle(
    function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_down.png');
        $("#contacts_ul").show();
    }, function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_right.png');
        $("#contacts_ul").hide();
    });
    
    $('#markup').toggle(
    function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_down.png');
        $("#markup_ul").show();
    }, function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_right.png');
        $("#markup_ul").hide();
    });
    
    $('#search_book').toggle(
    function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_down.png');
        $("#search_book_ul").show();
    }, function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_right.png');
        $("#search_book_ul").hide();
    });
    
    
    $('#bookings_payments').toggle(
    function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_down.png');
        $("#bookings_payments_ul").show();
    }, function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_right.png');
        $("#bookings_payments_ul").hide();
    });
    
    $('#events').toggle(
    function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_down.png');
        $("#events_ul").show();
    }, function() 
    {
        $(this).attr('src', '/fit_website/static/src/img/arrow_right.png');
        $("#events_ul").hide();
    });
  	
}); 