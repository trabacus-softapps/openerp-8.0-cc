$(document).ready(function () 
{  

	$('div[id="search_button"]').addClass('color'); 
	$("#progressbar").hide();
	$("#span_filter").hide();
	$("#distance").hide();
	$("#total_res").hide();
	$('#second_bookingline').hide();   
    $('#content').hide();
     
     // $('body').on('click','.empty_star', function()
	// {
		// var x = $(this).attr('class');
		// if(x.indexOf("fa-star-o") > -1)
		// {
			// $(this).attr('title','Remove from Favourites');
			// $(this).attr('class','fa fa-star');
		// }
		// else
		// {
			// $(this).attr('title','Add to Favourites');
			// $(this).attr('class','fa fa-star-o');
		// }
	// });
     
     jQuery('#filter').on('click', function(event) 
     {        
         jQuery('#content').slideToggle('show');
     });
  
	$('#sort').change(function(e) {
	    var $sort = this;
	    var wch_value = this.value;
	    var $table = $('#grid_table');
	    var $rows = $('tbody > tr',$table);
	    $rows.sort(function(a, b){
	        var keyA = $('td:eq(2)',a).text();
	        var keyB = $('td:eq(2)',b).text();
	        if(wch_value == 'low_to_high')
			{        
	        	return (keyA - keyB);
	        }
	    	if(wch_value == 'high_to_low')
	    	{
	        	return (keyB - keyA);
            }
	    });
	    $.each($rows, function(index, row){
	      $table.append(row);
	    });
	    
	    e.preventDefault();
	});
});

// GOOGLE MAPS
var markers = [];
var circleOptions = {
				      fillOpacity: 0.05,
      				  fillColor: '#686868',
  					  strokeColor: '#ad4bc2',
      				  strokeWeight: 2,
                      strokeOpacity: 0.8,
  					};
  					
var circle = new google.maps.Circle(circleOptions);
var infowindow;
var cntr_marker;

// Function Initialize to Display Map using default Co-ordinates
function initialize() 
{
	var center_pt = new google.maps.LatLng(51.517289,-0.125771);
	var mapOptions = {
					  zoom: 9,
					  center: center_pt,
					  mapTypeControl: false,
					  streetViewControl: false,
					  zoomControlOptions: {style: google.maps.ZoomControlStyle.DEFAULT}
					 };
	
	map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
	map.setMapTypeId(google.maps.MapTypeId.ROADMAP);
	var input = (document.getElementById('pac-input'));
	var autocomplete = new google.maps.places.Autocomplete(input);
	autocomplete.bindTo('bounds', map);
	infowindow = new google.maps.InfoWindow();
	google.maps.event.addListener(autocomplete, 'place_changed', function() 
	{  				  
	    infowindow.close();
	    var place = autocomplete.getPlace();
	    if (!place.geometry) 
	    {
	      return;
	    }
		if (place.geometry.viewport) 
		{	
	    	 map.fitBounds(place.geometry.viewport);
	    } 
		else 
		{
		    map.setCenter(place.geometry.location);
		}
		circle.set('radius', 2000);     
	    // get_places(place.geometry.location,circle.getRadius());
	    circle.setMap(map);
	  	circle.setCenter(place.geometry.location);
	  	map.setZoom(14);
	  	map.setCenter(place.geometry.location);
	});
	$('#filter_search').on('click',function()
	{
	 	get_places(circle.getCenter(),circle.getRadius());	 			 
	});
	initWidget(map);
}     

//Draw Widget Circle
function initWidget(map) 
{
    var distanceWidget = new DistanceWidget(map);

    google.maps.event.addListener(distanceWidget, 'distance_changed', function () 
    {
        displayInfo(distanceWidget); //Put you core filter logic here        
    });

    google.maps.event.addListener(distanceWidget, 'position_changed', function () 
    {
        displayInfo(distanceWidget); //Put you core filter logic here
    });    

}
//For display center and distance
function displayInfo(widget) 
{
    widget.get('distance');
}

