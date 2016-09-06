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
	$('body').on('click', 'a[rel*=external]', function(e) { // 打开外部链接，target=_blank不符合W3C标准
		window.open(this.href);
		e.preventDefault(); // 正确使用return false;
	});
	// 切换语言
	$('#setlang > .item:not(.active)').one('click', function() {
		$(this).prev().submit();
		e.preventDefault();
	});
});
