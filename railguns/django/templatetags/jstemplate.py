from django.template.base import Node, TOKEN_VAR, TOKEN_TEXT, TOKEN_BLOCK
from django.template.exceptions import TemplateSyntaxError
from django.template.library import Library


register = Library()


class JstemplateNode(Node):
    def __init__(self, content):
        self.content = content

    def render(self, context):
        output = ''
        for bit in self.content:
            if isinstance(bit, str):
                output += bit
            else:
                output += bit.render(context)
        return '<script id="entry-template" type="text/x-handlebars-template">\n{}</script>\n'.format(output)


@register.tag
def jstemplate(parser, token):
    content = []
    while 1:
        token = parser.tokens.pop(0)
        if token.contents == 'endjstemplate':
            break
        if token.token_type == TOKEN_VAR:
            content.append('{{')
            content.append(token.contents)
        elif token.token_type == TOKEN_TEXT:
            content.append(token.contents)
        elif token.token_type == TOKEN_BLOCK:
            try:
                command = token.contents.split()[0]
            except IndexError:
                parser.empty_block_tag(token)
            try:
                compile_func = parser.tags[command]
            except KeyError:
                parser.invalid_block_tag(token, command, None)
            try:
                node = compile_func(parser, token)
            except TemplateSyntaxError as e:
                if not parser.compile_function_error(token, e):
                    raise
            content.append(node)
        if token.token_type == TOKEN_VAR:
            content.append('}}')
    return JstemplateNode(content)
