"use strict";

var updateCheckList = function updateCheckList(selected) {
  console.warn('选中', selected);
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
      if (!_iteratorNormalCompletion && _iterator.return != null) {
        _iterator.return();
      }
    } finally {
      if (_didIteratorError) {
        throw _iteratorError;
      }
    }
  }
};

var content = new Vue({
  el: '#content',
  data: {
    items: [],
    params: {},
    currentValue: undefined // 更新用

  },
  mounted: function mounted() {
    var element = this.$el;

    if (element) {
      this.items = JSON.parse(getQueryString('options'));
    } else {
      console.error('#content 不存在');
    }
  },
  updated: function updated() {
    var _this = this;

    this.currentValue = getQueryString('selected'); // 第一次进来当前值从地址栏参数获取

    var _iteratorNormalCompletion2 = true;
    var _didIteratorError2 = false;
    var _iteratorError2 = undefined;

    try {
      var _loop = function _loop() {
        var li = _step2.value;

        if (li.attributes['class'].value === 'mdc-list-item') {
          if (li.attributes['datavalue'].value === _this.currentValue) {
            var i = li.getElementsByTagName('i');
            i[0].innerHTML = 'radio_button_checked';
          }

          li.onclick = function (e) {
            console.warn('on click');
            var selected = li.attributes['datavalue'].value;

            if (_this.currentValue != selected) {
              _this.currentValue = selected;
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
        if (!_iteratorNormalCompletion2 && _iterator2.return != null) {
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
    update: function update() {
      // 更新数据
      if (this.currentValue === getQueryString('selected')) {
        console.warn('与之前相同, 不提交服务器更新');
        history.back(); // 只返回不刷新
      } else {
        var endpoint = getQueryString('endpoint');
        var json_string = "{\"".concat(getQueryString('field'), "\": \"").concat(this.currentValue, "\"}"); // console.warn(json_string)

        this.params = JSON.parse(json_string);
        console.warn('Endpoint:', endpoint);
        console.warn('请求 更新', json_string);
        httpUtilenqueue('PATCH', endpoint, this.params, function (code, data) {
          console.log('Data:', data);
          history.back();
          location.replace(endpoint.replace('/api/v1/', '/'));
        });
      }
    }
  }
});