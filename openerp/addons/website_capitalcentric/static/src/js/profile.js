if($.browser.mozilla) 
{
	HTMLElement.prototype.click = function() {
	   var evt = this.ownerDocument.createEvent('MouseEvents');
	   evt.initMouseEvent('click', true, true, this.ownerDocument.defaultView, 1, 0, 0, 0, 0, false, false, false, false, 0, null);
	   this.dispatchEvent(evt); 
	};
}

// On Change of service charge included field
function sc_included_change(sc)
{
	if(sc.value == 'True')
	{
		$('input[name="menu_sc"]').prop('disabled',true);
		$('input[name="menu_sc"]').val('0.00');
	}
	else
	{	
		$('input[name="menu_sc"]').val($('#for_populating_sc').val());
		$('input[name="menu_sc"]').prop('disabled',false);
	}	
}

$(document).ready(function () 
{
	  $("#invoice_address").hide();
	  $("form[name='invoice_filter_form']").hide();
	  $(".inv_save").hide();
	  $("#modal-body").hide();
	  
// Invoice address Block text
	  jQuery('#invoice_address_block').on('click', function(event) 
	  {        
	         jQuery('#invoice_address').slideToggle('show');
	  });
// Invoice Filter Form
	  jQuery('#add_filters_button').on('click', function(event) 
	  {        
	         jQuery('#invoice_filter_form').slideToggle('show');
	  });
	    
	  if($('.inv_save').val() == 'yes')
	  {
	  	$("#invoice_address").show();
	  }
	    
	  var type = document.getElementById('type').innerHTML;
	  
	  $('div[id="invoicebutton"]').addClass('color');
	  
	  if(type == 'operator')
	  {
	    $("#second_bookingline").hide();
	  }
	  
	  $('#save_button').on('click',function()
	  {
	  	if ($("#check_element").length > 0)
	  	{
	  		if(($("input[name='menu_sc']").val() == '' || $("input[name='menu_sc']").val() <= 0.00) && $("select[name='sc_included']").val() == '')
	  		{
	  			alert("Please Enter service charge");
	  			$("input[name='menu_sc']").focus();
	  			return false;
	  		}
	  		$('#save_button').prop('type','submit');
	  	}
	  	else
	  	{
	  		$('#save_button').prop('type','submit');
	  	}
	  });
	 
	  
	  $("select[name='Country']").change(function () 
	  {
		   	$('#con_state').empty();
		   	$('#con_state').append('<option value="">Select a county ..</option>');
		   	// $('#con_city').empty().append('<option value="">Select City ..</option>');
		   	// $('#con_location').empty().append('<option value="">Select Location ..</option>');
		    var country = this.value;
			
			openerp.jsonRpc("/website_capitalcentric/state_json/", 'call', {'country': parseInt(country)})
            .then(function (data) 
            {
            	if(data[0].length > 0)	
            	{    
            		$("#con_state").attr('disabled',false);
            		$("#con_state").attr('title','Select a county ..');
				    for(var i=0; i<data[0].length; i++)
				    {	
			        	$('#con_state').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
				    }
			    }
			    else
			    {	
			    	$("#con_state").attr('disabled',true);
			    	$("#con_state").attr('title','Please Select United Kingdom as country to choose a county');
			    }
            });
 	  });
 	  
 	  $(".invoice_link").on('click',function()
      {
        var id = $(this).closest("tr");
        var invoice_id = id.find("#invoice_id").text();                                 
        openerp.jsonRpc("/website_capitalcentric/invoice_json/", 'call', {'invoice_id' : parseInt(invoice_id)})    	
        .then(function (data)
         {  
            $('.invoice_replaced_div').replaceWith(data); 
            var divToPrint = document.getElementById('modal-body');
            var popupWin = window.open("", "_blank","width=700,height=800,toolbar=no,menubar=no,scrollbars=yes,status=yes,resizable=yes");
            popupWin.document.writeln(divToPrint.innerHTML);
            popupWin.document.close();
            popupWin.focus();
         });
      });    
      
      
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
 	 
 	 $("#btnExport").click(function(e) {
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
        //getting data from our div that contains the HTML table
        var data_type = 'data:application/vnd.ms-excel';
        var no_of_rows = $('#invoice_table tr').length;
        if(no_of_rows > 1)
        {
	        var table_div = $('#invoice_table').clone();
			 //remove the unwanted columns
	 		table_div.find('td#invoice_id').remove();
	 		table_div.find('td#print_td').remove();
	        var table_html = table_div['0'].outerHTML.replace(/ /g, '%20');
	        // window.open('data:application/vnd.ms-excel,' + table_html);
	        a.href = data_type + ', ' + table_html;
	        
	        //setting the file name
	        a.download = 'exported_table.xls';
	        //triggering the function
			a.click();
	        //just in case, prevent default behaviour
	        e.preventDefault();
	     }
	     else
	     {
	     	alert("No data in the Invoice table to export");
	     }
    });
    
    var invoice_filter = ($('#inv_type').val() != '') || ($('#start_date').val() != '') || ($('#end_date').val() != '') || ($('#inv_status').val() != '');
    if(invoice_filter)
 	{
 		$("#invoice_filter_form").show();	
 	}	
 	else
 	{
 		$("#invoice_filter_form").hide();	
 	}   
 	
 	// Image Edit in Invoice Address
 	
 	$("img[class='img-rounded']").on("click", function()
    {
	 	 $("input[name='image_name']").trigger('click'); 
    });
    
    
   
   $("input[name='image_name']").on("change", function()
   {
    	// Get a reference to the fileList
	    var files = !!this.files ? this.files : [];
	    // If no files were selected, or no FileReader support, return
	    if ( !files.length || !window.FileReader ) return;
	
	    // Only proceed if the selected file is an image
	    if ( /^image/.test( files[0].type ) )
	    {
	        // Create a new instance of the FileReader
	        var reader = new FileReader();
	
	        // Read the local file as a DataURL
	        reader.readAsDataURL( files[0] );
			 
	        // When loaded, set image data as background of page
			reader.onloadend = function(e)
			{
				 $('#form_style_css').submit();
				 // $('#form_style_css').trigger('submit');
			     $("#to_image").attr('src',e.target.result);
			};
        }
        else
        {
        	alert("Please Choose an Image");	
        }
	});
});

// Reset Form Button for Bookings Filter Table
function resetForm()
{           
    $('select[name="inv_type"]').val('');
    $('input[name="start_date"]').val('');
    $('input[name="end_date"]').val('');
    $('select[name="inv_status"]').val('');
}
