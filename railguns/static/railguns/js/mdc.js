'use strict';

$(function() {
	// Drawer
	let drawer = new mdc.drawer.MDCTemporaryDrawer(document.querySelector('.mdc-temporary-drawer'));
	document.querySelector('.menu').addEventListener('click', () => drawer.open = true);
});
