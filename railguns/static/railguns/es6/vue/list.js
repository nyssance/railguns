var content = new Vue({
    el: '#content',
    data: function() {
        return {
            items: []
        }
    },
    mounted: function() {
        let element = this.$el
        if (element) {
            let endpoint = getEndpoint(element)
            if (endpoint) {
                getData(endpoint, null, function(response) {
                    this.items = response.results
                    if (this.items.length == 0) {
                    }
                }.bind(this))
            }
        } else {
            console.error('#content 不存在')
        }
    }
})
