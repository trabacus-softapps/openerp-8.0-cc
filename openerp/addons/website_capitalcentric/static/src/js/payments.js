$(document).ready(function () 
{
	$('#second_bookingline').hide();
	$(window).load(function() 
	{
		sort_result();
		if($(".error_inline").length > 0)
		{
			$(".error_inline").delay(5000).fadeOut("slow");
		}
	});  
	
	// Sort By Function
	$('#slct_sort').on('change',function()
	{
		$('#sort_by').val(this.value);
		sort_result();
	});
	
	// Expander Initiation
	if($('.desc').length > 0) 
	{
		// $('.desc').expander({
		    // slicePoint:600,
		    // preserveWords: true,
		    // userCollapsePrefix : '  ... '
    	// });		
    	$('.desc').readmore({
  			speed: 500,
  			moreLink: '<span class="read-more"><a href="#">... read more</a></span>',
			lessLink: '<span class="read-less"><a href="#">... read less</a></span>',
  			collapsedHeight : 120,
		});
	}
    
    // // read more.. link 
  	// $('.read-more').on('click',function()
  	// {
  		// $(this).parent().children('span.details').css('display','inline');
  	// });
	
	if($('#category').length > 0)
	{
		$("#category").multiselect({
            noneSelectedText: "Select Categories",
            selectedText : "# Category(s) Selected",
    	});
		$('button.ui-multiselect').css('width','100%');
	    $('.ui-multiselect').css('border-radius','5px');
	    $('.ui-multiselect').css('cursor','default');
	    $(".ui-state-default").css('background-image','none');
	    $(".ui-state-default").css('background-color','white');
	    $('.ui-multiselect-checkboxes label input').css('margin-right','3%');
	    $('.ui-multiselect-menu').outerWidth($('.ui-multiselect').outerWidth());  
	    $('div.ui-helper-clearfix a.ui-multiselect-close span').replaceWith(function()
	    {
	            return $("<span>Close</span>").append($(this).contents());
	    });
	    $(".ui-multiselect-header li.ui-multiselect-close").css('padding-right','1%');
	 }          

	// Modal resize on click of tabs
	$(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function () 
	{
		modal_resize();
	});

});

function choice_dining_func(p)
{	
	openerp.jsonRpc("/website_capitalcentric/choice_dining_enquiry/", 'call', {'id' : parseInt(p.id)})    	
	.then(function (data)
	{
		if(p.id)
		{
			$("#choice_dining_enquiry_modal").css('width','950px');	
		}
		else
		{
			$("#choice_dining_enquiry_modal").css('width','600px');
		}
		fader = document.getElementById('login_fader');
	    var login_box = document.getElementById('choice_dining_enquiry_modal');
	    fader.style.display = "block";
	    
	    $('.replace_div').replaceWith(data);
        $("#choice_dining_enquiry_modal").show();
        $(".datepicker").datepicker({dateFormat: 'dd-M-yy', showAnim: "fadeIn",minDate : 1,});
		$(".timepicker").timepicker({
			timeFormat	: 'hh:mm tt',
			showAnim	: "fadeIn",
		});
		
		modal_resize();
		
		// Hotel Slideshow...        
       	var w_triggers = $('ul.w_triggers li');
		var w_images = $('ul.w_images li');
		var w_lastElem = w_triggers.length-1;
		var w_target;
		
		w_triggers.first().addClass('selected');
		w_images.hide().first().show();
		
		function w_sliderResponse(w_target) 
		{
		    w_images.fadeOut(300).eq(w_target).fadeIn(300);
		    w_triggers.removeClass('selected').eq(w_target).addClass('selected');
		} 
		
		w_triggers.click(function() 
		{
		    if ( !$(this).hasClass('selected') ) 
		    {
		        w_target = $(this).index();
		        w_sliderResponse(w_target);
		        w_resetTiming();
		    }
		});
		$('.next').click(function() 
		{
		    w_target = $('ul.w_triggers li.selected').index();
		    w_target === w_lastElem ? w_target = 0 : w_target = w_target+1;
		    w_sliderResponse(w_target);
		    w_resetTiming();
		});
		$('.prev').click(function() 
		{
		    w_target = $('ul.w_triggers li.selected').index();
		    lastElem = w_triggers.length-1;
		    w_target === 0 ? w_target = w_lastElem : w_target = w_target-1;
		    w_sliderResponse(w_target);
		    w_resetTiming();
		});
		function w_sliderTiming() 
		{
		    w_target = $('ul.w_triggers li.selected').index();
		    w_target === w_lastElem ? w_target = 0 : w_target = w_target+1;
		    w_sliderResponse(w_target);
		}
		if($('ul.w_triggers li').length > 1)
		{
			var timingRun = setInterval(function() 
			{ 
				w_sliderTiming(); 
			},5000);
		}
		function w_resetTiming() 
		{
		    clearInterval(timingRun);
		    timingRun = setInterval(function() 
		    { 
		    	w_sliderTiming(); 
	    	},5000);
		} 
	});
}

function close_dialog()
{
	$("#choice_dining_enquiry_modal").hide();
	fader.style.display = "none";
}

function sort_result()
{
    var wch_value = $('#slct_sort').val();
    var $table = $('#search_result');
    var $rows = $('tbody > tr.individualrecord',$table);
    var count = 0;
    
    $rows.sort(function(a, b)
    {
    	if($('#slct_sort').val() == 'l_h' || $('#slct_sort').val() == 'h_l')
    	{
    		var keyA = parseFloat($('td:eq(1)',a).text());
        	var keyB = parseFloat($('td:eq(1)',b).text());	
    	}
        if(wch_value == 'l_h')
		{
			if (keyA == keyB)
			{
				var keyA = $('td:eq(2)',a).text().toLowerCase();
				var keyB = $('td:eq(2)',b).text().toLowerCase();
				if (keyA < keyB)
				{
        			return -1;
     			}
     			else if (keyA > keyB)
     			{
       				return  1;
     			}	
			}
        	return (keyA - keyB);
        }
    	if(wch_value == 'h_l')
    	{
    		// if (keyA == keyB)
			// {
				// var keyA = $('td:eq(2)',a).text().toLowerCase();
				// var keyB = $('td:eq(2)',b).text().toLowerCase();
				// if (keyA < keyB)
				// {
        			// return -1;
     			// }	     			
			// }
			// else if (keyA > keyB)
 			// {
   				// return  1;
 			// }	
        	return (keyB - keyA);
        }
        else
        {
        	
			var keyA = $('td:eq(2)',a).text().toLowerCase();
			var keyB = $('td:eq(2)',b).text().toLowerCase();
			if (keyA < keyB)
			{
    			return -1;
 			}
 			else if (keyA > keyB)
 			{
   				return  1;
 			}	
        	return (keyA - keyB);
        }
    });
   
    $.each($rows, function(index, row)
    {
    	$table.append(row);
    });
}

function reload_page(path)
{
	window.location.href = "/choice_dinning/groups/"+path+"";
}

function textarea_for_categ(e)
{	
	var opt = document.getElementById(e.id);
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
	document.getElementById("category_ids").innerHTML = selValue;    
}

function modal_resize()
{
	if($(window).height() < $("#choice_dining_enquiry_modal .modal-content").height())
	{
		$("#choice_dining_enquiry_modal .modal-content .modal-body").css({ 'overflow-y':'auto','height':''+($(window).height()) - 250+'px'});
	}
}

       