/*------------------------------------Create Distance Widget--------------------*/
function DistanceWidget(map) 
{
    this.set('map', map);
	this.set('position', map.getCenter());
//Anchored image
	var image = {url: '/website_capitalcentric/static/src/img/cursor-sizeall.png', 
				 size: new google.maps.Size(24, 24), origin: new google.maps.Point(0,0),   
				 anchor: new google.maps.Point(12, 12)
				};
//Cnter Marker 
 	cntr_marker = new google.maps.Marker({draggable: true,          
    									  icon: image,
    									  title: 'Drag to move new location!',
    									  raiseOnDrag: false,
										});      
    cntr_marker.bindTo('map', this);      
	cntr_marker.bindTo('position', this);

//Radius Widget
	var radiusWidget = new RadiusWidget();     
	radiusWidget.bindTo('map', this);      
	radiusWidget.bindTo('center', this, 'position');   
	this.bindTo('distance', radiusWidget);      
	this.bindTo('bounds', radiusWidget);
}

DistanceWidget.prototype = new google.maps.MVCObject();

/*------------------------------Create Radius widget-------------------------*/
function RadiusWidget() 
{    
    this.set('distance', 50);       
    this.bindTo('bounds', circle);     
    circle.bindTo('center', this);      
    circle.bindTo('map', this);       
    circle.bindTo('radius', this);
    // Add the sizer marker
    this.addSizer_();
}

RadiusWidget.prototype = new google.maps.MVCObject();

//Distance has changed event handler.      
RadiusWidget.prototype.distance_changed = function() 
{
    this.set('radius', this.get('distance') * 1000);
};

//Sizer handler
RadiusWidget.prototype.addSizer_ = function () 
{       
	var image = {url: '/website_capitalcentric/static/src/img/cursor-sizeh.png',  
	             size: new google.maps.Size(24, 24),
	             origin: new google.maps.Point(0,0),   
	             anchor: new google.maps.Point(12, 12)
	            };	
    var sizer = new google.maps.Marker({
								        draggable: true,
	      								icon: image,
									    cursor: 'ew-resize',
									    title: 'Showing Restaurants within ' +  parseInt((circle.getRadius()/1000))  + ' km \nDrag to change circle radius',
									    raiseOnDrag: false,
									  });
	
    sizer.bindTo('map', this);
  	sizer.bindTo('position', this, 'sizer_position');
	
  	var me = this;
	google.maps.event.addListener(sizer, 'drag', function () 
	{	
      me.setDistance();
      sizer.setOptions({title : 'Showing Restaurants within ' + parseInt((circle.getRadius()/1000)) + ' km \nDrag to change circle radius'});           
  	});
	
  	google.maps.event.addListener(sizer, 'dragend', function () 
  	{          
      me.fitCircle();  
      get_places(circle.getCenter(),circle.getRadius());          
  	});
};

//Center changed handler
RadiusWidget.prototype.center_changed = function() 
{
    var bounds = this.get('bounds');
    if (bounds) 
    {
      var lng = bounds.getNorthEast().lng();         
      var position = new google.maps.LatLng(this.get('center').lat(), lng);
  	  this.set('sizer_position', position);
  	  get_places(circle.getCenter(),circle.getRadius());
  	  geocoder = new google.maps.Geocoder();
  	  geocoder.geocode({'latLng': circle.getCenter()}, function(results, status) 
  	  {
      	if (status == google.maps.GeocoderStatus.OK) 
      	{
  			if (results[1]) 
  			{        		        		
   				cntr_marker.setOptions({title:results[1].formatted_address + '\n Drag to change center'});
  			} 
  	  	}
  	  });
  	}
};      
      
