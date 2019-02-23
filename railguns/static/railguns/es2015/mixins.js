const base = {
    data: {
        call: {method: null, endpoint: null}
    },
    methods: {
        onPrepare() {
            console.warn(JSON.stringify(this.$data))
        },
        onLoadSuccess(code, data) {
            console.warn('请覆写 onLoadSuccess')
        },
        onLoadFailure(code, message) {
            showAlert(code, message)
        },
        request(params) {
            httpUtilrequest(this.call.method, this.call.endpoint, params, (code, data) => {
                this.onLoadSuccess(code, data)
            }, (code, message) => {
                this.onLoadFailure(code, message)
            })
        }
    }
}

const get = {
    mounted() {
        this.call.method = 'GET'
        this.onPrepare()
        this.refresh()
    },
    methods: {
        // 💛 Action
        refresh(params) {
            if (this.call.endpoint && this.call.endpoint.trim()) {
                this.isLoading = true
                this.request()
            }
        }
    }
}

const post = {
    data: {
        params: {}, next: ''
    },
    mounted() {
        this.call.method = this.$el.dataset.method
        this.onPrepare()
    },
    methods: {
        onSubmit() {
        },
        onLoadSuccess(code, data) {
            const url = new URL(document.URL)
            const next = url.searchParams.get('next')
            next && (location = next)
        },
        // 💛 Action
        submit(event) {
            this.onSubmit()
            this.request(this.params)
        }
    }
}

const patch = {
    data: {
        params: {}
    },
    mounted() {
        this.call.method = this.$el.dataset.method
        this.onPrepare()
    },
    methods: {
        onSubmit() {
        },
        // 💛 Action
        submit(event) {
            this.onSubmit()
            this.request(this.params)
        }
    }
}
