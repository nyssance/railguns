"use strict";

// https://cn.vuejs.org/v2/guide/components.html#注册
// 对于自定义标签名，Vue.js 不强制要求遵循 W3C 规则 (小写，并且包含一个短杠)，尽管遵循这个规则比较好。
// https://cn.vuejs.org/v2/guide/components.html#组件命名约定
// 这意味着 PascalCase 是最通用的 声明约定 而 kebab-case 是最通用的 使用约定。
// 综上，使用 kebab-case 最不容易引起不必要的bug
// https://cn.vuejs.org/v2/style-guide/#Prop-名大小写-强烈推荐
// https://cn.vuejs.org/v2/style-guide/#指令缩写-强烈推荐
// Vue 太蠢, 不区分html注释和正式代码
var showActionSheet = function showActionSheet() {
  var menus = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : [];
  var actions = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : [];
  var options = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};
  weui.actionSheet(menus, actions, options);
};

var showAlert = function showAlert(title, message, action) {
  if (action) {
    weui.confirm(message, action, undefined, {
      title: title
    });
  } else {
    weui.alert(message, {
      title: title
    });
  }
};

var showSnackbar = function showSnackbar(message) {
  var duration = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 2000;
  weui.topTips(message, {
    duration: duration
  });
}; // 💙 组件


Vue.component('app-footer', {
  template: "\n        <!--<div class=\"weui-footer weui-footer_fixed-bottom\">-->\n        <div class=\"weui-footer\">\n            <br>\n            <br>\n            <p class=\"weui-footer__links\">\n                <!--<a href=\"javascript:home();\" class=\"weui-footer__link\">\u9996\u9875</a>-->\n            </p>\n            <p class=\"weui-footer__text\">Copyright &copy; 2019 www.yourdomain.com</p>\n        </div>"
}); // TabBar 底部导航

Vue.component('tabbar', {
  template: "\n        <div class=\"weui-tab\">\n            <div class=\"weui-tab__panel\">\n                <slot></slot>\n            </div>\n            <div class=\"weui-tabbar\">\n                <slot name=\"tab\"></slot>\n            </div>\n        </div>"
});
Vue.component('tabbar-item', {
  props: {
    icon: {
      type: String,
      required: true
    },
    title: {
      type: String,
      required: true
    },
    link: {
      type: String,
      required: true
    },
    selected: {
      type: Boolean,
      default: false
    }
  },
  template: "<a :href=\"link\" :class=\"'weui-tabbar__item' + selected_class\">\n                   <img :src=\"icon\" class=\"weui-tabbar__icon\" alt=\"\">\n                   <p class=\"weui-tabbar__label\">{{ title }}</p>\n               </a>",
  computed: {
    selected_class: function selected_class() {
      return this.selected ? ' weui-bar__item_on' : '';
    }
  }
}); // 菜单

Vue.component('menu-item', {
  props: {
    icon: {
      type: String,
      required: true
    },
    title: {
      type: String,
      required: true
    },
    link: {
      type: String,
      required: true
    }
  },
  template: "<a :href=\"link\" class=\"material-icons mdc-top-app-bar__action-item\" :aria-label=\"title\" :alt=\"title\">{{ icon }}</a>"
}); // Pager

Vue.component('pager', {
  template: "\n        <div class=\"weui-tab\">\n            <div class=\"weui-navbar\">\n                <slot name=\"tab\"></slot>\n            </div>\n            <div class=\"weui-tab__panel\">\n                <slot></slot>\n            </div>\n        </div>"
});
Vue.component('pager-item', {
  props: {
    title: {
      type: String,
      required: true
    },
    selected: {
      type: Boolean,
      default: false
    },
    method: {
      type: Function,
      required: false,
      default: function _default() {
        showSnackbar('请在 pager-item 组件中传入一个方法, 例如 :method="refresh"');
      }
    }
  },
  template: "\n        <div :class=\"'weui-navbar__item' + selected_class\" @click=\"toggle($event, method)\">\n            {{ title }}\n        </div>",
  computed: {
    selected_class: function selected_class() {
      return this.selected ? ' weui-bar__item_on' : '';
    }
  },
  methods: {
    toggle: function toggle(event, method) {
      // target 和 currentTarget 区别 https://juejin.im/post/59f16ffaf265da43085d4108
      var className = 'weui-bar__item_on';
      var before = document.getElementsByClassName(className)[0];
      var after = event.target;

      if (before !== after) {
        before.classList.remove(className);
        after.classList.add(className);
        method();
      }
    }
  }
});
Vue.component('pager-content', {
  template: "\n        <div class=\"weui-tab__content\">\n            <slot></slot>\n        </div>"
}); // 基本模版