//Distance calculator
RadiusWidget.prototype.distanceBetweenPoints_ = function (p1, p2) 
{
  	if (!p1 || !p2) 
  	{
       return 0;
    }

  	var R = 6371; // Radius of the Earth in km
	var dLat = (p2.lat() - p1.lat()) * Math.PI / 180;
  	var dLon = (p2.lng() - p1.lng()) * Math.PI / 180;
  	var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
  	Math.cos(p1.lat() * Math.PI / 180) * Math.cos(p2.lat() * Math.PI / 180) *
  	Math.sin(dLon / 2) * Math.sin(dLon / 2);
  	var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  	var d = R * c;
//Limit max 50km and min half km
	if (d > 50) 
	{
      d = 50;
  	}
  	if (d < 0.5) 
  	{
      d = 0.5;
  	}
  	return d;
};

//Set distance
RadiusWidget.prototype.setDistance = function() 
{       
    var pos = this.get('sizer_position');
	var center = this.get('center');
	var distance = this.distanceBetweenPoints_(center, pos);      
	this.set('distance', distance);
   
    var bounds = this.get('bounds');        
	if (bounds) 
	{
  		var lng = bounds.getNorthEast().lng();         
  		var position = new google.maps.LatLng(this.get('center').lat(), lng);
  		this.set('sizer_position', position);
	}
};

//Fit circle when changed
RadiusWidget.prototype.fitCircle = function () 
{
    var bounds = this.get('bounds');  
 
    if (bounds) 
    {
      map.fitBounds(bounds);
      var lng = bounds.getNorthEast().lng();        
      var position = new google.maps.LatLng(this.get('center').lat(), lng);
      this.set('sizer_position', position);
    }
};
    
function get_filter_values(check)  
{ 
	var opt = document.getElementById(check);
	var no_of_opt = opt.length;
	var selValue = new Array;
	var j = 0;  
	for (i=0; i < no_of_opt;i++)  
	{  
	if (opt[i].selected === true)  
	{  
	selValue[j] = parseInt(opt[i].value); 
	j++  ;
	}  
	}
	return selValue;  
}
// This function picks up the click and opens the corresponding info window
function myclick(i) 
{
	if(i.id == 'empty_star')
	{
		var x = $(i).attr('class');
		if(x.indexOf("fa-star-o") > -1)
		{
			$(i).attr('title','Remove from Favourites');
			$(i).attr('class','fa fa-star');
		}
		else
		{
			$(i).attr('title','Add to Favourites');
			$(i).attr('class','fa fa-star-o');
		}
		event.stopPropagation();
	}
	// var id = $(i).closest("tr");
	// id.css("background-color","red");
	else
	{
		google.maps.event.trigger(markers[i.id], "click");	
	}
  	
} 

function get_places(location,radius)
{
		$("#progressbar").show();
		var progressbar = $("#progressbar"),
	    progressLabel = $(".progress-label");
	    progressLabel.text("Loading...");
	    progressbar.progressbar({
	      value: false,
	      complete: function() 
	      {
	      		progressLabel.text("Complete!");
				$("#progressbar").hide();
	      },
	    });	    
//show the filter option on search option
	$('#span_filter').show();
	$("#actual_distance").text(Math.round(radius)+'m');
	$('#distance').show();
  	
    for (var i = 0; i < markers.length; i++)
    {
		markers[i].setMap(null);
	}	
	markers = [];
	console.log('location',location);
    //var arr_loc = Object.keys(location).map(function (key) {return location.key()});
    //console.log('location',arr_loc);
	center_pt = {'lat1':location.lat(),
	             'long1':location.lng(),
	             'radius':radius};
	             
    if($("#min_p").val() == '')
    {
    	min_p = 0;
    }
     else
    {
    	min_p = $("#min_p").val();
    }
    if($("#max_p").val() == '')
    {
    	max_p = 0;
    }
    else
    {
    	max_p = $("#max_p").val(); 
    }
    openerp.jsonRpc("/website_capitalcentric/json_maps_search/", 'call', {'center_pt':center_pt,'cuisine':get_filter_values($('#cuisine').attr('id')),'dining':get_filter_values($('#dining_style').attr('id')),'min_p':parseFloat(min_p),'max_p':parseFloat(max_p),'fav_maps':$("input[name='fav_maps']").is(':checked')})
    .then(function (data) 
	  {
	  	// for setting the sort to first option on change of the search input...
	  	var select_option = $('select[id="sort"]');
	  	select_option.val(select_option.find('option').first().val());
	  	
	  	$('#grid_table').empty();
	  	if(data.status == "ZERO_RESULTS")
	  	{	
	  		$('#total_res').hide();
	  		var new_grid_row = '<tr class="" style=""><td class="" style="cursor:default;text-align:center;font-size:10pt;"> No Results Found </td></tr>';
	  		$(new_grid_row).appendTo($("#grid_table"));
	  	}
		callback(data.results,data.status);
	  });
}

