$(function() {
    // jQuery Lazy
    $('.lazy').Lazy({
        effect: 'fadeIn',
        visibleOnly: true,
        onError: function(element) {
            console.log('error loading ' + element.data('src'))
        }
    })
})
