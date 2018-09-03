"use strict";

var base = {
  mounted: function mounted() {
    var element = this.$el;

    if (element) {
      this.endpoint = getEndpoint(element);
      this.onPrepare();
    } else {
      console.error('#content 不存在');
    }
  },
  methods: {
    onPrepare: function onPrepare() {
      if (this.endpoint) {
        this.reload();
      }
    },
    reload: function reload(params) {
      var _this = this;

      get(this.endpoint, params, function (response) {
        _this.onLoadSuccess(response);
      }.bind(this), function (error) {
        _this.onLoadFailure(error);
      });
    },
    onLoadSuccess: function onLoadSuccess(response) {
      console.warn('请覆写 onLoadSuccess');
    },
    onLoadFailure: function onLoadFailure(error) {
      var data = error.response.data;
      var message;

      if (data) {
        message = JSON.stringify(data);
      }

      showAlert(error.response.status, message ? message : error.response.statusText);
    }
  }
};