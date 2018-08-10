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
            this.showAlert(JSON.stringify(error.response.data))
        },
        showAlert: function (message) {
            bd.innerHTML = message ? message : error.response.status + ' ( ' + error.response.statusText + ' )'
            dialog.style.display = ''
        }
    }
}
