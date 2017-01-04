'use strict';

$(function() {
	// Handlebars
	var content = $('.page-content');
	var endpoint = content.data('endpoint');
	if ((typeof endpoint) == 'string' && endpoint != '') {
		$.getJSON(endpoint).done(function(data) {
			var source = $('#entry-template').html();
			var template = Handlebars.compile(source);
			content.html(template(data));
			componentHandler.upgradeDom() // https://github.com/google/material-design-lite/issues/4916
		}).fail(function() {
			alert('获取数据失败，请刷新页面重试！');
		}).always(function() {
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
