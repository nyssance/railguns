// https://cn.vuejs.org/v2/guide/components.html#注册
// 对于自定义标签名，Vue.js 不强制要求遵循 W3C 规则 (小写，并且包含一个短杠)，尽管遵循这个规则比较好。

// https://cn.vuejs.org/v2/guide/components.html#组件命名约定
// 这意味着 PascalCase 是最通用的 声明约定 而 kebab-case 是最通用的 使用约定。

// 综上，使用 kebab-case 最不容易引起不必要的bug
// https://cn.vuejs.org/v2/style-guide/#Prop-名大小写-强烈推荐
// https://cn.vuejs.org/v2/style-guide/#指令缩写-强烈推荐

// Vue 太蠢, 不区分html注释和正式代码

const showActionSheet = (title, actions, cancelAction) => {
  weui.actionSheet(actions, [{
    label: '取消', onClick: () => {
      cancelAction && cancelAction()
    }
  }], {
    title: title, onClose: () => {
    }
  })
}

const showAlert = (title, message, action) => {
  if (action) {
    weui.confirm(message, action, undefined, { title })
  } else {
    weui.alert(message, { title })
  }
}
const showSnackbar = (message, duration = 2000) => {
  weui.topTips(message, { duration })
}

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
            <p class="weui-footer__text">Copyright &copy; 2019 www.yourdomain.com</p>
        </div>`
})

// TabBar 底部导航
Vue.component('tabbar', {
  template: `
        <div class="weui-tab">
            <div class="weui-tab__panel">
                <slot></slot>
            </div>
            <div class="weui-tabbar">
                <slot name="tab"></slot>
            </div>
        </div>`
})

Vue.component('tabbar-item', {
  props: {
    icon: { type: String, required: true },
    title: { type: String, required: true },
    link: { type: String, required: true },
    selected: { type: Boolean, default: false }
  },
  template: `<a :href="link" :class="'weui-tabbar__item' + selected_class">
                   <img :src="icon" class="weui-tabbar__icon" alt="">
                   <p class="weui-tabbar__label">{{ title }}</p>
               </a>`,
  computed: {
    selected_class () {
      return this.selected ? ' weui-bar__item_on' : ''
    }
  }
})

// Pager
Vue.component('pager', {
  template: `
        <div class="weui-tab">
            <div class="weui-navbar">
                <slot name="tab"></slot>
            </div>
            <div class="weui-tab__panel">
                <slot></slot>
            </div>
        </div>`
})

Vue.component('pager-item', {
  props: {
    title: { type: String, required: true },
    selected: { type: Boolean, default: false },
    method: {
      type: Function,
      required: false,
      default: () => {
        showSnackbar('请在 pager-item 组件中传入一个方法, 例如 :method="refresh"')
      }
    }
  },
  template: `
        <div :class="'weui-navbar__item' + selected_class" @click="toggle($event, method)">
            {{ title }}
        </div>`,
  computed: {
    selected_class () {
      return this.selected ? ' weui-bar__item_on' : ''
    }
  },
  methods: {
    toggle (event, method) { // target 和 currentTarget 区别 https://juejin.im/post/59f16ffaf265da43085d4108
      const className = 'weui-bar__item_on'
      const before = document.getElementsByClassName(className)[0]
      const after = event.target
      if (before !== after) {
        before.classList.remove(className)
        after.classList.add(className)
        method()
      }
    }
  }
})

Vue.component('pager-content', {
  template: `
        <div class="weui-tab__content">
            <slot></slot>
        </div>`
})

Vue.component('msg-page', {
  props: {
    icon: {
      type: String,
      required: true,
      validator: value => [
        'success', 'success-no-circle',
        'info', 'info-circle',
        'warn',
        'waiting', 'circle', 'download', 'cancel', 'search'].includes(value)
    },
    title: {
      type: String,
      required: true
    },
    message: {
      type: String,
    },
    type: {
      type: String,
      default: '',
      validator: value => ['', '-primary'].includes(value)
    }
  },
  template: `
        <div class="weui-msg">
            <div class="weui-msg__icon-area"><i :class="'weui-icon-' + icon + ' weui-icon_msg' + type"></i></div>
            <div class="weui-msg__text-area">
                <h2 class="weui-msg__title">{{ title }}</h2>
                <p class="weui-msg__desc">{{ message }}</p>
            </div>
            <div class="weui-msg__opr-area">
                <p class="weui-btn-area">
                    <slot></slot>
                </p>
            </div>
            <div class="weui-msg__extra-area">
                <slot name="extra"></slot>
            </div>
    </div>`
})

// 基本模版
const icon = `<div v-if="icon" class="weui-cell__hd"><img :src="icon" style="width: 40px;border-radius: 50%;margin-right: 15px;display: block" alt=""></div>`

const icon1 = `<div v-if="icon" class="weui-cell__hd" :style="style"><i :class="'fas fa-fw fa-' + icon" style="margin-right: 15px;display: block;"></i></div>`

const accessory = `<div v-if="link" class="weui-cell__ft"></div>`

const list_item_default = `
    ${icon1}
    <div class="weui-cell__bd">
        <span v-if="badges" style="vertical-align: middle">{{ title }}</span>
        <p v-else>{{ title }}</p>
        <span v-for="badge in badges" class="weui-badge" style="margin-left: 5px;">{{ badge }}</span>
    </div>`

const list_item_subtitle = `
    ${icon}
    <div class="weui-cell__bd">
        <span v-if="badges" style="vertical-align: middle">{{ title }}</span>
        <p v-else>{{ title }}</p>
        <span v-for="badge in badges" class="weui-badge" style="margin-left: 5px;">{{ badge }}</span>
        <p style="font-size: 13px;color: #888888;">{{ subtitle }}</p>
    </div>`

// SO https://stackoverflow.com/questions/8122042/text-overflow-ellipsis-on-one-of-two-spans-inside-a-wrapper?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
const list_item_value1 = `
    ${icon}
    <div class="weui-cell__bd">
        <span v-if="badges" style="vertical-align: middle">{{ title }}</span>
        <p v-else>{{ title }}</p>
        <span v-for="badge in badges" class="weui-badge" style="margin-left: 5px;">{{ badge }}</span>
    </div>
    <div class="weui-cell__ft">{{ subtitle }}</div>`

// 列表视图 ListView
// - 网格列表
Vue.component('grid-view', {
  template: `
        <div class="weui-grids">
            <slot></slot>
        </div>`
})

// - 普通列表
Vue.component('list-view', {
  template: `
        <div style="background: #f8f8f8; width: 100vh; height: 100vh">
            <slot>
                <div class="weui-loadmore weui-loadmore_line">
                    <span class="weui-loadmore__tips">暂无数据</span>
                </div>
            </slot>
        </div>`
})

// - 普通列表区块
Vue.component('list-section', {
  template: `
        <div class="weui-cells">
            <slot></slot>
        </div>`
})

// 列表::区域头
Vue.component('list-section-header', {
  props: {
    title: { type: String, required: true }
  },
  template: `
        <div class="weui-cells__title">{{ title }}</div>`
})

// Grid Item
Vue.component('grid-item', {
  props: {
    icon: { type: String, },
    title: { type: String, required: true, default: '' },
    subtitle: { type: [String, Number], required: true, default: '' },
    badges: { type: Array },
    link: { type: String },
    iconColor: { type: String }
  },
  template: `
        <a :href="link" class="weui-grid">
            <div v-if="icon" class="weui-grid__icon">
                <img :src="icon" :style="style" alt="">
            </div>
            <p class="weui-grid__label">{{ subtitle }}</p>
            <p class="weui-grid__label">{{ title }}</p>
        </a>`,
  computed: {
    style () {
      return `color: ${this.iconColor}`
    }
  }
})

// 列表::项 List Item
// - 默认
Vue.component('list-item-default', {
  props: {
    icon: { type: String },
    title: { type: String, required: true, default: '' },
    accessory: { type: String },
    badges: { type: Array },
    link: { type: String },
    iconColor: { type: String }
  },
  template: `
        <a v-if="link" :href="link" class="weui-cell weui-cell_access">
            ${list_item_default}
            <div class="weui-cell__ft"></div>
        </a>
        <div v-else class="weui-cell">
            ${list_item_default}
        </div>`,
  computed: {
    style () {
      return `color: ${this.iconColor}`
    }
  }
})

// - 副标题
Vue.component('list-item-subtitle', {
  props: {
    icon: { type: String },
    title: { type: String, required: true, default: '' },
    subtitle: { type: [String, Number], required: true, default: '' },
    accessory: { type: String },
    badges: { type: Array },
    link: { type: String }
  },
  template: `
        <a v-if="link" :href="link" class="weui-cell weui-cell_access">
            ${list_item_subtitle}
            <div class="weui-cell__ft"></div>
        </a>
        <div v-else class="weui-cell">
            ${list_item_subtitle}
        </div>`
})

// - 左右
Vue.component('list-item-value1', {
  props: {
    icon: { type: String },
    title: { type: String, required: true, default: '' },
    subtitle: { type: [String, Number], required: true, default: '' },
    accessory: { type: String },
    badges: { type: Array },
    link: { type: String }
  },
  template: `
        <a v-if="link" :href="link" class="weui-cell weui-cell_access">
            ${list_item_value1}
        </a>
        <div v-else class="weui-cell">
            ${list_item_value1}
        </div>`
})

// - 卡片
Vue.component('card', {
  props: {
    icon: { type: String },
    title: { type: String, required: true, default: '' },
    subtitle: { type: [String, Number], required: true, default: '' },
    accessory: { type: String },
    badges: { type: Array },
    //
    meta: { type: [String, Number] },
    time: { type: String },
    extra: { type: [String, Number] },
    link: { type: String },
    //
    button: { type: String },
    buttonLink: { type: String }
  },
  template: `
        <a :href="link" class="weui-media-box weui-media-box_appmsg">
            <div v-if="icon" class="weui-media-box__hd">
                <img :src="icon" class="weui-media-box__thumb" alt="">
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
            <a v-if="button" :href="buttonLink" class="weui-btn weui-btn_mini weui-btn_primary">{{ button }}</a>
        </a>`
})

// 面板
Vue.component('panel', {
  props: {
    icon: { type: String, required: true },
    title: { type: String, required: true, default: '' },
    subtitle: { type: [String, Number], required: true, default: '' },
    badges: { type: Array },
    link: { type: String },
    //
    button: { type: String },
    buttonLink: { type: String }
  },
  template: `
        <a :href="link" class="weui-media-box weui-media-box_appmsg">
            <div class="weui-media-box__hd">
                <img class="weui-media-box__thumb" :src="icon" style="border-radius: 50%">
            </div>
            <div class="weui-media-box__bd">
                <h4 class="weui-media-box__title">{{ title }}</h4>
                <p class="weui-media-box__desc">{{ subtitle }}</p>
            </div>
            <a v-if="button" :href="buttonLink" class="weui-btn weui-btn_mini weui-btn_primary">{{ button }}</a>
        </a>`
})

// 文章
Vue.component('article-html', {
  props: ['text'],
  template: `<article class="weui-article" v-html="text"></article>`
})

// - 按钮
Vue.component('button-area', {
  template: `
        <div class="weui-btn-area">
            <slot></slot>
        </div>`
})

Vue.component('button-primary', {
  props: {
    title: { type: String, required: true }
  },
  template: `<button class="weui-btn weui-btn_primary">{{ title }}</button>`
})

Vue.component('button-default', {
  props: {
    title: { type: String, required: true }
  },
  template: `<button class="weui-btn weui-btn_default">{{ title }}</button>`
})

// - 表单
// 单选
Vue.component('form-area', {
  template: `
        <div class="weui-cells weui-cells_form">
            <slot></slot>
        </div>`
})

// 单选
Vue.component('option-set', {
  template: `
        <div class="weui-cells weui-cells_radio">
            <slot></slot>
        </div>`
})

Vue.component('option-radio', {
  props: {
    title: { type: String, required: true, default: '' },
    name: { type: String, required: true },
    value: { type: [String, Number] },
    id: { type: [String, Number], required: true }
  },
  template: `
        <label class="weui-cell weui-check__label" :for="id">
            <div class="weui-cell__bd">{{ title }}</div>
            <div class="weui-cell__ft">
                <input type="radio" class="weui-check" :name="name" :value="value" :id="id" required>
                <span class="weui-icon-checked"></span>
            </div>
        </label>`
})

// required 待优化 required pattern=".{1,}"
Vue.component('text-field', {
  props: {
    name: { type: String },
    placeholder: { type: String },
    value: { type: [String, Number] },
    type: {
      type: String,
      default: 'text',
      validator: value => ['text', 'number', 'tel', 'date', 'datetime-local', 'password'].includes(value)
    },
    required: { type: String }
  },
  template: `
        <div class="weui-cell">
            <div v-if="name" class="weui-cell__hd">
                <label class="weui-label">{{ name }}</label>
            </div>
            <div class="weui-cell__bd">
                <input class="weui-input" :placeholder="placeholder" :type="type" :required="required"
                       :value="value"
                       @input="$emit('input', $event.target.value)">
            </div>
        </div>`
})

// Swiper
Vue.component('swiper', {
  props: {
    height: { type: Number, default: 9 / 16 },
    delay: { type: Number, default: 3000 },
    loop: { type: Boolean, default: true },
    pagination: { type: Boolean, default: false }
  },
  template: `
        <div class="swiper-container">
            <div class="swiper-wrapper">
                <slot></slot>
            </div>
             <!-- 如果需要分页器 -->
             <div v-if="pagination" class="swiper-pagination"></div>
        </div>`,
  mounted () {
    const screenWidth = Math.max(document.documentElement.clientWidth, window.innerWidth || 0)
    const height = screenWidth * this.height
    this.$el.style.height = `${height}px`
  },
  updated () {
    const mySwiper = new Swiper('.swiper-container', {
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

Vue.component('swiper-item', {
  props: {
    image: { type: String },
    title: { type: String },
    link: { type: String }
  },
  template: `
        <a v-if="link" :href="link" class="swiper-slide">{{ title }}</a>
        <div v-else class="swiper-slide">{{ title }}</div>`,
  mounted () {
    if (this.image) {
      this.$el.style.backgroundImage = `url(${this.image})`
      this.$el.style.backgroundPosition = 'center'
      this.$el.style.backgroundSize = 'cover'
    } else {
      this.$el.style.backgroundColor = '#00e871'
    }
  }
})

// 💙 过滤器
// 时间过滤器 moment会自动容错输出当前时间, 真是多此一举.
Vue.filter('dateFormat', (dateStr, pattern = 'YYYY-MM-DD HH:mm:ss') => dateStr ? moment(dateStr).format(pattern) : 'null')
