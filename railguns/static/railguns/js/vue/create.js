'use strict';

var content = new Vue({
    mixins: [base],
    el: '#content',
    data: function data() {
        return {
            endpoint: '',
            data: {}
        };
    },
    methods: {
        onPrepare: function onPrepare() {
            console.warn('onPrepare overwrite');
        },
        submit: function submit(event) {
            var _this = this;

            // !this.data.name || !this.data.id_card_number ||
            if (!this.data.phone_number || !this.data.password || !this.data.code) {
                this.showAlert('请填写完整所有项');
                return;
            }
            if (this.errors) {
                this.showAlert(JSON.stringify(this.errors));
                return;
            }
            console.warn(this.data); // 返回的是一个包含很多内容东西的对象 里边还有不想要的东西
            var obj = JSON.stringify(this.data); // JSON.stringify() 方法用于将 JavaScript 值转换为 JSON 字符串. 为了清除不想要的东西
            console.log(obj);
            post(this.endpoint, this.data, function (response) {
                var url = new URL(document.URL);
                var next = url.searchParams.get('next');
                location = next ? next : '/';
            }, function (error) {
                _this.onLoadFailure(error);
            });
        },
        create_order: function create_order(event) {
            var _this2 = this;

            var product_id = getQueryString('product_id');
            // let product_id = obj.dataset.product_id
            if (!product_id) {
                this.showAlert('产品编号不能为空。');
                return;
            }
            var data = { product_id: product_id, merchant_id: 1, payment_number: 3 };
            post(this.endpoint, data, function (response) {
                _this2.showAlert('成功，订单编号: ' + JSON.stringify(response.id));
                // location = '/purchase/?order_id=' + response.id
            }, function (error) {
                _this2.onLoadFailure(error);
            });
        }
    }
});