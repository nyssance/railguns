'use strict';

$(function() {
	// Handlebars
	let content = $('#list');
	let endpoint = content.data('endpoint');
	if ((typeof endpoint) == 'string' && endpoint != '') {
		$.getJSON(endpoint).done(function(data) {
			let source = $('#entry-template').html();
			let template = Handlebars.compile(source);
			content.html(template(data));
		}).fail(function() {
			alert('获取数据失败，请刷新页面重试！');
		}).always(function() {
		});
	}

	var content = $('.page-content');
	var endpoint = content.data('endpoint');
	if ((typeof endpoint) == 'string' && endpoint != '') {
		$.getJSON(endpoint).done(function(data) {
			var source = $('#entry-template').html();
			var template = Handlebars.compile(source);
			content.html(template(data));
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
