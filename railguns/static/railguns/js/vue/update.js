'use strict'

var content = new Vue({
    el: '#content',
    data: {
        items: []
    },
    created: function() {},
    mounted: function() {
        let element = this.$el
        if (element != null) {
            let endpoint = queryString('endpoint')
            // let endpoint = '/api/v1/customers/33/'
            console.warn('Endpoint:', endpoint)
            this.items = JSON.parse(queryString('options'))
            console.error(this.$el + 'content不存在')
        } else {
            console.error('#content 不存在')
        }
    }
})
