const base = {
  data: {
    call: { method: undefined, endpoint: undefined }
  },
  methods: {
    onPrepare () {
      console.groupCollapsed('onPrepare')
      console.warn(JSON.stringify(this.$data))
      console.groupEnd()
    },
    onLoadSuccess (code, data) {
      console.warn('请覆写 onLoadSuccess')
    },
    onLoadFailure (code, message) {
      showAlert(code, message)
    },
    // 💛 快捷方法
    back () {
      history.back()
    },
    request (params) {
      httpUtilrequest(this.call.method, this.call.endpoint, params, (code, data) => {
        this.onLoadSuccess(code, data)
      }, (code, message) => {
        this.onLoadFailure(code, message)
      })
    }
  }
}

const get = {
  mounted () {
    this.call.method = 'GET'
    this.onPrepare()
    this.refresh()
  },
  methods: {
    // 💛 Action
    refresh (params) {
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
  mounted () {
    this.call.method = 'POST'
    this.onPrepare()
  },
  methods: {
    onSubmit () {
    },
    onLoadSuccess (code, data) {
      const url = new URL(document.URL)
      const next = url.searchParams.get('next')
      next && (location = next)
    },
    // 💛 Action
    submit (event) {
      this.onSubmit()
      this.request(this.params)
    }
  }
}

const patch = {
  data: {
    params: {}
  },
  mounted () {
    this.call.method = 'PATCH'
    this.onPrepare()
  },
  methods: {
    onSubmit () {
    },
    // 💛 Action
    submit (event) {
      this.onSubmit()
      this.request(this.params)
    }
  }
}
