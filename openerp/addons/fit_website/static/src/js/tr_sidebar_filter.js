
var services = (function(){
				var xml;
				$.ajax({
					type: "post",
					async: false,
					url: "/FIT/GetData",
					dataType: "json",
					success: function (data) {
					xml = data;
					}
				});

				return xml;
})();
console.log('services',services);
var resultLen = (services == undefined ? 0 : services.length);

$(document).ready(function() {

	var unique_id = 1;
	var prc_max_min = [];
	var table_max_min = [];
	var cuisine_arr = [];
	var dining_arr = [];
	var category_arr = [];
	for (var key in services)
	{
		if (services.hasOwnProperty(key))
		{
			var val = services[key];
			val['unique_id'] = unique_id++;
			for (var key in val)
			{
				if (val.hasOwnProperty(key))
				{
					if(key == 'min_price')
					{
						prc_max_min.push(val[key]);
					}
					if(key == 'max_covers')
					{
						table_max_min.push(val[key]);
					}
					if(key == 'cuisine')
					{
						for(var t = 0;t<val[key].length;t++)
						{
							var if_present = $.inArray(val[key][t].trim(), cuisine_arr);
							if(if_present == -1)
							{
								cuisine_arr.push(val[key][t].trim());
								cuisine_arr = cuisine_arr.sort();
							}
						}
						//val['cuisine'].push("All");
					}
					if(key == 'category')
					{
						for(var t = 0;t<val[key].length;t++)
						{
							var if_present = $.inArray(val[key][t].trim(), category_arr);
							if(if_present == -1)
							{
								category_arr.push(val[key][t].trim());
								category_arr = category_arr.sort();
							}
						}
						//val['cuisine'].push("All");
					}
					if(key == 'dining')
					{
						for(var t = 0;t<val[key].length;t++)
						{
							var if_present = $.inArray(val[key][t].trim(), dining_arr);
							if(if_present == -1)
							{
								dining_arr.push(val[key][t].trim());
								dining_arr = dining_arr.sort();
							}
						}
						//val['dining'].push("All");
					}
					// //Images for Hotels coming from Database
					//if(key == 'travel_type')
//	{
					//	val['image'] = '/website/image/product.product/'+val['id']+'/image';
					//}
					//if(key == 'min_price')
//				{
					//	val[key] = Math.round(val[key]*100)/100
//					}

					//Truncating Hotel Description
					if(key == 'kids_menu')
					{
						if(val['kids_menu']== true)
						{
							val['kidsmenu_btn'] = '<img src="/fit_website/static/src/img/kidsmenu.png" alt="Kids Menu Available" title="Kids Menu Available" style="width: 30px;display: inline-block;"/>';
						}
						else
						{
							val['kidsmenu_btn'] = '';
						}
					}
					if(key == 'is_markup')
					{
						val['is_markup'] = true;
						if(val['is_markup']== true)
						{
							val['markup_border'] = 'markup_border';
						}
					}
					if(key == 'avltimes')
					{
						var time_btn = '';
						if (val['avltimes'] !== null)
						{
							var times = val['avltimes'].split(',');
							for (i = 0;i<times.length; i++){
								time_btn += '<button class="btn btn-primary btn-sm butn_select" onclick="onclick_butn_select($(this))" style="margin-bottom: 15px;">'+ times[i] +'</button>'
							}
							val['time_btn'] = time_btn
						}
						else
						{
							val['time_btn'] = time_btn
						}

					}
					if(key == 'descp_venue')
					{
						if (val['descp_venue'] != null && val['descp_venue'].length > 150)
						{
							short_desc = val['descp_venue'].substring(0,150);
							val['short_desc'] = short_desc + ' ...';
						}
						else
							val['short_desc'] = val[key];
					}
				}
			}
		}
	}
	console.log('after services',services);

	var maxprice = (Math.max.apply(null, prc_max_min) + 1);
	var minprice = (Math.min.apply(null, prc_max_min) - 1);
	if (maxprice == -Infinity) maxprice = 0;
	if (minprice == Infinity || minprice == -1) minprice = 0;

	$("#price-range").slider({
		 range	: true,
		 min	: minprice,
		 max	: maxprice,
		 values	: [minprice, maxprice],
		 slide	: function( event, ui )
		 {
			$(".min-price-label").text('£'+ ' ' + ui.values[0].toFixed(2));
			$(".max-price-label").text('£'+ ' ' + ui.values[1].toFixed(2));// + ' - '+ ui.values[1] + ' ' + symbol
			$("#prc_input").val(ui.values[0] + '-' + ui.values[1]).trigger('change');
		 }
	});
	$(".min-price-label").html('£'+ ' ' + minprice.toFixed(2)); //+ ' - '+ maxprice+ ' ' + symbol
	$(".max-price-label").html('£'+ ' ' + maxprice.toFixed(2));
	$("#prc_input").val(minprice.toFixed(2) + '-' +  maxprice.toFixed(2));

	var maxtable = (Math.max.apply(null, table_max_min) + 1);
	var mintable = (Math.min.apply(null, table_max_min) - 1);
	$("#table-range").slider({
		 range	: true,
		 min	: mintable,
		 max	: maxtable,
		 values	: [mintable, maxtable],
		 slide	: function( event, ui )
		 {
			$(".min-table-label").text(ui.values[0]);
			$(".max-table-label").text(ui.values[1]);// + ' - '+ ui.values[1] + ' ' + symbol
			$("#table_input").val(ui.values[0] + '-' + ui.values[1]).trigger('change');
		 }
	});
	$(".min-table-label").html(mintable); //+ ' - '+ maxprice+ ' ' + symbol
	$(".max-table-label").html(maxtable);
	$("#table_input").val(mintable + '-' +  maxtable);

	for(var i = 0;i < category_arr.length;i++)
	{

		$('#res_category').append('<div class="checkbox-block job-type-checkbox full-time-checkbox" style="width: 100%;clear: both;"><input id="job_type_checkbox-category'+i+'" name="job_type_checkbox" type="checkbox" class="checkbox" value="'+category_arr[i]+'"><label class="" for="job_type_checkbox-category'+i+'">'+category_arr[i]+'</label></div>');
	}
	for(var i = 0;i < cuisine_arr.length;i++)
	{

		$('#res_cuisine').append('<div class="checkbox-block job-type-checkbox full-time-checkbox" style="width: 100%;clear: both;"><input id="job_type_checkbox-cuisine'+i+'" name="job_type_checkbox" type="checkbox" class="checkbox" value="'+cuisine_arr[i]+'"><label class="" for="job_type_checkbox-cuisine'+i+'">'+cuisine_arr[i]+'</label></div>');
	}
	console.log('dining_arr',dining_arr);
	for(var i = 0;i < dining_arr.length;i++)
	{

		$('#res_dining').append('<div class="checkbox-block job-type-checkbox full-time-checkbox" style="width: 100%;clear: both;"><input id="job_type_checkbox-dining'+i+'" name="job_type_checkbox" type="checkbox" class="checkbox" value="'+dining_arr[i]+'"><label class="" for="job_type_checkbox-dining'+i+'">'+dining_arr[i]+'</label></div>');
	}

	//$("#price_range").ionRangeSlider({
	//	type: "double",
	//	grid: true,
	//	min: 0,
	//	max: 5,
	//	from: 1,
	//	to: 800,
	//	prefix: ""
	//});


	if(services != false)
	{

		// Populating the data into Restaurant Div
		if ($("#restaurant_list").length > 0) {
			FilterJS(services, "#restaurant_list",
				{
					template: '#restaurant_template',
					search: { ele: '#hotel_namesearch' , fields: ['name','street','street2','city','country','zip'] ,start_length: 1},
					criterias: [
					//	//{field: 'nights', ele: '#dur_input', type: 'range'},
					{field: 'min_price',  ele: '#prc_input', type: 'range'},
					{field: 'max_covers', ele: '#table_input', type: 'range'},
						//ele: '.genres', event: 'change', selector: ':checked'
					{field: 'cuisine',    ele: '#res_cuisine :checkbox'},
					{field: 'dining',     ele: '#res_dining :checkbox'},
					{field: 'category',   ele: '#res_category :checkbox'},
					{field: 'kids_menu',  ele: '#kids_menu :checkbox'},
					{field: 'is_markup',  ele: '#markup_added :checkbox'},
					{field: 'fav',  	  ele: '#fav_only :checkbox'},
					//	//{field: 'theme', ele: '.holiday_theme :checkbox'},
					//	//{field: 'dest', ele: '.dest_ul :checkbox'},
					],
					callbacks: {
						afterAddRecords: function (result) {
							//$('.search-results-title b').text(this.recordsCount + ' of ' + resultLen);
							//var percent = parseInt((this.recordsCount / resultLen) * 100);
							//$('#stream_progress').text(percent + '%').attr('style', 'width: ' + percent + '%;');
							//if (percent == 100) {
							//	$('#stream_progress').parent().parent().fadeOut(1000);
//		}
						},
						afterFilter: function (result) {
							$('.sorting-title').text(result.length+' restaurant');
						},
					},
					pagination: {
						container: '#pagination',
						visiblePages: 1,
						perPage: {
							values: [50],
							container: '#per_page'
						},
					}
				});
		}
	}

	  	// Sort By Function
	$('#slct_sort').on('change',function()
	{
		console.log('this.value)',this.value);
		$('#sort_by').val(this.value);
		sort_result();
	});

	$("#table_size").ionRangeSlider({
		type: "double",
		grid: true,
		min: 0,
		max: 5,
		from: 1,
		to: 800,
		prefix: ""
	});



});


