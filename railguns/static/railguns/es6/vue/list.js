var content = new Vue({
    el: '#content',
    data: function () {
        return {
            endpoint: '',
            items: []
        }
    },
    mounted: function () {
        let element = this.$el
        if (element) {
            this.endpoint = getEndpoint(element)
            if (this.endpoint) {
                this.reload(null)
            }
        } else {
            console.error('#content 不存在')
        }
    },
    methods: {
        reload: function (params) {
            getData(this.endpoint, params, (response => {
                this.items = response.results
            }).bind(this))
        },
        // target 和 currentTarget 区别 https://juejin.im/post/59f16ffaf265da43085d4108
        toggle: function (event, params) {
            let className = 'weui-bar__item_on'
            let before = document.getElementsByClassName(className)[0]
            let after = event.target
            if (before !== after) {
                before.classList.remove(className)
                after.classList.add(className)
                this.reload(params)
            }
        }
    }
})
