"use strict";

var content = new Vue({
  mixins: [base],
  el: '#content',
  data: function data() {
    return {
      endpoint: '',
      count: 0,
      previous: null,
      next: null,
      items: []
    };
  },
  methods: {
    onLoadSuccess: function onLoadSuccess(response) {
      this.count = response.count;
      this.previous = response.previous;
      this.next = response.next;
      this.items = response.results;
    },
    // target 和 currentTarget 区别 https://juejin.im/post/59f16ffaf265da43085d4108
    toggle: function toggle(event, params) {
      var className = 'weui-bar__item_on';
      var before = document.getElementsByClassName(className)[0];
      var after = event.target;

      if (before !== after) {
        before.classList.remove(className);
        after.classList.add(className);
        this.reload(params);
      }
    }
  }
});