const base = {
    data: {
        endpoint: null
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
        }
    }
}

const get = {
    mounted() {
        this.endpoint = this.$el.dataset.endpoint || '' // 从页面获取 Endpoint
        this.onPrepare()
        this.refresh()
    },
    methods: {
        // 💛 Action
        refresh(params) {
            if (this.endpoint.trim()) {
                this.isLoading = true
                httpUtilenqueue('GET', this.endpoint, params, (code, data) => {
                    this.onLoadSuccess(code, data)
                }, (code, message) => {
                    this.onLoadFailure(code, message)
                })
            }
        }
    }
}

const post = {
    data: {
        params: {}, next: ''
    },
    mounted() {
        this.endpoint = this.$el.dataset.endpoint || '' // 从页面获取 Endpoint
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
        // 💛 Action`
        submit(event) {
            this.onSubmit()
            httpUtilenqueue('POST', this.endpoint, this.params, (code, data) => {
                this.onLoadSuccess(code, data)
            }, (code, message) => {
                this.onLoadFailure(code, message)
            })
        }
    }
}
