'use strict';

$(function () {
    // jQuery Lazy
    $('.lazy').Lazy({
        effect: 'fadeIn',
        visibleOnly: true,
        onError: function onError(element) {
            console.log('error loading ' + element.data('src'));
        }
    });
});