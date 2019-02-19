"use strict";

var content = new Vue({
  mixins: [base, get],
  el: '#content',
  data: {
    data: ''
  },
  updated: function updated() {// 组件挂载之后
    // generateUpdateLink()
  },
  methods: {
    onLoadSuccess: function onLoadSuccess(code, data) {
      this.data = data;
    }
  }
});