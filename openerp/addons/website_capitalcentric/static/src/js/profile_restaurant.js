var website = openerp.website;
 
//  Function for Request Change in Price Pop Up
function request_change_in_price()
{
	fader = document.getElementById('login_fader');
    login_box = document.getElementById('div4');
    fader.style.display = "block";
    login_box.style.display = "block";
    $("#div4").show(); 
}

function get_geolocation()
{
	  var con_sel = document.getElementById('con_country');
	  var country = con_sel.options[con_sel.selectedIndex].text;
	  if (country == 'Select Country..')
	  	  country = '';
	  var stat_sel = document.getElementById('con_state');
	  var state = stat_sel.options[stat_sel.selectedIndex].text;
	  if (state == 'Select County..')
	  	  state = '';
	  var city  = $('#con_city').val();
	  var zip   = $('#con_zip').val();
	  var add   = $('#street').val();
	  var add1  = $('#street2').val();
	  
  address   = add + add1 + ',' + zip + ' ' + city + ', '+ state + ' '+ country;
  $.post("https://maps.googleapis.com/maps/api/geocode/json?address=" + address,{},
  function(results, status)
  {
  	if (results.status == 'OK')
  		{
		  	var location = results['results'][0].geometry.location; 
		  	$("#latitude").val(location['lat']);
		  	$("#longitude").val(location['lng']);
		}
  });
}   

// On Change of service charge included, service charge and Price in drinks tab
function change_drink(d)
{
	var id = $(d).closest("tr");
	if(d.id == 'sc_included_drink')
	{	
		if(id.find('.sc_included_drink').val() == 'True')
		{
			id.find('.sc_per_drink').prop('disabled',true);
			id.find('.sc_per_drink').val('0.00');
		}
		else
		{
			if(id.find('#db_id').val() == 'undefined')
			{	
				id.find('.sc_per_drink').val('0.00');
			}
			else
			{
				id.find('.sc_per_drink').val(id.find('#for_populating').val());
			}
			id.find('.sc_per_drink').prop('disabled',false);
		}
	}
	if(id.find('.sc_per_drink').val().length !=0 || id.find('.drink_price').val().length !=0)
	{
		id.find(".total_price").val((parseFloat(id.find('.drink_price').val()) * (id.find('.sc_per_drink').val()/100) + parseFloat(id.find('.drink_price').val())).toFixed(2));
	}
	if(id.find('.drink_price').val().length == 0)
	{
		id.find(".total_price").val('0.00');
	}
}


// On Change of service charge included field
function sc_included_change(sc)
{
	var tp = [];
	if(sc.name == 'sc_included')
	{
		if(sc.value == 'True')
		{
			$('input[name="menu_sc"]').prop('disabled',true);
			$('input[name="menu_sc"]').val('0.00');
		}
		else
		{	
			if($('#for_populating_sc').length > 0)
			{
				$('input[name="menu_sc"]').val($('#for_populating_sc').val());
			}
			else
			{
				$('input[name="menu_sc"]').val('0.00');
			}
			$('input[name="menu_sc"]').prop('disabled',false);
		}	
	}
	var wch_sc = $("input[name='menu_sc']").val();
	
	if(($("input[name='menu_sc']").val() == 0.00 ) && (sc.value == ''))
	{
		wch_sc =  $("#user_menu_sc").val();
		console.log(wch_sc);
	}
	if(sc.name == 'menu_sc' || sc.name == 'rest_price' || sc.name == 'sc_included')
	{	
		console.log("Entered");
		$('table#menu_table tr').each(function()
        {   
          $(this).find('td:eq(6)').each(function()
            {	
               calculate_tp = ((parseFloat($(this).find("input.rest_price").val()) * (wch_sc/100) + parseFloat($(this).find("input.rest_price").val())).toFixed(2));
               console.log(calculate_tp);
               if(isNaN(calculate_tp))
               {
               	  calculate_tp = '';
               }
               tp.push(calculate_tp);
            });
        });
	        
        for (y=1; y<=9; y++)
        {
       	    var i=0;
       		$("table#menu_table tr").each(function()
	   		{
		       	 var $td = $(this).find('td').eq(y);        	
		         $td.each(function()
	        	 {   
	        		$(this).find("input.total_price").val(tp[i]);
	        		i++;
	        	 });
	     	});
        }
	}
		
}



$(function()
{ 
    $("#restdiv1").hide();
    $("#restdiv1").draggable();           
});

function private_rooms_change(p)
{
	console.log(p.value);
	if(p.value == 'no')
    {
    	$('.private_room_tab').addClass('hidden');
    }
    else
    {
    	$('.private_room_tab').removeClass('hidden');
    }
}
        
