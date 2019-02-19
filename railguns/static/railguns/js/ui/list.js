"use strict";

var content = new Vue({
  mixins: [base, get],
  el: '#content',
  data: {
    count: 0,
    previous: undefined,
    next: undefined,
    items: []
  },
  methods: {
    onLoadSuccess: function onLoadSuccess(code, data) {
      if (code >= 200 && code < 300) {
        // 200, 201 才重绘
        this.count = data.count;
        this.previous = data.previous;
        this.next = data.next;
        this.items = data.results;
      }
    }
  }
});