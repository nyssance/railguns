'use strict'

// https://cn.vuejs.org/v2/guide/components.html#注册
// 对于自定义标签名，Vue.js 不强制要求遵循 W3C 规则 (小写，并且包含一个短杠)，尽管遵循这个规则比较好。

// https://cn.vuejs.org/v2/guide/components.html#组件命名约定
// 这意味着 PascalCase 是最通用的 声明约定 而 kebab-case 是最通用的 使用约定。

// 综上，使用 kebab-case 最不容易引起不必要的bug

// 通用方法
// Vue 傻逼, 不区分html注释和正式代码
function getData(endpoint, params, success, failure) {
    axios(endpoint, {
            params: params
        })
        .then(function(response) {
            console.log('Response:', response)
            if (response.status === 200) { // 200 才重绘
                success && success(response.data)
            }
        })
        .catch(function(error) {
            failure && failure(error)
            if (error.response) { // 请求已经发出，但是服务器响应返回的状态吗不在2xx的范围内
                console.log(error.response.data)
                console.log(error.response.status)
                console.log(error.response.headers)
            } else if (error.request) { // 请求已经发出，没有响应
                console.log(error.request)
            } else { // 一些错误是在设置请求的时候触发
                console.log('Error:', error.message)
            }
            console.log(error.config)
        })
}

// 获取 Endpoint
function getEndpoint(element) {
    let endpoint = element.dataset.endpoint // element.getAttribute('data-endpoint')
    if ((typeof endpoint) == 'string' && endpoint != '') {
        console.warn(element.id, 'Endpoint:', endpoint)
    } else {
        console.error('没有endpoint')
    }
    return endpoint
}

function queryString(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i")
    var r = window.location.search.substr(1).match(reg)
    if (r != null) {
        return unescape(r[2])
    }
    return null
}

var app_bar = new Vue({
    el: '#app_bar',
    data: {
        message: 'Hello App bar!'
    }
})
