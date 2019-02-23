const content = new Vue({
    mixins: [base, get],
    el: '#content',
    data: {
        object: ''
    },
    methods: {
        onLoadSuccess(code, data) {
            this.object = data
        }
    }
})
