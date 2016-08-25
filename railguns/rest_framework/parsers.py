from rest_framework_xml import parsers


class XMLTextParser(parsers.XMLParser):
    media_type = 'text/xml'
