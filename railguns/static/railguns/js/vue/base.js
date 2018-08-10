'use strict';

var base = {
    mounted: function mounted() {
        var element = this.$el;
        if (element) {
            this.endpoint = getEndpoint(element);
            if (this.endpoint) {
                this.reload();
            }
        } else {
            console.error('#content 不存在');
        }
    },
    methods: {
        reload: function reload(params) {
            var _this = this;

            get(this.endpoint, params, function (response) {
                _this.items = response.results;
            }.bind(this));
        }
    }
};