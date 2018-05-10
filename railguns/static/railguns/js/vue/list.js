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
            this.getList(endpoint, null);
        } else {
            console.error('#content 不存在');
        }
    },
    methods: {
        getList: function getList(endpoint, params) {
            if (endpoint) {
                getData(endpoint, params, function (response) {
                    this.items = response.results;
                    if (this.items.length == 0) {}
                }.bind(this));
            }
        },
        // target 和 currentTarget 区别 https://juejin.im/post/59f16ffaf265da43085d4108
        toggle: function toggle(event, params) {
            var className = 'weui-bar__item_on';
            var before = document.getElementsByClassName(className)[0];
            var after = event.target;
            if (before !== after) {
                before.classList.remove(className);
                after.classList.add(className);
                var element = document.getElementById('content');
                var endpoint = getEndpoint(element);
                this.getList(endpoint, params);
            }
        }
    }
});