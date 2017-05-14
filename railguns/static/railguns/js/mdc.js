'use strict';

$(function() {
	// Drawer
	let drawer = new mdc.drawer.MDCTemporaryDrawer(document.querySelector('.mdc-temporary-drawer'));
	document.querySelector('.menu').addEventListener('click', () => drawer.open = true);

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
});
