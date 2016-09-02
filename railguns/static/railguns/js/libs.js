'use strict';

$(function() {
	// Handlebars
	var $content = $('#datacontent');
	var endpoint = $content.data('endpoint');
	if ((typeof endpoint) == 'string' && endpoint != '') {
		$.ajax({
			url : endpoint,
			dataType : 'json', // 兼容IE
			success : function(data) {
				var source = $('#entry-template').html();
				var template = Handlebars.compile(source);
				var $newItems = $(template(data));
				$content.html($newItems);
				return false;
			},
			error : function(e) {
				alert('获取数据失败，请刷新页面重试！');
			}
		});
	}
	// jQuery Lazy
	$('.lazy').Lazy({
		effect : 'fadeIn',
		visibleOnly : true,
		onError : function(element) {
			console.log('error loading ' + element.data('src'));
		}
	});
});
