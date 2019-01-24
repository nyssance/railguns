//  AUTO-GENERATED FILE. DO NOT MODIFY.
//
//  Copyright © {{ year }} NY <nyssance@icloud.com>. All rights reserved.
//

import Taylor
{# 【raw endraw 只是为了不输出头尾换行又要规避 {{ 连在一起的情况】 #}
extension API {% raw %}{{% endraw %}{% for path in paths %}
    static func {{ path.name }}({% if path.params %}{{ path.params }}{% endif %}) -> Call<{{ path.model }}> {
        return Call({% if path.method != 'GET' %}.{{ path.method|lower }}, {% endif %}"{{ path.endpoint}}")
    }
{% endfor %}{% raw %}}{% endraw %}

