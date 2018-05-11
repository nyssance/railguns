// https://cn.vuejs.org/v2/style-guide/#Prop-名大小写-强烈推荐
// https://cn.vuejs.org/v2/style-guide/#指令缩写-强烈推荐

// 💙 组件
Vue.component('app-footer', {
    template: `
        <!--<div class="weui-footer weui-footer_fixed-bottom">-->
        <div class="weui-footer">
            <br>
            <br>
            <p class="weui-footer__links">
                <!--<a href="javascript:home();" class="weui-footer__link">首页</a>-->
            </p>
            <p class="weui-footer__text">Copyright &copy; 2018 www.wowxjp.com</p>
        </div>`
})

// 菜单
Vue.component('menu-item', {
    props: ['icon', 'title', 'link'],
    template: `<a :href="link" class="material-icons mdc-top-app-bar__action-item" :aria-label="title" :alt="title">{{ icon }}</a>`
})

// 基本模版
const icon = `<div v-if="icon" class="weui-cell__hd"><img style="width: 40px;border-radius: 50%;margin-right: 15px;display: block" alt="" :src="icon"></div>`

const icon1 = `<div v-if="icon" class="weui-cell__hd" :style="style"><i :class="'fas fa-fw fa-' + icon" style="margin-right: 15px;display: block;"></i></div>`

const accessory = `<div v-if="link" class="weui-cell__ft"></div>`

const list_item_default = `
    ${icon1}
    <div class="weui-cell__bd">
        <span v-if="badges" style="vertical-align: middle">{{ title }}</span>
        <p v-else>{{ title }}</p>
        <span v-for="badge in badges" class="weui-badge" style="margin-left: 5px;">{{ badge }}</span>
    </div>
    <div class="weui-cell__ft"></div>`

const list_item_subtitle = `
    ${icon}
    <div class="weui-cell__bd">
        <span v-if="badges" style="vertical-align: middle">{{ title }}</span>
        <p v-else>{{ title }}</p>
        <span v-for="badge in badges" class="weui-badge" style="margin-left: 5px;">{{ badge }}</span>
        <p style="font-size: 13px;color: #888888;">{{ subtitle }}</p>
    </div>
    <div class="weui-cell__ft"></div>`

// SO: https://stackoverflow.com/questions/8122042/text-overflow-ellipsis-on-one-of-two-spans-inside-a-wrapper?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
const list_item_value1 = `
    ${icon}
    <div class="weui-cell__bd">
        <span v-if="badges" style="vertical-align: middle">{{ title }}</span>
        <p v-else>{{ title }}</p>
        <span v-for="badge in badges" class="weui-badge" style="margin-left: 5px;">{{ badge }}</span>
    </div>
    <div class="weui-cell__ft">{{ subtitle }}</div>`

// 列表 List
// - 网格列表
Vue.component('collection-list', {
    template: `
        <div class="weui-grids">
            <slot name="item"></slot>
        </div>`
})

// - 普通列表
Vue.component('table-list', {
    template: `
        <div>
            <slot name="section">Table List</slot>
        </div>`
})

// - 普通列表区块
Vue.component('table-list-section', {
    props: {
        grouped: {
            type: Boolean,
            default: true
        }
    },
    template: `
        <div v-if="grouped" class="weui-cells">
            <slot name="item"></slot>
        </div>
        <div v-else class="weui-cells" style="margin: 0">
            <slot name="item">
                <div class="weui-loadmore weui-loadmore_line">
                    <span class="weui-loadmore__tips">暂无数据</span>
                </div>
            </slot>
        </div>`
})

// 列表 : 区域头
Vue.component('list-section-header', {
    props: {
        title: {
            type: String,
            required: true
        }
    },
    template: `
        <div class="weui-cells__title">{{ title }}</div>`
})

// 列表 : 项 List Item
// - 默认
Vue.component('list-item-default', {
    props: ['icon', 'title', 'accessory', 'badges', 'link', 'datavalue', 'iconColor'],
    template: `
        <a v-if="link" :href="link" class="weui-cell weui-cell_access" :datavalue="datavalue">
            ${list_item_default}
        </a>
        <div v-else class="weui-cell" :datavalue="datavalue">
            ${list_item_default}
        </div>`,
    computed: { // SO: https://stackoverflow.com/a/42872117
        style() {
            return 'color: ' + this.iconColor
        }
    }
})

// - 副标题
Vue.component('list-item-subtitle', {
    props: ['icon', 'title', 'subtitle', 'accessory', 'badges', 'link'],
    template: `
        <a v-if="link" :href="link" class="weui-cell weui-cell_access">
            ${list_item_subtitle}
        </a>
        <div v-else class="weui-cell">
            ${list_item_subtitle}
        </div>`
})

// - 左右
Vue.component('list-item-value1', {
    props: ['icon', 'title', 'subtitle', 'accessory', 'badges', 'link', 'datavalue'],
    template: `
        <a v-if="link" :href="link" class="weui-cell weui-cell_access" :datavalue="datavalue">
            ${list_item_value1}
        </a>
        <div v-else class="weui-cell" :datavalue="datavalue">
            ${list_item_value1}
        </div>`
})

