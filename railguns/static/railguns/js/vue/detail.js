'use strict';

var content = new Vue({
    el: '#content',
    data: function data() {
        return {
            data: 'detail'
        };
    },
    mounted: function mounted() {
        var element = this.$el;
        if (element) {
            // 获取 endpoint
            var endpoint = getEndpoint(element);
            if (endpoint) {
                getData(endpoint, null, function (response) {
                    this.data = response;
                }.bind(this));
            }
        } else {
            console.error('#content 不存在');
        }
    },
    updated: function updated() {
        // 组件挂载之后
        var endpoint = '初始化';
        var element = this.$el;
        if (element) {
            // 获取 endpoint
            endpoint = getEndpoint(element);
        } else {
            console.error('#endpoint 不存在');
        }
        var as = document.getElementsByTagName('a');
        var _iteratorNormalCompletion = true;
        var _didIteratorError = false;
        var _iteratorError = undefined;

        try {
            for (var _iterator = as[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
                var _element = _step.value;

                var link = _element.attributes['href'].value;
                if (link.includes('checklistupdate')) {
                    (function () {
                        var value = _element.attributes['datavalue'].value;
                        //                console.warn(link)
                        _element.onclick = function (e) {
                            // console.warn(this.href) // 带有http前缀的完整路径
                            this.attributes['href'].value += '&selected=' + value;
                            this.attributes['href'].value += '&endpoint=' + encodeURI(endpoint);
                            console.warn(this.attributes['href'].value);
                            // return false
                        };
                    })();
                }
            }
        } catch (err) {
            _didIteratorError = true;
            _iteratorError = err;
        } finally {
            try {
                if (!_iteratorNormalCompletion && _iterator.return) {
                    _iterator.return();
                }
            } finally {
                if (_didIteratorError) {
                    throw _iteratorError;
                }
            }
        }
    }
});