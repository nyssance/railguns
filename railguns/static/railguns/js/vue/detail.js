'use strict';

var content = new Vue({
    el: '#content',
    data: function data() {
        return {
            endpoint: '',
            data: ''
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
    // updated: function () { // 组件挂载之后
    //     let endpoint = '初始化'
    //     let element = this.$el
    //     if (element) { // 获取 endpoint
    //         endpoint = getEndpoint(element)
    //     } else {
    //         console.error('#endpoint 不存在')
    //     }
    //     var as = document.getElementsByTagName('a')
    //     for (let element of as) {
    //         let link = element.attributes['href'].value
    //         if (link.includes('checklistupdate')) {
    //             let value = element.attributes['datavalue'].value
    //             //                console.warn(link)
    //             element.onclick = function (e) {
    //                 // console.warn(this.href) // 带有http前缀的完整路径
    //                 this.attributes['href'].value += '&selected=' + value
    //                 this.attributes['href'].value += '&endpoint=' + encodeURI(endpoint)
    //                 console.warn(this.attributes['href'].value)
    //                 // return false
    //             }
    //         }
    //     }
    // },
    methods: {
        reload: function reload(params) {
            var _this = this;

            getData(this.endpoint, params, function (response) {
                _this.data = response;
            }.bind(this));
        }
    }
});