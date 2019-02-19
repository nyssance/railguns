const content = new Vue({
    mixins: [base, get],
    el: '#content',
    data: {
        data: ''
    },
    updated() { // 组件挂载之后
        // generateUpdateLink()
    },
    methods: {
        onLoadSuccess(code, data) {
            this.data = data
        },
        // generateUpdateLink() {
        //     let endpoint = '初始化'
        //     const element = this.$el
        //     if (element) { // 获取 endpoint
        //         endpoint = this.getEndpoint(element)
        //     } else {
        //         console.error('#endpoint 不存在')
        //     }
        //     const as = document.getElementsByTagName('a')
        //     for (let element of as) {
        //         const link = element.attributes['href'].value
        //         if (link.includes('checklistupdate')) {
        //             const value = element.attributes['datavalue'].value
        //             //                console.warn(link)
        //             element.onclick = e => {
        //                 // console.warn(this.href) // 带有http前缀的完整路径
        //                 this.attributes['href'].value += `&selected=${value}`
        //                 this.attributes['href'].value += `&endpoint=${encodeURI(endpoint)}`
        //                 console.warn(this.attributes['href'].value)
        //                 // return false
        //             }
        //         }
        //     }
        // }
    }
})