$(document).ready(function () 
{
	// Initializing the multiselect fields
	$("#dining_style").multiselect(); 
	$("#cuisine").multiselect(); 
	$(".event_menu").multiselect({
		noneSelectedText: "Select Menus",
        selectedText : "# Menu(s) Selected"
	}); 
	// <!--$("#dining_style").multiselect({
	    // noneSelectedText: "Select Dining Styles",
	    // selectedText : "# Dining Style(s) Selected",
	// });
	// $("#cuisine").multiselect({
	    // noneSelectedText: "Select Cuisines",
	    // selectedText : "# Cuisine(s) Selected",
	// });-->
	$("#con_contact").multiselect(); 
	$("#inv_contact").multiselect(); 
	$('.ui-multiselect').css('width','100%');
	$('.ui-multiselect').css('border-radius','5px');
	$('.ui-multiselect').css('cursor','default');
	$(".ui-state-default").css('background-image','none');
	$(".ui-state-default").css('background-color','white');
	$('.ui-multiselect-menu').outerWidth($('.ui-multiselect').outerWidth());
	$('.ui-multiselect-checkboxes label input').css('margin-right','3%');                          
	$('div.ui-helper-clearfix a.ui-multiselect-close span').replaceWith(function()
	{
	    return $("<span>Close</span>").append($(this).contents());
	});
	$(".ui-multiselect-header li.ui-multiselect-close").css('padding-right','1%');
                            
    
    // Private Rooms tab for groups
    if($('select[name="private_rooms"]').val() == 'no')
    {
    	$('.private_room_tab').addClass('hidden');
    }
    else
    {
    	$('.private_room_tab').removeClass('hidden');
    }
    
    $("textarea.res_textarea").each(function() 
    {
	    var h =	(this.scrollHeight);
	    var x = $(this).height(h);
	});
	
	$("textarea.menu_desc").each(function() 
    {
	    var h =	(this.scrollHeight);
	    var x = $(this).height(h);
	});
	
    $(window).on('load',function()
	{	
		$(".datepicker").datepicker({dateFormat: 'dd-M-yy', showAnim: "fadeIn"});
		$("#dvLoading").hide();
		var d_from = []; var d_to = [];
		var d_from_e = []; var d_to_e = [];
		var month_nms = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
		$('table#blackout_table tr').each(function()
	        {   
	          $(this).find('td:eq(1)').each(function()
	            {	
	               var x = ($(this).find("input.black_from_date").val());
	               if (x != undefined)
	               {
	               	  var y = new Date(x);
	            	  if(y.getDate()<10) 
	  				  {
							date = '0' + y.getDate();
					  } 
					  else
					  {
							date = y.getDate();
					  }
					  
					  month = month_nms[y.getMonth()];
					  year = y.getFullYear();
					  date = date+'-'+month+'-'+year;
	            	  d_from.push(date);
            	   }
	            });
	            
	            $(this).find('td:eq(2)').each(function()
	            {	
	               var x = ($(this).find("input.black_to_date").val());
	               if (x != undefined)
	               {
	               	  var y = new Date(x);
	            	  if(y.getDate()<10) 
	  				  {
							date = '0' + y.getDate();
					  } 
					  else
					  {
							date = y.getDate();
					  }
					  month = month_nms[y.getMonth()];
					  year = y.getFullYear();
					  date = date+'-'+month+'-'+year;
	            	  d_to.push(date);
            	   }
	            });
	        });
	        for (y=1; y<=6; y++)
	        {
	       	    var i=0;
	       		$("table#blackout_table tr").each(function()
		   		{
			       	 var $td = $(this).find('td').eq(y);        	
			         $td.each(function()
		        	 {   
		        		$(this).find("input.black_from_date").val(d_from[i]);
		        		$(this).find("input.black_to_date").val(d_to[i]);
		        		i++;
		        	 });
		     	});
	        }
	        
	        $('table#events_table tr').each(function()
	        {   
	          $(this).find('td:eq(3)').each(function()
	            {	
	               var x = ($(this).find("input.black_from_date").val());
	               if (x != undefined)
	               { 
	               	  var y = new Date(x);
	            	  if(y.getDate()<10) 
	  				  {
							date = '0' + y.getDate();
					  } 
					  else
					  {
							date = y.getDate();
					  }
					  
					  month = month_nms[y.getMonth()];
					  year = y.getFullYear();
					  date = date+'-'+month+'-'+year;
	            	  d_from_e.push(date);
            	   }
	            });
	            
	            $(this).find('td:eq(4)').each(function()
	            {	
	               var x = ($(this).find("input.black_to_date").val());
	               if (x != undefined)
	               {
	               	  var y = new Date(x);
	            	  if(y.getDate()<10) 
	  				  {
							date = '0' + y.getDate();
					  } 
					  else
					  {
							date = y.getDate();
					  }
					  month = month_nms[y.getMonth()];
					  year = y.getFullYear();
					  date = date+'-'+month+'-'+year;
	            	  d_to_e.push(date);
            	   }
	            });
	        });
	        for (z=1; z<=10; z++)
	        {
	       	    var i=0;
	       		$("table#events_table tr").each(function()
		   		{
			       	 var $td = $(this).find('td').eq(z);        	
			         $td.each(function()
		        	 {   
		        		$(this).find("input.black_from_date").val(d_from_e[i]);
		        		$(this).find("input.black_to_date").val(d_to_e[i]);
		        		i++;
		        	 });
		     	});
	        }
	        $("#save_prompt").show().fadeOut(5000);
	});
	
	
	// Event for Request on Change Price Pop Up close 
	$('#cancel_button').on('click',function()
	{
	    $("#div4").hide();
	    fader.style.display = "none";
	});
	
	$('#div4').hide();
	$("#div4").draggable();
	
	
	// If Restaurant is 'active' then select & input tags are disabled in Menu Pricing Page 
	var venue_active_or_not = $("#venue_active_or_not").val();
	console.log(venue_active_or_not);
	if(venue_active_or_not == 'True')
	{
		$("#sc_included").prop('disabled', true);
		$("#sc_per").prop('disabled', true);
		$("#sc_disc").prop('disabled', true);
		$("#sc_included").css('background-color',"#ebebe4");
		$("#sc_disc").css('background-color',"#ebebe4");
		$('.input_menu').prop('disabled',true);
	}
	
	if($.browser.webkit) 
   	{
        $('#img_desc_save').css( "padding-top","2px" );
   	};

	$('.con_save_back').click(function()
    {
    	// var name = $('#required_name').val();
    	// if(name.length != 0)
    	// {  
    		// $("#save").remove();
    	// }
    	$('input[name="save"]').val('save_back');
    	if ($("#check_element").length > 0)
	  	{
	  		if(($("input[name='menu_sc']").val() == '' || $("input[name='menu_sc']").val() <= 0.00) && $("select[name='sc_included']").val() == '')
	  		{
	  			alert("Please Enter service charge");
	  			$("input[name='menu_sc']").focus();
	  			return false;
	  		}
	  		$('.con_save_back').prop('type','submit');
	  	}
	  	else
	  	{
	  		$('.con_save_back').prop('type','submit');
	  	}
    });
    
    $(".add_resdetls").on('click', function() 
    {
		alert("Please enter RESTAURANT DETAILS and SAVE to continue");
    });
    
    $('.con_save').click(function()
    {
    	// var name = $('#required_name').val();
    	// if(name.length != 0)
    	// {  
    		// $("#save_back").remove();
    	// }
    	$('input[name="save"]').val('save');
    	if ($("#check_element").length > 0)
	  	{
	  		if(($("input[name='menu_sc']").val() == '' || $("input[name='menu_sc']").val() <= 0.00) && $("select[name='sc_included']").val() == '')
	  		{
	  			alert("Please Enter service charge");
	  			$("input[name='menu_sc']").focus();
	  			return false;
	  		}
	  		$('.con_save').prop('type','submit');
	  	}
	  	else
	  	{
	  		$('.con_save').prop('type','submit');
	  	}
    });
    
    // Events Tab
    $('#events_menu_tab').addClass("time_button_common");
    $('#e_info').hide();   

	// To show menu tab as active while page loading..
    var chk_from_which = $("#chk_from_which").text();
	console.log("chk_from_which",chk_from_which);
	
	if(chk_from_which == 'res_details')
	{
		$('#other_button').addClass("button_common");
		$('#timings_info_outside').hide();
		$('#tables_info').hide();
		$('#menu_info').hide();
		$('#image_info').hide();
		$('#blackout_info').hide();
		$('#drinks_info').hide();
		$('#events_info').hide();
		$('#private_room_info').hide();
	} 
	if(chk_from_which == 'menu_go_back')
	{
		$('#menu_button').addClass("button_common");
		$('#timings_info_outside').hide();
		$('#tables_info').hide();
		$('#other_info').hide();
		$('#image_info').hide();
		$('#blackout_info').hide();
		$('#drinks_info').hide();
		$('#events_info').hide();
		$('#private_room_info').hide();
	} 
	if(chk_from_which == 'events')
	{
		$('#events_button').addClass("button_common");
		$('#timings_info_outside').hide();
		$('#tables_info').hide();
		$('#other_info').hide();
		$('#image_info').hide();
		$('#blackout_info').hide();
		$('#drinks_info').hide();
		$('#menu_info').hide();
	} 
	
    $("#breakfast").prop("checked");
	$('div[id="restaurantbutton"]').addClass('color');
    $("input.imenu_price").attr('disabled','disabled');
    
	
	if($('#active_status').length > 0) 
	{
    	status_value = document.getElementById("active_status").innerHTML;
		if(status_value == 'True')
		{
			$('.checkbox_active').attr('checked','checked');
		} 
	}
	
	$("select[name='Country']").change(function () 
	{ 
		   	$('#con_state').empty();
		   	$('#con_state').append('<option value="">Select County ..</option>');
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

	
// Venue Id : 
	var venue_id;
	venue_id = $("#venue_id").val();
	console.log("venue Id:",venue_id);
	
//  Restaurant Buttons 
	$(".res_button").click(function()
    { 	  
      var id = $(this).attr('id');
      $(this).addClass('button_common');
      if(id == 'other_button') 
      {
      		$('#tables_button').removeClass("button_common");
      		$('#menu_button').removeClass("button_common");
      		$('#drinks_button').removeClass("button_common");
      		$('#events_button').removeClass("button_common");
      		$('#image_button').removeClass("button_common");
      		$('#blackout_button').removeClass("button_common");
      		$('#private_room_button').removeClass("button_common");
      		$('#tables_info').hide();
      		$('#menu_info').hide();
      		$('#drinks_info').hide();
      		$('#events_info').hide();
      		$('#image_info').hide();
      		$('#blackout_info').hide();
      		$('#private_room_info').hide();
      		$('#other_info').show();
      }
      if(id == 'tables_button') 
      {
      		$('#other_button').removeClass("button_common");
      		$('#menu_button').removeClass("button_common");
      		$('#drinks_button').removeClass("button_common");
      		$('#events_button').removeClass("button_common");
      		$('#image_button').removeClass("button_common");
      		$('#blackout_button').removeClass("button_common");
      		$('#private_room_button').removeClass("button_common");
      		$('#other_info').hide();
      		$('#menu_info').hide();
      		$('#drinks_info').hide();
      		$('#events_info').hide();
      		$('#image_info').hide();
      		$('#blackout_info').hide();
      		$('#private_room_info').hide();
      		$('#tables_info').show();
      }   
      if(id == 'menu_button') 
      {
      		$('#other_button').removeClass("button_common");
      		$('#tables_button').removeClass("button_common");
      		$('#drinks_button').removeClass("button_common");
      		$('#events_button').removeClass("button_common");
      		$('#image_button').removeClass("button_common");
      		$('#blackout_button').removeClass("button_common");
      		$('#private_room_button').removeClass("button_common");
      		$('#other_info').hide();
      		$('#tables_info').hide();
      		$('#drinks_info').hide();
      		$('#events_info').hide();
      		$('#image_info').hide();
      		$('#blackout_info').hide();
      		$('#private_room_info').hide();
      		$('#menu_info').show();
      }      
      if(id == 'drinks_button') 
      {
      		$('#other_button').removeClass("button_common");
      		$('#tables_button').removeClass("button_common");
      		$('#menu_button').removeClass("button_common");
      		$('#events_button').removeClass("button_common");
      		$('#image_button').removeClass("button_common");
      		$('#blackout_button').removeClass("button_common");
      		$('#private_room_button').removeClass("button_common");
      		$('#other_info').hide();
      		$('#tables_info').hide();
      		$('#menu_info').hide();
      		$('#events_info').hide();
      		$('#image_info').hide();
      		$('#blackout_info').hide();
      		$('#private_room_info').hide();
      		$('#drinks_info').show();
      }
      if(id == 'events_button') 
      {
      		$('#other_button').removeClass("button_common");
      		$('#tables_button').removeClass("button_common");
      		$('#menu_button').removeClass("button_common");
      		$('#drinks_button').removeClass("button_common");
      		$('#image_button').removeClass("button_common");
      		$('#blackout_button').removeClass("button_common");
      		$('#private_room_button').removeClass("button_common");
      		$('#other_info').hide();
      		$('#tables_info').hide();
      		$('#menu_info').hide();
      		$('#drinks_info').hide();
      		$('#image_info').hide();
      		$('#blackout_info').hide();
      		$('#events_info').show();
      		$('#private_room_info').hide();
      }
      if(id == 'image_button') 
      {
      		$('#other_button').removeClass("button_common");
      		$('#tables_button').removeClass("button_common");
      		$('#menu_button').removeClass("button_common");
      		$('#drinks_button').removeClass("button_common");
      		$('#events_button').removeClass("button_common");
      		$('#blackout_button').removeClass("button_common");
      		$('#private_room_button').removeClass("button_common");
      		$('#other_info').hide();
      		$('#tables_info').hide();
      		$('#menu_info').hide();
      		$('#drinks_info').hide();
      		$('#events_info').hide();
      		$('#blackout_info').hide();
      		$('#image_info').show();
      		$('#private_room_info').hide();
      }      
      if(id == 'blackout_button') 
      {
      		$('#other_button').removeClass("button_common");
      		$('#tables_button').removeClass("button_common");
      		$('#menu_button').removeClass("button_common");
      		$('#drinks_button').removeClass("button_common");
      		$('#events_button').removeClass("button_common");
      		$('#image_button').removeClass("button_common");
      		$('#private_room_button').removeClass("button_common");
      		$('#other_info').hide();
      		$('#tables_info').hide();
      		$('#menu_info').hide();
      		$('#drinks_info').hide();
      		$('#events_info').hide();
      		$('#image_info').hide();
      		$('#blackout_info').show();
      		$('#private_room_info').hide();
      }
      if(id == 'private_room_button') 
      {
      		$('#other_button').removeClass("button_common");
      		$('#tables_button').removeClass("button_common");
      		$('#menu_button').removeClass("button_common");
      		$('#drinks_button').removeClass("button_common");
      		$('#events_button').removeClass("button_common");
      		$('#image_button').removeClass("button_common");
      		$('#blackout_button').removeClass("button_common");
      		$('#tables_info').hide();
      		$('#other_info').hide();
      		$('#menu_info').hide();
      		$('#drinks_info').hide();
      		$('#events_info').hide();
      		$('#image_info').hide();
      		$('#blackout_info').hide();
      		$('#private_room_info').show();
      }
      else
      {
      	
      }
    });  
 
    
	$('.checkbox').on("click", function() 
	{
    	if ($(this).prop("checked")) 
    	{
    		openerp.jsonRpc("/website_capitalcentric/address_json/", 'call')
			.then(function(data)
			{  	
			   for(var i = 0;i<data.length;i++)
			   {	
			   		if(i == 0)
			   		{ 
			   			$("#street").val(data[i]);
			   		}
			   		if(i == 1)
			   		{ 
			   			$("#street2").val(data[i]);
			   		}
			   		if(i == 2)
				   		{ 
				   			$("#con_country").find('option[value="'+data[i]+'"]').prop("selected","selected");
				   		}
			   		if(i == 3)
			   		{ 
			   			countryname = data[i-1];
			   			var state = data[i];
			   			$('#con_state').empty().append('<option value="">Select County ..</option>');
			   			openerp.jsonRpc("/website_capitalcentric/state_json/", 'call', {'country': countryname})
	                    .then(function (data) 
	                    {
		            		
					    	for(var i=0; i<data[0].length; i++)
					    	{
					         	$('#con_state').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
					         	$("#con_state").find('option[value="'+state+'"]').prop("selected","selected");
			   				}
					 	});
	   				}
			   		if(i == 4)
			   		{ 
			   			$("#con_city").val(data[i]);
			   		}
			   		if(i == 6)
			   		{ 
			   			$("#con_zip").val(data[i]);
			   		}
		   	    } 	
				
			});
		}
		else
		{
			$('#street').val('');
			$('#street2').val('');
			$('#con_zip').val('');
			$("#con_country option:first").prop("selected","selected");
			$("#con_state").empty().append('<option value="">Select County ..</option>');
			$("#con_city").val('');
			$("#con_location").empty().append('<option value="">Select Location ..</option>');
		}
	});  
	
	$('.checkbox_edit').on("click", function()
	{
		var address = '';
    	if ($(this).prop("checked")) 
    	{
			openerp.jsonRpc("/website_capitalcentric/address_json/", 'call')
			.then(function(data)
			{
			   for(var i = 0;i<data.length;i++)
			   {
			   		if(i == 0)
			   		{ 
			   			$("#street").val(data[i]);
			   			address = data[i];
			   		}
			   		if(i == 1)
			   		{ 
			   			$("#street2").val(data[i]);
			   			address += data[i];
			   		}
			   		if(i == 2)
			   		{ 
			   			$("#con_country").find('option[value="'+data[i]+'"]').prop("selected","selected");
			   			address += data[i];
			   		}
			   		if(i == 3)
			   		{ 
			   			countryname = data[i-1];
			   			var state = data[i];
			   			
			   			$('#con_state').empty().append('<option value="">Select County..</option>');
			   			openerp.jsonRpc("/website_capitalcentric/state_json/", 'call', {'country': countryname})
	                    .then(function (data) 
	                    {
		            		
					    	for(var i=0; i<data[0].length; i++)
					    	{
					         	$('#con_state').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
					         	$("#con_state").find('option[value="'+state+'"]').prop("selected","selected");
					         	if (state == data[1][i])
					         		address += data[0][i];
		   					}
					 	});
		   			}
		   			if(i == 4)
			   		{ 
			   			$("#con_city").val(data[i]);
			   			address += data[i];
			   		}
			   		if(i == 6)
			   		{ 
			   			$("#con_zip").val(data[i]);
			   			address += data[i];
		   			}
		   	   } 	
			
			get_geolocation();	
			});
		}
		else
		{
		   var partner_id = parseInt(document.getElementById("partnerid").innerHTML);
		   console.log(partner_id);
		   openerp.jsonRpc("/website_capitalcentric/existing_address_json/", 'call',{'partner_id':partner_id})
			.then(function(data)
			{
			   for(var i = 0;i<data.length;i++)
			   {
			   		console.log("existing",data[i]);
			   		if(i == 0)
			   		{ 
			   			$("#street").val(data[i]);
			   			address = data[i];
			   		}
			   		if(i == 1)
			   		{ 
			   			$("#street2").val(data[i]);
			   			address += data[i];
			   		}
			   		if(i == 2)
			   		{ 
			   			console.log(data[i]);
			   			$("#con_country").find('option[value="'+data[i]+'"]').prop("selected","selected");
			   			address += data[i];
			   		}
			   		if(i == 3)
			   		{ 
			   			countryname = data[i-1];
			   			var state = data[i];
			   			$('#con_state').empty().append('<option value="">Select County..</option>');
			   			openerp.jsonRpc("/website_capitalcentric/state_json/", 'call', {'country': countryname})
	                    .then(function (data) 
	                    {
		            		
					    	for(var i=0; i<data[0].length; i++)
					    	{
					         	$('#con_state').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
					         	$("#con_state").find('option[value="'+state+'"]').prop("selected","selected");
					         	if (state == data[1][i])
					         		address += data[0][i];
			   				}
					 	});
		   			}
			   		if(i == 4)
			   		{ 
			   			$("#con_city").val(data[i]);
			   			address += data[i];
			   		}
			   		if(i == 6)
			   		{ 
			   			$("#con_zip").val(data[i]);
			   			address += data[i];
			   		}
		   	   }
		   	   
			get_geolocation();
			});
		}
 	});
 	
 	// Time & Allocations Tab
 	$('#bf_tab').addClass("time_button_common");
    $('#lunch_info').hide();
	$('#at_info').hide();
	$('#dinner_info').hide();
	
 	$(".time_button").click(function()
    { 	          
      var id = $(this).attr('id');
      $(this).addClass('time_button_common');
      if( id == 'bf_tab')
      {
      		$('#lunch_tab').removeClass("time_button_common");
      		$('#at_tab').removeClass("time_button_common");
      		$('#dinner_tab').removeClass("time_button_common");
      		$('#lunch_info').hide();
      		$('#at_info').hide();
      		$('#dinner_info').hide();
      		$('#bf_info').show();
      }
      if( id == 'lunch_tab')
      {
      		$('#bf_tab').removeClass("time_button_common");
      		$('#at_tab').removeClass("time_button_common");
      		$('#dinner_tab').removeClass("time_button_common");
      		$('#bf_info').hide();
      		$('#at_info').hide();
      		$('#dinner_info').hide();
      		$('#lunch_info').show();
      }
      if( id == 'at_tab')
      {
      		$('#bf_tab').removeClass("time_button_common");
      		$('#lunch_tab').removeClass("time_button_common");
      		$('#dinner_tab').removeClass("time_button_common");
      		$('#bf_info').hide();
      		$('#lunch_info').hide();
      		$('#dinner_info').hide();
      		$('#at_info').show();
      }
      if( id == 'dinner_tab')
      {
      		$('#bf_tab').removeClass("time_button_common");
      		$('#lunch_tab').removeClass("time_button_common");
      		$('#at_tab').removeClass("time_button_common");
      		$('#bf_info').hide();
      		$('#lunch_info').hide();
      		$('#at_info').hide();
      		$('#dinner_info').show();
      }
    });
    
    
   
 	
	
 	$(".events_button").click(function()
    {   
      var id = $(this).attr('id');
      $(this).addClass('time_button_common');
      if( id == 'events_menu_tab')
      {
      		$('#events_tab').removeClass("time_button_common");
      		$('#e_info').hide();
      		$('#e_menu_info').show();
      }
      if( id == 'events_tab')
      {
      		$('#events_menu_tab').removeClass("time_button_common");
      		$('#e_menu_info').hide();
      		$('#e_info').show();
      }
    });
    


////////////////////////                       Adding Of New Records in Time & Allocations Tab                  /////////////////////////   
    
    $("a.add_new_type").on('click',function(event)
    {	
    	var type = $(this).attr('id');
    	if(type == 'opening_hours')
    	{
    		type = 'break_fast';
    		var newRow =  '<tr class=""><td class="hidden"><input id="db_id" value="undefined"/></td><td class="singleblock_center"><select title="Day" class="alloc_day" style="padding:1px;" name="day"><option> Select Day.. </option><option value="monday"> Monday </option><option value="tuesday"> Tuesday </option><option value="wednesday"> Wednesday </option><option value="thursday"> Thursday </option><option value="friday"> Friday </option><option value="saturday"> Saturday </option><option value="sunday"> Sunday </option></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="B/F From" class="alloc_from_time non_frm_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="B/F To" class="alloc_from_time non_to_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Lunch From" class="alloc_from_time std_frm_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Lunch To" class="alloc_from_time std_to_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Dinner From" class="alloc_from_time pre_frm_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Dinner To" class="alloc_from_time pre_to_id" name="time"></select>'+
	    	'<td class="singleblock_center"><a id="apply_to_all_opening" class="bookinginfolink save" name="apply"> <img src="/web/static/src/img/icons/gtk-apply.png" id="img_icons" title="Click here to copy the details entered in this record to all other rows"/> </a></td>'+
	    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click here to delete this record" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';
    	}
    	else
    	{
	    	var newRow =  '<tr class=""><td class="hidden"><input id="db_id" value="undefined"/></td><td class="hidden"><input id="alloc_type" value="'+type+'"/></td><td class="singleblock_center"><select title="Day" class="alloc_day" style="padding:1px;" name="day"><option> Select Day.. </option><option value="monday"> Monday </option><option value="tuesday"> Tuesday </option><option value="wednesday"> Wednesday </option><option value="thursday"> Thursday </option><option value="friday"> Friday </option><option value="saturday"> Saturday </option><option value="sunday"> Sunday </option></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Non-Premium From" class="non_frm_id alloc_from_time" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Non-Premium To" class="alloc_from_time non_to_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Standard From" class="alloc_from_time std_frm_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Standard To" class="alloc_from_time std_to_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Premium From" class="alloc_from_time pre_frm_id" name="time"></select>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="Premium To" class="alloc_from_time pre_to_id" name="time"></select>'+
	    	'<td class="singleblock_center"><input title="Covers Allocated (30 min. slot)" class="alloc_covers" type="text" value="0" id="" name="covers"/></td>'+
			'<td class="singleblock_center"><input title="Max. Covers" class="max_covers" type="text" value="0" id="" name="max_covers"/></td>'+
	    	'<td class="singleblock_center"><a id="apply_to_all" class="bookinginfolink save" name="apply"> <img src="/web/static/src/img/icons/gtk-apply.png" id="img_icons" title="Click here to copy the details entered in this record to all other rows"/> </a></td>'+
	    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click here to delete this record" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';
    	}   
    	$(newRow).appendTo($("#"+type+"_table"));
        $("#"+type+"_table tr td select.alloc_day").focus();
        
        openerp.jsonRpc("/website_capitalcentric/time/", 'call', {})
	    .then(function (data) 
	    {
		    for(var i=0; i<data[0].length; i++)
		    {	
	        	$('table#'+type+'_table tr:last .alloc_from_time').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
		    }
		});
    });
    
  
////////////////////////                      Apply to All in Time & Allocations Tab                     /////////////////////////    
     
    $(".alloc_data").on('click','.save',function(event)
    {	
    	var link_name = $(this).attr('name');
    	var id = $(this).closest("tr");
    	var db_id = id.find("#db_id").val();
    	var type = id.find("#alloc_type").val();
    	if($(this).attr('id') == 'apply_to_all_opening')
    	{
    		type = "break_fast";
    	}
    	var chkwhich = link_name;
    	
    	if(db_id != 'undefined')
    	{
    		db_id = parseInt(db_id);
    	}
    	else
    	{
    		db_id = 'false';
    	}
    	
        week_day 		= id.find(".alloc_day").val();
        non_frm_id 		= id.find(".non_frm_id").val();	
        non_to_id		= id.find(".non_to_id").val();
        std_frm_id		= id.find(".std_frm_id").val();
        std_to_id		= id.find(".std_to_id").val();
        pre_frm_id 		= id.find(".pre_frm_id").val();
        pre_to_id 		= id.find(".pre_to_id").val();
        covers 			= id.find(".alloc_covers").val();
		cap             = id.find(".max_covers").val();

        if($(this).attr('id') == 'apply_to_all_opening')
        {
        	covers = '1';
        }
        
        if($(this).attr('id') == 'apply_to_all_opening')
    	{
    		var alert_type_first  = 'B/F';
    		var alert_type_second = 'Lunch';
    		var alert_type_third  = 'Dinner';
    	}
    	else
    	{	
    		var alert_type_first  = 'Non Premium';
    		var alert_type_second = 'Standard';
    		var alert_type_third  = 'Premium';
    	}
        
         if(week_day == "Select Day..")
		 {
		 	id.find('.alloc_day').focus();
		    alert("Please Select a Day");
		    return;
		 }
		 if(non_frm_id == 1 && non_to_id != 1)
		 {
		 	alert("Please Select From TIME for "+ alert_type_first +"");
		 	id.find('.non_frm_id').focus();
		 	return;
		 }
		 if(non_to_id == 1 && non_frm_id != 1)
		 {
		 	alert("Please Select To TIME for "+ alert_type_first +"");
		 	id.find('.non_to_id').focus();
		 	return;
		 }
		 if(std_frm_id == 1 && std_to_id != 1)
		 {
		 	alert("Please Select From TIME for "+ alert_type_second +"");
		 	id.find('.std_frm_id').focus();
		 	return;
		 }
		 if(std_to_id == 1 && std_frm_id != 1)
		 {
		 	alert("Please Select To TIME for "+ alert_type_second +"");
		 	id.find('.std_to_id').focus();
		 	return;
		 }
		 if(pre_frm_id == 1 && pre_to_id != 1)
		 {
		 	alert("Please Select From TIME for "+ alert_type_third +"");
		 	id.find('.pre_frm_id').focus();
		 	return;
		 }
		 if(pre_to_id == 1 && pre_frm_id != 1)
		 {
		 	alert("Please Select To TIME for "+ alert_type_third +"");
		 	id.find('.pre_to_id').focus();
		 	return;
		 }
		 var numbers = /^[-+]?[0-9]+$/;

		 if (!cap.match(numbers))
		{
			alert("Please enter number of Max. Covers");
      		id.find(".max_covers").focus();
      		id.find(".max_covers").select();
      		return;
		}

         if(covers.match(numbers))
         {
			if(link_name == 'apply')
			{	 
			$("table#"+type+"_table tr").each(function()
			 {
			 	id.find('.alloc_covers');
		 		$(this).find('td').each(function()
		   		 {
		        	$(this).find(".non_frm_id").val(non_frm_id);
		        	$(this).find(".non_to_id").val(non_to_id);
		        	$(this).find(".std_frm_id").val(std_frm_id);
		        	$(this).find(".std_to_id").val(std_to_id);
		        	$(this).find(".pre_frm_id").val(pre_frm_id);
		        	$(this).find(".pre_to_id").val(pre_to_id);
		        	if($(this).attr('id') != 'apply_to_all_opening')
		        	{
		        		$(this).find(".alloc_covers").val(covers);
						$(this).find(".max_covers").val(cap);
		        	}
		    	 });
		 	  });
			} 
	        openerp.jsonRpc("/website_capitalcentric/existing_alloc_record/", 'call', {'value':chkwhich,'type':type,'db_id' : db_id, 'partner_id':parseInt(venue_id),'name' : week_day, 'non_frm_id' : non_frm_id, 'non_to_id' : non_to_id, 'std_frm_id' : std_frm_id, 'std_to_id' : std_to_id, 'pre_frm_id' : pre_frm_id, 'pre_to_id' : pre_to_id, 'covers' : covers, 'cap':cap})
	        .then(function (data) 
	        {	
	        	new_id = id.find('#db_id').val(data);
	        	if(link_name == 'new' && new_id != '')
		    	{
		    		id.find("#save").attr("name","existing");
		    	}
		    	$("html, body").animate({
            		scrollTop: 0
        	  	}, 600);
	         	document.getElementById('save_prompt').innerHTML="Applied Successfully to All !!";
				$("#save_prompt").stop(true,true).show().fadeOut(5000);
	        });
        }
        else
      	{
      		alert("Please enter number of covers allotted"); 
      		id.find(".alloc_covers").focus();
      		id.find(".alloc_covers").select();
      		return;
      	}
    });
   
     
////////////////////////                       Deletion of Records in Time & Allocations Tab                 /////////////////////////
     
     
     $(".alloc_data").on('click','#db_delete',function(event)
     {
    	var id = $(this).closest("tr");
    	var wch_table = $(this).attr("name");
    	if(wch_table == 'opening_hrs_table')
    	{
    		wch_table = 'opening_hrs_table';
    	}
    	else
    	{
    		wch_table = 'allocations_table';
    	}
        var db_id = id.find("#db_id").val();
        if(db_id == 'undefined')
        {
        	var r=confirm("Are you sure you want to delete?");
	        if (r==true)
			{
			  $(this).parent().parent().remove();
			  // document.body.scrollTop = document.documentElement.scrollTop = 0;
			  $("html, body").animate({
            		scrollTop: 0
        	  }, 600);
			  document.getElementById('save_prompt').innerHTML="Deleted !!";
			  $("#save_prompt").stop(true,true).show().fadeOut(5000);
			}
	    }
	    else
	    {
		    var r=confirm("Are you sure you want to permanently delete this record?");
	        if (r==true)
	        {
			    openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value' : wch_table , 'db_id' : parseInt(db_id)})
		        .then(function (data) 
		        {
		         	id.remove();
		         	// document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	$("html, body").animate({
            			scrollTop: 0
        	  		}, 600);
		         	document.getElementById('save_prompt').innerHTML="Deleted !!";
					$("#save_prompt").stop(true,true).show().fadeOut(5000);
		        });
	        }
        }
     });
    
    
    //  Menu Tab..
    
////////////////////////                       Adding Of New Records in Menu Tab                  /////////////////////////
    
    $("a#menu_add,a#menu_add_group").click(function()
    {	
    	venue_id = $('#venue_id').val();
    	if(this.id == 'menu_add_group')
    	{
    		var newRow =  '<tr class=""><td class="hidden"><input id="db_id" value="undefined"/></td><td class="singleblock_center menu_checkbox"><div id ="checkbox_type" title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER"><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> B </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="break_fast" class="type_checkbox" id="break_fast"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> L </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="lunch" class="type_checkbox" id="lunch"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> D </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="dinner" class="type_checkbox" id="dinner"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> Kids Menu </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="kids_menu" class="type_checkbox" id="kids_menu""></input></div></td>'+
	    	'<td class="singleblock_center"><input title="Enter the name of the menu" type="text" name ="menu_name" class="menu_name" style=""></input></td>'+
			'<td class="singleblock_center" style="vertical-align:middle;padding:0.5%;"><textarea title="Enter the details of the menu. Please specify the inclusions in detail" type="text" name ="menu_desc" class="menu_desc" style="resize:none;"></textarea></td>'+
			'<td class="singleblock_center"><select style="width:100%;padding:1px;" title="Select the menu course" name="course" class="menu_course"><option value="c1"> 1 </option><option value="c2"> 2 </option><option value="c3"> 3 </option><option value="c4"> 4 </option><option value="c5"> 5 </option><option value="c6"> 6 </option></select></td>'+
			'<td class="singleblock_center"><input style="width:100%;" value="1" name="min_covers" class="min_covers" title="Enter the minimum number of Covers"/></td>'+
	    	'<td class="singleblock_center"><select style="width:100%;padding:1px;" title="All menus are in ACTIVE state by default. In case you do not choose to display a menu to the tour operator, change the status to INACTIVE and SAVE" name="active" class="menu_status"><option value="True"> Active </option><option value="False"> Inactive </option></select></td>'+
	    	'<td class="singleblock_center"><input style="width:100%;text-align:right;padding-right:5px;padding-left:5px;" name="rest_price" onchange="javascript:sc_included_change(this)" class="alloc_day rest_price" title="Enter the Restuarant Price of the menu" value=""/></td>'+
	    	'<td class="singleblock_center" style="padding:0;"><input disabled="disabled" class="input-control total_price" style="height:22px;width:100%;padding-left:5px;text-align:right;padding-right:5px;" type="text" value="" title=""/></td>'+
	    	'<td class="singleblock_center"><a id="duplicate" class="bookinginfolink" name="dup_grp"> <img title="Click to copy the details of the menu created to a new record" src="/web/static/src/img/icons/gtk-copy.png" id="img_icons" id="img_icons"/> </a></td>'+
	    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete the menu" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td><form></tr>';
    	}
    	else
    	{
	    	var newRow =  '<tr class=""><form action="/capital_centric/profile/restaurant/edit_restaurant/menu" method="post"><td class="hidden"><input id="db_id" value="undefined"/></td><td class="singleblock_center menu_checkbox"><div id ="checkbox_type" title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER"><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> B </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="break_fast" class="type_checkbox" id="break_fast"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> L </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="lunch" class="type_checkbox" id="lunch"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> AT </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="afternoon_tea" class="type_checkbox" id="afternoon_tea"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> D </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="dinner" class="type_checkbox" id="dinner"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> Kids Menu </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="kids_menu" class="type_checkbox" id="kids_menu""></input></div></td>'+
	    	'<td class="singleblock_center"><input title="Enter the name of the menu" type="text" name ="menu_name" class="menu_name" style="width:100%;"></input></td>'+
			'<td class="singleblock_center" style="vertical-align:middle;padding:0.5%;"><textarea title="Enter the details of the menu. Please specify the inclusions in detail" type="text" name ="menu_desc" class="menu_desc" style="resize:none;"></textarea></td>'+
			'<td class="singleblock_center"><select style="width:100%;padding:1px;" title="Select the menu course" name="course" class="menu_course"><option value="c1"> 1 </option><option value="c2"> 2 </option><option value="c3"> 3 </option><option value="c4"> 4 </option><option value="c5"> 5 </option><option value="c6"> 6 </option></select></td>'+
			'<td class="singleblock_center"><input style="width:100%;" value="1" name="min_covers" class="min_covers" title="Enter the minimum number of Covers"/></td>'+
	    	'<td class="singleblock_center"><select style="width:100%;padding:1px;" title="All menus are in ACTIVE state by default. In case you do not choose to display a menu to the tour operator, change the status to INACTIVE and SAVE" name="active" class="menu_status"><option value="True"> Active </option><option value="False"> Inactive </option></select></td>'+
	    	'<td class="singleblock_center"><input name="menu_id" class="hidden" value=""></input><input name="partner_id" class="hidden" value="'+venue_id+'"></input><button class="button menu_table_button" id="menu_table_button" title="Click to add PRICING to the menu added"> Pricing </button></td></form>'+
	    	'<td class="singleblock_center"><a id="duplicate" class="bookinginfolink" name="dup_fit"> <img title="Click to copy the details of the menu created to a new record" src="/web/static/src/img/icons/gtk-copy.png" id="img_icons" id="img_icons"/> </a></td>'+
	    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete the menu" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';
    	}   
    	$(newRow).appendTo($("#menu_table"));
    	$("#menu_table tr td input.menu_name").focus();
    	
    });
    
    	
////////////////////////                      Duplicating Of Records in Menu Tab                     /////////////////////////

    $(".menu_data").on('click','#duplicate',function(event)
    {	    
	    $('#dvLoading').show();	
 		var id = $(this).closest("tr");  
        var dict = {};   
        var count=1;      
        dict['name']	 		 = id.find(".menu_name").val();
        dict['description']		 = id.find(".menu_desc").val();
        dict['active']	 		 = id.find(".menu_status").val();
    	dict['course']	 	 	 = id.find(".menu_course").val();
    	dict['break_fast']	 	 = id.find("#break_fast").is(':checked');
    	dict['lunch']	 	 	 = id.find("#lunch").is(':checked');
    	dict['min_covers']	 = id.find(".min_covers").val();
    	if($(this).attr('name') == 'dup_fit')
    	{
    		dict['afternoon_tea']	 = id.find("#afternoon_tea").is(':checked');
    	}
    	else
    	{
    		dict['afternoon_tea']	= 'False';
    		dict['rest_price']	 	= id.find(".rest_price").val();
    		dict['total_price']	 	= id.find(".total_price").val();
    		dict['sc_included']   	=  $('select[name="sc_included"]').val();
    		dict['service_charge']  =  $('input[name="menu_sc"]').val();
    		if(dict['sc_included'] == '')
    		{
    			dict['sc_included']   =  'False';
    		}
    	}
    	dict['dinner']	 	 	 = id.find("#dinner").is(':checked');
    	dict['kids_menu']	 	 = id.find("#kids_menu").is(':checked');
    	dict['food_type']	 	 = 'meal';
    	
  	    var db_id = id.find("#db_id").val();
  		if (db_id == 'undefined')
  		{
  			db_id = 'create_1';
  			id.find("#db_id").val(db_id);
		    count++;
    	}
    		
		if(dict['break_fast'] == true)
		{
			var bf = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" checked type="checkbox" name="break_fast" class="type_checkbox" id="break_fast"></input>';
		}
		else
		{	
			var bf = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="break_fast" class="type_checkbox" id="break_fast"></input>';	
		}
		if(dict['lunch'] == true)
		{
			var lunch = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" checked type="checkbox" name="lunch" class="type_checkbox" id="lunch"></input>';
		}
		else
		{
			var lunch = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="lunch" class="type_checkbox" id="lunch"></input>';
		}
		if($(this).attr('name') == 'dup_fit')
    	{
			if(dict['afternoon_tea'] == true)
			{
				var at = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" checked type="checkbox" name="afternoon_tea" class="type_checkbox" id="afternoon_tea"></input>';
			}
			else
			{
				var at = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="afternoon_tea" class="type_checkbox" id="afternoon_tea"></input>';	
			}
		}
		if(dict['dinner'] == true)
		{
			var dinner = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="dinner" checked class="type_checkbox" id="dinner"></input>';
		}
		else
		{
			var dinner = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="dinner" class="type_checkbox" id="dinner"></input>';
		}
		if(dict['kids_menu'] == true)
		{
			var kids_menu = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="kids_menu" checked class="type_checkbox" id="kids_menu"></input>';
		}
		else
		{
			var kids_menu = '<input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="kids_menu" class="type_checkbox" id="kids_menu"></input>';
		}
		if(dict['course'] == 'c1')
		{
			var c1 = '<option selected value="c1"> 1 </option>';
		}
		else
		{
			var c1 = '<option value="c1"> 1 </option>';
		}
		if(dict['course'] == 'c2')
		{
			var c2 = '<option selected value="c2"> 2 </option>';
		}
		else
		{
			var c2 = '<option value="c2"> 2 </option>';
		}
		if(dict['course'] == 'c3')
		{
			var c3 = '<option selected value="c3"> 3 </option>';
		}
		else
		{
			var c3 = '<option value="c3"> 3 </option>';
		}
		if(dict['course'] == 'c4')
		{
			var c4 = '<option selected value="c4"> 4 </option>';
		}
		else
		{
			var c4 = '<option value="c4"> 4 </option>';
			
		}
		if(dict['course'] == 'c5')
		{
			var c5 = '<option selected value="c5"> 5 </option>';
		}
		else
		{
			var c5 = '<option value="c5"> 5 </option>';
		}
		if(dict['course'] == 'c6')
		{
			var c6 = '<option selected value="c6"> 6 </option>';
		}
		else
		{
			var c6 = '<option value="c6"> 6 </option>';
		}
		if(dict['active'] == 'True')
		{
			var Ac = '<option selected value="True"> Active </option>';
		}
		else
		{
			var Ac = '<option value="True"> Active </option>';
		}
		if(dict['active'] == 'Inactive')
		{
			var InAc = '<option selected value="False"> Inactive </option>';
		}
		else
		{
			var InAc = '<option value="False"> Inactive </option>';
		}
		
		
		if($(this).attr('name') == 'dup_grp')
		{
			var newRow =  '<tr class=""><td class="hidden"><input id="db_id" value="create_'+ String(count) +'"/></td><td class="singleblock_center menu_checkbox"><div id ="checkbox_type" title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER"><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> B </span>'+bf+'<span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> L </span>'+lunch+'<span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> D </span>'+dinner+'<span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> Kids Menu </span>'+kids_menu+'</div></td>'+
	    	'<td class="singleblock_center"><input style="width:100%;" title="Enter the name of the menu" type="text" name ="menu_name" class="menu_name" value="'+dict['name']+'"></input></td>'+
			'<td class="singleblock_center"><textarea style="resize:none;" title="Enter the details of the menu. Please specify the inclusions in detail" type="text" name ="menu_desc" class="menu_desc">'+dict['description']+'</textarea></td>'+
			'<td class="singleblock_center"><select style="width:100%;padding:1px;" title="Select the menu course" name="course" class="menu_course">'+c1+''+c2+''+c3+''+c4+''+c5+''+c6+'</select></td>'+
			'<td class="singleblock_center"><input style="width:100%;" value="'+dict['min_covers']+'" name="min_covers" class="min_covers" title="Enter the minimum number of Covers"/></td>'+
	    	'<td class="singleblock_center"><select style="width:100%;padding:1px;" title="All menus are in ACTIVE state by default. In case you do not choose to display a menu to the tour operator, change the status to INACTIVE and SAVE" name="active" class="menu_status">'+Ac+''+InAc+'</select></td>'+
	    	'<td class="singleblock_center"><input style="width:100%;text-align:right;padding-right:5px;padding-left:5px;" name="rest_price" onchange="javascript:sc_included_change(this)" class="alloc_day rest_price" title="Enter the Restuarant Price of the menu" value="'+dict['rest_price']+'"/></td>'+
	    	'<td class="singleblock_center"><input disabled="disabled" class="input-control total_price" style="height:22px;width:100%;padding-left:5px;text-align:right;padding-right:5px;" type="text" value="'+dict['total_price']+'" title=""/></td>'+
	    	'<td class="singleblock_center"><a id="duplicate" class="bookinginfolink" name="dup_grp"> <img src="/web/static/src/img/icons/gtk-copy.png" id="img_icons" title="Click to copy the details of the menu created to a new record"/> </a></td>'+
	    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete the menu" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';
		}
		else
		{
			var newRow =  '<tr class=""><td class="hidden"><input id="db_id" value="create_'+ String(count) +'"/></td><td class="singleblock_center menu_checkbox"><form action="/capital_centric/profile/restaurant/edit_restaurant/menu" method="post"><div id ="checkbox_type" title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER"><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> B </span>'+bf+'<span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> L </span>'+lunch+'<span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> AT </span>'+at+'<span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> D </span>'+dinner+'<span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> Kids Menu </span>'+kids_menu+'</div></td>'+
	    	'<td class="singleblock_center"><input style="width:100%;" title="Enter the name of the menu" type="text" name ="menu_name" class="menu_name" value="'+dict['name']+'"></input></td>'+
			'<td class="singleblock_center"><textarea style="resize:none;" title="Enter the details of the menu. Please specify the inclusions in detail" type="text" name ="menu_desc" class="menu_desc">'+dict['description']+'</textarea></td>'+
			'<td class="singleblock_center"><select style="padding:1px;" title="Select the menu course" name="course" class="menu_course">'+c1+''+c2+''+c3+''+c4+''+c5+''+c6+'</select></td>'+
			'<td class="singleblock_center"><input style="width:100%;" value="'+dict['min_covers']+'" name="min_covers" class="min_covers" title="Enter the minimum number of Covers"/></td>'+
	    	'<td class="singleblock_center"><select style="padding:1px;" title="All menus are in ACTIVE state by default. In case you do not choose to display a menu to the tour operator, change the status to INACTIVE and SAVE" name="active" class="menu_status">'+Ac+''+InAc+'</select></td>'+
	    	'<td class="singleblock_center"><input name="menu_id" class="hidden" t-att-value="menus.id "></input><input name="partner_id" class="hidden" value="'+venue_id+'"></input><button title="Click to add PRICING to the menu added" class="button menu_table_button" id="menu_table_button"> Pricing </button></td>'+
	    	'<td class="singleblock_center"><a id="duplicate" class="bookinginfolink" name="dup_fit"> <img src="/web/static/src/img/icons/gtk-copy.png" id="img_icons" title="Click to copy the details of the menu created to a new record"/> </a></td>'+
	    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete the menu" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td><form></tr>';	
		}
		
    	$(newRow).appendTo($("#menu_table"));
        
        openerp.jsonRpc("/website_capitalcentric/existing_menu_record/", 'call', {'partner_id':parseInt(venue_id),'db_id' : db_id,'dict_menu' : dict})
        .then(function (data) 
        {	
        	$('table#menu_table tr:gt(0)').each(function()
	        {	
	        	db_value = data[$(this).find('#db_id').val()];
	        	if (db_value != undefined)
	        	{
	        		$(this).find('#db_id').val(db_value);
        		}
	        });
	        window.location.href = "/capital_centric/profile/restaurant/edit_restaurant/"+parseInt(venue_id)+"/menu?chk_wch=duplicate";
        });   
    });
    
////////////////////////                 Validation On Click oF Pricing Button in Menu tab                /////////////////////////

	$("#menu_table").on('click','#menu_table_button',function(event)
	{  
		var id 				= $(this).closest("tr");
    	var break_fast 	 	= id.find("#break_fast").is(':checked');
    	var lunch	 	 	= id.find("#lunch").is(':checked');
    	var afternoon_tea 	= id.find("#afternoon_tea").is(':checked');
    	var dinner 	 	 	= id.find("#dinner").is(':checked');
    	var min_covers 	= id.find(".min_covers").val();
    	var numbers = /^[-+]?[0-9]+$/;  
    	
    	if(break_fast == true || lunch == true || afternoon_tea == true || dinner == true)
    	{
    		if((min_covers.match(numbers)) && min_covers!=0)
    		{
    			id.find('#pricing_form').submit();	
    		}
    		else
    		{
    			alert("Please Enter Min. Covers as numbers greater than 0");
	  			id.find(".min_covers").focus();
	  			id.find(".min_covers").select();
	  			return false;
    		}
    	}
    	else
    	{	
    		alert('Please select a value under AVAILABLE FOR');	
    		return false;
    	}
	});



////////////////////////                       Deletion Of Records in Menu Tab                  /////////////////////////
    
     $("#menu_table").on('click','#db_delete',function(event)
	 {
    	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").val();
        if (db_id == 'undefined')
        {
        	var r=confirm("Are you sure you want to permanently delete?");
	        if (r==true)
			{
			  $(this).parent().parent().remove();
			  // document.body.scrollTop = document.documentElement.scrollTop = 0;
			  $("html, body").animate({
            		scrollTop: 0
        	  }, 600);
			  document.getElementById('save_prompt').innerHTML="Deleted !!";
			  $("#save_prompt").stop(true,true).show().fadeOut(5000);
			}
        }
        else
        {
        	var r=confirm("Are you sure you want to permanently delete this record?");
	        if (r==true)
	        {
		    	openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value':'menus_table','db_id' : parseInt(db_id)})
		        .then(function (data) 
		        {
		         	id.remove();
		         	// document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	$("html, body").animate({
		            	scrollTop: 0
		        	}, 600);
		         	document.getElementById('save_prompt').innerHTML="Menu Deleted !!";
					$("#save_prompt").stop(true,true).show().fadeOut(3000);
		        });
		    }
        }
	});
	
    
