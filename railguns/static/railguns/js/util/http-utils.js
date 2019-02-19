"use strict";

// https://github.com/axios/axios/issues/983
// const JSONbig = require('json-bigint')
// axios.defaults.transformResponse = [data => JSONbig.parse(data)]
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

var httpUtilenqueue = function httpUtilenqueue() {
  var method = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : 'GET';
  var endpoint = arguments.length > 1 ? arguments[1] : undefined;
  var params = arguments.length > 2 ? arguments[2] : undefined;
  var success = arguments.length > 3 ? arguments[3] : undefined;
  var failure = arguments.length > 4 ? arguments[4] : undefined;
  var complete = arguments.length > 5 ? arguments[5] : undefined;
  var isGet = method === 'GET';
  axios({
    method: method,
    url: endpoint,
    params: isGet ? params : {},
    data: isGet ? {} : params
  }).then(function (res) {
    var code = res.status;
    console.debug('✅', code, method, "".concat(location.origin).concat(endpoint), 'params:', params);
    success && success(code, res.data);
  }).catch(function (error) {
    var message;

    if (error.response) {
      // 请求已经发出，但是服务器响应返回的状态吗不在2xx的范围内
      var data = error.response.data;
      message = data ? JSON.stringify(data) : error.response.statusText;
    } else if (error.request) {
      // 请求已经发出，没有响应
      message = error.request;
    } else {
      // 一些错误是在设置请求的时候触发
      message = error.message;
    }

    console.error(message);
    failure && failure(error.response.status, message);
  }).then(function () {
    complete && complete();
  });
};

var getQueryString = function getQueryString(name) {
  var regexp = new RegExp("(^|&)".concat(name, "=([^&]*)(&|$)"), 'i');
  var r = location.search.substr(1).match(regexp);
  return !!r ? decodeURIComponent(r[2]) : undefined;
};

var regexp = {
  regexp: {
    IDNUM: /(?:^\d{15}$)|(?:^\d{18}$)|^\d{17}[\dXx]$/,
    VCODE: /^.{4}$/
  }
};