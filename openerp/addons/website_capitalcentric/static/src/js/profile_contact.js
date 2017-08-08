$(document).ready(function () 
{
	// $("select").css("background-color", "white");
	$('select').css("color","black");
	// $('input').css("color","black");
	// $('input').css("background-color","white");
	$(".hidden").hide();
	$('div[id="contactbutton"]').addClass('color');
	$('#second_bookingline').hide();
	$('#plz_select_res').hide();
	$('#sel_usr_role').hide();
	$('#cont_button').addClass("button_common");
	$('#1').css('display','block');	
	$('#cont_psswd').hide();
	
   	// if($.browser.msie) 
    // {
        // $('table').css("table-layout","auto");
    // };
    
    $('#chng_pswrd').on('click',function()
    {
        fader = document.getElementById('login_fader');
        login_box = document.getElementById('ch_pswrd');
        fader.style.display = "block";
        login_box.style.display = "block";
        $("#ch_pswrd").show();
        // document.getElementById("BuyForm").reset();
		$('input[name="chnge_pswrd"]').prop('required',true);
        $('input[name="chnge_pswrd"]').val('');
    });
    
    $(".common_button").click(function() 
    { 	  
      var id = $(this).attr('id');
      $(this).addClass('button_common');
      if(id == 'cont_button') 
      {
      	$('#cust_button').removeClass("button_common");
      	$('#2').css('display','none');
      	$('#1').css('display','block');
      }
      else
      {
      	$('#cont_button').removeClass("button_common");
      	$('#1').css('display','none');
      	$('#2').css('display','block');
      }
    });
	
	$("select[name='Country']").change(function () 
	{		    
	   	// $('#con_city').empty().append('<option value="">Select City ..</option>');
	   	// $('#con_location').empty().append('<option value="">Select Location ..</option>');
   		$('#con_state').empty();
	   	$('#con_state').append('<option value="">Select a county ..</option>');
		// alert(this.value);
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
		
		
		  $("select[name='State']").change(function () 
		  {  
		   	$('#con_city').empty().append('<option value="">Select City ..</option>');
		    state = this.value;
			openerp.jsonRpc("/website_capitalcentric/city_json/", 'call', {'state': parseInt(state)})
	            .then(function (data) {            	
				    for(var i=0; i<data[0].length; i++)
					    {	
				        $('#con_city').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
					    }
	            }); 
	       });
	       
	      $("select[name='City']").change(function () 
		  { 
		   	$('#con_location').empty().append('<option value="">Select Location..</option>');
		    city = this.value;
			openerp.jsonRpc("/website_capitalcentric/location_json/", 'call', {'city': parseInt(city),'value': 'city_clicked' })
	            .then(function (data) {
				    for(var i=0; i<data[0].length; i++)
					    {	
				        $('#con_location').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
					    }
	            });
	       });
	       
	      $("select[name='Location']").change(function () 
		  { 
		   	$('#post_code').empty();
		    city = this.value;
			openerp.jsonRpc("/website_capitalcentric/location_json/", 'call', {'city': parseInt(city),'value': 'location_clicked' })
	            .then(function (data)
	            {
					$('#con_zip').val(data);            	
		        });
	       });
		
		$('.checkbox').on("click", function() {
			
	    	if ($(this).prop("checked")) 
	    	{
				openerp.jsonRpc("/website_capitalcentric/address_json/", 'call')
				.then(function(data)
				{
				   for(var i = 0;i<data.length;i++)
				   {
				   		console.log(data[i]);
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
				   			console.log(countryname);
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
				   		if(i == 5)
				   		{ 
				   			cityname = data[i-1];
				   			var location = data[i];
				   			$('#con_location').empty().append('<option value="">Select Location ..</option>');
				   			openerp.jsonRpc("/website_capitalcentric/location_json/", 'call', {'city': cityname, 'value':'city_clicked'})
		                    .then(function (data) 
		                    {
						    	for(var i=0; i<data[0].length; i++)
						    	{
						         	$('#con_location').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
						         	$("#con_location").find("option").each(function()
				 		  			{ 
					      				if( $(this).val() == location ) 
				     		 			{
						         	 		$(this).attr("selected","selected");
				     		 			}
			                		});
				   			
				   				}
						 	});
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
		
		console.log($("#user_role").val());
		if(($("#user_role").val() == 'client_user') || ($("#user_role").val() == 'venue_user'))
		{
			$('#res_td').removeClass('hidden');
			$('.ui-multiselect-menu').outerWidth($('.ui-multiselect').outerWidth());
			$('#res_label').show();
			
		}
		else
		{
			// $('.res_con_contact').hide();
			$('#res_td').addClass('hidden');
			$('#res_label').hide();
			$('#plz_select_res').hide(); 
		}
		
		$('.checkbox_edit').on("click", function()
		{
			
	    	if ($(this).prop("checked")) 
	    	{
				openerp.jsonRpc("/website_capitalcentric/address_json/", 'call')
				.then(function(data)
				{
				   for(var i = 0;i<data.length;i++)
				   {
				   		console.log(data[i]);
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
				   		if(i == 5)
				   		{ 
				   			cityname = data[i-1];
				   			var location = data[i];
				   			$('#con_location').empty().append('<option value="">Select Location ..</option>');
				   			openerp.jsonRpc("/website_capitalcentric/location_json/", 'call', {'city': cityname,'value':'city_clicked'})
		                    .then(function (data) 
		                    {
			            		
						    	for(var i=0; i<data[0].length; i++)
						    	{
						         	$('#con_location').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
						         	$("#con_location").find("option").each(function()
				 		  			{ 
					      				if( $(this).val() == location ) 
				     		 			{
						         	 		$(this).attr("selected","selected");
				     		 			}
			                		});
				   			
				   				}
						 	});
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
			   var partner_id = parseInt(document.getElementById("partnerid").innerHTML);
			   console.log(partner_id);
			   openerp.jsonRpc("/website_capitalcentric/existing_address_json/", 'call',{'partner_id':partner_id})
				.then(function(data)
				{
				   for(var i = 0;i<data.length;i++)
				   {
				   		console.log(data[i]);
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
				   		if(i == 5)
				   		{ 
				   			cityname = data[i-1];
				   			console.log(cityname);
				   			var location = data[i];
				   			$('#con_location').empty().append('<option value="">Select Location ..</option>');
				   			openerp.jsonRpc("/website_capitalcentric/location_json/", 'call', {'city': cityname,'value':'city_clicked'})
		                    .then(function (data) 
		                    {
			            		
						    	for(var i=0; i<data[0].length; i++)
						    	{
						         	$('#con_location').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
						         	$("#con_location").find("option").each(function()
				 		  			{ 
					      				if( $(this).val() == location ) 
				     		 			{
						         	 		$(this).attr("selected","selected");
				     		 			}
			                		});
				   				}
						 	});
				   		}
				   		if(i == 6)
				   		{ 
				   			$("#con_zip").val(data[i]);
				   		}
			   	   } 	
					
				});
			}
	 	});


    $('.button').click(function()
    {
    	$("#save").val($(this).attr('id'));
    	var role_sel = document.getElementById('user_role');
  		var role = role_sel.options[role_sel.selectedIndex].value;
    	if($(this).attr('id') == 'activate_user')
    	{
    		if($('input[name="type"]').val() == 'restaurant' && (role == 'client_user' || role == 'venue_user'))
	    	{
	    		console.log($('#txtEditions').text());
		    	if($('#res_con_contact option:selected').length == 0)
		    	{
			    		$('#res_con_contact').focus();
			    		console.log("entered if");
			    		$('#plz_select_res').show();
			    		return false;
		    	}
	    	}
	    	if (role == '')
	    	{
	    		$('#user_role').focus();
	    		$('#sel_usr_role').show();
	    		return false;
	    	}		
    	}
    });
    
  
    // $("input[name='email']").bind('blur', function() 
    // {
	    // openerp.jsonRpc("/website_capitalcentric/check_email/", 'call', {'value': $(this).val(), 'db_id' : parseInt($("#partner_id").val())})
	 	// .then(function(data)
	 	// {	
	 		// if(data == true)
	 		// {    
	 		    // $("input[name='email']").css('border','2px solid #c00000');
				// $("input[name='email']").css('border','2px solid #c00000');
	 		    // document.getElementById('email_error_line').innerHTML="Someone already has this email.Please Try another!!";
	 		    // document.getElementById("activate_user").disabled = true ;
	 		    // document.getElementById("deactivate_user").disabled = true ;
	 		    // $('.con_save').attr('disabled','disabled');
	 		    // document.getElementById("save_back").disabled = true ;
	 		    // $(".button").addClass('disabled');
	 		    // return false;
	 		// }
	 		// else
	 		// {
	 			 // $("input[name='email']").css("border","1px solid #CCC");
	 			 // $("input[name='email']").css("border","1px solid #CCC");
	 			 // document.getElementById('email_error_line').innerHTML = '';
	 			 // document.getElementById("activate_user").disabled = false ;
	 			 // document.getElementById("deactivate_user").disabled = false ;
	 			 // $('.con_save').removeAttr('disabled','disabled');
	 			 // document.getElementById("save_back").disabled = false ;
	 			 // $(".button").removeClass('disabled');
	 		// }
	 	// });
    // });
//     

 	$("#con_table").on('click','#db_delete',function(event)
     {
     	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").text();
	    var r=confirm("Are you sure you want to permanently delete this record?");
        if (r==true)
        {
	    	openerp.jsonRpc("/website_capitalcentric/delete_records/", 'call', {'value':'partner_table', 'db_id' : parseInt(db_id)})
	        .then(function (data) 
	        { 
	        	if(data == 'contact')
	         	{	
	         		$("html, body").animate({
            		scrollTop: 0
        	  	 	}, 600);
	         	 	document.getElementById('prompt_msg').innerHTML="Contact cannot Be Deleted!!";
				 	$("#prompt_msg").stop(true,true).show().fadeOut(5000);
	         	}
	         	else
	         	{
	         		id.remove();
	         		$("html, body").animate({
            		scrollTop: 0
        	  	 	}, 600);
	         	 	document.getElementById('prompt_msg').innerHTML="Contact Deleted !!";
				 	$("#prompt_msg").stop(true,true).show().fadeOut(5000);
	         	}
	        });
	    }
	});
});
function show_res_in_cont()  
{  
    var opt = document.getElementById("res_con_contact");
    var no_of_opt = opt.length;  
    var selValue = new Array;
    var j = 0;  
    for (i=0; i<no_of_opt;i++)  
    {  
	    if (opt[i].selected === true)  
	    {  
		    selValue[j] = parseInt(opt[i].value); 
		    j++;
	    }  
    }
    selValue = selValue.join(",");
    console.log('selValue',selValue);
    document.getElementById("txtEditions").innerHTML = selValue;  
}

function change_role()
{
	console.log($("textarea[name='res_cont_selected']").length);
	var role_sel = document.getElementById('user_role');
	var role = role_sel.options[role_sel.selectedIndex].value;
	if (role == 'venue_mng' || role == 'client_mng')
	{
		$('#res_td').addClass('hidden');
		$('#res_label').hide();
		$('#plz_select_res').hide(); 
		$('#cont_psswd').show();
		$('#contpasswd').attr('required', true);
	}
	else
	{
		console.log("Enetr");
		$('#res_td').removeClass('hidden');
		$('#res_td').removeAttr('style');
		$('#res_label').show();
		$('#plz_select_res').show();
		$('#cont_psswd').show(); 
		$('#contpasswd').attr('required', true);
		if($("textarea[name='res_cont_selected']").val() != 0)
		{
			$('#plz_select_res').hide();
		}
		$('.ui-multiselect-menu').outerWidth($('.ui-multiselect').outerWidth());
		// $('.ui-multiselect').show();
	}
	if (role == '')
	{
		$('#res_td').addClass('hidden');
		$('#cont_psswd').hide();		
		$('#contpasswd').attr('required', false);
		$('#res_label').hide();
		$('#sel_usr_role').show();
		$('#plz_select_res').hide(); 
		return false;
	}	
	$('#sel_usr_role').hide();
}