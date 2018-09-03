const base = {
    mounted: function () {
        let element = this.$el
        if (element) {
            this.endpoint = getEndpoint(element)
            this.onPrepare()
        } else {
            console.error('#content 不存在')
        }
    },
    methods: {
        onPrepare: function () {
            if (this.endpoint) {
                this.reload()
            }
        },
        reload: function (params) {
            get(this.endpoint, params, (response => {
                this.onLoadSuccess(response)
            }).bind(this), error => {
                this.onLoadFailure(error)
            })
        },
        onLoadSuccess(response) {
            console.warn('请覆写 onLoadSuccess')
        },
        onLoadFailure(error) {
            let data = error.response.data
            let message
            if (data) {
                message = JSON.stringify(data)
            }
            showAlert(error.response.status, message ? message : error.response.statusText)
        }
    }
}
