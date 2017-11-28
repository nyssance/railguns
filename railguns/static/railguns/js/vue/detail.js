'use strict'

var content = new Vue({
    el: '#content',
    data: function() {
        return {
            data: 'detail'
        }
    },
    mounted: function() {
        let element = this.$el
        if (element != null) { // 获取 endpoint
            let endpoint = getEndpoint(element)
            getData(endpoint, null, function(response) {
                this.data = response
            }.bind(this))
        } else {
            console.error('#content 不存在')
        }
    },
    updated: function() { // 组件挂载之后
        let endpoint = '初始化'
        let element = this.$el
        if (element != null) { // 获取 endpoint
            endpoint = getEndpoint(element)
        } else {
            console.error('#endpoint 不存在')
        }
        var as = document.getElementsByTagName('a')
        for (let element of as) {
            let link = element.attributes['href'].value
            if (link.includes('checklistupdate')) {
                let value = element.attributes['datavalue'].value
                //                console.warn(link)
                element.onclick = function(e) {
                    // console.warn(this.href) // 带有http前缀的完整路径
                    this.attributes['href'].value += '&selected=' + value
                    this.attributes['href'].value += '&endpoint=' + encodeURI(endpoint)
                    console.warn(this.attributes['href'].value)
                    // return false
                }
            }
        }
    }
})
