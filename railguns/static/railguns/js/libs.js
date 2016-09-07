'use strict';

$(function() {
	// Handlebars
	var $content = $('#datacontent');
	var endpoint = $content.data('endpoint');
	$.ajax(endpoint).done(function(data) {
		var source = $('#entry-template').html();
		var template = Handlebars.compile(source);
		var $newItems = $(template(data));
		$content.html($newItems);
		return false;
	}).fail(function() {
		alert('获取数据失败，请刷新页面重试！');
	}).always(function() {
	});
	// jQuery Lazy
	$('.lazy').Lazy({
		effect : 'fadeIn',
		visibleOnly : true,
		onError : function(element) {
			console.log('error loading ' + element.data('src'));
		}
	});
});
