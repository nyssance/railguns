const content = new Vue({
    mixins: [base],
    el: '#content',
    data: {
        // endpoint: '',
        count: 0,
        previous: null,
        next: null,
        items: []
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