// callback Function 
function callback(results, status) 
{
	$("#progressbar").show();
	var progressbar = $("#progressbar"),
    progressLabel = $(".progress-label");
    progressLabel.text("Loading...");
    progressbar.progressbar({
      value: false,
      complete: function() 
      {
      		progressLabel.text("Complete!");
			$("#progressbar").hide();
      },
    });	
  	var i = 0 ;   	
    $('#res_count').text(0);
    function progress() 
    {
	      var val = progressbar.progressbar( "value" ) || 0;
	      progressbar.progressbar( "value", val + 100/results.length );
	      if ( val <= 99.9999999999 && results.length > 0 ) 
	      {	      	
	      	if(results[i].is_fav == true)
	      	{
	      		var star = 'fa-star';
	      		var star_title="Remove from Favourites";
	      	}
	      	else
	      	{
      			var star = 'fa-star-o';
      			var star_title="Add to Favourites";
	      	}
      		createMarker(results[i],i);
	  		var new_grid_row = '<tr onclick="javascript:myclick(this)" class="alternative_record" style="padding:5px;" id="'+i+'"><td class="" style="width:40%"><img style="width:80px;height:70px;padding-top:5px;padding-bottom:5px;" src="data:image/png;base64,' + results[i].image + '"/></td>'+
		  		'<td class="" style="font-size:x-small;width:60%"><span style="font-weight:bold;font-size:x-small">'+results[i].name+'</span>'+"<p style='margin:0px;'></p>"+'<span style="font-size:x-small;">'+results[i].cuisine+'<br></span><span style="font-size:x-small;">'+results[i].dining_style+'</span>'+"<p style='margin:0px;'></p>"+'<span style="font-size:x-small"> '+results[i].symbol+''+results[i].min_price.toFixed(2)+' to '+results[i].symbol+''+results[i].max_price.toFixed(2)+' </span>'+
		  		'<a class="main_color" href="/capital_centric/star/'+results[i].partner+'" style="float:right"><i onclick="javascript:myclick(this)" class="empty_star fa '+star+' main_color" style="cursor:pointer;font-size:1.2em;" title="'+star_title+'" id="empty_star"/></a></td>'+
		  		'<td class="hidden">' + results[i].min_price + '</td>'+
		  		'</tr>';
		  		$(new_grid_row).appendTo($("#grid_table"));	  	
      		i++;      				  		
			$('#res_count').text(i);
	        setTimeout( progress, 80 );
	      }
	 }
	 setTimeout(progress,2000);
	 $('#total_res').show();
}


