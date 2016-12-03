'use strict';

$(function() {
	$('.dropdown').dropdown({ // 下拉菜单
		on : 'hover'
	});
	$('.message .close').on('click', function() { // 关闭消息框
		$(this).closest('.message').transition('fade');
	});
});
