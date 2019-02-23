const content = new Vue({
    mixins: [base, patch],
    el: '#content',
    data: {
        property: undefined, oldValue: undefined, newValue: undefined, items: []
    },
    updated() { // 组件挂载之后
        document.querySelectorAll('input').forEach(it => {
            if (it.attributes['type'].value === 'radio') {
                // SO: https://stackoverflow.com/questions/11973678/difference-between-element-value-and-element-getattributevalue
                if (this.oldValue.toString() === it.value) {
                    it.setAttribute('checked', 'checked')
                } else {
                    // it.removeAttribute('checked')
                }
                it.onclick = event => {
                    this.newValue = it.value
                    if (this.oldValue.toString() === this.newValue) { // === 无法判断数字
                        console.warn('与之前相同, 不提交服务器更新')
                        // history.back() // 只返回不刷新
                    } else {
                        this.submit()
                    }
                }
            }
        })
    },
    methods: {
        onPrepare() { // TODO: 动态获取这些值
            this.call.endpoint = '/api/v1/me/'
            this.property = 'gender'
            this.oldValue = 'f'
            this.items = [
                {label: '男', value: 'm'},
                {label: '女', value: 'f'}
            ]
        },
        onSubmit() {
            this.params = {[this.property]: this.newValue}
        },
        onLoadSuccess(code, data) { // 默认模式是返回
            this.oldValue = this.newValue
            // history.back()
            // location.replace(endpoint.replace('/api/v1/', '/'))
        }
    }
})
