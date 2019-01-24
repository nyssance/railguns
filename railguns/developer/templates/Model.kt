/* AUTO-GENERATED FILE. DO NOT MODIFY.
 *
 * Copyright {{ year }} NY <nyssance@icloud.com>. All rights reserved.
 */
{% set data_types = {
            'bool': 'Boolean',
            'int': 'Long',
            'str': 'String',
            'date': 'String',
        } %}
package {{ package }}.model

import com.google.gson.annotations.SerializedName
{% set my_string = [] %}{% for property in properties %}{% do my_string.append('{}val {}: {}'.format(
    '@SerializedName("{}") '.format(property.key) if property.key != property.name else '',
    property.name,
    property.name if property.is_reference_type else data_types[property.type])) %}{% endfor %}
data class {{ name }}(
        {{ my_string|join(',\n        ') }}
)