function onclick_butn_select(e)
{
		var id = e.closest('form');
		console.log("timeeeee",e.text().trim());
		id.find('input[name=time_selected]').val(e.text().trim());
		var res_id = parseInt(id.find('input[name=restaurant_id]').val());
		var lead_id = '';
		var booking_date = id.find('input[name=resv_date]').val();
		var booking_type = id.find('input[name=type]').val();
		var booking_time = e.text().trim();
		var booking_covers = parseInt(id.find('input[name=no_persons]').val());
		//e.preventDefault();
		openerp.jsonRpc("/get_availability", 'call', {'res_id' : res_id, 'lead_id' : lead_id, 'booking_date' : booking_date, 'booking_type' : booking_type, 'booking_time' : booking_time,  'booking_covers' : booking_covers})
      	.then(function (data)
      	{

		  if (data == true)
		  {
		    id.submit();
		  }
		  else
		  {
			alert("Seats are not available for the selected time.");
		  }
      	});
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
function sort_results(e)
{
	if(e[0].children.length == 1)
	{
		e.parent().addClass('active');
		$(".GridLex-grid-middle div").each(function()
		{
			if($(this)[0].className != e.parent()[0].className)
			{
				$(this).removeClass('active');

				if ($(this).children().children().hasClass("fa fa-caret-up"))
					$(this).children().children().removeClass('fa fa-caret-up');
				else
					$(this).children().children().removeClass('fa fa-caret-down');
			}
		});
	}

	if(e[0].children.length != 0)
	{
		if(e[0].children[0].className == "fa fa-caret-up")
		{
			e[0].children[0].className = "fa fa-caret-down";
		}
		else
		{
			e[0].children[0].className = "fa fa-caret-up";
		}
	}
	var ul = [];
	var items = [];
	var h_l_condition = (e.parent().hasClass('sort-by-price') && e[0].children[0].className == "fa fa-caret-down");
	var ul = $('#restaurant_list');
	var items = $('#restaurant_list li.fjs_item').get();
	call_sorting(e, ul, items, h_l_condition);

};
function call_sorting(e, ul, items, h_l_condition)
{

	items.sort(function(a,b)
		{
			if(e.parent().hasClass('sort-by-price'))
			{
				var keyA = parseFloat($(a).find('.price_sort').text());
				var keyB = parseFloat($(b).find('.price_sort').text());
			}
			if(e.parent().hasClass('sort-by-table'))
			{
				var keyA = parseFloat($(a).find('.table_sort').text());
				var keyB = parseFloat($(b).find('.table_sort').text());
			}
			if(e.parent().hasClass('sort-by-group'))
			{
				var keyA = parseFloat($(a).find('.group_sort').text());
				var keyB = parseFloat($(b).find('.group_sort').text());
			}

			if(h_l_condition)
			{
				if (keyA < keyB)
				{
					return 1;
				}
				else if (keyA > keyB)
				{
					return -1;
				}
				return (keyA - keyB);
			}
			else
			{
				if (keyA > keyB)
				{
					return 1;
				}
				else if (keyA < keyB)
				{
					return -1;
				}
				return (keyB - keyA);
			}
		});

	$.each(items, function(i, li)
	{
	  	ul.append(li);
	});

	/*setTimeout(function(){
    	$('.loader').hide();
	}, 2000);*/



};

