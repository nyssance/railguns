"use strict";

var base = {
  mounted: function mounted() {
    this.onPrepare();
    this.refresh();
  },
  methods: {
    onPrepare: function onPrepare() {
      this.endpoint = this.$el.dataset.endpoint || ''; // 从页面获取 Endpoint
    },
    onLoadSuccess: function onLoadSuccess(code, data) {
      console.warn('请覆写 onLoadSuccess');
    },
    onLoadFailure: function onLoadFailure(code, message) {
      showAlert(code, message);
    },
    // 💛 Action
    refresh: function refresh(params) {
      var _this = this;

      if (this.endpoint.trim()) {
        this.isLoading = true;
        httpUtilenqueue('get', this.endpoint, params, function (code, data) {
          _this.onLoadSuccess(code, data);
        }.bind(this), function (code, message) {
          _this.onLoadFailure(code, message);
        });
      }
    }
  }
};