//   Black-Out Tab

// ////////////////////////                       Saving Of Records in Black-Out Tab                  /////////////////////////
// 
    // $("#blackout_table").on('click','#save',function(event)
     // {
     		// var id = $(this).closest("tr");  		
		    // db_id = id.find("#db_id").val();
            // black_date = id.find(".black_date").val();
	        // black_desc = id.find(".black_desc").val();
	        // black_from_time = id.find(".black_from_time").val();
	        // black_to_time = id.find(".black_to_time").val();
// 	        
	        // var link_name = $(this).attr('name');
		    // var chkwhich = link_name;
		    // if(db_id != 'undefined')
	    	// {
	    		// db_id = parseInt(db_id);
	    	// }
	    	// else
	    	// {
	    		// db_id = 'false';
	    	// }
	        // if ( black_date == "" )
			// {
			    // alert("Please Select a Date");
			    // return;
			// }
	        // openerp.jsonRpc("/website_capitalcentric/blackout_json/", 'call', {'value':chkwhich,'partner_id':venue_id,'db_id' : db_id,'date': black_date, 'black_from_time':black_from_time, 'black_to_time':black_to_time, 'name':black_desc })
	        // .then(function (data) 
	        // {
	        	// new_id = id.find('#db_id').val(data);
	        	// if(link_name == 'new' && new_id != '')
		    	// {
		    		// id.find("#save").attr("name","existing");
		    	// }
				// document.getElementById('save_prompt').innerHTML="Saved Successfully!!";
				// $("#save_prompt").stop(true,true).show().fadeOut(5000);
	        // });   
    // });


