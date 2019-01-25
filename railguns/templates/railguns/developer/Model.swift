//  AUTO-GENERATED FILE. DO NOT MODIFY.
//
//  Copyright © {{ year }} NY <nyssance@icloud.com>. All rights reserved.
//{% set data_types = {
            'bool': 'Bool',
            'int': 'Int',
            'str': 'String',
            'date': 'Date'
        } %}
{% set default_values = {
            'bool': 'false',
            'int': '0',
            'str': '""',
            'date': 'Date(timeIntervalSince1970: 0)',
        } %}
struct {{ name }}: Codable {
{% for property in properties %}    var {{ property.name }} = {% if property.is_reference_type %}{{ property.type }}(){% else %}{{ default_values[property.type] }}{% endif %}
{% endfor %}
    enum CodingKeys: String, CodingKey {
{% for property in properties %}        case {{ property.name }}{% if property.key != property.name %} = "{{ property.key }}"{% endif %}
{% endfor %}    }

    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        do {
{% for property in properties %}            {{ property.name }} = try values.decodeIfPresent({% if property.is_reference_type %}{{ property.type }}{% else %}{{ data_types[property.type] }}{% endif %}.self, forKey: .{{ property.name }}) ?? {% if property.is_reference_type %}{{ property.type }}(){% else %}{{ default_values[property.type] }}{% endif %}
{% endfor %}        } catch let error {
            print("{{ name }} Decode Error: \(error)")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        do {
{% for property in properties %}            try container.encode({{ property.name }}, forKey: .{{ property.name }})
{% endfor %}        } catch let error {
            print("{{ name }} Encode Error: \(error)")
        }
    }
}

