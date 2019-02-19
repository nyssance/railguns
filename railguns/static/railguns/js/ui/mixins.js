"use strict";

var base = {
  data: {
    endpoint: null
  },
  methods: {
    onPrepare: function onPrepare() {
      console.warn(JSON.stringify(this.$data));
    },
    onLoadSuccess: function onLoadSuccess(code, data) {
      console.warn('请覆写 onLoadSuccess');
    },
    onLoadFailure: function onLoadFailure(code, message) {
      showAlert(code, message);
    }
  }
};
var get = {
  mounted: function mounted() {
    this.endpoint = this.$el.dataset.endpoint || ''; // 从页面获取 Endpoint

    this.onPrepare();
    this.refresh();
  },
  methods: {
    // 💛 Action
    refresh: function refresh(params) {
      var _this = this;

      if (this.endpoint.trim()) {
        this.isLoading = true;
        httpUtilenqueue('GET', this.endpoint, params, function (code, data) {
          _this.onLoadSuccess(code, data);
        }, function (code, message) {
          _this.onLoadFailure(code, message);
        });
      }
    }
  }
};
var post = {
  data: {
    params: {},
    next: ''
  },
  mounted: function mounted() {
    this.endpoint = this.$el.dataset.endpoint || ''; // 从页面获取 Endpoint

    this.onPrepare();
  },
  methods: {
    onSubmit: function onSubmit() {},
    onLoadSuccess: function onLoadSuccess(code, data) {
      var url = new URL(document.URL);
      var next = url.searchParams.get('next');
      next && (location = next);
    },
    // 💛 Action`
    submit: function submit(event) {
      var _this2 = this;

      this.onSubmit();
      httpUtilenqueue('POST', this.endpoint, this.params, function (code, data) {
        _this2.onLoadSuccess(code, data);
      }, function (code, message) {
        _this2.onLoadFailure(code, message);
      });
    }
  }
};