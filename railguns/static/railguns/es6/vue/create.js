// axios.defaults.xsrfCookieName = 'csrftoken'
// axios.defaults.xsrfHeaderName = 'X-CSRFToken'

var content = new Vue({
    el: '#content',
    data: function () {
        return {
            data: {
                name: '',
                region: '',
                type: ''
            }
        }
    },
    methods: {
        create: function () {
            let element = this.$el
            if (element) {
                console.warn(this.data) // 返回的是一个包含很多内容东西的对象 里边还有不想要的东西
                let obj = JSON.stringify(this.data) // JSON.stringify() 方法用于将 JavaScript 值转换为 JSON 字符串. 为了清除不想要的东西
                console.log(obj)
                let endpoint = getEndpoint(element)
                if (endpoint) {
                    axios.post(endpoint, this.data, {
                        xsrfCookieName: 'csrftoken',
                        xsrfHeaderName: 'X-CSRFToken',
                    })
                        .then(function (response) {
                            console.log('Response:', response)
                            // history.back()
                            // location.reload(true)
                            // location.href = document.referrer
                        })
                        .catch(function (error) {
                            console.log(error.response)
                        })
                }
            } else {
                console.error('#content 不存在')
            }
        }
    }
})
