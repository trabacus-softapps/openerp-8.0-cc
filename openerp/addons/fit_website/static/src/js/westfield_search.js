$(document).ready(function()
{
	// Replacing the URL after ? mark
	// window.history.pushState("string", "Title",document.URL.split('?')[0]);
	$(".datepicker").datepicker({dateFormat: 'dd-M-yy', showAnim: "fadeIn"});
		
	// $("#from_which").hide(); 
	var from_which = $("#from_which").text();
	var fader;
	$("#no_partners").hide();
	
	$(window).load(function() 
	{
		sort_result();
	});  

	// $("#partners_length").hide(); 
	if(document.getElementById('partners_length').innerHTML == 0) 
	{
		fader = document.getElementById('login_fader');
      	var login_box = document.getElementById('div1');
      	fader.style.display = "block";
        $("#no_partners").show();
	}
	else
	{
		$("#no_partners").hide();
	}


// On click of Close button on "No Partners" pop up
	$('#close_partners_tab').on('click',function()
	{
		$("#no_partners").hide();
		fader.style.display = "none";
    });

	if(from_which == 'westfield_search')
	{
		$('div[id="partnerbutton"]').addClass('color');
		$('a[id="westfield_link"]').css({'color':'#c00000'});
	}
	if(from_which == 'greenwich_search')
	{
		$('div[id="partnerbutton"]').addClass('color');
		$('a[id="greenwich_link"]').css('color','#c00000');
	}
	if(from_which == 'grid_view')
	{
		$('div[id="search_button"]').addClass('color');
		$('#second_bookingline').hide();
		$("#display_result").css('margin-top','0');
	}
	if(from_which == 'events')
	{
		$('div[id="eventsbutton"]').addClass('color');
		$('#second_bookingline').hide();
		$("#display_result").css('margin-top','0');
	}
	
	
	$("#resetbutton").on('click',function()
	{
		// $("input[name='min_p']").val('');
		// $("input[name='max_p']").val('');
		// $("input[name='post_code']").val(''); 
		// $("select[name='tstation']").val('');
		// $("#cuisine").multiselect("uncheckAll");
		// $("#dining_style").multiselect("uncheckAll");
		if(from_which == 'grid_view')
		{
			window.location.href = "/capital_centric/fit/grid_view";	
		}
		if(from_which == 'westfield_search')
		{
			window.location.href = "/capital_centric/fit/westfield_search";
		}
		if(from_which == 'greenwich_search')
		{
			window.location.href = "/capital_centric/fit/greenwich_search";
		}
		if(from_which == 'events')
		{
			window.location.href = "/capital_centric/fit/events";
		}
	});
	
	$('.menurounded').expander({
		    slicePoint:270,
		    preserveWords: true,
		    userCollapsePrefix : '  ... '
    });
	
    $('#westfield_ffp').expander({
		    slicePoint:1300,
		    preserveWords: true,
		    userCollapsePrefix : '... '
    });
	
	$('.empty_star').click(function()
	{
		var x = $(this).attr('class');
		if(x.indexOf("fa-star-o") > -1)
		{
			$(this).attr('title','Remove from Favourites');
			$(this).attr('class','fa fa-star');
		}
		else
		{
			$(this).attr('title','Add to Favourites');
			$(this).attr('class','fa fa-star-o');
		}
	}); 
	
	$('.empty_checkbox').click(function()
	{
		var x = $(this).attr('class');
		if(x.indexOf("fa-check-square-o") > -1)
		{
			$(this).attr('class','fa fa-square-o');
		}
		else
		{
			$(this).attr('class','fa fa-check-square-o');
		}
	}); 
	  
	$('#searchbutton').on('click',function()
	{
		var numbers =/^[-+]?[0-9]+$/;  
        var float_numbers =/^[-+]?[0-9]+\.[0-9]+$/;
		
		if($('input[name="min_p"]').val().match(numbers) || $('input[name="min_p"]').val().match(float_numbers) || $('input[name="min_p"]').val() == '')
        {
        	$('#searchbutton').prop('type','submit');
        }
        else
        {	
        	$('input[name="min_p"]').select();
        	return false;
        }
        if($('input[name="max_p"]').val().match(numbers) || $('input[name="max_p"]').val().match(float_numbers) || $('input[name="max_p"]').val() == '')
        {
        	$('#searchbutton').prop('type','submit');
        }
        else
        {
        	$('input[name="max_p"]').select();
        	return false;
        }       
	});
  	
  	// Sort By Function
	$('#slct_sort').on('change',function()
	{
		$('#sort_by').val(this.value);
		sort_result();
	});
	 
	// Westfeild slideshow...
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
});

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
    		var keyA = parseFloat($('td:eq(4)',a).text());
        	var keyB = parseFloat($('td:eq(4)',b).text());	
    	}
    	if($('#slct_sort').val() == 'l_tbl_sz' || $('#slct_sort').val() == 'h_tbl_sz')
    	{
    		var keyA = parseFloat($('td:eq(5)',a).text());
        	var keyB = parseFloat($('td:eq(5)',b).text());	
    	}
    	if($('#slct_sort').val() == 'l_grp_sz' || $('#slct_sort').val() == 'h_grp_sz')
    	{
    		var keyA = parseFloat($('td:eq(6)',a).text());
        	var keyB = parseFloat($('td:eq(6)',b).text());	
    	}
        if(wch_value == 'l_h' || wch_value == 'l_tbl_sz' || wch_value == 'l_grp_sz')
		{
			if (keyA == keyB)
			{
				var keyA = $('td:eq(8)',a).text();	
				var keyB = $('td:eq(8)',b).text();
				if (keyA == keyB)
				{
					var keyA = $('td:eq(7)',a).text().toLowerCase();
					var keyB = $('td:eq(7)',b).text().toLowerCase();
					if (keyA < keyB)
					{
	        			return -1;
	     			}
	     			else if (keyA > keyB)
	     			{
	       				return  1;
	     			}	
				}
			}    
        	return (keyA - keyB);
        }
    	if(wch_value == 'h_l' || wch_value == 'h_tbl_sz' || wch_value == 'h_grp_sz')
    	{
    		if (keyA == keyB)
			{
				var keyA = parseFloat($('td:eq(8)',a).text());	
				var keyB = parseFloat($('td:eq(8)',b).text());
				if (keyA == keyB)
				{
					var keyA = $('td:eq(7)',a).text().toLowerCase();
					var keyB = $('td:eq(7)',b).text().toLowerCase();
					if (keyA < keyB)
					{
	        			return -1;
	     			}	     			
				}
				else if (keyA > keyB)
     			{
       				return  1;
     			}	
			}
        	return (keyB - keyA);
        	
        }
        else
        {
        	var keyA = $('td:eq(8)',a).text();	
			var keyB = $('td:eq(8)',b).text();
			if (keyA == keyB)
			{
				var keyA = $('td:eq(7)',a).text().toLowerCase();
				var keyB = $('td:eq(7)',b).text().toLowerCase();
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
    });
   
    $.each($rows, function(index, row)
    {
    	$table.append(row);
    });
    
    $('table#search_result tr.tr_space').each(function()
    {
    	document.getElementById('search_result').deleteRow($(this));
    });
    $('table#search_result tr.individualrecord').each(function()
    {
    	$("<tr class='tr_space'><td style='height:7px;'></td></tr>").insertAfter($(this));
    });
   
}

function textarea_for_c_n_d(e)
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
    if(e.id == 'cuisine')
    	document.getElementById("cuisine_ids").innerHTML = selValue;
    if(e.id == 'dining_style')
    	document.getElementById("dining_ids").innerHTML = selValue;    
}


