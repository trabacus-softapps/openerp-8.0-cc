// (function($) {
// 
    // $.fn.imgPreview = function(options) {
// 
        // var settings = $.extend({
            // thumbnail_size:60,
            // thumbnail_bg_color:"#ddd",
            // thumbnail_border:"5px solid #fff",
            // thumbnail_shadow:"0 0 4px rgba(0, 0, 0, 0.5)",
            // // label_text:"Select an Image File",
            // warning_message:"Not an image file.",
            // warning_text_color:"#f00",
        // },options);
// 
        // $(this).each(function() {
            // if(typeof FileReader == "undefined") return true; 
// 
            // var elem = $(this);
            // var scaleWidth = settings.thumbnail_size * 1.5;
            // var fileInput = $('<input>').attr({
                // type:"file",
                // name:elem.attr("name")
            // }).bind('change', function(e) {
                // doImgPreview(e);
            // });
// 
            // var form = elem.parent();
// 
            // while(!form.is("form")) {
                // form = form.parent();
            // }
// 
            // form.bind('submit', function(e) {
                // e.stopImmediatePropagation();
                // if($('.image-error', form).length > 0) {
                    // alert("Please select a valid image file.");
                    // return false;
                // }
            // });
// 
            // if(elem.prev().is("label")) {
                // var labelText = elem.prev().text();
                // elem.prev().remove();
            // } else {
                // var labelText = settings.label_text;
            // }
// // 
             // var newFileInput = $('<div>')
                // .addClass('image-preview-wrapper')
                // .css({
                    // "box-sizing": "border-box",
                    // "position": "relative",
                    // "-moz-box-sizing": "border-box",
                    // "-webkit-box-sizing": "border-box",
                    // "padding":"0.5em",
                    // "overflow": "hidden"
                // })
                // .append($('<div>')
                    // .addClass('image-preview').css({
                        // "box-sizing": "border-box",
                        // "position": "relative",
                        // "-moz-box-sizing": "border-box",
                        // "-webkit-box-sizing": "border-box",
                        // "background-color":settings.thumbnail_bg_color,
                        // "border":settings.thumbnail_border,
                        // "box-shadow":settings.thumbnail_shadow,
                        // "-moz-box-shadow":settings.thumbnail_shadow,
                        // "-webkit-box-shadow":settings.thumbnail_shadow,
                        // "width":settings.thumbnail_size + "px",
                        // "height":settings.thumbnail_size + "px",
                        // "background-size":scaleWidth + "px, auto",
                        // "background-position":"50%, 50%",
                        // "display":"inline-block",
                        // "float":"left",
                        // "margin-right":"1em"
                    // })
                // )
                // .append($('<label>')
                    // .text(labelText)
                    // .css({
                        // "box-sizing": "border-box",
                        // "position": "relative",
                        // "-moz-box-sizing": "border-box",
                        // "-webkit-box-sizing": "border-box",
                        // "display":"block",
                        // "font-weight":"bold",
                        // "margin":"0.5em 0"
                    // })
                // ).append(fileInput.css({
                    // "box-sizing": "border-box",
                    // "positionpreviewDiv": "relative",
                    // "-moz-box-sizing": "border-box",
                    // "-webkit-box-sizing": "border-box",
                    // "display":"block"
                // })
            // );
// 
            // elem.replaceWith(newFileInput);
// 
            // var doImgPreview = function(e) {
                // var files = e.target.files;
                // $('label > small', newFileInput).remove();
				// console.log('reader',files);
                // for (var i=0, file; file=files[i]; i++) {
                	// console.log('file',file);
                    // if (file.type.match('image.*')) {
                        // var reader = new FileReader();
                        // reader.onload = (function(theFile) {
                            // return function(e) {
                                // var image = e.target.result;
                                // console.log('image',image);
                                // console.log('image',newFileInput);
                                // previewDiv = $('.image-preview', newFileInput);
                                // previewDiv.css({
                                    // "background-image":"url("+image+")",
                                // });
                            // };
                        // })(file);
                        // reader.readAsDataURL(file);
                     	// console.log('file',file['type']);
                        // reader.onloadend = function(upload) {
                    		// var data = upload.target.result;
                    		// data = data.split(',')[1];
                    		// console.log('data',data)
                		// };
//                         
                    // } else {
                        // $('label', newFileInput).append(
                            // $('<small>').addClass('image-error')
                            // .text(settings.warning_message)
                            // .css({
                                // "font-size":"80%",
                                // "color":settings.warning_text_color,
                                // "display":"inline-block",
                                // "font-weight":"normal",
                                // "margin-left":"1em",
                                // "font-style":"italic"
                            // })
                        // );
                    // }
                // }
            // }
// 
        // });
    // }
// })(jQuery);



