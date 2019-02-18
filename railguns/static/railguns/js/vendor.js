"use strict";

$(function () {
  var _this = this;

  // 通用 TODO: 如何兼容vue
  $('body').on('click', 'a[rel*=external]', function (e) {
    // 打开外部链接，target=_blank不符合W3C标准
    window.open(_this.href);
    e.preventDefault(); // 正确使用return false
  }); // Django 切换语言

  $('#setlang > .item:not(.active)').one('click', function () {
    $(_this).prev().submit();
    e.preventDefault();
  }); // jQuery Lazy

  $('.lazy').Lazy({
    effect: 'fadeIn',
    visibleOnly: true,
    onError: function onError(element) {
      console.log('error loading', element.data('src'));
    }
  });
});