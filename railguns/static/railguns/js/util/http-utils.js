"use strict";

// https://cn.vuejs.org/v2/guide/components.html#注册
// 对于自定义标签名，Vue.js 不强制要求遵循 W3C 规则 (小写，并且包含一个短杠)，尽管遵循这个规则比较好。
// https://cn.vuejs.org/v2/guide/components.html#组件命名约定
// 这意味着 PascalCase 是最通用的 声明约定 而 kebab-case 是最通用的 使用约定。
// 综上，使用 kebab-case 最不容易引起不必要的bug
// 通用方法
// Vue 太蠢, 不区分html注释和正式代码
// https://github.com/axios/axios/issues/983
// const JSONbig = require('json-bigint')
// axios.defaults.transformResponse = [data => JSONbig.parse(data)]
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

var httpUtilenqueue = function httpUtilenqueue() {
  var method = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : 'get';
  var endpoint = arguments.length > 1 ? arguments[1] : undefined;
  var params = arguments.length > 2 ? arguments[2] : undefined;
  var success = arguments.length > 3 ? arguments[3] : undefined;
  var failure = arguments.length > 4 ? arguments[4] : undefined;
  var complete = arguments.length > 5 ? arguments[5] : undefined;
  var isGet = method === 'get';
  axios({
    method: method,
    url: endpoint,
    params: isGet ? params : {},
    data: isGet ? {} : params
  }).then(function (response) {
    console.debug('Endpoint:', "".concat(location.origin).concat(endpoint));
    console.debug('Content-Type:', response.headers['content-type']);
    console.debug('Response:', response);
    console.debug('Params:', params);
    var status = response.status;

    if (status >= 200 && status < 300) {
      // 200, 201 才重绘
      success && success(status, response.data);
    } else {
      console.warn(response.status);
    }
  }).catch(function (error) {
    if (error.response) {
      // 请求已经发出，但是服务器响应返回的状态吗不在2xx的范围内
      var data = error.response.data;
      var message = data ? JSON.stringify(data) : error.response.statusText;
      console.log(message);
      failure && failure(error.response.status, message);
    } else if (error.request) {
      // 请求已经发出，没有响应
      console.log(error.request);
    } else {
      // 一些错误是在设置请求的时候触发
      console.error('Error:', error.message);
    }
  }).then(function () {
    complete && complete();
  });
};

var getQueryString = function getQueryString(name) {
  var regexp = new RegExp("(^|&)".concat(name, "=([^&]*)(&|$)"), 'i');
  var r = location.search.substr(1).match(regexp);
  return !!r ? decodeURIComponent(r[2]) : null;
};

var regexp = {
  regexp: {
    IDNUM: /(?:^\d{15}$)|(?:^\d{18}$)|^\d{17}[\dXx]$/,
    VCODE: /^.{4}$/
  }
};