var icon = "<div v-if=\"icon\" class=\"weui-cell__hd\"><img :src=\"icon\" style=\"width: 40px;border-radius: 50%;margin-right: 15px;display: block\" alt=\"\"></div>";
var icon1 = "<div v-if=\"icon\" class=\"weui-cell__hd\" :style=\"style\"><i :class=\"'fas fa-fw fa-' + icon\" style=\"margin-right: 15px;display: block;\"></i></div>";
var accessory = "<div v-if=\"link\" class=\"weui-cell__ft\"></div>";
var list_item_default = "\n    ".concat(icon1, "\n    <div class=\"weui-cell__bd\">\n        <span v-if=\"badges\" style=\"vertical-align: middle\">{{ title }}</span>\n        <p v-else>{{ title }}</p>\n        <span v-for=\"badge in badges\" class=\"weui-badge\" style=\"margin-left: 5px;\">{{ badge }}</span>\n    </div>");
var list_item_subtitle = "\n    ".concat(icon, "\n    <div class=\"weui-cell__bd\">\n        <span v-if=\"badges\" style=\"vertical-align: middle\">{{ title }}</span>\n        <p v-else>{{ title }}</p>\n        <span v-for=\"badge in badges\" class=\"weui-badge\" style=\"margin-left: 5px;\">{{ badge }}</span>\n        <p style=\"font-size: 13px;color: #888888;\">{{ subtitle }}</p>\n    </div>"); // SO: https://stackoverflow.com/questions/8122042/text-overflow-ellipsis-on-one-of-two-spans-inside-a-wrapper?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa

var list_item_value1 = "\n    ".concat(icon, "\n    <div class=\"weui-cell__bd\">\n        <span v-if=\"badges\" style=\"vertical-align: middle\">{{ title }}</span>\n        <p v-else>{{ title }}</p>\n        <span v-for=\"badge in badges\" class=\"weui-badge\" style=\"margin-left: 5px;\">{{ badge }}</span>\n    </div>\n    <div class=\"weui-cell__ft\">{{ subtitle }}</div>"); // 列表视图 ListView
// - 网格列表

Vue.component('grid-view', {
  template: "\n        <div class=\"weui-grids\">\n            <slot></slot>\n        </div>"
}); // - 普通列表

Vue.component('list-view', {
  template: "\n        <div style=\"background: #f8f8f8; width: 100vh; height: 100vh\">\n            <slot>\n                <div class=\"weui-loadmore weui-loadmore_line\">\n                    <span class=\"weui-loadmore__tips\">\u6682\u65E0\u6570\u636E</span>\n                </div>\n            </slot>\n        </div>"
}); // - 普通列表区块

Vue.component('list-section', {
  template: "\n        <div class=\"weui-cells\">\n            <slot></slot>\n        </div>"
}); // 列表 : 区域头

Vue.component('list-section-header', {
  props: {
    title: {
      type: String,
      required: true
    }
  },
  template: "\n        <div class=\"weui-cells__title\">{{ title }}</div>"
}); // Grid Item

Vue.component('grid-item', {
  props: {
    icon: {
      type: String
    },
    title: {
      type: String,
      required: true,
      default: ''
    },
    subtitle: {
      type: [String, Number],
      required: true,
      default: ''
    },
    badges: {
      type: Array
    },
    link: {
      type: String
    },
    iconColor: {
      type: String
    }
  },
  template: "\n        <a :href=\"link\" class=\"weui-grid\">\n            <div v-if=\"icon\" class=\"weui-grid__icon\">\n                <img :src=\"icon\" :style=\"style\" alt=\"\">\n            </div>\n            <p class=\"weui-grid__label\">{{ subtitle }}</p>\n            <p class=\"weui-grid__label\">{{ title }}</p>\n        </a>",
  computed: {
    style: function style() {
      return "color: ".concat(this.iconColor);
    }
  }
}); // 列表 : 项 List Item
// - 默认