////////////////////////                       Deletion Of Records in Black-Out Tab                  /////////////////////////
    
    $("#blackout_table").on('click','#db_delete',function(event)
	 {
    	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").val();
        if(db_id == "undefined")
        {
	        var r=confirm("Are you sure you want to permanently delete?");
	        if (r==true)
			{
			  $(this).parent().parent().remove();
			  // document.body.scrollTop = document.documentElement.scrollTop = 0;
			  $("html, body").animate({
            		scrollTop: 0
        	  }, 600);
			  document.getElementById('save_prompt').innerHTML="Deleted !!";
			  $("#save_prompt").stop(true,true).show().fadeOut(5000);
			}
		}
		else
		{
		    var r=confirm("Are you sure you want to permanently delete this record?");
	        if (r==true)
	        {
		    	openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value':'black_out_table', 'db_id' : parseInt(db_id)})
		        .then(function (data) 
		        {
		         	id.remove();
		         	// document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	$("html, body").animate({
            			scrollTop: 0
        	  		}, 600);
		         	document.getElementById('save_prompt').innerHTML="Deleted !!";
		         	$("#save_prompt").stop(true,true).show().fadeOut(5000);
		        });
		    }
	   }
	});

////////////////////////                       Adding Of New Records in Black-Out Tab                  /////////////////////////

	$("a#blackout_add").click(function()
    {	
    	var newRow =  '<tr class=""><td class="hidden"><input id="db_id" value="undefined"/></td><td class="singleblock_text"><input style="padding-left:5px" title="Select the blackout date" type="text" class="datepicker black_inputs black_from_date" id=""></input></td>'+
    	'<td class="singleblock_text"><input style="padding-left:5px" title="Select the blackout date" type="text" class="datepicker black_inputs black_to_date" id=""></input></td>'+
    	'<td class="singleblock_center"><select style="padding:1px;" title="Select start time of blackout. If you set the selection to N/A, the system will consider the entire day as a blackout day. If you enter a FROM and TO time, the blackout will be applicable only for the duration entered" class="black_inputs black_from_time" id="" name="time"></select></td>'+
    	'<td class="singleblock_center"><select style="padding:1px;" title="Select end time of blackout. If you set the selection to N/A, the system will consider the entire day as a blackout day. If you enter a FROM and TO time, the blackout will be applicable only for the duration entered" class="black_inputs black_to_time" id="" name="time"></select></td>'+  
    	'<td class="singleblock_text"><input style="padding-left:5px" title="Enter the reason for the blackout" type="text" class="black_inputs black_desc"></input></td>'+
    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete this record" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';   
    	$(newRow).appendTo($("#blackout_table"));
    	// $("#blackout_table tr td input.black_from_date").focus();
    	$(".datepicker").datepicker({dateFormat: "dd-M-yy",showAnim: "fadeIn"});
    	
    	openerp.jsonRpc("/website_capitalcentric/time/", 'call', {})
	    .then(function (data) 
	    {  
		     for(var i=0; i<data[0].length; i++)
	    	 {	
	         	$('table#blackout_table tr:last .black_to_time').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
	         	$('table#blackout_table tr:last .black_from_time').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
		     }
		});
    });
    
    
    
