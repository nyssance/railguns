const updateCheckList = selected => {
    console.warn('选中', selected)
    for (let li of document.getElementsByTagName('li')) {
        if (li.attributes['class'].value === 'mdc-list-item') {
            const i = li.getElementsByTagName('i')
            if (li.attributes['datavalue'].value === selected) {
                i[0].innerHTML = 'radio_button_checked'
            } else {
                i[0].innerHTML = 'radio_button_unchecked'
            }
        }
    }
}

const content = new Vue({
    el: '#content',
    data: {
        items: [],
        data: {},
        currentValue: undefined // 更新用
    },
    mounted() {
        const element = this.$el
        if (element) {
            this.items = JSON.parse(getQueryString('options'))
        } else {
            console.error('#content 不存在')
        }
    },
    updated() {
        this.currentValue = getQueryString('selected') // 第一次进来当前值从地址栏参数获取
        for (let li of document.getElementsByTagName('li')) {
            if (li.attributes['class'].value === 'mdc-list-item') {
                if (li.attributes['datavalue'].value === this.currentValue) {
                    const i = li.getElementsByTagName('i')
                    i[0].innerHTML = 'radio_button_checked'
                }
                li.onclick = e => {
                    console.warn('on click')
                    const selected = li.attributes['datavalue'].value
                    if (this.currentValue != selected) {
                        this.currentValue = selected
                        updateCheckList(selected)
                    }
                }
            }
        }
    },
    methods: {
        update() { // 更新数据
            if (this.currentValue === getQueryString('selected')) {
                console.warn('与之前相同, 不提交服务器更新')
                history.back() // 只返回不刷新
            } else {
                const endpoint = getQueryString('endpoint')
                const json_string = `{"${getQueryString('field')}": "${this.currentValue}"}`
                // console.warn(json_string)
                this.data = JSON.parse(json_string)
                console.warn('Endpoint:', endpoint)
                console.warn('请求 更新', json_string)
                httpUtilenqueue('PATCH', endpoint, this.data, (code, data) => {
                    console.log('Data:', data)
                    history.back()
                    location.replace(endpoint.replace('/api/v1/', '/'))
                })
            }
        }
    }
})
