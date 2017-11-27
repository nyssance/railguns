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
    }
})
