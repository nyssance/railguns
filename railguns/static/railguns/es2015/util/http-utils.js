// https://github.com/axios/axios/issues/983
// const JSONbig = require('json-bigint')
// axios.defaults.transformResponse = [data => JSONbig.parse(data)]
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const httpUtilrequest = (method, url, params, success, failure, complete) => {
  method = method.toUpperCase()
  const isGet = method === 'GET'
  axios({
    method,
    url,
    params: isGet ? params : {},
    data: isGet ? {} : params
  }).then(res => {
    const code = res.status
    console.debug(`%c${method}`, getCss(method), `${location.origin}${url}`, '✅', code, res.statusText)
    params && params.password && (params.password = '******') // log不输出密码
    if (params) {
      console.debug('⬆️ 参数', JSON.stringify(params))
    }
    success && success(code, res.data)
  }).catch(error => {
    let message
    if (error.response) { // 请求已经发出，但是服务器响应返回的状态吗不在2xx的范围内
      const data = error.response.data
      message = data ? JSON.stringify(data) : error.response.statusText
    } else if (error.request) { // 请求已经发出，没有响应
      message = error.request
    } else { // 一些错误是在设置请求的时候触发
      message = error.message
    }
    console.error(message)
    failure && failure(error.response.status, message)
  }).then(() => {
    complete && complete()
  })

  // SO https://stackoverflow.com/questions/7505623/colors-in-javascript-console
  const getCss = method => {
    let bgcolor
    switch (method) {
      case 'OPTIONS':
      case 'GET':
        bgcolor = '#248fb2'
        break
      case 'POST':
        bgcolor = '#6bbd5b'
        break
      case 'PATCH':
        bgcolor = '#e09d43'
        break
      case 'DELETE':
        bgcolor = '#e27a7a'
        break
      default:
        bgcolor = '#9b708b'
    }
    return `background-color: ${bgcolor}; color: #fff; padding: 1px 9px; border-radius: 2px;`
  }
}
