$(document).ready(function () 
{
	$('div[id="markupbutton"]').addClass('color');
    $('#second_bookingline').hide();
    // $("#markup_dialog").hide();
 	// $("#markup_dialog").draggable();
 	// $('.alert-danger').hide();
 	 $(".multiple_menu").multiselect({
 	 	noneSelectedText: "Select Menus",
        selectedText : "# Menu(s) Selected",
 	 }); 
 	 $('.ui-multiselect').css('width','100%');
     $('.ui-multiselect').css('border-radius','5px');
     $('.ui-multiselect').css('cursor','default');
     $(".ui-state-default").css('background-image','none');
     $(".ui-state-default").css('background-color','white');
     $('.ui-multiselect-menu').outerWidth($('.ui-multiselect').outerWidth());
     $('.ui-multiselect-checkboxes label input').css('margin-right','3%');
     //$('div.ui-helper-clearfix a.ui-multiselect-close span').replaceWith(function()
     //{
     //    return $("<span>Close</span>").append($(this).contents());
     //});
     $(".ui-multiselect-header li.ui-multiselect-close").css('padding-right','1%');
    
    // Dynamically generate the id of multi select tag  
 	var i=-1;
	$('.multiple_menu').each(function()
	{
		i++;
		var newID = i;
		$(this).attr('id',newID);
	});
     
     
// Adding new Records for Restaurant Level & Menu Level Exceptions Table
	$("a.mrkup_links").click(function()
    {	
    	var id_name = $(this).attr('id');
    	var ul = '';
        
        if(id_name == 'res_l_add')
        {
        	 var newRow ="<tr>"+
	    	"<td class='hidden'><input id='db_id' value='undefined'/></td>"+
	    	"<td class='singleblock_text' style=''><select id='res_select_ex' class='form-control restaurant_select' style=''><option value=''> Select a Restaurant </option></select></td>"+
	    	"<td class='singleblock_number' style=''><input type='text' id='' class='form-control res_mrkup_per' style=''></input></td>"+
	    	"<td class='singleblock_center' style=''><a id='db_delete' class='bookinginfolink'><img title='' src='/fit_website/static/src/img/delete_t.png' style='width:18px;height:18px;'/></a></td>"+
	    	"</tr>";
	    	
	    	$(newRow).appendTo($("#res_ex_table"));
    		$("#res_ex_table tr td select").focus();
    		
    		openerp.jsonRpc("/fit_website/markup_json/", 'call', {'from_which':'restaurant','restaurant_id':' '})
	        .then(function (data) 
	        {	                
			    for(var i=0; i<data[0].length; i++)
			    {	
		        	$('table#res_ex_table tr:last .restaurant_select').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
			    }
	        });
        }
        else
        {
        	var x = $('table#menu_ex_table tr:last .multiple_menu').attr('id');
        	var newRow ="<tr>"+
	    	"<td class='hidden'><input id='db_id' value='undefined'/></td>"+
	    	"<td class='singleblock_text' style=''><select id='res_select_ex' class='form-control restaurant_select new_record' onchange='javascript:change_rest(this)' style=''><option value=''> Select a Restaurant </option></select></td>"+
	    	'<td class="singleblock_text"><select disabled="disabled" multiple="multiple" name="multiple_select_name" id="'+ (parseInt(x)+1) +'" class="form-control input_val multiple_menu" title="" onchange="javascript:get_menusvalues(this)"></select><textarea class="hidden" name="menus_selected" id="menu_ids"></textarea></td>'+
	    	"<td class='singleblock_number' style=''><input type='text' id='' class='form-control menu_mrkup_per' style=''></input></td>"+
	    	"<td class='singleblock_center' style=''><a id='db_delete' class='bookinginfolink'><img title='' src='/fit_website/static/src/img/delete_t.png' style='width:18px;height:18px;'/></a></td>"+
	    	"</tr>";
	    	
	    	$(newRow).appendTo($("#menu_ex_table"));
    		$("#menu_ex_table tr td select").focus();
    		
    		openerp.jsonRpc("/fit_website/markup_json/", 'call', {'from_which':'restaurant','restaurant_id':' '})
	        .then(function (data) 
	        {	                
			    for(var i=0; i<data[0].length; i++)
			    {	
		        	$('table#menu_ex_table tr:last .restaurant_select').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
			    }
	        });
	         			
			$(".multiple_menu").multiselect({
				noneSelectedText: "Select Menus",
        		selectedText : "# Menu(s) Selected",
			}); 
			$('table#menu_ex_table tr:last .ui-state-disabled').css({'background-color':'#f2f2f2','opacity':'1'});
			$('.ui-multiselect').css('width','100%');
        }
    });
    
//Deletion of Records for Restaurant Level & Menu Level Exceptions Table
    $(".common_del").on('click','#db_delete',function(event)
    {
    	var id = $(this).closest("tr");
        var db_id = id.find("#db_id").val();
        if(db_id == 'undefined')
        {
        	var r=confirm("Are you sure you want to delete?");
	        if (r==true)
			{
			  $(this).parent().parent().remove();
			  document.body.scrollTop = document.documentElement.scrollTop = 0;
			  document.getElementById('save_prompt_markup').innerHTML="Deleted !!";
			  $("#save_prompt_markup").stop(true,true).show().fadeOut(5000);
			}
	    }
	    else
	    {
		    var r=confirm("Are you sure you want to permanently delete this record?");
	        if (r==true)
	        {
			    openerp.jsonRpc("/fit_website/delete_records/", 'call', {'value' : 'markup_table', 'db_id' : parseInt(db_id)})
		        .then(function (data) 
		        {
		         	id.remove();
		         	document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	document.getElementById('save_prompt_markup').innerHTML="Deleted !!";
					$("#save_prompt_markup").stop(true,true).show().fadeOut(5000);
		        });
	        }
        }
        var i=-1;
		$('.multiple_menu').each(function()
		{
    		i++;
    		var newID = i;
    		$(this).attr('id',newID);
		});
     });   
     

// Save for Markup Table
	$(".save_markup").click(function()
    {
    	var vals = {};
    	var count = 1;
    	$('table#res_ex_table tr:gt(0)').each(function()
        {            
        	var dict={};
            dict['restaurant_id'] 	= 	$(this).find(".restaurant_select").val();
            dict['markup_perc']  	= 	$(this).find(".res_mrkup_per").val();
            dict['mrkup_lvl']       =   'rest_lvl';
            
            if(dict['restaurant_id'].length == 0)
        	{
        		alert("Please Select a restaurant");
        		$(this).find(".restaurant_select").focus();
	  			document.getElementById("check_value").value = 1;
	  			return false;
        	}
            
	  		var db_id = $(this).find("#db_id").val();
	  		if (db_id == 'undefined')
	  		{
	  			db_id = 'create_'+(count++);
	  			$(this).find('#db_id').val(db_id);
	  		}
	  		vals[db_id] = dict;
		});
		
		$('table#menu_ex_table tr:gt(0)').each(function()
        {     
        	var dict={};      
        	dict['restaurant_id']   = 	$(this).find(".restaurant_select").val();
            dict['markup_perc']  	= 	$(this).find(".menu_mrkup_per").val();
            dict['menu_ids']  		=   $(this).find("#menu_ids").val();
            dict['mrkup_lvl']       =   'menu_lvl';
            
            console.log( dict['menu_ids']);
            
            if(dict['restaurant_id'].length == 0)
        	{
        		alert("Please Select a restaurant");
        		$(this).find(".restaurant_select").focus();
	  			document.getElementById("check_value").value = 1;
	  			return false;
        	}
            
	  		var db_id = $(this).find("#db_id").val();
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
			var markup_perc;
			if($('.markup_perc').val() == '')
			{
				markup_perc = 0.00;
			}
			else
			{
				markup_perc = $('.markup_perc').val();
			}
			openerp.jsonRpc("/fit_website/save_time_rec/", 'call', {'dict_time':vals,'type':'','venue_id':parseFloat(markup_perc),'create_count':count,'chkwhich':'markup'})
		  	.then(function (data)
		  	{	console.log('data',data);
			  	$('table#res_ex_table tr:gt(0)').each(function()
		        {	
		        	db_value = data[$(this).find('#db_id').val()];
		        	if (db_value != undefined)
		        		$(this).find('#db_id').val(db_value);
		        });
		        $('table#menu_ex_table tr:gt(0)').each(function()
		        {	
		        	db_value = data[$(this).find('#db_id').val()];
		        	if (db_value != undefined)
		        		$(this).find('#db_id').val(db_value);
		        	
		        });
		        $("html, body").animate({
        			scrollTop: 0
	  			}, 600);
		  		document.getElementById('save_prompt_markup').innerHTML="Saved Successfully!!";
		        $("#save_prompt_markup").stop(true,true).show().fadeOut(5000);	
		 	});
		}
    });
    
	


// // Adding a new markup
    // $("a#new_markup_add_link").click(function()
    // {	
    	// openerp.jsonRpc("/fit_website/markup_json/", 'call', {'from_which':'restaurant','restaurant_id':' '})
        // .then(function (data) 
        // {	                
		    // for(var i=0; i<data[0].length; i++)
		    // {	
	        	// $('select[name="restaurant_id"]').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
		    // }
        // });
    	// var newRow ="<tr>"+
    	// "<td class='hidden'><input id='db_id' value='undefined'/></td>"+
    	// "<td class='singleblock_text' style='padding-top:1%;padding-bottom:1%;'><select title='' class='form-control' onchange='javascript:partner_onchange(this)' style='color:black;padding-left:0.5%;width:100%;height:24px;' id='restaurant_id' name='restaurant_id'><option value=''> Select a Restaurant </option></select></td>"+
    	// "<td class='singleblock_text' style='padding-top:1%;padding-bottom:1%;'><select required='required' title='' class='form-control' style='color:black;padding-left:0.5%;width:100%;height:24px;' id='menu_id' name='menu_id'></select></td>"+
    	// "<td class='singleblock_center' style='padding-top:1%;padding-bottom:1%;'><button class='button' style='width:120px;height:24px;' id='add_markup_button' title=''> Add Markup </button></td>"+
    	// "<td class='singleblock_center' style='padding-top:1%;padding-bottom:1%;'><a id='db_delete' class='bookinginfolink'><img title='' src='/fit_website/static/src/img/delete_t.png' style='width:18px;height:18px;' id='img_icons'/></a></td>"+
    	// "</tr>";
//     	
    	// $(newRow).appendTo($("#markup_table"));
    	// $("#markup_table tr td select#restuarants").focus();
    // });
//     
//     
// // Cancel Button on Dialog Box  	
 	// $('button.cancel_button_markup').click(function()
	// {
		// $("#markup_dialog").hide();
		// fader.style.display = "none";
		// location.reload();
	// });
    
    
// //Add Markup Button in markup Table
    // $(".markup_table").on('click','#add_markup_button',function(event)
    // {	 
    	 // $('.alert-danger').hide();
    	 // var id = $(this).closest("tr");
    	 // db_id = id.find("#db_id").val();
    	 // restaurant_id = id.find("#restaurant_id").val();
    	 // if(restaurant_id == '')
    	 // {
    	 	// id.find("#restaurant_id").focus();
    	 	// return false;
    	 // }
    	 // menu_id = id.find("#menu_id").val();
    	 // if(menu_id == '')
    	 // {
    	 	// id.find("#menu_id").focus();
    	 	// return false;
    	 // }
    	 // openerp.jsonRpc("/fit_website/markup_pricing/", 'call', {'partner_id':parseInt($("#partner_id").val()),'restaurant_id' : parseInt(restaurant_id),'menu_id' : parseInt(menu_id), 'db_id' : parseInt(db_id)})
        // .then(function (data) 
        // {
        	// fader = document.getElementById('login_fader');
   			// login_box = document.getElementById('div3');
    		// fader.style.display = "block";
   			// $('.replaced_div').replaceWith(data);
    		// $("#markup_dialog").show();
        // });
    // });  
    
    
    
// //Deletion of a markup
    // $(".markup_table").on('click','#db_delete',function(event)
    // {
    	// var id = $(this).closest("tr");
        // db_id = id.find("#db_id").val();
        // if(db_id == 'undefined')
        // {
        	// var r=confirm("Are you sure you want to delete?");
	        // if (r==true)
			// {
			  // $(this).parent().parent().remove();
			  // document.body.scrollTop = document.documentElement.scrollTop = 0;
			  // document.getElementById('save_prompt_markup').innerHTML="Markup Deleted !!";
			  // $("#save_prompt_markup").stop(true,true).show().fadeOut(5000);
			// }
	    // }
	    // else
	    // {
		    // var r=confirm("Are you sure you want to permanently delete this record?");
	        // if (r==true)
	        // {
			    // openerp.jsonRpc("/fit_website/delete_records/", 'call', {'value' : 'markup_table', 'db_id' : parseInt(db_id)})
		        // .then(function (data) 
		        // {
		         	// id.remove();
		         	// document.body.scrollTop = document.documentElement.scrollTop = 0;
		         	// document.getElementById('save_prompt_markup').innerHTML="Markup Deleted !!";
					// $("#save_prompt_markup").stop(true,true).show().fadeOut(5000);
		        // });
	        // }
        // }
     // });
//      
//      
// //Save on dialog box
	    // $('button.save_button_markup').click(function()
        // {
        	// var m = [];
        	// var a = [];
        	// var dict = {};
        	// var j = 0;
        	// var i;
        	// var vals = {};
        	// var markup_id = $("#markup_id").val();
	        // $('table#markup_price_table tr').each(function()
	        // {   
	          // $(this).find('td').each(function()
	            // {	
	               // var x = ($(this).find("input.markup_price").val());
	               // if (x != undefined)
	            	  // m.push(x);
	            // });
	        // });
// 	        
// 	        
            // $('table#markup_price_table tr:eq(1)').each(function()
	        // {
	        	// $(this).find("td").each(function()
		        	// {
		        		// var y = $(this).attr('id');
		        		// if (y != undefined)
		        			// if (y != "")
		        				// a.push(y);
		            // });
	        // });
// 	        
	        // for (i=0;i < m.length; i++)
	   		// {	
	   			// if (a[j]=='db_id')
	   			// {
					// db_id = m[i];
					// j++;
					// continue;
				// }	 			
				// dict[a[j]] = m[i];
				// if (a[j]=='sun_to_mu')
				// {
					// vals[db_id] = dict;
					// var dict = {};
					// j=-1;
				// }
				// j++;
	 		// } 	
// 
	 		// openerp.jsonRpc("/fit_website/pricing_json/", 'call', {'dict_pricing':vals,'menu_id':parseInt(markup_id), 'chkwhich':'m_save','sc_included':'','service_charge':'', 'sc_disc':''})
		  	// .then(function (data)
		  	// {	
		  		// document.getElementById('alert_text').innerHTML="Saved Successfully!!";
		  		// $('.alert-danger').show();
		 	// });	 	
// 
	    // });
// 	    
// //Apply To All on dialog box	    
	    // $('.apply_link').click(function()
		// {
			// var link_id = $(this).attr('id');
	   	    // document.getElementById("apply_link").value = link_id;
	   	    // var num = document.getElementById("apply_link").value;
	   	    // console.log(num);
			// var markup = $("#markup_id").val();
	   		// var a = [];
	   		// var m = [];
	   		// // num = parseInt(num) + 1;
// 	   		
	   		// $("table#markup_price_table tr").each(function()
	   		// {
	        	// $(this).find("td:eq(0)").each(function()
	        	// {
	        		// var x = ($(this).find('input#db_id').val());
	        		// a.push(parseInt(x));
	            // });
// 	        	
	        	// $(this).find("td:eq("+num+")").each(function()
	        	// {
	        		// var z = ($(this).find("input.markup_price").val());
		        	// m.push(z);
	        	// });
	        // });
// 	        
	       // for (y=2; y<=15; y++)
	       // {
		        // var i=0;
		       	// $("table#markup_price_table tr").each(function()
		   		// {
			       	 // var $td = $(this).find('td').eq(y);        	
			         // $td.each(function()
		        	 // {   
		        		// $(this).find("input.markup_price").val(m[i]);
		        		// i++;
		        	 // });
	     	    // });
	        // }
// 	        
		    // var dict = {};
		    // for (i = 0; i < a.length; i++) 
		    // {
	    		// dict[a[i]] = m[i];
		    // }
		    // console.log(dict);
		    // openerp.jsonRpc("/fit_website/pricing_json/", 'call', {'dict_pricing':dict,'menu_id':parseInt(markup), 'chkwhich':'m_apply_all','sc_included':'','service_charge':'', 'sc_disc':''})
		   // .then(function (data)
		   // { 
			 // document.getElementById('alert_text').innerHTML="Applied Successfully to All!!";
  			 // $('.alert-danger').show();
		   // });
	   // });
	
});

 function get_menusvalues(e)  
 {  
 	 var p_id = $($(e).parent()).parent();                        
     var opt = p_id.find("select[name='multiple_select_name']");
     var no_of_opt = opt[0].length;
     var selValue = new Array;
     var j = 0;  
     for (i=0; i < no_of_opt;i++)  
     {  
     	 console.log(opt[0][i],opt[0][i].selected);
	     if (opt[0][i].selected === true)  
	     {  
	         selValue[j] = parseInt(opt[0][i].value) ;
	         j++  ;
	     }  
     }                       
     p_id.find("#menu_ids").text("[" + selValue + "]")  ;
 } 
     
              
function change_rest(e)
{	
	var id = $(e).closest("tr");
	var db_id = id.find("#db_id").val();
	var id_select = id.find(".multiple_menu").attr('id');
	var z = parseInt(id_select) + parseInt(id_select);
	var ul = '';
	openerp.jsonRpc("/fit_website/markup_json/", 'call', {'from_which':'menu','restaurant_id':parseInt(e.value)})
    .then(function (data) 
    {      	
    	 if(data[0].length > 0)
    	 {	 	 
	    	 var x = $('div.ui-widget-content:eq('+ id_select +') ul.ui-multiselect-checkboxes');
	    	 id.find('.multiple_menu').removeAttr('disabled','disabled');
	    	 id.find('button.ui-multiselect').removeClass('ui-state-disabled');
	    	 id.find('button.ui-multiselect').removeAttr('disabled','disabled');
	    	 id.find('button.ui-multiselect span:last-child').empty();
	    	 id.find('textarea#menu_ids').empty();
	    	 id.find('.multiple_menu').empty();
		     for(var i=0; i<data[0].length; i++)
	    	 {	
	         	id.find('.multiple_menu').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
	         	ul += '<li class=" "><label for=ui-multiselect-'+z+'-option-'+i+' class="ui-corner-all"><input id="ui-multiselect-'+z+'-option-'+i+'" name="multiselect_'+z+'" type="checkbox" value="'+ data[1][i]+'"><span>'+data[0][i]+'</span></input></label></li>';
		     }
		     x.html(ul);
		     id.find('.multiple_menu').multiselect("refresh");
		     $('.ui-multiselect').css('width','100%');
		     $('.ui-multiselect').css('border-radius','5px');
		     $('.ui-multiselect').css('cursor','default');
		     id.find(".ui-state-default").css('background-image','none');
		     id.find(".ui-state-default").css('background-color','white');
		     $('.ui-multiselect-menu').outerWidth($('.ui-multiselect').outerWidth());
		     $('.ui-multiselect-checkboxes label input').css('margin-right','3%');
		     $('div.ui-widget-content:eq('+ id_select +') div.ui-widget-header ul li:last-child a').empty().html('<span>Close</span>');
		     $(".ui-multiselect-header li.ui-multiselect-close").css('padding-right','1%');	
	  	}
	  	else
	  	{
	  		alert("No menus are present for this Venue.Select some other Venue");
	  		id.find('.restaurant_select').val('');
	  		id.find('textarea#menu_ids').empty();
	    	id.find('.multiple_menu').empty();
	  		id.find('.multiple_menu').multiselect("refresh");
	    	$('.ui-multiselect').css('width','100%');
	  		id.find('.multiple_menu').attr('disabled','disabled');
	    	id.find('button.ui-multiselect').addClass('ui-state-disabled');
	    	id.find('button.ui-multiselect').attr('disabled','disabled');
	    	id.find('button.ui-state-disabled').css({'background-color':'#f2f2f2','opacity':'1'});
	    	
	  	}
	});
}


// // Onchange function for partner
// function partner_onchange(e)
// {    
	  // $('select[name="menu_id"]').empty().append('<option value="">Select a Menu </option>');
	  // openerp.jsonRpc("/fit_website/markup_json/", 'call', {'from_which':'menu','restaurant_id':parseInt(e.value)})
	    // .then(function (data) 
	    // {	                	
	    	// console.log(data);                
		    // for(var i=0; i<data[0].length; i++)
		    // {	
	        	// $('select[name="menu_id"]').append('<option value="'+ data[1][i]+'">'+data[0][i]+'</option>');
		    // }
	    // });
// }	