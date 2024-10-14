$(function () {
  // 通用 TODO: 如何兼容vue
  $('body').on('click', 'a[rel*=external]', e => { // 打开外部链接，target=_blank不符合W3C标准
    window.open(this.href)
    e.preventDefault() // 正确使用return false
  })
  // Django 切换语言
  $('#setlang > .item:not(.active)').one('click', () => {
    $(this).prev().submit()
    e.preventDefault()
  })
  // jQuery Lazy
  $('.lazy').Lazy({
    effect: 'fadeIn',
    visibleOnly: true,
    onError (element) {
      console.log('error loading', element.data('src'))
    }
  })
})
