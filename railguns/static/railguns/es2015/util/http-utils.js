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
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const httpUtilenqueue = (method = 'get', endpoint, params, success, failure, complete) => {
    const isGet = method === 'get'
    axios({
        method,
        url: endpoint,
        params: isGet ? params : {},
        data: isGet ? {} : params
    }).then(response => {
        console.debug('Endpoint:', `${location.origin}${endpoint}`)
        console.debug('Content-Type:', response.headers['content-type'])
        console.debug('Response:', response)
        console.debug('Params:', params)
        const status = response.status
        if (status >= 200 && status < 300) { // 200, 201 才重绘
            success && success(status, response.data)
        } else {
            console.warn(response.status)
        }
    }).catch(error => {
        if (error.response) { // 请求已经发出，但是服务器响应返回的状态吗不在2xx的范围内
            const data = error.response.data
            const message = data ? JSON.stringify(data) : error.response.statusText
            console.log(message)
            failure && failure(error.response.status, message)
        } else if (error.request) { // 请求已经发出，没有响应
            console.log(error.request)
        } else { // 一些错误是在设置请求的时候触发
            console.error('Error:', error.message)
        }
    }).then(() => {
        complete && complete()
    })
}

const getQueryString = name => {
    const regexp = new RegExp(`(^|&)${name}=([^&]*)(&|$)`, 'i')
    let r = location.search.substr(1).match(regexp)
    return !!r ? decodeURIComponent(r[2]) : null
}

const regexp = {
    regexp: {
        IDNUM: /(?:^\d{15}$)|(?:^\d{18}$)|^\d{17}[\dXx]$/,
        VCODE: /^.{4}$/
    }
}
