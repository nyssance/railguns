const patch = {
    data: {
        items: [], params: {}, currentValue: undefined // 更新用
    },
    mounted() {
        this.endpoint = this.$el.dataset.endpoint || '' // 从页面获取 Endpoint
        this.onPrepare()
    },
    methods: {
        onSubmit() {
        },
        // 💛 Action`
        submit(event) {
            console.error('submit')
            this.onSubmit()
            return
            // if (this.currentValue === getQueryString('selected')) {
            //     console.warn('与之前相同, 不提交服务器更新')
            //     history.back() // 只返回不刷新
            // } else {
            //     httpUtilenqueue('PATCH', this.endpoint, this.params, (code, data) => {
            //         this.onLoadSuccess(code, data)
            //     }, (code, message) => {
            //         this.onLoadFailure(code, message)
            //     })
            // }
        }
    }
}

const content = new Vue({
    mixins: [base, patch],
    el: '#content',
    // updated() {
    //     this.currentValue = getQueryString('selected') // 第一次进来当前值从地址栏参数获取
    //     for (let li of document.getElementsByTagName('li')) {
    //         if (li.attributes['class'].value === 'mdc-list-item') {
    //             if (li.attributes['datavalue'].value === this.currentValue) {
    //                 const i = li.getElementsByTagName('i')
    //                 i[0].innerHTML = 'radio_button_checked'
    //             }
    //             li.onclick = e => {
    //                 console.warn('on click')
    //                 const selected = li.attributes['datavalue'].value
    //                 if (this.currentValue != selected) {
    //                     this.currentValue = selected
    //                     updateCheckList(selected)
    //                 }
    //             }
    //         }
    //     }
    // },
    methods: {
        onPrepare() {
            this.endpoint = '/api/v1/me/'
            this.items = [
                {label: '男112ss', value: 'm'},
                {label: '女222', value: 'f'}
            ]

            for (let li of document.getElementsByTagName('li')) {
                //         if (li.attributes['class'].value === 'mdc-list-item') {
                //             if (li.attributes['datavalue'].value === this.currentValue) {
                //                 const i = li.getElementsByTagName('i')
                //                 i[0].innerHTML = 'radio_button_checked'
                //             }
                //             li.onclick = e => {
                //                 console.warn('on click')
                //                 const selected = li.attributes['datavalue'].value
                //                 if (this.currentValue != selected) {
                //                     this.currentValue = selected
                //                     updateCheckList(selected)
                //                 }
                //             }
                //         }
            }
        },
        onSubmit() {
            // ❗ currentValue 应该是 option-item 点击后获得值 设置 checked="checked"
            const json_string = `{"gender": "${this.currentValue}"}`
            console.warn(json_string)
            this.params = JSON.parse(json_string)
        },
        onLoadSuccess(code, data) { // 默认模式是返回
            history.back()
            location.replace(endpoint.replace('/api/v1/', '/'))
        }
    }
})

// const updateCheckList = selected => {
//     console.warn('选中', selected)
//     for (let li of document.getElementsByTagName('li')) {
//         if (li.attributes['class'].value === 'mdc-list-item') {
//             const i = li.getElementsByTagName('i')
//             if (li.attributes['datavalue'].value === selected) {
//                 i[0].innerHTML = 'radio_button_checked'
//             } else {
//                 i[0].innerHTML = 'radio_button_unchecked'
//             }
//         }
//     }
// }
