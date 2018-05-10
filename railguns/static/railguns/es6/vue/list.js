var content = new Vue({
    el: '#content',
    data: function () {
        return {
            items: []
        }
    },
    mounted: function () {
        let element = this.$el
        if (element) {
            let endpoint = getEndpoint(element)
            this.getList(endpoint, null)
        } else {
            console.error('#content 不存在')
        }
    },
    methods: {
        getList: function (endpoint, params) {
            if (endpoint) {
                getData(endpoint, params, function (response) {
                    this.items = response.results
                    if (this.items.length == 0) {
                    }
                }.bind(this))
            }
        },
        // target 和 currentTarget 区别 https://juejin.im/post/59f16ffaf265da43085d4108
        toggle: function (event, params) {
            let className = 'weui-bar__item_on'
            let before = document.getElementsByClassName(className)[0]
            let after = event.target
            if (before !== after) {
                before.classList.remove(className)
                after.classList.add(className)
                let element = document.getElementById('content')
                let endpoint = getEndpoint(element)
                this.getList(endpoint, params)
            }
        }
    }
})
