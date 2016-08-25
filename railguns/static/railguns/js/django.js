'use strict';

// https://docs.djangoproject.com/en/dev/ref/csrf/#ajax
var csrftoken = Cookies.get('csrftoken');
function csrfSafeMethod(method) {
	// these HTTP methods do not require CSRF protection
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
	beforeSend : function(xhr, settings) {
		if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
			xhr.setRequestHeader('X-CSRFToken', csrftoken);
		}
	}
});

$(function() {
	var str = document.getElementsByTagName("body")[0]
			.getAttribute("data-nav_name")
	var side_str = document.getElementsByTagName("body")[0]
			.getAttribute("data-side_nav_name")
	if (side_str != '' && side_str != 'None') {
		$('#side_' + side_str).addClass('cur');
	}
	if (str != '' && str != 'None') {
		$('#nav_' + str).addClass('active');
	}
	$('body').on('click', 'a[rel*=external]', function(e) { // 打开外部链接，target=_blank不符合W3C标准
		window.open(this.href);
		e.preventDefault(); // 正确使用return false;
	});
	$('body').append('<a target="_blank" href="http://wpa.b.qq.com/cgi/wpa.php?ln=1&key=XzkzODE3NDg3OF8zODUyMjVfNDAwODM4NjM3Nl8yXw" id="side-qqservice"></a>');
	// 切换语言
	$('#setlang > .item:not(.active)').one('click', function() {
		$(this).prev().submit();
		e.preventDefault();
	});
});
