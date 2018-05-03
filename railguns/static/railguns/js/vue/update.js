'use strict';

var currentValue = null; // 更新用

function updateCheckList(selected) {
    console.warn('选中 ' + selected);
    var _iteratorNormalCompletion = true;
    var _didIteratorError = false;
    var _iteratorError = undefined;

    try {
        for (var _iterator = document.getElementsByTagName('li')[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
            var li = _step.value;

            if (li.attributes['class'].value === 'mdc-list-item') {
                var i = li.getElementsByTagName('i');
                if (li.attributes['datavalue'].value === selected) {
                    i[0].innerHTML = 'radio_button_checked';
                } else {
                    i[0].innerHTML = 'radio_button_unchecked';
                }
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

var content = new Vue({
    el: '#content',
    data: {
        items: [],
        data: {}
    },
    mounted: function mounted() {
        var element = this.$el;
        if (element != null) {
            this.items = JSON.parse(getQueryString('options'));
        } else {
            console.error('#content 不存在');
        }
    },
    updated: function updated() {
        currentValue = getQueryString('selected'); // 第一次进来当前值从地址栏参数获取
        var _iteratorNormalCompletion2 = true;
        var _didIteratorError2 = false;
        var _iteratorError2 = undefined;

        try {
            var _loop = function _loop() {
                var li = _step2.value;

                if (li.attributes['class'].value === 'mdc-list-item') {
                    if (li.attributes['datavalue'].value === currentValue) {
                        var i = li.getElementsByTagName('i');
                        i[0].innerHTML = 'radio_button_checked';
                    }
                    li.onclick = function (e) {
                        console.warn('on click');
                        var selected = li.attributes['datavalue'].value;
                        if (currentValue != selected) {
                            currentValue = selected;
                            updateCheckList(selected);
                        }
                    };
                }
            };

            for (var _iterator2 = document.getElementsByTagName('li')[Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
                _loop();
            }
        } catch (err) {
            _didIteratorError2 = true;
            _iteratorError2 = err;
        } finally {
            try {
                if (!_iteratorNormalCompletion2 && _iterator2.return) {
                    _iterator2.return();
                }
            } finally {
                if (_didIteratorError2) {
                    throw _iteratorError2;
                }
            }
        }
    },
    methods: {
        patch: function patch() {
            // 更新数据
            if (currentValue === getQueryString('selected')) {
                console.warn('与之前相同, 不提交服务器更新');
                history.back(); // 只返回不刷新
            } else {
                var endpoint = getQueryString('endpoint');
                var json_string = '{"' + getQueryString('field') + '": "' + currentValue + '"}';
                // console.warn(json_string)
                this.data = JSON.parse(json_string);
                console.warn('Endpoint:', endpoint);
                console.warn('请求 更新 ' + json_string);
                axios.patch(endpoint, this.data, {
                    xsrfCookieName: 'csrftoken',
                    xsrfHeaderName: 'X-CSRFToken'
                }).then(function (response) {
                    console.log('Response:', response);
                    history.back();
                    location.replace(endpoint.replace('/api/v1/', '/'));
                }).catch(function (error) {
                    alert(error.response);
                    console.log(error.response);
                });
            }
        }
    }
});