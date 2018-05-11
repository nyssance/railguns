'use strict';

var content = new Vue({
    el: '#content',
    data: function data() {
        return {
            endpoint: '',
            items: []
        };
    },
    mounted: function mounted() {
        var element = this.$el;
        if (element) {
            this.endpoint = getEndpoint(element);
            if (this.endpoint) {
                this.reload(null);
            }
        } else {
            console.error('#content 不存在');
        }
    },
    methods: {
        reload: function reload(params) {
            var _this = this;

            getData(this.endpoint, params, function (response) {
                _this.items = response.results;
            }.bind(this));
        },
        // target 和 currentTarget 区别 https://juejin.im/post/59f16ffaf265da43085d4108
        toggle: function toggle(event, params) {
            var className = 'weui-bar__item_on';
            var before = document.getElementsByClassName(className)[0];
            var after = event.target;
            if (before !== after) {
                before.classList.remove(className);
                after.classList.add(className);
                this.reload(params);
            }
        }
    }
});