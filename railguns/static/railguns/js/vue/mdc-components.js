"use strict";

// 组件
Vue.component('app', {
  template: "<div class=\"container\"><div class=\"topBar\">\u8FD9\u4E2A\u5730\u65B9\u5728\u6E32\u67D3\u540E\u4E0D\u4F1A\u88AB\u5360\u7528</div><slot></slot></div>"
});
Vue.component('app-header', {
  template: "<div class=\"header\" slot=\"header\">this is header</div>"
});
Vue.component('app-content', {
  template: "<div class=\"content\">this is content</div>"
});
Vue.component('app-footer', {
  template: "<div style=\"text-align: center; padding: 20px 0;\">{{ title }}</div>"
}); // 菜单

Vue.component('menu-item', {
  props: ['icon', 'title', 'link'],
  template: "<a :href=\"link\" class=\"material-icons mdc-top-app-bar__action-item\" :aria-label=\"title\" :alt=\"title\">{{ icon }}</a>"
}); // 基本模版

var icon = "<img v-if=\"icon\" class=\"mdc-list-item__graphic\" :src=\"icon\">"; // style="color: #fce4ec; background-color: #ec407a; width: 40px; height: 40px; border-radius: 50%;" 

var icon1 = "<span v-if=\"icon\" class=\"mdc-list-item__graphic\" role=\"presentation\" :style=\"style\">\n  <i class=\"material-icons\" aria-hidden=\"true\">{{ icon }}</i>\n</span>";
var accessory_link = "    <a v-if=\"accessory\" href=\"#\" class=\"mdc-list-item__meta material-icons\"\n        aria-label=\"Add to favorites\" title=\"Add to favorites\"\n        onclick=\"event.preventDefault()\">{{ accessory }}</a>";
var accessory = "<i v-if=\"accessory\" class=\"mdc-list-item__meta material-icons\">{{ accessory }}</i>\n<i v-else-if=\"link\" class=\"mdc-list-item__meta material-icons\">chevron_right</i>";
var list_item_default = "\n    ".concat(icon1, "\n    {{ title }}\n    ").concat(accessory);
var list_item_subtitle = "\n    ".concat(icon, "\n    <span class=\"mdc-list-item__text\">\n        {{ title }}\n        <span class=\"mdc-list-item__secondary-text\">{{ subtitle }}</span>\n    </span>\n    ").concat(accessory); // SO: https://stackoverflow.com/questions/8122042/text-overflow-ellipsis-on-one-of-two-spans-inside-a-wrapper?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa

var list_item_value1 = "\n    ".concat(icon, "\n    {{ title }}\n    <span style=\"margin-left: auto; margin-right: 8px; color: var(--mdc-theme-text-secondary-on-background,rgba(0,0,0,.54));\">{{ subtitle }}</span>\n    ").concat(accessory); // 列表 List
// - 网格列表

Vue.component('collection-list', {
  template: "\n        <div class=\"mdc-grid-list>\n            <ul class=\"mdc-grid-list__tiles\">\n                <slot></slot>\n            </ul>\n        </div>"
}); // - 普通列表

Vue.component('table-list', {
  props: ['grouped'],
  template: "\n        <div class=\"mdc-list-group\">\n            <slot>Table List</slot>\n        </div>"
}); // - 普通列表

Vue.component('table-list-section', {
  props: ['title'],
  template: "\n        <div>\n            <slot name=\"section-header\"><h3 class=\"mdc-list-group__subheader\">{{ title }}&#xA0;</h3></slot>\n            <hr class=\"mdc-list-divider\">\n            <ul class=\"mdc-list mdc-list--avatar-list\">\n                <slot></slot>\n            </ul>\n            <hr class=\"mdc-list-divider\">\n        </div>"
}); // 列表 : 区域头

Vue.component('list-section-header', {
  props: ['title'],
  template: "\n        <h3 class=\"mdc-list-group__subheader\">{{ title }}&#xA0;</h3>"
}); // 列表 : 项 List Item
// - 默认

Vue.component('list-item-default', {
  props: ['icon', 'title', 'accessory', 'link', 'datavalue', 'iconColor'],
  template: "\n        <a v-if=\"link\" :href=\"link\" class=\"mdc-list-item\" data-mdc-auto-init=\"MDCRipple\" :datavalue=\"datavalue\">\n            ".concat(list_item_default, "\n        </a>\n        <li v-else class=\"mdc-list-item\" :datavalue=\"datavalue\">\n            ").concat(list_item_default, "\n        </li>"),
  computed: {
    // SO: https://stackoverflow.com/a/42872117
    style: function style() {
      return 'color: ' + this.iconColor;
    }
  }
}); // - 副标题

Vue.component('list-item-subtitle', {
  props: ['icon', 'title', 'subtitle', 'accessory', 'link', 'divider'],
  template: "\n        <a v-if=\"link\" :href=\"link\" class=\"mdc-list-item\" data-mdc-auto-init=\"MDCRipple\">\n            ".concat(list_item_subtitle, "\n        </a>\n        <li v-else class=\"mdc-list-item\">\n            ").concat(list_item_subtitle, "\n        </li>")
}); // - 左右

Vue.component('list-item-value1', {
  props: ['icon', 'title', 'subtitle', 'accessory', 'link', 'datavalue'],
  template: "\n        <a v-if=\"link\" :href=\"link\" class=\"mdc-list-item\" data-mdc-auto-init=\"MDCRipple\" :datavalue=\"datavalue\">\n            ".concat(list_item_value1, "\n        </a>\n        <li v-else class=\"mdc-list-item\">\n            ").concat(list_item_value1, "\n        </li>")
}); // 其他
// 卡片

Vue.component('small-card', {
  props: ['title', 'action', 'link'],
  template: "\n        <div class=\"mdc-card\">\n            <section class=\"mdc-card__media\">\n                <h1 class=\"mdc-card__title mdc-card__title--large\">{{ title }}</h1>\n            </section>\n            <section class=\"mdc-card__actions\">\n                <a :href=\"link\" class=\"mdc-button mdc-button--compact mdc-card__action\">{{ action }}</a>\n            </section>\n        </div>"
}); // 表单
// required 待优化 required pattern=".{1,}"

Vue.component('text-field', {
  props: ['name', 'helper_text', 'value'],
  template: "\n        <div>\n            <div class=\"mdc-text-field mdc-text-field--fullwidth\">\n                <input type=\"text\" class=\"mdc-text-field__input\"\n                    v-bind:value=\"value\"\n                    v-on:input=\"updateValue($event.target.value)\">\n                <span class=\"mdc-text-field__label\">{{ name }}</span>\n                <div class=\"mdc-text-field__bottom-line\"></div>\n            </div>\n            <p v-if=\"helper_text\" class=\"mdc-text-field-helper-text mdc-text-field-helper-text--persistent\">\n                {{ helper_text }}\n            </p>\n        </div>",
  methods: {
    updateValue: function updateValue(value) {
      this.$emit('input', value);
    }
  }
});