// $(document).ready(function () 
// {
// 	
	// $("select").css("background-color","white");
	// $("select").css("color","black");
	// $("input[name='operator']").hide();
	// $(".hidden").hide();
// 	
	// if($.browser.mozilla) 
   	// {
        // $('select.input-control').css( "padding-top","2px" );
   	// };
// 	
// 
    // $("select[name='Country']").change(function () { 
		    // $("select[name='State']").removeAttr('disabled').css("background-color", "white");
		   	// $('#con_state').empty().append('<option value="">Select County..</option>');
			// // alert(this.value);
		    // countryname = this.value;
// 			
			// openerp.jsonRpc("/fit_website/state_json/", 'call', {'country': parseInt(countryname)})
	            // .then(function (data) {
	                // // console.log('state',data[0]);
					// // console.log('state Length',data[0].length);	                	                
				    // for(var i=0; i<data[0].length; i++)
				    // {
				    // //console.log('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');	
			        // $('#con_state').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
				    // }
	            // });
	// });
// 	
// 	
	// $("select[name='State']").change(function () 
	  // {  
	   	// $('#con_city').empty().append('<option value="">Select City..</option>');
	    // state = this.value;
		// openerp.jsonRpc("/fit_website/city_json/", 'call', {'state': parseInt(state)})
            // .then(function (data) {            	
			    // for(var i=0; i<data[0].length; i++)
				    // {	
			        // $('#con_city').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
				    // }
            // });
       // });
//        
       // $("select[name='City']").change(function () 
	  // { 
	   	// $('#con_location').empty().append('<option value="">Select Location..</option>');
	    // city = this.value;
		// openerp.jsonRpc("/fit_website/location_json/", 'call', {'city': parseInt(city),'value': 'city_clicked' })
            // .then(function (data) {
			    // for(var i=0; i<data[0].length; i++)
				    // {	
			        // $('#con_location').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
				    // }
            // });
       // });
//        
       // $("select[name='Location']").change(function () 
	  // { 
	   	// $('#post_code').empty();
	    // city = this.value;
		// openerp.jsonRpc("/fit_website/location_json/", 'call', {'city': parseInt(city),'value': 'location_clicked' })
            // .then(function (data)
            // {
				// $('#post_code').val(data);            	
	        // });
       // });
//     
//      
//      
     // $("#venue_email").blur(function()
     // {
     	// var e = $(this).val();
//      	
        // $("#venue_email").focus(function()
     	// {
     		// console.log("focus");
     		// $("#venue_email").css("border","2px solid #ad4bc2");
     	// });
//      	
     	// if(e.length > 0)
     	// {
     		// console.log("length");
     		// $("#venue_email").css("border","2px solid #CCC");
     		// document.getElementById('email_id').innerHTML="";
     		// document.getElementById('email').value = e;
     	// }
     	// else
     	// {
     		 // console.log("No length");
     		 // $("#venue_email").css("border","2px solid #c00000");
     		 // document.getElementById('email_id').innerHTML="Please Enter an Email!!";
     	// }
//      	
//      	
     // }); 
//      
     // $("#venue_cemail").bind('blur', function() 
     // {
     	// var confirm_email = $(this).val();
     	// var c_email = document.getElementById('email').value;
     	// $("#venue_cemail").focus(function()
     	// {
     		// console.log("focus");
     		// $("#venue_cemail").css("border","2px solid #ad4bc2");
     	// });
     	// if(confirm_email.length > 0)
     	// {
     		// document.getElementById('email_c_id').innerHTML="";
     		// if(c_email != confirm_email)
	     	// {
	     		// $("#venue_email").css('border','2px solid #c00000');
	     		// $("#venue_cemail").css('border','2px solid #c00000');
	     		// document.getElementById('email_c_id').innerHTML="Emails Do not Match";
	 		    // return;
	     	// }
// 	     	
	     	// else
	     	// {
	     		// openerp.jsonRpc("/fit_website/check_email/", 'call', {'email': $(this).val()})
	     	 	// .then(function(data)
	     	 	// {	
	     	 		// if(data == true)
	     	 		// {    
	     	 		    // $("#venue_email").css('border','2px solid #c00000');
	     				// $("#venue_cemail").css('border','2px solid #c00000');
	     	 		    // document.getElementById('email_c_id').innerHTML="Someone already has this email.Please Try another!!";
// 	     	 		    
// 	     	 		   
	     	 		    // return;
	     	 		// }
	     	 		// else
	     	 		// {
	     	 			 // $("#venue_cemail").css("border","2px solid #CCC");
	     	 			 // $("#venue_email").css("border","2px solid #CCC");
	     	 		// }
	     	 	// });
	     	// }
// 	     	
     	// }
     	// else
     	// {
     		 // $("#venue_cemail").css("border","2px solid #c00000");
     		 // document.getElementById('email_c_id').innerHTML="Please Enter an Email!!";
     	// }
//      	
     // });
//      
     // $("#venue_password").blur(function()
     // {
     	// var p = $(this).val();
     	// // if(p == '')
     	// // {
     		// // document.getElementById('first_password').innerHTML="Please Enter a Password";
     		// // $('#venue_password').focus();
     		// // return;
     	// // }
     	 // $("#venue_password").focus(function()
     	// {
     		// console.log("focus");
     		// $("#venue_password").css("border","2px solid #ad4bc2");
     	// });
     	// if(p.length > 0)
     	// {
     		// console.log("length");
     		// $("#venue_password").css("border","2px solid #CCC");
     		// document.getElementById('first_password').innerHTML="";
     		// document.getElementById('password').value = p;
     	// }
     	// else
     	// {
     		 // console.log("No length");
     		 // $("#venue_password").css("border","2px solid #c00000");
     		 // document.getElementById('first_password').innerHTML="Please Enter a Password!!";
     	// }
     // });
//      
     // $("#venue_cpassword").blur(function()
     // {
     	// var confirm_p = $(this).val();
     	// var c_p = document.getElementById('password').value;
     	// $("#venue_cpassword").focus(function()
     	// {
     		// console.log("focus");
     		// $("#venue_cpassword").css("border","2px solid #ad4bc2");
     	// });
     	// if(confirm_p.length > 0)
     	// {
	     	// if(c_p != confirm_p)
	     	// {
	     		// document.getElementById('c_password').innerHTML="Passwords Do not Match";
	     		// $("#venue_password").css('border','2px solid #c00000');
	     	    // $("#venue_cpassword").css('border','2px solid #c00000');
	 		    // return;
	     	// }
	     	// else
	     	// {
	     		// $("#venue_password").css("border","2px solid #CCC");
	     	    // $("#venue_cpassword").css("border","2px solid #CCC");
	     	    // document.getElementById('c_password').innerHTML="";
	     	// }
     	// }
     	// else
     	// {
     		// $("#venue_cpassword").css("border","2px solid #c00000");
     		 // document.getElementById('c_password').innerHTML="Please Enter a Password!!";
     	// }
     // });
//      
//      
     // $('#reset_button').click(function()
     // {
     	// document.getElementById('c_password').innerHTML ='';
     	// document.getElementById('first_password').innerHTML="";
     	// document.getElementById('email_c_id').innerHTML ='';
     // });
// });