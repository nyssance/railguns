'use strict'

var content = new Vue({
    el: '#content',
    data: {
        items: []
    },
    mounted: function() {
        let element = this.$el
        if (element != null) {
            this.items = JSON.parse(getQueryString('options'))
        } else {
            console.error('#content 不存在')
        }
    },
    updated: function() {
        let endpoint = getQueryString('endpoint')
        let selected = getQueryString('selected')
        console.warn('Endpoint:', endpoint)
        console.warn('Selected:', selected)
        for (let a of document.getElementsByTagName('a')) {
            if (a.attributes['class'].value == 'mdc-list-item') {
                let i = a.getElementsByTagName('i')
                if (a.attributes['datavalue'].value == selected) {
                    i[0].innerHTML = 'radio_button_checked'
                }
            }
        }
    }
})
