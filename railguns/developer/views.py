import io
import os
import shutil
import zipfile

from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import render
from jinja2 import Environment, PackageLoader
from railguns.utils.text import underscore_to_camelcase


def index(request):
    return render(request, 'developer_index.html', locals())


def downloads(request):
    return render(request, 'downloads.html', locals())


# def show_urls(request):
#     resolver = get_resolver(urls)
#     url_info = os.popen('python ./manage.py show_urls |grep cmcaifu.apps.api.views |grep api/v2')
#     info = ''
#     f = open('/tmp/service.java', 'a')
#     for url in url_info.readlines():
#         url_list = url.strip().split('\t')
#         seriaizer_obj = 'views.{}'.format(url_list[1].replace('cmcaifu.apps.api.views.', ''))
#         if getattr(eval(seriaizer_obj), 'serializer_class', None):
#             class_name = get_class_name(url_list[1].replace('cmcaifu.apps.api.views.', ''))
#             method_list = dir(eval('views.{}'.format(url_list[1].replace('cmcaifu.apps.api.views.', ''))))
#             serializer_name = eval('views.{}.serializer_class'.format(url_list[1].replace('cmcaifu.apps.api.views.', '')))
#             if getattr(serializer_name, 'Meta', None):
#                 model_name = eval('views.{}.serializer_class.Meta.model.__name__'.format(url_list[1].replace('cmcaifu.apps.api.views.', '')))
#             else:
#                 if 'DetailSerializer' in eval('views.{}.serializer_class.__name__'.format(url_list[1].replace('cmcaifu.apps.api.views.', ''))):
#                     model_name = eval('views.{}.serializer_class.__name__'.format(url_list[1].replace('cmcaifu.apps.api.views.', '')))[:-16]
#                 if 'ListSerializer' in eval('views.{}.serializer_class.__name__'.format(url_list[1].replace('cmcaifu.apps.api.views.', ''))):
#                     model_name = eval('views.{}.serializer_class.__name__'.format(url_list[1].replace('cmcaifu.apps.api.views.', '')))[:-14]
#                 else:
#                     model_name = eval('views.{}.serializer_class.__name__'.format(url_list[1].replace('cmcaifu.apps.api.views.', '')))[:-10]
#             if 'list' in method_list:
#                 if 'pk' in url_list[0]:
#                     if 'cards' in url_list[0]:
#                         write_to_file(f, 'LIST', url_list[0], model_name, class_name, 'id', 'Long')
#                     else:
#                         write_to_file(f, 'LIST', url_list[0], model_name, class_name, 'id', 'Int')
#                 elif 'name' in url_list[0]:
#                     write_to_file(f, 'LIST', url_list[0], model_name, class_name, 'name', 'String')
#                 else:
#                     write_to_file(f, 'LIST', url_list[0], model_name, class_name)
#             if 'retrieve' in method_list:
#                 if 'pk' in url_list[0]:
#                     if 'cards' in url_list[0]:
#                         write_to_file(f, 'GET', url_list[0], model_name, class_name, 'id', 'Long')
#                     else:
#                         write_to_file(f, 'GET', url_list[0], model_name, class_name, 'id', 'Int')
#                 elif 'name' in url_list[0]:
#                     write_to_file(f, 'GET', url_list[0], model_name, class_name, 'name', 'String')
#                 else:
#                     pass
#             if 'create' in method_list:
#                 write_to_file(f, 'POST', url_list[0], model_name, class_name, '{}'.format(model_name), '{}'.format(model_name.lower()))
#             if 'put' in method_list:
#                 if 'pk' in url_list[0]:
#                     if 'cards' in url_list[0]:
#                         write_to_file(f, 'PUT', url_list[0], model_name, class_name, 'id', 'Long')
#                     else:
#                         write_to_file(f, 'PUT', url_list[0], model_name, class_name, 'id', 'Int')
#                 elif 'name' in url_list[0]:
#                     write_to_file(f, 'PUT', url_list[0], model_name, class_name, 'name', 'String')
#                 else:
#                     pass
#             if 'delete' in method_list:
#                 if 'pk' in url_list[0]:
#                     if 'cards' in url_list[0]:
#                         write_to_file(f, 'DELETE', url_list[0], model_name, class_name, 'id', 'Long')
#                     else:
#                         write_to_file(f, 'DELETE', url_list[0], model_name, class_name, 'id', 'Int')
#                 elif 'name' in url_list[0]:
#                     write_to_file(f, 'DELETE', url_list[0], model_name, class_name, 'name', 'String')
#                 else:
#                     pass
#     f.close()
#     return render(request, 'show_urls.html', locals())