////////////////////////                       Deletion Of Records in Drinks Tab                  /////////////////////////
    
    $("#drinks_table").on('click','#db_delete',function(event)
	 {
    	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").val();
        if(db_id == "undefined")
        {
	        var r=confirm("Are you sure you want to permanently delete?");
	        if (r==true)
			{
			  $(this).parent().parent().remove();
			  // document.body.scrollTop = document.documentElement.scrollTop = 0;
			  $("html, body").animate({
            		scrollTop: 0
        	  }, 600);
			  document.getElementById('save_prompt').innerHTML="Deleted!!";
			  $("#save_prompt").stop(true,true).show().fadeOut(5000);
			}
		}
		else
		{
		    var r=confirm("Are you sure you want to permanently delete this record?");
	        if (r==true)
	        {
		    	openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value':'menus_table', 'db_id' : parseInt(db_id)})
		        .then(function (data) 
		        {
		         	id.remove();
		         	// document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	$("html, body").animate({
            			scrollTop: 0
        	  		}, 600);
		         	document.getElementById('save_prompt').innerHTML="Deleted!!";
		         	$("#save_prompt").stop(true,true).show().fadeOut(5000);
		        });
		    }
	    }
	});

////////////////////////                       Adding Of New Records in Drinks Tab                  /////////////////////////

	$("a#drink_add").click(function() 
    {	
    	var newRow = '<tr class=""><td class="hidden"><input id="db_id" value="undefined"/></td><td class="singleblock_text"><input style="padding-left:5px;width:100%;" class="input-control black_inputs drink_name" title=""></input></td>'+
    	'<td class="singleblock_text"><textarea style="padding-left:5px;width:100%;height:70px;resize:none;" type="text" class="menu_desc drink_desc" title=""/></td>'+
    	'<td class="singleblock_center"><input style="padding-left:5px;text-align:right;padding-right:5px;" type="text" class="input-control black_inputs drink_size" title=""/></td>'+
    	'<td class="singleblock_center"><input style="padding-left:5px;text-align:right;padding-right:5px;" type="text" onchange="javascript:change_drink(this)" id="price" class="input-control black_inputs drink_price" title=""/></td>'+
    	'<td class="singleblock_center"><select style="height:22px;width:100%;" class="input-control sc_included_drink" onchange="javascript:change_drink(this)" id="sc_included_drink" title=""><option value="True">Yes</option><option value="False" selected="selected">No</option></select></td>'+
    	'<td class="singleblock_center"><input style="height:22px;width:100%;padding-left:5px;text-align:right;padding-right:5px;" type="text" onchange="javascript:change_drink(this)" id="sc" class="input-control sc_per_drink" title=""/></td>'+
    	'<td class="singleblock_center"><input disabled="disabled" style="height:22px;width:100%;padding-left:5px;text-align:right;padding-right:5px;" type="text" class="input-control total_price" title=""/></td>'+
    	'<td class="singleblock_center"><select style="padding:1px;" title="" name="active" class="menu_status"><option value="True"> Active </option><option value="False"> Inactive </option></select></td>'+
    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete this record" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';   
    	$(newRow).appendTo($("#drinks_table"));
    	$("#drinks_table tr td input.drink_name").focus();
    });
    
    
    ////////////////////////                       Deletion Of Records in Events Menus Tab                 /////////////////////////
    
    $("#events_menu_table").on('click','#db_delete',function(event)
	 {
    	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").val();
        if(db_id == "undefined")
        {
	        var r=confirm("Are you sure you want to permanently delete?");
	        if (r==true)
			{
			  $(this).parent().parent().remove();
			  // document.body.scrollTop = document.documentElement.scrollTop = 0;
			  $("html, body").animate({
            		scrollTop: 0
        	  }, 600);
			  document.getElementById('save_prompt').innerHTML="Deleted!!";
			  $("#save_prompt").stop(true,true).show().fadeOut(5000);
			}
		}
		else
		{
		    var r=confirm("Are you sure you want to permanently delete this record?");
	        if (r==true)
	        {
		    	openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value':'menus_table', 'db_id' : parseInt(db_id)})
		        .then(function (data) 
		        {
		         	id.remove();
		         	// document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	$("html, body").animate({
            			scrollTop: 0
        	  		}, 600);
		         	document.getElementById('save_prompt').innerHTML="Deleted!!";
		         	$("#save_prompt").stop(true,true).show().fadeOut(5000);
		        });
		    }
	    }
	});

////////////////////////                       Adding Of New Records in Events Menu Tab                  /////////////////////////

	$("a#events_menu_add").click(function() 
    {	
    	var newRow = '<tr class=""><td class="hidden"><input id="db_id" value="undefined"/></td>'+
    	'<td class="singleblock_center menu_checkbox"><div id ="checkbox_type" title="Check the appropriate boxes to indicate the timing of availability of the Event Menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER"><span title="Check the appropriate boxes to indicate the timing of availability of the Event Menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> B </span><input title="Check the appropriate boxes to indicate the timing of availability of the Event Menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="break_fast" class="type_checkbox" id="break_fast"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> L </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="lunch" class="type_checkbox" id="lunch"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> AT </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="afternoon_tea" class="type_checkbox" id="afternoon_tea"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> D </span><input title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="dinner" class="type_checkbox" id="dinner"></input><span title="Check the appropriate boxes to indicate the timing of availability of the menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" id="add_label_active"> Kids Menu </span><input title="Check the appropriate boxes to indicate the timing of availability of the Event Menu. B - BREAKFAST, L - LUNCH, AT - AFTERNOON TEA, D - DINNER" type="checkbox" name="kids_menu" class="type_checkbox" id="kids_menu"></input></div></td>'+
    	'<td class="singleblock_text"><input style="padding-left:5px;width:100%;" class="input-control black_inputs drink_name" title=""></input></td>'+
    	'<td class="singleblock_text"><textarea style="padding-left:5px;width:100%;height:70px;resize:none;" type="text" class="menu_desc drink_desc" title=""/></td>'+
    	'<td class="singleblock_center"><input style="padding-left:5px;text-align:right;padding-right:5px;" type="text" onchange="javascript:change_drink(this)" id="price" class="input-control black_inputs drink_price" title=""/></td>'+
    	'<td class="singleblock_center"><select style="height:22px;width:100%;" class="input-control sc_included_drink" onchange="javascript:change_drink(this)" id="sc_included_drink" title=""><option value="True">Yes</option><option value="False" selected="selected">No</option></select></td>'+
    	'<td class="singleblock_center"><input style="height:22px;width:100%;padding-left:5px;text-align:right;padding-right:5px;" type="text" onchange="javascript:change_drink(this)" id="sc" class="input-control sc_per_drink" title=""/></td>'+
    	'<td class="singleblock_center"><input disabled="disabled" style="height:22px;width:100%;padding-left:5px;text-align:right;padding-right:5px;" type="text" class="input-control total_price" title=""/></td>'+
    	'<td class="singleblock_center"><select style="padding:1px;width:100%;" title="" name="active" class="menu_status"><option value="True"> Active </option><option value="False"> Inactive </option></select></td>'+
    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete this record" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';   
    	$(newRow).appendTo($("#events_menu_table"));
    	$("#events_menu_table tr td input.drink_name").focus();
    });
    
    
    
    
////////////////////////                       Deletion Of Records in Events Tab                 /////////////////////////
    
    $("#events_table").on('click','#db_delete',function(event)
	 {
    	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").val();
        if(db_id == "undefined")
        {
	        var r=confirm("Are you sure you want to permanently delete?");
	        if (r==true)
			{
			  $(this).parent().parent().remove();
			  // document.body.scrollTop = document.documentElement.scrollTop = 0;
			  $("html, body").animate({
            		scrollTop: 0
        	  }, 600);
			  document.getElementById('save_prompt').innerHTML="Deleted!!";
			  $("#save_prompt").stop(true,true).show().fadeOut(5000);
			}
		}
		else
		{
		    var r=confirm("Are you sure you want to permanently delete this record?");
	        if (r==true)
	        {
		    	openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value':'events_table', 'db_id' : parseInt(db_id)})
		        .then(function (data) 
		        {
		         	id.remove();
		         	// document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	$("html, body").animate({
            			scrollTop: 0
        	  		}, 600);
		         	document.getElementById('save_prompt').innerHTML="Deleted!!";
		         	$("#save_prompt").stop(true,true).show().fadeOut(5000);
		        });
		    }
	    }
	});

////////////////////////                       Adding Of New Records in Events Menu Tab                  /////////////////////////

	$("a#event_add").click(function() 
    {	
    	var ul = ''; 
    	var newRow = '<tr class="last_tr"><td class="hidden"><input id="db_id" value="undefined"/></td><td class="singleblock_text"><input style="padding:5px;width:100%;" class="input-control black_inputs drink_name" title=""></input></td>'+
    	'<td class="singleblock_text"><textarea style="padding-left:5px;width:100%;height:70px;resize:none;" type="text" class="menu_desc drink_desc" title=""/></td>'+
    	'<td class="singleblock_text"><input style="padding-left:5px" title="Select the blackout date" type="text" class="datepicker black_inputs black_from_date" id=""></input></td>'+
    	'<td class="singleblock_text"><input style="padding-left:5px" title="Select the blackout date" type="text" class="datepicker black_inputs black_to_date" id=""></input></td>'+
    	'<td class="singleblock_text"><div><table id="sub_events_table" style="width:100%"><tr><td style="width:15%"><p style="display:inline-block;font-weight:bold;"> B : </p></td><td style="width:85%"><select id="bf_time_frm" style="display:inline-block;padding:1px;width:45%" class="black_inputs black_from_time" title=""></select>&nbsp;<span style="display:inline-block;"> - </span>&nbsp;<select id="bf_time_to" style="display:inline-block;padding:1px;width:45%" class="black_inputs black_to_time" title=""></select></td></tr></table>'+
    	'<table id="sub_events_table" style="width:100%;"><tr><td style="width:15%"><p style="display:inline-block;font-weight:bold;"> L : </p></td><td style="width:85%"><select id="l_time_frm" style="display:inline-block;padding:1px;width:45%" class="black_inputs black_from_time" title=""></select>&nbsp;<span style="display:inline-block;"> - </span>&nbsp;<select id="l_time_to" style="display:inline-block;padding:1px;width:45%" class="black_inputs black_to_time" title=""></select></td></tr></table>'+
    	'<table id="sub_events_table" style="width:100%;"><tr><td style="width:15%"><p style="display:inline-block;font-weight:bold;"> AT : </p></td><td style="width:85%"><select id="at_time_frm" style="display:inline-block;padding:1px;width:45%" class="black_inputs black_from_time" title=""></select>&nbsp;<span style="display:inline-block;"> - </span>&nbsp;<select id="at_time_to" style="display:inline-block;padding:1px;width:45%" class="black_inputs black_to_time" title=""></select></td></tr></table>'+
    	'<table id="sub_events_table" style="width:100%;"><tr><td style="width:15%"><p style="display:inline-block;font-weight:bold;"> D : </p></td><td style="width:85%"><select id="d_time_frm" style="display:inline-block;padding:1px;width:45%" class="black_inputs black_from_time" title=""></select>&nbsp;<span style="display:inline-block;"> - </span>&nbsp;<select id="d_time_to" style="display:inline-block;padding:1px;width:45%" class="black_inputs black_to_time" title=""></select></td></tr></table><div></td>'+
    	'<td class="singleblock_text" id="multi"><select name="event_menu_name" id="event_menu" class="input-control input_val event_menu_new" title="" multiple="multiple" onchange="javascript:get_eventvalues(this)"></select><textarea class="hidden" name="e_menu_selected" id="event_menu_ids"></textarea></td>'+
    	'<td class="singleblock_text"><input class="alloc_covers" type="text" title=""></input></td>'+
    	'<td class="singleblock_center"><select style="padding:1px;width:100%;" title="" name="active" class="menu_status"><option value="True"> Active </option><option value="False"> Inactive </option></select></td>'+
    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete this record" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';   
    	$(newRow).appendTo($("#events_table"));
    	$("#events_table tr td input.drink_name").focus();
    	$(".datepicker").datepicker({dateFormat: "dd-M-yy",showAnim: "fadeIn"});
    	
    	$(".event_menu_new").multiselect({
    		noneSelectedText: "Select Menus",
        	selectedText : "# Menu(s) Selected"
       	});  
       	$('.ui-multiselect').css('width','100%');	       	
    	
        	
        openerp.jsonRpc("/website_capitalcentric/time/", 'call', {})
	    .then(function (data) 
	    {  
		     for(var i=0; i<data[0].length; i++)
	    	 {	
	         	$('#events_table tr.last_tr:last .black_to_time').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
	         	$('#events_table tr.last_tr:last .black_from_time').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
		     }
		});	
		
    	var x = $("div.ui-widget-content:last ul.ui-multiselect-checkboxes");
		openerp.jsonRpc("/website_capitalcentric/events_menu/", 'call', {'partner_id':parseInt(venue_id)})
	    .then(function (data) 
	    {   
		     for(var i=0; i<data[0].length; i++)
	    	 {	
	         	$('#events_table tr.last_tr:last #event_menu').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
	         	ul += '<li class=" "><label for=ui-multiselect-event_menu-option-'+i+' class="ui-corner-all"><input id="ui-multiselect-event_menu-option-'+i+'" name="multiselect_event_menu" type="checkbox" value="'+ data[1][i]+'"><span>'+data[0][i]+'</span></input></label></li>';
		     }		    	
		     x.html(ul);
		     $('#events_table tr.last_tr:last .event_menu_new').multiselect('refresh');	
		     $('.ui-multiselect').css('width','100%');	  
		     $('.ui-multiselect').css('border-radius','5px');
		     $('.ui-multiselect').css('cursor','default');
		     $(".ui-state-default").css('background-image','none');
		     $(".ui-state-default").css('background-color','white');
		     $('.ui-multiselect-menu').outerWidth($('.ui-multiselect').outerWidth());
		     $('div.ui-widget-content:last ul.ui-multiselect-checkboxes label input').css('margin-right','3%');
		     $('div.ui-widget-content:last div.ui-widget-header ul li:last-child a').empty().html('<span>Close</span>');
		     $(".ui-multiselect-header li.ui-multiselect-close").css('padding-right','1%');   
		});
    });
    
    
