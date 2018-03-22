'use strict'

var content = new Vue({
    el: '#content',
    data: function() {
        return {
            items: []
        }
    },
    mounted: function() {
        let element = this.$el
        if (element != null) {
            let endpoint = getEndpoint(element)
            getData(endpoint, null, function(response) {
                this.items = response['results']
            }.bind(this))
        } else {
            console.error('#content 不存在')
        }
    }
})
