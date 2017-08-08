$(document).ready(function () 
{
	// if ($.browser.msie && $.browser.version < 10) {
	    // $('#form_to_validate [required]').addClass('required').removeAttr('required');
	// }
    // $(window).on('load', function(event)  
    // {
    	// if(window.event)
    	// {
			// console.log('window',window.event.target.URL,window.event.target.referrer);
			// openerp.jsonRpc("/fit_website/state_json/", 'call', {'country': 1})
			// .then(function (data) 
            // {	      
            // });
		// // if (window.event.target.URL == 'http://localhost:8069/' && window.event.target.URL != window.event.target.referrer)
		// // {
			// // window.location.replace(window.event.target.referrer);
		// // }          
    	// }
	// }); 
	
	
	// For White Labelling and Group Websites
	$('#myCarousel .item').each(function()
	{
  		  var next = $(this).next();
		  // if (!next.length) {
		    // next = $(this).siblings(':first');
		  // }
		  // next.children(':first-child').clone().appendTo($(this));
		  
		  if (next.next().length>0) 
		  {
		    next.next().children(':first-child').clone().appendTo($(this));
		  }
		  else 
		  {
		  	$(this).siblings(':first').children(':first-child').clone().appendTo($(this));
		  }
	});

	$("input[name='operator']").hide();
    $("select[name='Country']").change(function ()
    {  
		    // $("select[name='State']").removeAttr('disabled').css("background-color", "white");
		   	$('#con_state').empty();
	   	    $('#con_state').append('<option value="">Select a county ..</option>');
		    var countryname = this.value;
			openerp.jsonRpc("/fit_website/state_json/", 'call', {'country': parseInt(countryname)})
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
	
	$("#venue_name").blur(function()
    {
     	var e = $(this).val();
     	$("#venue_name").focus(function()
     	{
     		$("#venue_name").css("border","1px solid #ad4bc2");
     	});
     	if(e.length > 0)
     	{
     		$("#venue_name").css("border","1px solid #CCC");
     		document.getElementById('name_error').innerHTML="";
     		document.getElementById('name_error').value = e;
     	}
     	else
     	{
     		 $("#venue_name").css("border","2px solid #c00000");
     		 document.getElementById('name_error').innerHTML="Please Enter a Name!!";
     	}
     	
    });
     
    //$("#contact_name").blur(function()
    //{
    // 	var e = $(this).val();
    // 	$("#contact_name").focus(function()
    // 	{
    // 		$("#contact_name").css("border","1px solid #ad4bc2");
    // 	});
    // 	if(e.length > 0)
    // 	{
    // 		$("#contact_name").css("border","1px solid #CCC");
    // 		document.getElementById('cname_error').innerHTML="";
    // 		document.getElementById('cname_error').value = e;
    // 	}
    // 	else
    // 	{
    // 		 $("#contact_name").css("border","2px solid #c00000");
    // 		 document.getElementById('cname_error').innerHTML="Please Enter a Contact Name!!";
    // 	}
    // });
   
     $("#venue_email").blur(function()
     {
     	var e = $(this).val();
        $("#venue_email").focus(function()
     	{
     		$("#venue_email").css("border","1px solid #ad4bc2");
     	});
     	
     	if(e.length > 0)
     	{
     		$("#venue_email").css("border","1px solid #CCC");
     		document.getElementById('email_id').innerHTML="";
     		//document.getElementById('email').val(e);
			openerp.jsonRpc("/fit_website/check_email/", 'call', {'value': e,'db_id' :''})
			.then(function(data)
			{
				if(data == true)
				{
					$("#venue_email").css('border','2px solid #c00000');
					document.getElementById('email_id').innerHTML="Someone already has this email.Please Try another!!";
					$('#submit_button').attr('disabled','disabled');
				}
				else
				{
					 $("#venue_email").css("border","1px solid #CCC");
					 $('#submit_button').removeAttr('disabled');
				}
			});
     	}
     	else
     	{
     		 $("#venue_email").css("border","2px solid #c00000");
     		 document.getElementById('email_id').innerHTML="Please Enter an Email!!";
     	}
     }); 
     
     //$("#venue_cemail").bind('blur', function()
     //{
     //	var confirm_email = $(this).val();
     //	var c_email = document.getElementById('email').value;
     //	$("#venue_cemail").focus(function()
     //	{
     //		console.log("focus");
     //		$("#venue_cemail").css("border","1px solid #ad4bc2");
     //	});
     //	if(confirm_email.length > 0)
     //	{
     //		document.getElementById('email_c_id').innerHTML="";
     //		if(c_email != confirm_email)
	  //   	{
	  //   		$("#venue_email").css('border','2px solid #c00000');
	  //   		$("#venue_cemail").css('border','2px solid #c00000');
	  //   		document.getElementById('email_c_id').innerHTML="Emails Do not Match";
	 	//	    return;
	  //   	}
	  //
	  //   	else
	  //   	{
	  //
	  //   	}
	  //
     //	}
     //	else
     //	{
     //		 $("#venue_cemail").css("border","2px solid #c00000");
     //		 document.getElementById('email_c_id').innerHTML="Please Enter Confirm Email!!";
     //	}
     //
     //});
     
     $("#venue_password").blur(function()
     {
     	var p = $(this).val();
     	 if(p == '')
     	
     	 {
     		 document.getElementById('first_password').innerHTML="Please Enter a Password";
     		 $('#venue_password').focus();
     		 return;
     	 }
     	$("#venue_password").focus(function()
     	{
     		$("#venue_password").css("border","1px solid #ad4bc2");
     	});
     	if(p.length > 0)
     	{
     		$("#venue_password").css("border","1px solid #CCC");
     		document.getElementById('first_password').innerHTML="";
     		//document.getElementById('password').value = p;
     	}
     	else
     	{
     		 $("#venue_password").css("border","2px solid #c00000");
     		 document.getElementById('first_password').innerHTML="Please Enter a Password!!";
     	}
     });
     
     $("#venue_cpassword").blur(function()
     {
     	var confirm_p = $(this).val();
     	var c_p = $('#venue_password').val();
     	$("#venue_cpassword").focus(function()
     	{
     		$("#venue_cpassword").css("border","1px solid #ad4bc2");
     	});
     	if(confirm_p.length > 0)
     	{
	     	if(c_p != confirm_p)
	     	{
	     		document.getElementById('c_password').innerHTML="Passwords Do not Match";
				$('.button_common_res').attr('disabled','disabled');
	     		$("#venue_password").css('border','2px solid #c00000');
	     	    $("#venue_cpassword").css('border','2px solid #c00000');
	 		    return;
	     	}
	     	else
	     	{
	     		$("#venue_password").css("border","1px solid #CCC");
	     	    $("#venue_cpassword").css("border","1px solid #CCC");
	     	    document.getElementById('c_password').innerHTML="";
				$('.button_common_res').removeAttr('disabled');
	     	}
     	}
     	else
     	{
     		$("#venue_cpassword").css("border","2px solid #c00000");
			$('.button_common_res').attr('disabled','disabled');
     		document.getElementById('c_password').innerHTML="Please Enter Confirm Password!!";
     	}
     });
     
     
     $('#reset_button').click(function()
     {
     	var field_name = $(this).attr('name');
     	if(field_name == 'contact_us_reset')
     	{
	     	window.location.href="/capital_centric/contact_us";
     	}
     	else
     	{	
	     	if($('input[name="type"]').val() == 'venue')
	     	{
	     		var path = 'restaurant'; 
	     	}
	     	else
	     	{
	     		var path = 'operator';
	     	}
	     	window.location.href="/capital_centric/sign_up/"+path+"";
     	}
     });
     
     $('#submit_button').click(function()
     {

     	var field_name = $(this).attr('name');
     	console.log(field_name);
     	if(field_name == 'contact_submit_button')
     	{
     		if ( $.browser.msie ) 
     		{	
  				if($.browser.version == '9.0' || $.browser.version == '8.0')
  				{
  					if($('#contact_form_name').val() == '')
		     		{
		     			$('#contact_form_name').focus();
		     			return false;
		     		}
		     		if($('#contact_form_email').val() == '')
		     		{
		     			$('#contact_form_email').focus();
		     			return false;
		     		}
		     		if($('#contact_form_phone').val() == '')
		     		{
		     			$('#contact_form_phone').focus();
		     			return false;
		     		}
		     		if($('#contact_form_message').val() == '')
		     		{
		     			$('#contact_form_message').focus();
		     			return false;
		     		}
  				}
			}
     	}
     	else
     	{
     		if(($('#email_id').text() == '') && ($('#email_c_id').text() == '') && ($('#first_password').text() == '') && ($('#c_password').text() == '') && ($('#name_error').text() == ''))
	     	{
	     		
	     	}
	     	else
	     	{
	     		return false;
	     	}	
     	}
     });
     
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
     
     // $('.tc_signup').click(function()
     // {
     	// console.log("HElllo");
     	// fader = document.getElementById('login_fader');
        // login_box = document.getElementById('tc_signup_dialog');
        // fader.style.display = "block";
        // login_box.style.display = "block";
        // $("#tc_signup_dialog").show();
     // });
    
     var check_which = $('#check_which').text();
     console.log('check_which',check_which);
     if(check_which == 'reset')
     {
     	// $('#email_res').hide();
     	$('#from_wch_button').val('forget_password');
     }
     
//Image Slider 	  
// var triggers = $('ul.triggers li');
// var images = $('ul.images li');
// var lastElem = triggers.length-1;
// var target;
// 
// triggers.first().addClass('selected');
// images.hide().first().show();
// 
// function sliderResponse(target) {
    // images.fadeOut(300).eq(target).fadeIn(300);
    // triggers.removeClass('selected').eq(target).addClass('selected');
// } 
// 
// triggers.click(function() {
    // if ( !$(this).hasClass('selected') ) {
        // target = $(this).index();
        // sliderResponse(target);
        // resetTiming();
    // }
// });
// $('.next').click(function() {
    // target = $('ul.triggers li.selected').index();
    // target === lastElem ? target = 0 : target = target+1;
    // sliderResponse(target);
    // resetTiming();
// });
// $('.prev').click(function() {
    // target = $('ul.triggers li.selected').index();
    // lastElem = triggers.length-1;
    // target === 0 ? target = lastElem : target = target-1;
    // sliderResponse(target);
    // resetTiming();
// });
// function sliderTiming() {
    // target = $('ul.triggers li.selected').index();
    // target === lastElem ? target = 0 : target = target+1;
    // sliderResponse(target);
// }
// var timingRun = setInterval(function() { sliderTiming(); },5000);
// function resetTiming() {
    // clearInterval(timingRun);
    // timingRun = setInterval(function() { sliderTiming(); },5000);
// }    
     

// Banner
var w_triggers = $('ul.w_triggers li');
var w_images = $('ul.w_images li');
var w_lastElem = w_triggers.length-1;
var w_target;

w_triggers.first().addClass('selected');
w_images.hide().first().show();

function w_sliderResponse(w_target) {
    w_images.fadeOut(300).eq(w_target).fadeIn(300);
    w_triggers.removeClass('selected').eq(w_target).addClass('selected');
} 

w_triggers.click(function() {
    if ( !$(this).hasClass('selected') ) {
        w_target = $(this).index();
        w_sliderResponse(w_target);
        w_resetTiming();
    }
});
$('.next').click(function() {
    w_target = $('ul.w_triggers li.selected').index();
    w_target === w_lastElem ? w_target = 0 : w_target = w_target+1;
    w_sliderResponse(w_target);
    w_resetTiming();
});
$('.prev').click(function() {
    w_target = $('ul.w_triggers li.selected').index();
    lastElem = w_triggers.length-1;
    w_target === 0 ? w_target = w_lastElem : w_target = w_target-1;
    w_sliderResponse(w_target);
    w_resetTiming();
});
function w_sliderTiming() {
    w_target = $('ul.w_triggers li.selected').index();
    w_target === w_lastElem ? w_target = 0 : w_target = w_target+1;
    w_sliderResponse(w_target);
}
var timingRun = setInterval(function() { w_sliderTiming(); },5000);
function w_resetTiming() {
    clearInterval(timingRun);
    timingRun = setInterval(function() { w_sliderTiming(); },5000);
}  

// First Slider
var l_triggers = $('ul.l_triggers li');
var l_images = $('ul.l_images li');
var l_lastElem =l_triggers.length-1;
var l_target;

l_triggers.first().addClass('selected');
l_images.hide().first().show();

function l_sliderResponse(l_target) {
    l_images.fadeOut(300).eq(l_target).fadeIn(300);
    l_triggers.removeClass('selected').eq(l_target).addClass('selected');
} 

l_triggers.click(function() {
    if ( !$(this).hasClass('selected') ) {
        l_target = $(this).index();
        l_sliderResponse(l_target);
        l_resetTiming();
    }
});
$('.next').click(function() {
    l_target = $('ul.l_triggers li.selected').index();
    l_target === l_lastElem ? l_target = 0 : l_target = l_target+1;
    l_sliderResponse(l_target);
    l_resetTiming();
});
$('.prev').click(function() {
    l_target = $('ul.l_triggers li.selected').index();
    lastElem = l_triggers.length-1;
    l_target === 0 ? l_target = l_lastElem : l_target = l_target-1;
    l_sliderResponse(l_target);
    l_resetTiming();
});
function l_sliderTiming() {
    l_target = $('ul.l_triggers li.selected').index();
    l_target === l_lastElem ? l_target = 0 : l_target = l_target+1;
    l_sliderResponse(l_target);
}
var timingRun = setInterval(function() { l_sliderTiming(); },6000);
function l_resetTiming() {
    clearInterval(timingRun);
    timingRun = setInterval(function() { l_sliderTiming(); },6000);
} 


// 2nd Slider
var r_triggers = $('ul.r_triggers li');
var r_images = $('ul.r_images li');
var r_lastElem =r_triggers.length-1;
var r_target;

r_triggers.first().addClass('selected');
r_images.hide().first().show();

function r_sliderResponse(l_target) {
    r_images.fadeOut(300).eq(r_target).fadeIn(300);
    r_triggers.removeClass('selected').eq(r_target).addClass('selected');
} 

r_triggers.click(function() {
    if ( !$(this).hasClass('selected') ) {
        r_target = $(this).index();
        r_sliderResponse(r_target);
        r_resetTiming();
    }
});
$('.next').click(function() {
    r_target = $('ul.r_triggers li.selected').index();
    r_target === r_lastElem ? r_target = 0 : r_target = r_target+1;
    r_sliderResponse(r_target);
    r_resetTiming();
});
$('.prev').click(function() {
    r_target = $('ul.r_triggers li.selected').index();
    lastElem = r_triggers.length-1;
    r_target === 0 ? r_target = r_lastElem : r_target = r_target-1;
    r_sliderResponse(r_target);
    r_resetTiming();
});
function r_sliderTiming() {
    r_target = $('ul.r_triggers li.selected').index();
    r_target === r_lastElem ? r_target = 0 : r_target = r_target+1;
    r_sliderResponse(r_target);
}
var timingRun = setInterval(function() { r_sliderTiming(); },6000);
function r_resetTiming() {
    clearInterval(timingRun);
    timingRun = setInterval(function() { r_sliderTiming(); },6000);
}


// 3rd Slider
var ll_triggers = $('ul.ll_triggers li');
var ll_images = $('ul.ll_images li');
var ll_lastElem =ll_triggers.length-1;
var ll_target;

ll_triggers.first().addClass('selected');
ll_images.hide().first().show();

function ll_sliderResponse(ll_target) {
    ll_images.fadeOut(300).eq(ll_target).fadeIn(300);
    ll_triggers.removeClass('selected').eq(ll_target).addClass('selected');
} 

ll_triggers.click(function() {
    if ( !$(this).hasClass('selected') ) {
        ll_target = $(this).index();
        ll_sliderResponse(ll_target);
        ll_resetTiming();
    }
});
$('.next').click(function() {
    ll_target = $('ul.ll_triggers li.selected').index();
    ll_target === ll_lastElem ? ll_target = 0 : ll_target = ll_target+1;
    ll_sliderResponse(ll_target);
    ll_resetTiming();
});
$('.prev').click(function() {
    ll_target = $('ul.ll_triggers li.selected').index();
    lastElem = ll_triggers.length-1;
    ll_target === 0 ? ll_target = ll_lastElem : ll_target = ll_target-1;
    ll_sliderResponse(ll_target);
    ll_resetTiming();
});
function ll_sliderTiming() {
    ll_target = $('ul.ll_triggers li.selected').index();
    ll_target === ll_lastElem ? ll_target = 0 : ll_target = ll_target+1;
    ll_sliderResponse(ll_target);
}
var timingRun = setInterval(function() { ll_sliderTiming(); },6000);
function ll_resetTiming() {
    clearInterval(timingRun);
    timingRun = setInterval(function() { ll_sliderTiming(); },6000);
}


// $th Slider
var rr_triggers = $('ul.rr_triggers li');
var rr_images = $('ul.rr_images li');
var rr_lastElem =rr_triggers.length-1;
var rr_target;

rr_triggers.first().addClass('selected');
rr_images.hide().first().show();

function rr_sliderResponse(rr_target) {
    rr_images.fadeOut(300).eq(rr_target).fadeIn(300);
    rr_triggers.removeClass('selected').eq(rr_target).addClass('selected');
} 

rr_triggers.click(function() {
    if ( !$(this).hasClass('selected') ) {
        rr_target = $(this).index();
        rr_sliderResponse(rr_target);
        rr_resetTiming();
    }
});
$('.next').click(function() {
    rr_target = $('ul.rr_triggers li.selected').index();
    rr_target === rr_lastElem ? rr_target = 0 : rr_target = rr_target+1;
    rr_sliderResponse(rr_target);
    rr_resetTiming();
});
$('.prev').click(function() {
    rr_target = $('ul.rr_triggers li.selected').index();
    lastElem = rr_triggers.length-1;
    rr_target === 0 ? rr_target = rr_lastElem : rr_target = rr_target-1;
    rr_sliderResponse(rr_target);
    rr_resetTiming();
});
function rr_sliderTiming() {
    rr_target = $('ul.rr_triggers li.selected').index();
    rr_target === rr_lastElem ? rr_target = 0 : rr_target = rr_target+1;
    rr_sliderResponse(rr_target);
}
var timingRun = setInterval(function() { rr_sliderTiming(); },6000);
function rr_resetTiming() {
    clearInterval(timingRun);
    timingRun = setInterval(function() { rr_sliderTiming(); },6000);
}

});