////////////////////////                       Adding Of New Records in Private Rooms Tab                  /////////////////////////

	$("a#pvt_room_add").click(function() 
    {	
    	var newRow = '<tr class=""><td class="hidden"><input id="db_id" value="undefined"/></td><td class="singleblock_text"><input style="width:100%;text-align:left;padding-left:5px;padding-right:5px;" class="alloc_day pvt_room_name" title="Enter the name of the private room"/></td>'+
    	'<td class="singleblock_number"><input style="text-align:right;padding-right:5px;" class="alloc_day covers_seated" title="Enter the no. of covers seated"/></td>'+
    	'<td class="singleblock_number"><input style="text-align:right;padding-right:5px;" class="alloc_day covers_standing" title="Enter the no. of covers standing"/></td>'+
    	'<td class="singleblock_number"><input style="text-align:right;padding-right:5px;" class="alloc_day max_no" title="Enter the max no. on one table"/></td>'+
    	'<td class="singleblock_center"><select style="width:100%;padding:1px;" class="alloc_day av_screen" title="Select AV Screen"><option value="yes"> Yes </option><option selected = "selected" value="no"> No </option></select></td>'+
    	'<td class="singleblock_center"><select style="padding:1px;width:100%;" class="alloc_day projector" title="Select Projector"><option value="yes"> Yes </option><option selected = "selected" value="no"> No </option></select></td>'+
    	'<td class="singleblock_text"><input style="width:100%;text-align:left;padding-left:5px;padding-right:5px;" class="alloc_day others" title=""/></td>'+
    	'<td class="singleblock_center"><a id="db_delete" class="bookinginfolink"> <img title="Click to delete this record" src="/website_capitalcentric/static/src/img/delete_t.png" id="img_icons"/> </a></td></tr>';   
    	$(newRow).appendTo($("#pvt_room_table"));
    	$("#pvt_room_table tr td input.pvt_room_name").focus();
    });
    
    
    
////////////////////////                       Deletion Of Records in Private Rooms Tab                 /////////////////////////
    
    $("#pvt_room_table").on('click','#db_delete',function(event)
	{
    	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").val();
        if(db_id == "undefined")
        {
	        var r=confirm("Are you sure you want to permanently delete?");
	        if (r==true)
			{
			  $(this).parent().parent().remove();
			  // document.body.scrollTop = document.documentElement.scrollTop = 0;
			  $("html, body").animate({
            		scrollTop: 0
        	  }, 600);
			  document.getElementById('save_prompt').innerHTML="Deleted!!";
			  $("#save_prompt").stop(true,true).show().fadeOut(5000);
			}
		}
		else
		{
		    var r=confirm("Are you sure you want to permanently delete this record?");
	        if (r==true)
	        {
		    	openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value':'private_room_table', 'db_id' : parseInt(db_id)})
		        .then(function (data) 
		        {
		         	id.remove();
		         	// document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	$("html, body").animate({
            			scrollTop: 0
        	  		}, 600);
		         	document.getElementById('save_prompt').innerHTML="Deleted!!";
		         	$("#save_prompt").stop(true,true).show().fadeOut(5000);
		        });
		    }
	    }
	});
    

//  For Image Tab
	 
   $("img[class='img-rounded']").on("click", function()
   {
   	 var img_id = $(this).attr('id');
   	 document.getElementById("id_name").value = img_id;
 	 $("input[name='image_name']").trigger('click'); 
 	
   });
	  
   $("input[name='image_name']").on("change", function()
   {
    	// Get a reference to the fileList
    	$("#dvLoading").show();
	    var files = !!this.files ? this.files : [];
		var x = document.getElementById("id_name").value;
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
				 $('.image_form').submit();
			     $("#"+x).attr('src',e.target.result);
				 document.getElementById('save_prompt').innerHTML="Image Saved Successfully !!";
				 $("#save_prompt").stop(true,true).show().fadeOut(5000);
				 $("#image_input_"+x).removeAttr('disabled','disabled');
				 $("#image_input_"+x).css('background-color','white');
				 $("#image_input_"+x).focus();		 			 
				 setTimeout(function(){$("#dvLoading").hide();},6000);
				 
			};
        }
        else
        {
        	alert("Please Choose an Image");	
        }
	});
	
	// Save for Image Description 
	$("#img_desc_save").on('click',function()
	{ 
		var a = {};
		for(var i=1;i<=5;i++)
		{
			a['desc_image'+i] = $("#image_input_"+i).val();			
		}
		openerp.jsonRpc("/website_capitalcentric/image_desc/", 'call', {'partner_id':parseInt(venue_id), 'dict' : a})
        .then(function (data)
        {
        	$("html, body").animate({
            		scrollTop: 0
        	  }, 600);
        	document.getElementById('save_prompt').innerHTML="Image Description Saved Successfully !!";
	        $("#save_prompt").stop(true,true).show().fadeOut(5000);
        });
	});
	
// For Deletion of The Restaurants
     $("#res_table").on('click','#db_delete',function(event)
     {
     	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").text();
	    var r=confirm("Are you sure you want to permanently delete this record?");
        if (r==true)
        {
	    	openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value':'partner_table', 'db_id' : parseInt(db_id)})
	        .then(function (data) 
	        {
        	    $("html, body").animate({
            		scrollTop: 0
        	  	}, 600);
	        	if(data == 'restaurant')
	        	{	
		         	document.getElementById('save_prompt').innerHTML="Restaurant Cannot Be Deleted !!";
		         	$("#save_prompt").stop(true,true).show().fadeOut(5000);
	         	}
	         	else
	        	{
		         	id.remove();
		         	document.getElementById('save_prompt').innerHTML="Restaurant Deleted !!";
		         	$("#save_prompt").stop(true,true).show().fadeOut(5000);
	         	}
	        });
	    }
    }); 
   
   // Apply To all link in Pricing Table
	$('.apply_link').click(function()
	{
			var link_id = $(this).attr('id');
	   	    document.getElementById("apply_link").value = link_id;
	   	    var num = document.getElementById("apply_link").value;
	   	    var num_fp = parseInt(num) + 1;
			var x = $('#menu_id').text();
			var menu = $("#menu_id").val();
	   		var a = [];
	   		var m = [];
	   		var fp = [];
	   		var sc_included = $("#sc_included").val();
	    	var service_charge = $("#sc_per").val();
	    	var sc_disc = $("#sc_disc").val();
	    	
	   		$("table#menu_individual tr").each(function()
	   		{
	        	$(this).find("td:eq(0)").each(function()
	        	{
	        		var x = ($(this).find('input#db_id').val());
	        		a.push(parseInt(x));
	            });
	        	
	        	$(this).find("td:eq("+num+")").each(function()
	        	{
	        		var x = ($(this).find("input.day").val());
		        	m.push(x);
	        	});
	        	
	        	$(this).find("td:eq("+num_fp+")").each(function()
	        	{
	        		var final_price = ($(this).find("input").val());
	        		fp.push(final_price);
	        	});
	        });
	       
	        for (y=2; y<=15; y++)
	        {
		       	var i=0;
		       	$("table#menu_individual tr").each(function()
		   		{
		       	 var $td = $(this).find('td').eq(y);        	
		         $td.each(function()
		        	{   
		        		$(this).find("input").val(m[i]);
		        		$(this).find("input.final_price").val(fp[i]);
		        		i++;
		        	});
		     	});
	        }
		    m.pop();
		    a.pop();
		    var dict = {};
		    for (i = 0; i < a.length; i++) 
		    {
	    		dict[a[i]] = m[i];
		    } 
		   
		    openerp.jsonRpc("/website_capitalcentric/pricing_json/", 'call', {'dict_pricing':dict,'menu_id':parseInt(menu),'chkwhich':'apply_all','sc_included':sc_included,'service_charge':service_charge, 'sc_disc':sc_disc})
		   .then(function (data)
		   { 
	         	 $("html, body").animate({
            		scrollTop: 0
        	  	 }, 600);
			  	 document.getElementById('save_prompt').innerHTML="Applied Successfully to All!!";
				 $("#save_prompt").stop(true,true).show().fadeOut(5000);
                
			});
			$("#check_value").val('');
	});
	
//On load of pricing page
	var sc_included_value = $('#sc_included').val();
	if(sc_included_value == 'True')
	{
		$('#service_charge_div').hide();
		$('#service_disc_div').hide();
	}
	else
	{
		$("#sc_disc").prop('disabled',true);
		$("#sc_disc").css('background-color','#ebebe4');
	}
	
//On Change of sc_included in pricing table
	$('#sc_included').change(function()
	{
		if(this.value == 'False')
		{
			$('#service_charge_div').show();
			$('#service_disc_div').show();
			$('#sc_per').val('');
			$("#sc_disc").prop('disabled',true);
			$("#sc_disc").val($("#sc_disc option:eq(0)").val());
			$("#sc_disc").css('background-color','#ebebe4');
		}
		else
		{	
			$('#service_charge_div').hide();
			$('#service_disc_div').hide();
			$('#sc_per').val($('#service_charge_per').val());
			$("#sc_disc").val($("#sc_disc option:eq(1)").val());
		}
	});

//On Change of sc_percentage in pricing table	
	$('#sc_per').on('blur',function()
	{	
		var m = [];
		var t = []; var w =[]; var th =[]; var f =[]; var sa =[]; var su =[];  
		var a = [];
		var sc = (this.value /100);
		$("table#menu_individual tr").each(function()
   		{	
        	$(this).find("td:eq(2)").each(function()
        	{
        		if ($(this).find("input").val() != undefined)
        		{
        		var x = (parseFloat($(this).find("input").val()) * sc + parseFloat($(this).find("input").val()));
	        	m.push(x);
	        	}
        	});
        	$(this).find("td:eq(4)").each(function()
        	{
        		if ($(this).find("input").val() != undefined)
        		{
        		var tp = (parseFloat($(this).find("input").val()) * sc + parseFloat($(this).find("input").val()));
	        	t.push(tp);
	        	}
        	});
        	$(this).find("td:eq(6)").each(function()
        	{
        		if ($(this).find("input").val() != undefined)
        		{
        		var wp = (parseFloat($(this).find("input").val()) * sc + parseFloat($(this).find("input").val()));
	        	w.push(wp);
	        	}
        	});
        	$(this).find("td:eq(8)").each(function()
        	{
        		if ($(this).find("input").val() != undefined)
        		{
        		var thp = (parseFloat($(this).find("input").val()) * sc + parseFloat($(this).find("input").val()));
	        	th.push(thp);
	        	}
        	});
        	$(this).find("td:eq(10)").each(function()
        	{
        		if ($(this).find("input").val() != undefined)
        		{
        		var fp = (parseFloat($(this).find("input").val()) * sc + parseFloat($(this).find("input").val()));
	        	f.push(fp);
	        	}
        	});
        	$(this).find("td:eq(12)").each(function()
        	{
        		if ($(this).find("input").val() != undefined)
        		{
        		var sap = (parseFloat($(this).find("input").val()) * sc + parseFloat($(this).find("input").val()));
	        	sa.push(sap);
	        	}
        	});
        	$(this).find("td:eq(14)").each(function()
        	{
        		if ($(this).find("input").val() != undefined)
        		{
        		var sup = (parseFloat($(this).find("input").val()) * sc + parseFloat($(this).find("input").val()));
	        	su.push(sup);
	        	}
        	});
        });
       
        for(y=2; y<=15; y++)
        {
       	    var i=0;
	       	$("table#menu_individual tr").each(function()
	   		{
	       	 var $td = $(this).find('td').eq(y);        	
	         $td.each(function()
        	 {  
        	 	if ($(this).find("input").val() != undefined)
        		{
	        		$(this).find("input#monday_finalprice").val(m[i].toFixed(2));
	        		$(this).find("input#tuesday_finalprice").val(t[i].toFixed(2));
	        		$(this).find("input#wednesday_finalprice").val(w[i].toFixed(2));
	        		$(this).find("input#thursday_finalprice").val(th[i].toFixed(2));
	        		$(this).find("input#friday_finalprice").val(f[i].toFixed(2));
	        		$(this).find("input#saturday_finalprice").val(sa[i].toFixed(2));
	        		$(this).find("input#sunday_finalprice").val(su[i].toFixed(2));
	        		i++;
        		}
        	 });
	     });
       }
	});
	
//On Change of individual day fields in pricing table if SC is present or not
	$('.day').on('blur',function()
	{
		var day_id = $(this).attr('id');
		var id = $(this).closest("tr");
		var sc_included_value = $('#sc_included').val();
	    if($('#sc_included').val() == 'True')
	    {
	    	id.find("#"+day_id+"_finalprice").val(this.value);
	    }
	    else
	    {   
	    	if($('#sc_per').val() == '' || $('#sc_per').val() == '0.00')
	    	{
	    		alert("Please Enter the Service Charge");
	    		$('#sc_per').focus();
	    		return false;
	    	}
	    	id.find("#"+day_id+"_finalprice").val((parseFloat(this.value) * ($('#sc_per').val()/100) + parseFloat(this.value)).toFixed(2));
	    }
	});

