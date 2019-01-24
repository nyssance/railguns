/* AUTO-GENERATED FILE. DO NOT MODIFY.
 *
 * Copyright {{ year }} NY <nyssance@icloud.com>. All rights reserved.
 */

package {{ package }}

import {{ package }}.model.*
import retrofit2.Call
import retrofit2.http.*
{# 【raw endraw 只是为了不输出头尾换行又要规避 {{ 连在一起的情况】 #}
interface APIService {% raw %}{{% endraw %}{% for path in paths %}
    @{{ path.method }}("{{ path.endpoint }}")
    fun {{ path.name }}({% if path.params %}{{ path.params }}{% endif %}): Call<{{ path.model }}>
{% endfor %}{% raw %}}{% endraw %}