// 面板
Vue.component('panel', {
    props: ['icon', 'title', 'subtitle', 'badges', 'link'],
    template: `
        <a :href="link" class="weui-media-box weui-media-box_appmsg">
            <div class="weui-media-box__hd">
                <img class="weui-media-box__thumb" :src="icon" style="border-radius: 50%">
            </div>
            <div class="weui-media-box__bd">
                <h4 class="weui-media-box__title">{{ title }}</h4>
                <p class="weui-media-box__desc">{{ subtitle }}</p>
            </div>
        </a>`
})

// - 卡片
Vue.component('small-card', {
    props: ['icon', 'title', 'subtitle', 'accessory', 'badges', 'meta', 'time', 'extra', 'link'],
    template: `
        <a :href="link" class="weui-media-box weui-media-box_appmsg">
            <div v-if="icon" class="weui-media-box__hd">
                <img class="weui-media-box__thumb" alt="" :src="icon">
            </div>
            <div class="weui-media-box__bd">
                <h4 class="weui-media-box__title">{{ title }}</h4>
                <p class="weui-media-box__desc">{{ subtitle }}</p>
                <ul class="weui-media-box__info">
                    <li class="weui-media-box__info__meta">{{ meta }}</li>
                    <li class="weui-media-box__info__meta">{{ time }}</li>
                    <li class="weui-media-box__info__meta weui-media-box__info__meta_extra">{{ extra }}</li>
                </ul>
            </div>
        </a>`
})

// Grid Item
Vue.component('grid-item', {
    props: ['icon', 'title', 'subtitle', 'badges', 'link', 'iconColor'],
    template: `
        <a :href="link" class="weui-grid">
            <div v-if="icon" class="weui-grid__icon">
                <img :src="icon" :style="style" alt="">
            </div>
            <p class="weui-grid__label">{{ subtitle }}</p>
            <p class="weui-grid__label">{{ title }}</p>
        </a>`,
    computed: {
        style() {
            return 'color: ' + this.iconColor
        }
    }
})

// 表单
// required 待优化 required pattern=".{1,}"
Vue.component('text-field', {
    // props: ['name', 'helper_text', 'value', 'type'],
    props: {
        id: {
            type: String
        },
        name: {
            type: String
        },
        placeholder: {
            type: String,
            required: false
        },
        value: {
            type: String,
            required: false
        },
        type: {
            type: String,
            default: 'text'
        }
    },
    template: `
        <div class="weui-cell">
            <div class="weui-cell__hd">
                <label class="weui-label">{{ name }}</label>
            </div>
            <div class="weui-cell__bd">
                <input class="weui-input" :placeholder="placeholder" :type="type" :id="id">
            </div>
        </div>`,
    methods: {
        updateValue: function (value) {
            this.$emit('input', value)
        }
    }
})

Vue.component('text-field1', {
    props: ['name', 'helper_text', 'value'],
    template: `
        <div class="weui-cell">
            <div class="weui-cell__hd">
                <label class="weui-label">{{ name }}</label>
            </div>
            <div class="weui-cell__bd">
                <input type="text" 
                    v-bind:value="value"
                    v-on:input="updateValue($event.target.value)">
            </div>
        </div>`,
    methods: {
        updateValue: function (value) {
            this.$emit('input', value)
        }
    }
})

// Swiper
Vue.component('swiper', {
    props: {
        height: {
            type: Number,
            default: 9 / 16
        },
        delay: {
            type: Number,
            default: 3000
        },
        loop: {
            type: Boolean,
            default: true
        },
        pagination: {
            type: Boolean,
            default: false
        }
    },
    template: `
        <div class="swiper-container">
            <div class="swiper-wrapper">
                <slot name="slide"></slot>
            </div>
             <!-- 如果需要分页器 -->
             <div v-if="pagination" class="swiper-pagination"></div>
        </div>`,
    mounted: function () {
        let screenWidth = Math.max(document.documentElement.clientWidth, window.innerWidth || 0)
        let height = screenWidth * this.height
        this.$el.style.height = height + 'px'
    },
    updated: function () {
        let mySwiper = new Swiper('.swiper-container', {
            autoplay: {
                delay: this.delay
            },
            loop: this.loop,
            pagination: {
                el: '.swiper-pagination'
            }
        })
    }
})

Vue.component('swiper-slide', {
    props: ['title', 'image', 'link'],
    template: `
        <a v-if="link" :href="link" class="swiper-slide">{{ title }}</a>
        <div v-else class="swiper-slide">{{ title }}</div>`,
    mounted: function () {
        if (this.image) {
            this.$el.style.backgroundImage = 'url(' + this.image + ')'
            this.$el.style.backgroundPosition = 'center'
            this.$el.style.backgroundSize = 'cover'
        } else {
            this.$el.style.backgroundColor = '#00e871'
        }
    }
})

// 💙 过滤器
Vue.filter('dateFormat', (dateStr, pattern = 'YYYY-MM-DD HH:mm:ss') => {
    return dateStr ? moment(dateStr).format(pattern) : 'null' // moment会自动容错输出当前时间, 真是多此一举.
})