Vue.component('list-item-default', {
  props: {
    icon: {
      type: String
    },
    title: {
      type: String,
      required: true,
      default: ''
    },
    accessory: {
      type: String
    },
    badges: {
      type: Array
    },
    link: {
      type: String
    },
    datavalue: {
      type: String
    },
    iconColor: {
      type: String
    }
  },
  template: "\n        <a v-if=\"link\" :href=\"link\" class=\"weui-cell weui-cell_access\" :datavalue=\"datavalue\">\n            ".concat(list_item_default, "\n            <div class=\"weui-cell__ft\"></div>\n        </a>\n        <div v-else class=\"weui-cell\" :datavalue=\"datavalue\">\n            ").concat(list_item_default, "\n        </div>"),
  computed: {
    style: function style() {
      return "color: ".concat(this.iconColor);
    }
  }
}); // - 副标题

Vue.component('list-item-subtitle', {
  props: {
    icon: {
      type: String
    },
    title: {
      type: String,
      required: true,
      default: ''
    },
    subtitle: {
      type: [String, Number],
      required: true,
      default: ''
    },
    accessory: {
      type: String
    },
    badges: {
      type: Array
    },
    link: {
      type: String
    }
  },
  template: "\n        <a v-if=\"link\" :href=\"link\" class=\"weui-cell weui-cell_access\">\n            ".concat(list_item_subtitle, "\n            <div class=\"weui-cell__ft\"></div>\n        </a>\n        <div v-else class=\"weui-cell\">\n            ").concat(list_item_subtitle, "\n        </div>")
}); // - 左右

Vue.component('list-item-value1', {
  props: {
    icon: {
      type: String
    },
    title: {
      type: String,
      required: true,
      default: ''
    },
    subtitle: {
      type: [String, Number],
      required: true,
      default: ''
    },
    accessory: {
      type: String
    },
    badges: {
      type: Array
    },
    link: {
      type: String
    },
    datavalue: {
      type: String
    }
  },
  template: "\n        <a v-if=\"link\" :href=\"link\" class=\"weui-cell weui-cell_access\" :datavalue=\"datavalue\">\n            ".concat(list_item_value1, "\n        </a>\n        <div v-else class=\"weui-cell\" :datavalue=\"datavalue\">\n            ").concat(list_item_value1, "\n        </div>")
}); // - 卡片

Vue.component('card', {
  props: {
    icon: {
      type: String
    },
    title: {
      type: String,
      required: true,
      default: ''
    },
    subtitle: {
      type: [String, Number],
      required: true,
      default: ''
    },
    accessory: {
      type: String
    },
    badges: {
      type: Array
    },
    //
    meta: {
      type: [String, Number]
    },
    time: {
      type: String
    },
    extra: {
      type: [String, Number]
    },
    link: {
      type: String
    },
    //
    button: {
      type: String
    },
    buttonLink: {
      type: String
    }
  },
  template: "\n        <a :href=\"link\" class=\"weui-media-box weui-media-box_appmsg\">\n            <div v-if=\"icon\" class=\"weui-media-box__hd\">\n                <img :src=\"icon\" class=\"weui-media-box__thumb\" alt=\"\">\n            </div>\n            <div class=\"weui-media-box__bd\">\n                <h4 class=\"weui-media-box__title\">{{ title }}</h4>\n                <p class=\"weui-media-box__desc\">{{ subtitle }}</p>\n                <ul class=\"weui-media-box__info\">\n                    <li class=\"weui-media-box__info__meta\">{{ meta }}</li>\n                    <li class=\"weui-media-box__info__meta\">{{ time }}</li>\n                    <li class=\"weui-media-box__info__meta weui-media-box__info__meta_extra\">{{ extra }}</li>\n                </ul>\n            </div>\n            <a v-if=\"button\" :href=\"buttonLink\" class=\"weui-btn weui-btn_mini weui-btn_primary\">{{ button }}</a>\n        </a>"
}); // 面板

