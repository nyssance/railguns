import io
import os
import shutil
import zipfile

from django.conf import settings
from django.http.response import HttpResponse
from django.views.decorators.http import require_safe

from . import utils


@require_safe
def zip_view(request, language):
    top = f'tmp/{settings.PROJECT_NAME}/{language}/'
    utils.generate_api_service(language, top)
    utils.generate_model(language, top, ['apps.api.serializers', 'apps.api_auto.serializers'])
    # 打包
    buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(top):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            zip_file.write(path, path[len(top):])
    zip_file.close()
    shutil.rmtree(top)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{language}.zip"'
    return response
