let content = new Vue({
    mixins: [base],
    el: '#content',
    data: function () {
        return {
            endpoint: '',
            count: 0,
            previous: null,
            next:null,
            items: []
        }
    },
    methods: {
        onLoadSuccess(response) {
            this.count = response.count
            this.previous = response.previous
            this.next = response.next
            this.items = response.results
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
