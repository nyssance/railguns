var currentValue = null // 更新用

function updateCheckList(selected) {
    console.warn('选中 ' + selected)
    for (let li of document.getElementsByTagName('li')) {
        if (li.attributes['class'].value === 'mdc-list-item') {
            let i = li.getElementsByTagName('i')
            if (li.attributes['datavalue'].value === selected) {
                i[0].innerHTML = 'radio_button_checked'
            } else {
                i[0].innerHTML = 'radio_button_unchecked'
            }
        }
    }
}

var content = new Vue({
    el: '#content',
    data: {
        items: [],
        data: {

        }
    },
    mounted: function() {
        let element = this.$el
        if (element != null) {
            this.items = JSON.parse(getQueryString('options'))
        } else {
            console.error('#content 不存在')
        }
    },
    updated: function() {
        currentValue = getQueryString('selected') // 第一次进来当前值从地址栏参数获取
        for (let li of document.getElementsByTagName('li')) {
            if (li.attributes['class'].value === 'mdc-list-item') {
                if (li.attributes['datavalue'].value === currentValue) {
                    let i = li.getElementsByTagName('i')
                    i[0].innerHTML = 'radio_button_checked'
                }
                li.onclick = function(e) {
                    console.warn('on click')
                    let selected = li.attributes['datavalue'].value
                    if (currentValue != selected) {
                        currentValue = selected
                        updateCheckList(selected)
                    }
                }
            }
        }
    },
    methods: {
        patch: function() { // 更新数据
            if (currentValue === getQueryString('selected')) {
                console.warn('与之前相同, 不提交服务器更新')
                history.back() // 只返回不刷新
            } else {
                let endpoint = getQueryString('endpoint')
                let json_string = '{"' + getQueryString('field') + '": "' + currentValue + '"}'
                // console.warn(json_string)
                this.data = JSON.parse(json_string)
                console.warn('Endpoint:', endpoint)
                console.warn('请求 更新 ' + json_string)
                axios.patch(endpoint, this.data, {
                        xsrfCookieName: 'csrftoken',
                        xsrfHeaderName: 'X-CSRFToken',
                    })
                    .then(function(response) {
                        console.log('Response:', response)
                        history.back()
                        location.replace(endpoint.replace('/api/v1/', '/'))
                    })
                    .catch(function(error) {
                        alert(error.response)
                        console.log(error.response)
                    })
            }
        }
    }
})
