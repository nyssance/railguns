"use strict";

// https://cn.vuejs.org/v2/guide/components.html#注册
// 对于自定义标签名，Vue.js 不强制要求遵循 W3C 规则 (小写，并且包含一个短杠)，尽管遵循这个规则比较好。
// https://cn.vuejs.org/v2/guide/components.html#组件命名约定
// 这意味着 PascalCase 是最通用的 声明约定 而 kebab-case 是最通用的 使用约定。
// 综上，使用 kebab-case 最不容易引起不必要的bug
// 通用方法
// Vue 傻逼, 不区分html注释和正式代码
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

function get(endpoint, params, success, failure, complete) {
  request('get', endpoint, params, {}, success, failure, complete);
}

function post(endpoint, data, success, failure, complete) {
  request('post', endpoint, {}, data, success, failure, complete);
}

function patch(endpoint, data, success, failure, complete) {
  request('patch', endpoint, {}, data, success, failure, complete);
}

function request(method, endpoint, params, data, success, failure, complete) {
  axios({
    method: method,
    url: endpoint,
    params: params,
    data: data
  }).then(function (response) {
    console.debug('Content-Type:', response.headers['content-type']);
    console.debug('Response:', response);

    if (response.status >= 200 && response.status < 300) {
      // 200, 201 才重绘
      success && success(response.data);
    } else {
      console.warn(response.status);
    }
  }).catch(function (error) {
    if (error.response) {
      // 请求已经发出，但是服务器响应返回的状态吗不在2xx的范围内
      if (failure) {
        failure && failure(error);
      }

      console.log(error.response.data);
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
} // 获取 Endpoint


function getEndpoint(element) {
  var endpoint = (element.dataset.endpoint || '').trim(); // element.getAttribute('data-endpoint')

  if (endpoint) {
    console.debug(element.id, 'Endpoint:', location.origin + endpoint);
  } else {
    console.warn('没有 endpoint');
  }

  return endpoint;
}

function getQueryString(name) {
  var regexp = new RegExp("(^|&)".concat(name, "=([^&]*)(&|$)"), 'i');
  var r = location.search.substr(1).match(regexp);
  return !!r ? decodeURIComponent(r[2]) : null;
}