//Centralized save() for all one2many objects
	$('.save_all').click(function(event)
	{    
        var tr = 1;
        var m = [];
        var a = [];
        var dict = {};
        var menu = $("#menu_id").val();
        var button_clk = $(this).attr('id');        
        var j = 0; 
       	var vals = {};
       	var x = '';
       	var y = '';
       	var venue_id = $("#venue_id").val();
       	var alloc_type = '';
       	// var xmlid = '';
       	
//save for pricing table
        if(button_clk == 'pri_save')
        {
        	var sc_included = $("#sc_included").val();
        	var service_charge = $("#sc_per").val();
        	var sc_disc = $("#sc_disc").val();
	        $('table#menu_individual tr').each(function()
	        {   
	          $(this).find('td').each(function()
	            {	
	               var x = ($(this).find("input.day").val());
	               if (x != undefined)
	            	  m.push(x);
	            });
	        });
	        
            $('table#menu_individual tr:eq(1)').each(function()
	        {
	        	$(this).find("td").each(function()
		        	{
		        		var y = $(this).attr('id');
		        		if (y != undefined)
		        			if (y != "")
		        				a.push(y);
		            });
	        });
	       
	        for (i=0;i < m.length; i++)
	   		{	
	   			if (a[j]=='db_id')
	   			{
					var db_id = m[i];
					j++;
					continue;
				}	 			
				dict[a[j]] = m[i];
				if (a[j]=='sunday')
				{
					vals[db_id] = dict;
					var dict = {};
					j=-1;
				}
				j++;
	 		} 	
	 		
	 		openerp.jsonRpc("/website_capitalcentric/pricing_json/", 'call', {'dict_pricing':vals,'menu_id':parseInt(menu), 'chkwhich':'save','sc_included':sc_included,'service_charge':service_charge, 'sc_disc':sc_disc})
		  	.then(function (data)
		  	{	
		  	    $("html, body").animate({
            		scrollTop: 0
        	  	}, 600);
		  		document.getElementById('save_prompt').innerHTML="Saved Successfully !!";
		        $("#save_prompt").stop(true,true).show().fadeOut(5000);
		 	});	 	

	    }

//Save for Time & Allocations table
	    if (button_clk == 'bf_save' || button_clk == 'pr_save')
	    	xmlid = 'break_fast_table'; 
	    else if (button_clk == 'lun_save')
	    	xmlid = 'lunch_table'; 
	    else if (button_clk == 'at_save')
	    	xmlid = 'at_table';
	    else if (button_clk == 'din_save')
	    	xmlid = 'dinner_table';
	    	 
	    var count = 1;
	    if (button_clk == 'bf_save' || button_clk == 'lun_save' || button_clk == 'at_save' || button_clk == 'din_save' || button_clk == 'pr_save')
	    {
	    	$('table#' + xmlid + ' tr:gt(0)').each(function()
	        {   
	        	var dict={};
	        	alloc_type 	= $(this).find("#alloc_type").val();
	        	dict['name'] 	   	= $(this).find(".alloc_day").val();
	            dict['non_frm_id'] 	= $(this).find(".non_frm_id").val();
	            dict['non_to_id']  	= $(this).find(".non_to_id").val();
	        	dict['std_frm_id'] 	= $(this).find(".std_frm_id").val();
	        	dict['std_to_id']  	= $(this).find(".std_to_id").val();
	        	dict['pre_frm_id'] 	= $(this).find(".pre_frm_id").val();
	        	dict['pre_to_id']  	= $(this).find(".pre_to_id").val();
	        	dict['covers'] 	   	= $(this).find(".alloc_covers").val();
				dict['cap'] 	   	= $(this).find(".max_covers").val();
	        	
	        	if(button_clk == 'pr_save')
	        	{
	        		alloc_type 	= 'break_fast';
	        		dict['name'] 	   	= $(this).find(".alloc_day").val();
	            	dict['bf_from'] 	= $(this).find(".non_frm_id").val();
	            	dict['bf_to']  		= $(this).find(".non_to_id").val();
	        		dict['lunch_from'] 	= $(this).find(".std_frm_id").val();
	        		dict['lunch_to']  	= $(this).find(".std_to_id").val();
	        		dict['dinner_from'] = $(this).find(".pre_frm_id").val();
	        		dict['dinner_to']  	= $(this).find(".pre_to_id").val();
	        		dict['covers'] 	   	= '1';
					dict['cap']			= '1';
	        	}
	        	var covers = dict['covers'];
				var cap = dict['cap'];
	        	if(button_clk == 'bf_save')
	        	{
	        		var alert_type_first  = 'Non Premium';
	        		var alert_type_second = 'Standard';
	        		var alert_type_third  = 'Premium';
	        	}
	        	else
	        	{
	        		var alert_type_first  = 'B/F';
	        		var alert_type_second = 'Lunch';
	        		var alert_type_third  = 'Dinner';
	        	}
	        	if(dict['name'] == "Select Day..")
	        	{
	        		alert("Please Select a day");
	        		$(this).find(".alloc_day").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
	        	}
			    if(dict['non_frm_id'] == 1 && dict['non_to_id'] != 1 )
		        {	
				 	alert("Please Select From TIME for "+alert_type_first+"");
				 	$(this).find('.non_frm_id').focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
			    }
			    if(dict['non_to_id'] == 1 && dict['non_frm_id'] != 1 )
		        {	
				 	alert("Please Select To TIME for "+alert_type_first+"");
				 	$(this).find('.non_to_id').focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
			    }
				if(dict['std_frm_id'] == 1 && dict['std_to_id'] != 1)
				{	
				 	alert("Please Select From TIME for "+alert_type_second+"");
				 	$(this).find('.std_frm_id').focus();				 	
		  			document.getElementById("check_value").value = 1;
				 	return false;
				}
				if(dict['std_frm_id'] != 1 && dict['std_to_id'] == 1)
				{	
				 	alert("Please Select To TIME for "+alert_type_second+"");
				 	$(this).find('.std_to_id').focus();				 	
		  			document.getElementById("check_value").value = 1;
				 	return false;
				}
				if(dict['pre_frm_id'] == 1 && dict['pre_to_id'] != 1)
				{
				 	alert("Please Select From TIME for "+alert_type_third+"");	
				 	$(this).find('.pre_frm_id').focus();			 	
		  			document.getElementById("check_value").value = 1;
				 	return false;
				}
				if(dict['pre_frm_id'] != 1 && dict['pre_to_id'] == 1)
				{
				 	alert("Please Select To TIME for "+alert_type_third+"");	
				 	$(this).find('.pre_to_id').focus();			 	
		  			document.getElementById("check_value").value = 1;
				 	return false;
				}
		        var numbers = /^[-+]?[0-9]+$/;  
		        if(covers == undefined)
		        {
		        	return;
		        }
				if(!cap.match(numbers))
        		{
		        	alert("Please enter number of max.covers");
		  			$(this).find(".max_covers").focus();
		  			$(this).find(".max_covers").select();
		  			return false;
		  		}
        		if(covers.match(numbers))
        		{
		        	dict['type'] 	   = $(this).find("#alloc_type").val();
			  		var db_id = $(this).find("#db_id").val();
			  		if (db_id == 'undefined')
			  		{
			  			db_id = 'create_'+(count++);
			  			$(this).find('#db_id').val(db_id);
			  		}
			  		vals[db_id] = dict;
		  		}
		  		else
		  		{
		  			alert("Please enter number of covers allotted");
		  			$(this).find(".alloc_covers").focus();
		  			$(this).find(".alloc_covers").select();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
			});
			var check_value = document.getElementById('check_value').value;
			if(check_value == 1)
			{
				$("#check_value").val('');
				return false;
			}
			else
			{
				openerp.jsonRpc("/website_capitalcentric/save_time_rec/", 'call', {'dict_time':vals,'type':alloc_type,'venue_id':parseInt(venue_id),'create_count':count,'chkwhich':'allocations'})
			  	.then(function (data)
			  	{	console.log('data',data);
				  	$('table#' + xmlid + ' tr:gt(0)').each(function()
			        {	
			        	db_value = data[$(this).find('#db_id').val()];
			        	if (db_value != undefined)
			        		$(this).find('#db_id').val(db_value);
			        	
			        });	
			        $("html, body").animate({
	            		scrollTop: 0
	        	  	}, 600);
			  		document.getElementById('save_prompt').innerHTML="Saved Successfully !!";
			        $("#save_prompt").stop(true,true).show().fadeOut(5000);
			 	});
			}
	    }
	     
//Save for black-out table
	    if(button_clk == 'bo_save')
        {
	    	$('table#blackout_table tr:gt(0)').each(function()
	        {   var dict={};         
	            dict['date'] 		 = $(this).find(".black_from_date").val();
	            dict['date_to']      = $(this).find(".black_to_date").val();
	            dict['name'] 		 = $(this).find(".black_desc").val();
	            dict['from_time_id'] = $(this).find(".black_from_time").val();
	        	dict['to_time_id'] 	 = $(this).find(".black_to_time").val();
		  		var db_id = $(this).find("#db_id").val();
		  		
		  		if(dict['date'] == '')
		  		{
		  			alert("Please Enter Date From");
		  			$(this).find(".black_from_date").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
		  		if(dict['date_to'] == '')
		  		{
		  			alert("Please Enter Date To");
		  			$(this).find(".black_to_date").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
		  		if (db_id == 'undefined')
		  		{
		  			db_id = 'create_'+(count++);
		  			$(this).find('#db_id').val(db_id);
		  		}
		  		vals[db_id] = dict;
			});
			// if(Object.keys(vals).length == 0)
			// {
				// alert("Please add a Black-out day and then click on Save Button");
				// document.getElementById("check_value").value = 1;
			// }
			var check_value = document.getElementById('check_value').value;
			if(check_value == 1)
			{
				$("#check_value").val('');
				return false;
			}
			else
			{
				openerp.jsonRpc("/website_capitalcentric/save_time_rec/", 'call', {'dict_time':vals,'type':'','venue_id':parseInt(venue_id),'create_count':count,'chkwhich':'black_out'})
			  	.then(function (data)
			  	{	console.log('data',data);
				  	$('table#break_fast_table tr:gt(0)').each(function()
			        {	
			        	db_value = data[$(this).find('#db_id').val()];
			        	if (db_value != undefined)
			        		$(this).find('#db_id').val(db_value);
			        	
			        });	
			        $("html, body").animate({
            		scrollTop: 0
        	  		}, 600);
			  		document.getElementById('save_prompt').innerHTML="Saved Successfully !!";
			        $("#save_prompt").stop(true,true).show().fadeOut(5000);
			 	});
			   }
		   }
		
//Save for drinks table
	    if(button_clk == 'drink_save')
        {
	    	$('table#drinks_table tr:gt(0)').each(function()
	        {   var dict={};         
	            dict['name'] 		 	= 	$(this).find(".drink_name").val();
	            dict['description']  	= 	$(this).find(".drink_desc").val();
	            dict['drink_size']   	= 	$(this).find(".drink_size").val();
	            dict['sc_included']  	= 	$(this).find(".sc_included_drink").val();
	            dict['service_charge']  = 	$(this).find(".sc_per_drink").val();
	            dict['rest_price']   	= 	$(this).find(".drink_price").val();
	            dict['food_type']	 	=	'drink';
	        	
	        	if ($(this).find(".menu_status").val() == 'False')
                	dict['active'] = false;
                else 
                	dict['active'] = true;
                	
		  		var db_id = $(this).find("#db_id").val();
		  		if(dict['name'] == '')
		  		{
		  			alert("Please Enter a Drink");
		  			$(this).find(".drink_name").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
				if(dict['rest_price'] == '')
				{
					dict['rest_price'] = '0.00';
				}
				if((dict['service_charge'] == '' || dict['service_charge'] <= 0.00) && dict['sc_included'] == 'False')
				{
					alert("Please enter service charge");
					$(this).find(".sc_per_drink").focus();
					document.getElementById("check_value").value = 1;
					return false;
				}
		  		if (db_id == 'undefined')
		  		{
		  			db_id = 'create_'+(count++);
		  			$(this).find('#db_id').val(db_id);
		  		}
		  		vals[db_id] = dict;
			});
			var check_value = document.getElementById('check_value').value;
			if(check_value == 1)
			{
				$("#check_value").val(''); 
				return false;
			}
			else
			{
				openerp.jsonRpc("/website_capitalcentric/save_time_rec/", 'call', {'dict_time':vals,'type':'','venue_id':parseInt(venue_id),'create_count':count,'chkwhich':'drinks'})
			  	.then(function (data)
			  	{	
				  	$('table#drinks_table tr:gt(0)').each(function()
			        {	
			        	db_value = data[$(this).find('#db_id').val()];
			        	if (db_value != undefined)
			        		$(this).find('#db_id').val(db_value);
			        	
			        });	
			        $("html, body").animate({
            			scrollTop: 0
    	  			}, 600);
			  		document.getElementById('save_prompt').innerHTML="Saved Successfully!!";
			        $("#save_prompt").stop(true,true).show().fadeOut(5000);
			 	});
		     }
		}
		
//Save for Private Room table
	    if(button_clk == 'pvt_room_save')
        {
	    	$('table#pvt_room_table tr:gt(0)').each(function()
	        {   var dict={};         
	            dict['name'] 		   = $(this).find(".pvt_room_name").val();
	            dict['no_of_seated']   = $(this).find(".covers_seated").val();
	            dict['no_of_standing'] = $(this).find(".covers_standing").val();
	            dict['max_nos']   	   = $(this).find(".max_no").val();
	            dict['av_screen']      = $(this).find(".av_screen").val();
	        	dict['projector'] 	   = $(this).find(".projector").val();
	        	dict['others'] 	   	   = $(this).find(".others").val();
		  		var db_id = $(this).find("#db_id").val();
		  		if(dict['name'] == '')
		  		{
		  			alert("Please Enter a Private Room Name");
		  			$(this).find(".pvt_room_name").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
		  		// console.log(dict['no_of_seated']);
		  		// var numbers = /^[-+]?[0-9]+$/;
		  		// if(Number.isInteger(dict['no_of_seated']))
		  		// {
		  			// alert("Please Enter a Number");
		  			// $(this).find(".covers_seated").focus();
		  			// document.getElementById("check_value").value = 1;
		  			// return false;
		  		// }
		  		
		  		if (db_id == 'undefined')
		  		{
		  			db_id = 'create_'+(count++);
		  			$(this).find('#db_id').val(db_id);
		  		}
		  		vals[db_id] = dict;
			});
			var check_value = document.getElementById('check_value').value;
			if(check_value == 1)
			{
				$("#check_value").val('');
				return false;
			}
			else
			{
				openerp.jsonRpc("/website_capitalcentric/save_time_rec/", 'call', {'dict_time':vals,'type':'','venue_id':parseInt(venue_id),'create_count':count,'chkwhich':'private_room'})
			  	.then(function (data)
			  	{	console.log('data',data);
				  	$('table#pvt_room_table tr:gt(0)').each(function()
			        {	
			        	db_value = data[$(this).find('#db_id').val()];
			        	if (db_value != undefined)
			        		$(this).find('#db_id').val(db_value);
			        	
			        });	
			        $("html, body").animate({
            		scrollTop: 0
        	  		}, 600);
			  		document.getElementById('save_prompt').innerHTML="Saved Successfully !!";
			        $("#save_prompt").stop(true,true).show().fadeOut(5000);
			 	});
			  }
		   }
		
//Save for Events Menu table
	    if(button_clk == 'events_menu_save')
        {	
        	$("#dvLoading").show();
	    	$('table#events_menu_table tr:gt(0)').each(function()
	        {   var dict={};         
	        	dict['break_fast']    	 =  $(this).find("#break_fast").is(':checked');;
	        	dict['lunch'] 		  	 =  $(this).find("#lunch").is(':checked');
                dict['afternoon_tea'] 	 =  $(this).find("#afternoon_tea").is(':checked');
                dict['dinner'] 		     =  $(this).find("#dinner").is(':checked');
                dict['kids_menu'] 		 =  $(this).find("#kids_menu").is(':checked');
	            dict['name'] 		 	 = 	$(this).find(".drink_name").val();
	            dict['description']  	 = 	$(this).find(".drink_desc").val();
	            dict['sc_included']  	 = 	$(this).find(".sc_included_drink").val();
	            dict['service_charge']   = 	$(this).find(".sc_per_drink").val();
	            dict['rest_price']   	 = 	$(this).find(".drink_price").val();
	            dict['food_type']	 	 =	'events';
	        	
	        	if ($(this).find(".menu_status").val() == 'False')
                	dict['active'] = false;
                else 
                	dict['active'] = true;
                	
		  		var db_id = $(this).find("#db_id").val();
		  		if(dict['name'] == '')
		  		{
		  			$("#dvLoading").hide();
		  			alert("Please Enter an Events Menu Name");
		  			$(this).find(".drink_name").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
				if(dict['rest_price'] == '')
				{
					dict['rest_price'] = '0.00';
				}
				if((dict['service_charge'] == '' || dict['service_charge'] <= 0.00) && dict['sc_included'] == 'False')
				{
					$("#dvLoading").hide();
					alert("Please enter service charge");
					$(this).find(".sc_per_drink").focus();
					document.getElementById("check_value").value = 1;
					return false;
				}
		  		if (db_id == 'undefined')
		  		{
		  			db_id = 'create_'+(count++);
		  			$(this).find('#db_id').val(db_id);
		  		}
		  		vals[db_id] = dict;
			});
			var check_value = document.getElementById('check_value').value;
			if(check_value == 1)
			{
				$("#check_value").val(''); 
				return false;
			}
			else
			{
				openerp.jsonRpc("/website_capitalcentric/save_time_rec/", 'call', {'dict_time':vals,'type':'','venue_id':parseInt(venue_id),'create_count':count,'chkwhich':'events_menu'})
			  	.then(function (data)
			  	{	console.log('data',data);
				  	$('table#events_menu_table tr:gt(0)').each(function()
			        {	
			        	db_value = data[$(this).find('#db_id').val()];
			        	if (db_value != undefined)
			        		$(this).find('#db_id').val(db_value);
			        	
			        });	
			        // $("html, body").animate({
            			// scrollTop: 0
    	  			// }, 600);
			  		// document.getElementById('save_prompt').innerHTML="Saved Successfully!!";
			        // $("#save_prompt").stop(true,true).show().fadeOut(5000);
			        window.location.href = "/capital_centric/profile/restaurant/edit_restaurant/"+parseInt(venue_id)+"/events?chk_wch=events"; 
			 	});
		     }
		}
		
//Save for Events table
	    if(button_clk == 'event_save')
        {
	    	$('table#events_table tr:gt(0)').each(function()
	        {   var dict={};         
	            dict['name'] 		 	= 	$(this).find(".drink_name").val();
	            dict['description']  	= 	$(this).find(".drink_desc").val();
                dict['date_from'] 		= 	$(this).find(".black_from_date").val();
	            dict['date_to']      	= 	$(this).find(".black_to_date").val();
	        	dict['bt_from'] 	 	= 	$(this).find("#bf_time_frm").val();
	        	dict['bt_to'] 	 	    = 	$(this).find("#bf_time_to").val();
        	    dict['lt_from'] 	 	= 	$(this).find("#l_time_frm").val();
	        	dict['lt_to'] 	 	    = 	$(this).find("#l_time_to").val();
	        	dict['att_from'] 	 	= 	$(this).find("#at_time_frm").val();
	        	dict['att_to'] 	 	    = 	$(this).find("#at_time_to").val();
	        	dict['dt_from'] 	 	= 	$(this).find("#d_time_frm").val();
	        	dict['dt_to'] 	 	    = 	$(this).find("#d_time_to").val();
	        	dict['covers'] 		 	= 	$(this).find(".alloc_covers").val();
	        	dict['menu_ids']  		=   $(this).find("#event_menu_ids").val();
	        	
	        	if ($(this).find(".menu_status").val() == 'False')
                	dict['active'] = false;
                else 
                	dict['active'] = true;
                	
		  		db_id = $(this).find("#db_id").val();
		  		if(dict['name'] == '')
		  		{
		  			alert("Please Enter an Events Name");
		  			$(this).find(".drink_name").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
		  		if(dict['date_from'] == '')
		  		{
		  			alert("Please Enter Date From");
		  			$(this).find(".black_from_date").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
		  		if(dict['date_to'] == '')
		  		{
		  			alert("Please Enter Date To");
		  			$(this).find(".black_to_date").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
		  		if (db_id == 'undefined')
		  		{
		  			db_id = 'create_'+(count++);
		  			$(this).find('#db_id').val(db_id);
		  		}
		  		vals[db_id] = dict;
			});
			var check_value = document.getElementById('check_value').value;
			if(check_value == 1)
			{
				$("#check_value").val(''); 
				return false;
			}
			else
			{
				openerp.jsonRpc("/website_capitalcentric/save_time_rec/", 'call', {'dict_time':vals,'type':'','venue_id':parseInt(venue_id),'create_count':count,'chkwhich':'events'})
			  	.then(function (data)
			  	{	console.log('data',data);
				  	$('table#events_table tr:gt(0)').each(function()
			        {	
			        	db_value = data[$(this).find('#db_id').val()];
			        	if (db_value != undefined)
			        		$(this).find('#db_id').val(db_value);
			        	
			        });	
			        $("html, body").animate({
            			scrollTop: 0
    	  			}, 600);
			  		document.getElementById('save_prompt').innerHTML="Saved Successfully!!";
			        $("#save_prompt").stop(true,true).show().fadeOut(5000);
			 	});
		     }
		}
		
		
//save for menus table
	    if(button_clk == 'menu_save' || button_clk == 'menu_save_group')
        {
        	$("#dvLoading").show();
	    	$('table#menu_table tr:gt(0)').each(function()
	        {   var dict={};         
		        dict['name']          = $(this).find(".menu_name").val();
	            dict['description']   = $(this).find(".menu_desc").val();	            
	            dict['break_fast']    = $(this).find("#break_fast").is(':checked');;
	        	dict['lunch'] 		  = $(this).find("#lunch").is(':checked');
	        	if(button_clk == 'menu_save')
	        	{
	        		dict['afternoon_tea'] = $(this).find("#afternoon_tea").is(':checked');	
	        	}
	        	if(button_clk == 'menu_save_group')
	        	{
	        		dict['afternoon_tea'] 	= 'False';
	        		dict['sc_included']   	=  $('select[name="sc_included"]').val();
	        		if(dict['sc_included'] == '')
	        		{
	        			dict['sc_included']   	=  'False';
	        		}
	        		dict['service_charge']  =  $('input[name="menu_sc"]').val();	
	        	}
                dict['dinner'] 		  = $(this).find("#dinner").is(':checked');
                dict['kids_menu'] 	  = $(this).find("#kids_menu").is(':checked');
                dict['course']		  = $(this).find(".menu_course").val();
                dict['min_covers']    = $(this).find(".min_covers").val();
                dict['food_type']	  = 'meal';
                
                if(button_clk == 'menu_save_group')
                {
                	dict['rest_price']  =  $(this).find(".rest_price").val();
                	if(dict['rest_price'] == '')
					{
						dict['rest_price'] = '0.00';
					}
                }
               
                if ($(this).find(".menu_status").val() == 'False')
                	dict['active'] = false;
                else 
                	dict['active'] = true;
                // dict['cc_fit'] 		  = 'fit';	
                
                if(dict['name'] == '')
		  		{
		  			$("#dvLoading").hide();
		  			alert("Please Enter Menu Name");
		  			$(this).find(".menu_name").focus();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
		  		
		  		var numbers = /^[-+]?[0-9]+$/;  
		        if(dict['min_covers'] == undefined)
		        {
		        	return;
		        }
        		if(dict['min_covers'].match(numbers) && dict['min_covers'] != 0)
        		{
	        		var db_id = $(this).find("#db_id").val();
			  		if (db_id == 'undefined')
			  		{
			  			db_id = 'create_'+(count++);
			  			$(this).find('#db_id').val(db_id);
			  		}
			  		vals[db_id] = dict;
		  		}
		  		else
		  		{
		  			$("#dvLoading").hide();
		  			alert("Please Enter Min. Covers as numbers greater than 0");
		  			$(this).find(".min_covers").focus();
		  			$(this).find(".min_covers").select();
		  			document.getElementById("check_value").value = 1;
		  			return false;
		  		}
			});
			
			var check_value = document.getElementById('check_value').value;
			if(check_value == 1)
			{
				$("#check_value").val(''); 
				return false;
			}
			else
			{
				openerp.jsonRpc("/website_capitalcentric/save_time_rec/", 'call', {'dict_time':vals,'type':'','venue_id':parseInt(venue_id),'create_count':count,'chkwhich':'menu'})
			  	.then(function (data)
			  	{	
				  	$('table#menu_table tr:gt(0)').each(function()
			        {	
			        	db_value = data[$(this).find('#db_id').val()];
			        	if (db_value != undefined)
			        		$(this).find('#db_id').val(db_value);
			        	
			        });	
			        window.location.href = "/capital_centric/profile/restaurant/edit_restaurant/"+parseInt(venue_id)+"/menu?chk_wch=save";
			 	});
		    }
		}
	});
	
	
// On Change of Input fields in time & allocations...
	$(".alloc_data").on('change','.alloc_from_time',function()
	{	
		var title 		= $(this).attr('title');
		var id_name 	= $(this).attr('id');
		var id 			= $(this).closest("tr");
		var non_frm 	= parseInt(id.find(".non_frm_id").val());
		var non_to 		= parseInt(id.find(".non_to_id").val());
	    var std_frm 	= parseInt(id.find(".std_frm_id").val());
		var std_to 		= parseInt(id.find(".std_to_id").val());
		var pre_frm 	= parseInt(id.find(".pre_frm_id").val());
		var pre_to 		= parseInt(id.find(".pre_to_id").val());
		
		var non_arr = [];
		for(var n=non_frm;n<non_to;n++)
		{	
			non_arr.push(parseInt(n));
		}
		var std_arr = [];
		for( var i=std_frm;i<std_to;i++)
		{
			std_arr.push(parseInt(i));
		}	
		var pre_arr = [];
		for( var i= pre_frm;i<pre_to;i++)
		{
			pre_arr.push(parseInt(i));
		}
		if(title == 'Non-Premium From' || title == 'B/F From')
		{
			var focus_title = ".non_frm_id";
			var x = (this.value >= std_frm && this.value < std_to || this.value >= pre_frm && this.value < pre_to);
			if(non_frm != 1)
			{
				if( x === false)
				{	
					for (var i = 0; i < std_arr.length; i++) {
					    if (non_arr.indexOf(std_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
					for (var i = 0; i < pre_arr.length; i++) {
					    if (non_arr.indexOf(pre_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
				}
			}
		}
		if(title == 'Non-Premium To' || title == 'B/F To')
		{
			var focus_title = ".non_to_id";
			var x = (this.value > std_frm && this.value <= std_to || this.value > pre_frm && this.value <= pre_to);
			if(non_frm != 1)
			{
				if( x === false)
				{	
					for (var i = 0; i < std_arr.length; i++) {
					    if (non_arr.indexOf(std_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
					for (var i = 0; i < pre_arr.length; i++) {
					    if (non_arr.indexOf(pre_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
				}
			}
		}
		if(title == 'Standard From' || title == 'Lunch From')
		{
			var focus_title = ".std_frm_id";
			var x = (this.value >= non_frm && this.value < non_to || this.value >= pre_frm && this.value < pre_to);
			if(std_frm != 1)
			{
				if( x === false)
				{	
					for (var i = 0; i < non_arr.length; i++) {
					    if (std_arr.indexOf(non_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
					for (var i = 0; i < pre_arr.length; i++) {
					    if (std_arr.indexOf(pre_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
				}
			}
		}
		if(title == 'Standard To' || title == 'Lunch To')
		{
			var focus_title = ".std_to_id";
			var x = (this.value > non_frm && this.value <= non_to || this.value > pre_frm && this.value <= pre_to);
			if(std_frm != 1)
			{
				if( x === false)
				{	
					for (var i = 0; i < non_arr.length; i++) {
					    if (std_arr.indexOf(non_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
					for (var i = 0; i < pre_arr.length; i++) {
					    if (std_arr.indexOf(pre_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
				}
			}
		}
		if(title == 'Premium From' || title == 'Dinner From')
		{
			var focus_title = ".pre_frm_id";
			var x = (this.value >= non_frm && this.value < non_to || this.value >= std_frm && this.value < std_to);
			if(pre_frm != 1)
			{
				if( x === false)
				{	
					for (var i = 0; i < non_arr.length; i++) 
					{
						    if (pre_arr.indexOf(non_arr[i]) > -1) 
						    {
						        x = true;
						        break;
						    }
					}
					for (var i = 0; i <std_arr.length; i++) 
					{
					    if (pre_arr.indexOf(std_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
				}
			}
		}
		if(title == 'Premium To' || title == 'Dinner To')
		{
			var focus_title = ".pre_to_id";
			var x = (this.value > non_frm && this.value <= non_to || this.value > std_frm && this.value <= std_to);
			if(pre_frm != 1)
			{
				if( x === false)
				{	
					for (var i = 0; i < non_arr.length; i++) 
					{
						    if (pre_arr.indexOf(non_arr[i]) > -1) 
						    {
						        x = true;
						        break;
						    }
					}
					for (var i = 0; i <std_arr.length; i++) 
					{
					    if (pre_arr.indexOf(std_arr[i]) > -1) 
					    {
					        x = true;
					        break;
					    }
					}
				}
			}
		}
		if(x)
		{	
			alert("Time chosen by you is conflicting with other slot.Please Check");
			id.find(focus_title).focus();
			id.find(focus_title).val('');
			return;
		}
	});

//Check on restaurant name if special char entered	
	$('#required_name').on('blur',function()
	{
		var str = this.value;
		if(/^[a-zA-Z0-9-,' ]*$/.test(str) == false) 
		{
	    	fader = document.getElementById('login_fader');
	    	login_box = document.getElementById('restdiv1');
	    	fader.style.display = "block";
	        $("#restdiv1").show();
		}
		return true;
	});
	
// On click of cancel button pop up
	$('.cancel_button').on('click',function()
	{
			$("#restdiv1").hide();
			fader.style.display = "none";
			$("#required_name").focus();
    });	
});

function get_eventvalues(e)  
 {  
 	 p_id = $($(e).parent()).parent();                        
     var opt = p_id.find("#event_menu");
     var no_of_opt = opt[0].length;
     var selValue = new Array;
     var j = 0;  
     for (i=0; i < no_of_opt;i++)  
     {  
     if (opt[0][i].selected === true)  
     {  
         selValue[j] = parseInt(opt[0][i].value) ;
         j++  ;
     }  
     }                       
    p_id.find("#event_menu_ids").text("[" + selValue + "]")  ;
 } 