def write_to_file(f, method, url, model_name, class_name, params='', params_type=''):
    url = url.replace('<pk>', '{pk}').replace('<name>', '{name}')
    if method == 'LIST':
        f.write('@{}("{}")\n'.format('GET', url))
        f.write('Call<ListModel<{}>> {}({});\n'.format(model_name, class_name, '@Path("{0}") {1} {0}'.format(params, params_type) if params else ''))
    elif method == 'POST':
        f.write('@{}("{}")\n'.format(method, url))
        f.write('Call<{}> {}({});\n'.format(model_name, class_name, '@Body {} {}'.format(params, params_type)))
    else:
        f.write('@{}("{}")\n'.format(method, url))
        f.write('Call<{}> {}({});\n'.format(model_name, class_name, '@Path("{0}") {1} {0}'.format(params, params_type) if params else ''))
    f.write('\n')


def get_class_name(class_name):
    if 'View' in class_name:
        class_name = class_name[:-4]
    return class_name[0].lower() + class_name[1:]


def models_zip(request):
    env = Environment(loader=PackageLoader(settings.PROJECT_NAME))
    env.filters['underscore_to_camelcase'] = underscore_to_camelcase
    env.filters['is_model'] = is_model
    env.filters['is_list_model'] = is_list_model
    env.filters['name_transform'] = filter_name_transform
    env.filters['field_type'] = filter_field_type
    env.filters['swift_map'] = filter_swift_map
    with open(os.path.join(settings.PROJECT_NAME, 'apps/api/serializers.py')) as file:
        global model_list
        model_list = []
        for line in file.readlines():
            if line.startswith('class') and 'DetailSerializer(' in line:
                model_list.append(line.split(' ')[1].split('(')[0][:-16])
    file.close()
    top = 'tmp/models/'
    os.makedirs(os.path.join(top, 'java'), exist_ok=True)
    os.makedirs(os.path.join(top, 'swift'), exist_ok=True)
    template_java = env.get_template('model_java.txt')
    template_swift = env.get_template('model_swift.txt')
    for class_name in model_list:
        env.globals['author'] = settings.DOMAIN_NAME
        env.globals['class_name'] = class_name
        env.globals['type_name'] = type_name
        env.globals['choice_value'] = choice_value
        fields = eval('serializers.{}DetailSerializer().fields'.format(class_name))
        with open(os.path.join(top, 'java', '{}.java'.format(class_name)), 'w') as fp:
            fp.write(template_java.render(package='.'.join(settings.DOMAIN_NAME.split('.')[::-1]), fields=fields))
        fp.close()
        with open(os.path.join(top, 'swift', '{}.swift'.format(class_name)), 'w') as fp:
            fp.write(template_swift.render(fields=fields))
        fp.close()
    # 打包
    buffer = io.BytesIO()
    zip = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(top):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            zip.write(path, path[len(top):])
    zip.close()
    shutil.rmtree(top)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="models.zip"'
    return response


def choice_value(value):
    return type_name(list(value.choices)[0])


def is_list_model(field):
    return field in ['cards', 'specials', 'featured', 'coupons', 'projects', 'tags', 'branches', 'contracts', 'comments', 'likes', 'cities']


def is_model(field):
    return field[0].title() in model_list or field[0] in [
        'cards', 'specials', 'coupons', 'projects', 'publishers', 'tags', 'contracts', 'images', 'featured', 'comments', 'likes', 'cities', 'branches', 'type', 'status'
    ]


def filter_field_type(field):
    name = field[0]
    type = field[1]
    if name in ['cards', 'comments', 'likes', 'specials', 'coupons', 'projects', 'publishers', 'tags', 'contracts']:
        return 'ListModel<{}>'.format(name.capitalize()[:-1])
    elif name in ['images', 'featured', 'cities', 'branches']:
        return 'ListModel<{}>'.format(field_names[name])
    elif name in ['type', 'status', 'repaymentType']:
        return 'StatusModel'
    elif name.title() in model_list:
        return name.title()
    elif name.endswith('_str'):
        return '""'
    elif type_name(type) == 'ChoiceField':
        return field_mapping[type_name(list(type.choices)[0])]
    else:
        return field_mapping[type_name(type)]


def filter_name_transform(field):
    name = field[0]
    if name == 'description':
        return 'desc'
    else:
        return underscore_to_camelcase(name)


def filter_swift_map(field):
    name = field[0]
    if name.endswith('_time'):
        return '(map["{}"], SmartDateTransform())'.format(name)
    else:
        return 'map["{}"]'.format(name)


def type_name(value):
    return type(value).__name__


field_names = {'images': 'ImageModel', 'branches': 'Branch', 'featured': 'Featured', 'cities': 'City'}

field_mapping = {
    'BooleanField': 'false',
    'IntegerField': '0',
    'DateTimeField': 'Date(timeIntervalSince1970: 0)',
    'CharField': '""',
    'EmailField': '""',
    'URLField': '""',
    'SerializerMethodField': '""',
    'int': '0',
    'str': '""'
}
