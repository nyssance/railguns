'use strict';

var content = new Vue({
    el: '#content',
    data: function data() {
        return {
            items: []
        };
    },
    mounted: function mounted() {
        var element = this.$el;
        if (element) {
            var endpoint = getEndpoint(element);
            if (endpoint) {
                getData(endpoint, null, function (response) {
                    this.items = response.results;
                    if (this.items.length == 0) {}
                }.bind(this));
            }
        } else {
            console.error('#content 不存在');
        }
    }
});