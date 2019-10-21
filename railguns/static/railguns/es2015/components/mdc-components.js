// 组件
Vue.component('app', {
    template: `<div class="container"><div class="topBar">这个地方在渲染后不会被占用</div><slot></slot></div>`
})
Vue.component('app-header', {
    template: `<div class="header" slot="header">this is header</div>`
})
Vue.component('app-content', {
    template: `<div class="content">this is content</div>`
})
Vue.component('app-footer', {
    template: `<div style="text-align: center; padding: 20px 0;">{{ title }}</div>`
})

// 基本模版
const icon = `<img v-if="icon" class="mdc-list-item__graphic" :src="icon">`

// style="color: #fce4ec; background-color: #ec407a; width: 40px; height: 40px; border-radius: 50%;" 
const icon1 = `<span v-if="icon" class="mdc-list-item__graphic" role="presentation" :style="style">
  <i class="material-icons" aria-hidden="true">{{ icon }}</i>
</span>`

const accessory_link = `    <a v-if="accessory" href="#" class="mdc-list-item__meta material-icons"
        aria-label="Add to favorites" title="Add to favorites"
        onclick="event.preventDefault()">{{ accessory }}</a>`

const accessory = `<i v-if="accessory" class="mdc-list-item__meta material-icons">{{ accessory }}</i>
<i v-else-if="link" class="mdc-list-item__meta material-icons">chevron_right</i>`

const list_item_default = `
    ${icon1}
    {{ title }}
    ${accessory}`

const list_item_subtitle = `
    ${icon}
    <span class="mdc-list-item__text">
        {{ title }}
        <span class="mdc-list-item__secondary-text">{{ subtitle }}</span>
    </span>
    ${accessory}`

// SO https://stackoverflow.com/questions/8122042/text-overflow-ellipsis-on-one-of-two-spans-inside-a-wrapper?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
const list_item_value1 = `
    ${icon}
    {{ title }}
    <span style="margin-left: auto; margin-right: 8px; color: var(--mdc-theme-text-secondary-on-background,rgba(0,0,0,.54));">{{ subtitle }}</span>
    ${accessory}`

// 列表视图 ListView
// - 网格列表
Vue.component('grid-view', {
    template: `
        <div class="mdc-grid-list>
            <ul class="mdc-grid-list__tiles">
                <slot></slot>
            </ul>
        </div>`
})

// - 普通列表
Vue.component('list-view', {
    template: `
        <div class="mdc-list-group">
            <slot>Table List</slot>
        </div>`
})

// - 普通列表
Vue.component('list-section', {
    props: ['title'],
    template: `
        <div>
            <slot name="section-header"><h3 class="mdc-list-group__subheader">{{ title }}&#xA0;</h3></slot>
            <hr class="mdc-list-divider">
            <ul class="mdc-list mdc-list--avatar-list">
                <slot></slot>
            </ul>
            <hr class="mdc-list-divider">
        </div>`
})

// 列表 : 区域头
Vue.component('list-section-header', {
    props: ['title'],
    template: `
        <h3 class="mdc-list-group__subheader">{{ title }}&#xA0;</h3>`
})

// 列表 : 项 List Item
// - 默认
Vue.component('list-item-default', {
    props: ['icon', 'title', 'accessory', 'link', 'iconColor'],
    template: `
        <a v-if="link" :href="link" class="mdc-list-item" data-mdc-auto-init="MDCRipple">
            ${list_item_default}
        </a>
        <li v-else class="mdc-list-item">
            ${list_item_default}
        </li>`,
    computed: { // SO https://stackoverflow.com/questions/42872002/in-vue-js-component-how-to-use-props-in-css#42872117
        style() {
            return `color: ${this.iconColor}`
        }
    }
})

// - 副标题
Vue.component('list-item-subtitle', {
    props: ['icon', 'title', 'subtitle', 'accessory', 'link', 'divider'],
    template: `
        <a v-if="link" :href="link" class="mdc-list-item" data-mdc-auto-init="MDCRipple">
            ${list_item_subtitle}
        </a>
        <li v-else class="mdc-list-item">
            ${list_item_subtitle}
        </li>`
})

// - 左右
Vue.component('list-item-value1', {
    props: ['icon', 'title', 'subtitle', 'accessory', 'link'],
    template: `
        <a v-if="link" :href="link" class="mdc-list-item" data-mdc-auto-init="MDCRipple">
            ${list_item_value1}
        </a>
        <li v-else class="mdc-list-item">
            ${list_item_value1}
        </li>`
})

// 其他
// 卡片
Vue.component('card', {
    props: ['title', 'action', 'link'],
    template: `
        <div class="mdc-card">
            <section class="mdc-card__media">
                <h1 class="mdc-card__title mdc-card__title--large">{{ title }}</h1>
            </section>
            <section class="mdc-card__actions">
                <a :href="link" class="mdc-button mdc-button--compact mdc-card__action">{{ action }}</a>
            </section>
        </div>`
})

// 表单
// required 待优化 required pattern=".{1,}"
Vue.component('text-field', {
    props: ['name', 'helper_text', 'value'],
    template: `
        <div>
            <div class="mdc-text-field mdc-text-field--fullwidth">
                <input type="text" class="mdc-text-field__input"
                    v-bind:value="value"
                    v-on:input="$emit('input', $event.target.value)">
                <span class="mdc-text-field__label">{{ name }}</span>
                <div class="mdc-text-field__bottom-line"></div>
            </div>
            <p v-if="helper_text" class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent">
                {{ helper_text }}
            </p>
        </div>`
})
