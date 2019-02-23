const content = new Vue({
    mixins: [base, get],
    el: '#content',
    data: {
        count: 0, previous: undefined, next: undefined, items: []
    },
    methods: {
        onLoadSuccess(code, data) {
            this.count = data.count
            this.previous = data.previous
            this.next = data.next
            this.items = data.results
        }
    }
})
