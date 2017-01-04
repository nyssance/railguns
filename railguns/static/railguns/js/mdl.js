'use strict';

$(function() {
	// Handlebars
	var content = $('#list');
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
});