Vue.component('panel', {
  props: {
    icon: {
      type: String,
      required: true
    },
    title: {
      type: String,
      required: true,
      default: ''
    },
    subtitle: {
      type: [String, Number],
      required: true,
      default: ''
    },
    badges: {
      type: Array
    },
    link: {
      type: String
    },
    //
    button: {
      type: String
    },
    buttonLink: {
      type: String
    }
  },
  template: "\n        <a :href=\"link\" class=\"weui-media-box weui-media-box_appmsg\">\n            <div class=\"weui-media-box__hd\">\n                <img class=\"weui-media-box__thumb\" :src=\"icon\" style=\"border-radius: 50%\">\n            </div>\n            <div class=\"weui-media-box__bd\">\n                <h4 class=\"weui-media-box__title\">{{ title }}</h4>\n                <p class=\"weui-media-box__desc\">{{ subtitle }}</p>\n            </div>\n            <a v-if=\"button\" :href=\"buttonLink\" class=\"weui-btn weui-btn_mini weui-btn_primary\">{{ button }}</a>\n        </a>"
}); // 文章

Vue.component('article-html', {
  props: ['text'],
  template: "<article class=\"weui-article\" v-html=\"text\"></article>"
}); // 表单
// required 待优化 required pattern=".{1,}"

Vue.component('text-field', {
  props: {
    name: {
      type: String,
      required: true
    },
    placeholder: {
      type: String
    },
    value: {
      type: String
    },
    type: {
      type: String,
      default: 'text',
      validator: function validator(value) {
        return ['text', 'number', 'tel', 'date', 'datetime-local'].includes(value);
      }
    }
  },
  template: "\n        <div class=\"weui-cell\">\n            <div class=\"weui-cell__hd\">\n                <label class=\"weui-label\">{{ name }}</label>\n            </div>\n            <div class=\"weui-cell__bd\">\n                <input class=\"weui-input\" :placeholder=\"placeholder\" :type=\"type\" :value=\"currentValue\" @input=\"updateValue\">\n            </div>\n        </div>",
  data: function data() {
    // SF https://segmentfault.com/q/1010000016557863/a-1020000016558329
    return {
      currentValue: this.value //将prop属性绑定到data属性上，以便修改prop属性（Vue不允许直接修改prop属性的值）

    };
  },
  methods: {
    updateValue: function updateValue(event) {
      var value = event.target.value;
      this.$emit('input', value);
    }
  }
}); // Swiper

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
  template: "\n        <div class=\"swiper-container\">\n            <div class=\"swiper-wrapper\">\n                <slot></slot>\n            </div>\n             <!-- \u5982\u679C\u9700\u8981\u5206\u9875\u5668 -->\n             <div v-if=\"pagination\" class=\"swiper-pagination\"></div>\n        </div>",
  mounted: function mounted() {
    var screenWidth = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
    var height = screenWidth * this.height;
    this.$el.style.height = "".concat(height, "px");
  },
  updated: function updated() {
    var mySwiper = new Swiper('.swiper-container', {
      autoplay: {
        delay: this.delay
      },
      loop: this.loop,
      pagination: {
        el: '.swiper-pagination'
      }
    });
  }
});
Vue.component('swiper-item', {
  props: {
    image: {
      type: String
    },
    title: {
      type: String
    },
    link: {
      type: String
    }
  },
  template: "\n        <a v-if=\"link\" :href=\"link\" class=\"swiper-slide\">{{ title }}</a>\n        <div v-else class=\"swiper-slide\">{{ title }}</div>",
  mounted: function mounted() {
    if (this.image) {
      this.$el.style.backgroundImage = "url(".concat(this.image, ")");
      this.$el.style.backgroundPosition = 'center';
      this.$el.style.backgroundSize = 'cover';
    } else {
      this.$el.style.backgroundColor = '#00e871';
    }
  }
}); // 💙 过滤器
// 时间过滤器 moment会自动容错输出当前时间, 真是多此一举.

Vue.filter('dateFormat', function (dateStr) {
  var pattern = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'YYYY-MM-DD HH:mm:ss';
  return dateStr ? moment(dateStr).format(pattern) : 'null';
});