// createMarker Function 
function createMarker(place,count) 
{ 
  var placeLoc = place.geometry.location;
  var marker = new google.maps.Marker
  ({
    map: map,
    position: place.geometry.location,
    icon:'/website_capitalcentric/static/src/img/restaurant.png',
  });
  markers.push(marker);
 
  google.maps.event.addListener(marker, 'click', function() 
  {
     
    
     if(place.description == '') 
     {
     	after_desc = 'NA';	
     }
     else
     {
     	after_desc = '...';	
     }
    
     // <var contentString = '<div class="main_div">'+
                               // '<div id="bodyContent" style="padding:10px;border: 1px solid #bfbfbf;">'+
                               // '<div style="display:table-cell;vertical-align:middle;"><img style="width:100px;height:80px;" src="data:image/png;base64,' + (place.image)  + '"/></div>'+
                                // '<div style="display:table-cell; width:200px;padding-right:1%;border-right:solid 1px #bfbfbf;padding-left:1%;"><span style="font-weight:bold;font-size:10pt;">'+place.name+'</span>'+"<br>"+'<span style="font-size:8pt;">'+place.cuisine+' | </span><span style="font-size:8pt;">'+place.dining_style+'</span></div>'+
                               // '<div style="font-size:9pt;width:350px;padding-left:1%;padding-right:1%;display:table-cell;border-right:solid 1px #bfbfbf;" title="'+place.description+'">'+place.description.substring(0,160)+''+after_desc+'</div>'+
                               // '<div style="text-align:center;display:table-cell;vertical-align:middle;width:100px;padding-left:1%;"><span style="font-size:9pt;font-weight:bold;"> '+place.symbol+''+place.min_price.toFixed(2)+' to '+place.symbol+''+place.max_price.toFixed(2)+' </span>'+"<br>"+' <a href="/capital_centric/fit/search/result/'+place.partner+'" style="text-decoration: none !important;height:20px;display:block;" class="button"> Select </a></div>'+
                               // '</div>'+
                               // '</div>';></var>
	 var contentString = '<table class="table table-bordered" style="margin-bottom:0;"><tr><td><img style="width:100px;height:80px;" src="data:image/png;base64,' + (place.image)  + '"/></td>'+
	 					 '<td style="width:30%;"><div style="padding-right:1%;padding-left:1%;"><span style="font-weight:bold;font-size:10pt;">'+place.name+'</span>'+"<br>"+'<span style="font-size:8pt;">'+place.cuisine+' | </span><span style="font-size:8pt;">'+place.dining_style+'</span></div></td>'+
	 					 '<td style="width:40%;"><div style="font-size:9pt;padding-left:1%;padding-right:1%;" title="'+place.description+'">'+place.description.substring(0,160)+''+after_desc+'</div></td>'+
	 					 '<td style="width:10%;"><div style="text-align:center;vertical-align:middle;padding-left:1%;"><span style="font-size:9pt;font-weight:bold;"> '+place.symbol+''+place.min_price.toFixed(2)+' to '+place.symbol+''+place.max_price.toFixed(2)+' </span>'+"<br>"+' <a href="/capital_centric/fit/search/result/'+place.partner+'" style="text-decoration: none !important;height:20px;display:block;" class="button"> Select </a></div></td>'+
	 					 '</tr></table>';                     
  	 infowindow.setContent(contentString);
     infowindow.open(map, this);
     var container = $('#grid_table_div');
     
     // $('table#grid_table tr').each(function()
     // {
    	// if(this.id == count)
    	// {
    		// // var scrollTo = $(this);
// //     		 		
			// // $("#grid_table_div").animate({
            		// // scrollTop: scrollTo.offset().top - container.offset().top + container.scrollTop()
        	  // // }, 600);
        	  // // $("#grid_table").focus();
		// // $("#grid_table").parentNode.scrollTop = rows[i].offsetTop - rows[0].offsetHeight;		
    		// // return false;
//     		
//     		
//     		
    // var w = $(window);
    // var row = $('#grid_table').find(this);
        // // .removeClass('active')
        // // .eq( +$('#line').val() )
        // // .addClass('active');
//     
    // if (row.length)
    // {
        // // $('#grid_view').animate({scrollTop: row.offset().top - 100}, 1000 );
        // // $('#grid_view').animate({scrollTo: row.offset().top - 345}, 600 );
        // $('body').scrollTo(row);
        // // $('#grid_view').scrollTop( row.offset().top - (w.height()/2) );
//         
        // $(this).addClass('hover_color');
        // // return false;
 	// }
//     
//     
    	// }
     // });
     
  });
}


