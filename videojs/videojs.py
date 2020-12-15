""" videojsXBlock main Python class"""

import codecs
import os
import uuid
from HTMLParser import HTMLParser

import pkg_resources
from django.conf import settings
from django.template import Context, Template
from pycaption import detect_format
from pycaption.webvtt import WebVTTWriter
from xblock.core import XBlock
from xblock.fields import Scope, String, Dict
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from webob import Response
import json
import hashlib
from django.utils import translation

_ = lambda text: text
loader = ResourceLoader(__name__)


@XBlock.needs('i18n')
@XBlock.wants('completion')
class videojsXBlock(XBlock):
    '''
    Icon of the XBlock. Values : [other (default), video, problem]
    '''
    icon_class = "video"

    languages = {
        'pl': _('Polish'),
        'en': _('English'),
        'fr': _('French'),
        'es': _('Spanish'),
        'ru': _('Russian'),
        'cn': _('Chinese'),
        'pt': _('Portuguese'),
        'cz': _('Czech'),
        'sk': _('Slovak'),
        'lv': _('Latvian'),
        'ua': _('Ukrainian'),
        'by': _('Belarusian'),
    }

    '''
    Fields
    '''
    display_name = String(display_name=_("Display Name"),
                          default=_("Video JS"),
                          scope=Scope.settings)

    url = String(display_name=_("Youtube URL or Navoica movie ID"),
                 default="7b465d7b-6118-4b8a-80cd-3f40748fab74",
                 scope=Scope.content,
                 help=_("Enter url from website youtube.com or use id number previously uploaded movie"))

    # old fallback
    subtitle_text = String(display_name=_("Subtitle - Polish"),
                           default="",
                           scope=Scope.content,
                           help=_("Paste subtitles VVT"))

    # old fallback
    subtitle_url = String(display_name=_("Subtitle - URL - Polish"),
                          default="",
                          scope=Scope.content,
                          help="")

    subtitles = Dict(display_name=_("Subtitles RAW"),
                     default={},
                     scope=Scope.content
                     )

    subtitles_url = Dict(display_name=_("Subtitles URL"),
                         default={},
                         scope=Scope.content
                         )

    def load_resource(self, resource_path):
        """
        Gets the content of a resource
        """
        resource_content = pkg_resources.resource_string(__name__,
                                                         resource_path)
        return unicode(resource_content)

    def render_template(self, template_path, context={}):
        """
        Evaluate a template by resource path, applying the provided context
        """
        template_str = self.load_resource(template_path)
        return Template(template_str).render(Context(context))

    '''
    Main functions
    '''

    def student_view(self, context=None):
        """
        The primary view of the XBlock, shown to students
        when viewing courses.
        """

        subtitles_url = {}
        for lang, subtitle_text in dict(self.subtitles).items():
            file = self.create_subtitles_file(subtitle_text)
            if file:
                subtitles_url[lang] = file

        if len(subtitles_url.get("pl", "")) == 0 and self.subtitle_url:
            """Stara wersja zawierala jedynie napisy w jezyku PL. Dlatego musimy byc wsteczni kompatybilni"""
            subtitles_url['pl'] = self.subtitle_url

        frag = Fragment()

        context = {
            'display_name': self.display_name,
            'url': self.url,
            'uid': uuid.uuid4().hex,
            'subtitles_url': subtitles_url,
        }

        frag.add_content(loader.render_django_template(
            'static/html/videojs_view.html',
            context=context,
            i18n_service=self.runtime.service(self, "i18n"),
        ))

        frag.add_css(self.load_resource("static/css/video-js.css"))
        frag.add_css(self.load_resource("static/css/qualityselector.css"))
        frag.add_javascript(self.load_resource("static/js/video.js"))
        frag.add_javascript(self.load_resource("static/js/pl.js"))
        frag.add_javascript(self.load_resource("static/js/qualityselector.js"))
        frag.add_javascript(self.load_resource("static/js/youtube.js"))
        frag.add_javascript(self.load_resource("static/js/videojs_view.js"))
        frag.add_javascript(self.get_translation_content())

        frag.initialize_js('videojsXBlockInitView')
        return frag

    def studio_view(self, context=None):

        if not 'pl' in self.subtitles and self.subtitle_url:
            if os.path.isfile(self.subtitle_url):
                with open(self.subtitle_url, 'r') as f:
                    data = f.read()
                    self.subtitles['pl'] = data
            elif self.subtitle_text:
                reader = detect_format(self.subtitle_text)
                if reader:
                    subtitle = WebVTTWriter().write(reader().read(self.subtitle_text))
                    h = HTMLParser()
                    self.subtitles['pl'] = h.unescape(subtitle)
                    self.create_subtitles_file(self.subtitles['pl'])

        languages_subtitles = {code: {'name': self.languages[code], 'subtitle': self.subtitles[code]} for code in
                               self.languages.keys()}

        context = {
            'display_name': self.display_name,
            'url': self.url.strip(),
            'languages': languages_subtitles,
            'subtitles': self.subtitles,
        }

        frag = Fragment()

        frag.add_content(loader.render_django_template(
            'static/html/videojs_edit.html',
            context=context,
            i18n_service=self.runtime.service(self, "i18n"),
        ))

        frag.add_javascript(self.get_translation_content())
        frag.add_javascript(self.load_resource("static/js/videojs_edit.js"))
        frag.initialize_js('videojsXBlockInitStudio')
        return frag

    @XBlock.json_handler
    def save_videojs(self, data, suffix=''):
        """
        The saving handler.
        """
        i18n_ = self.runtime.service(self, "i18n").ugettext

        self.display_name = data['display_name']
        self.url = data['url'].strip()

        for language in self.languages.keys():
            subtitle_text = data['subtitle_text_' + language].strip()
            if subtitle_text:
                reader = detect_format(subtitle_text)
                if reader:
                    subtitle = WebVTTWriter().write(reader().read(subtitle_text))
                    h = HTMLParser()
                    self.subtitles[language] = h.unescape(subtitle)

                    self.create_subtitles_file(self.subtitles[language])
                else:
                    return Response(json.dumps(
                        {'error': i18n_("Error occurred while saving VTT subtitles for language %s") % language.upper()}),
                        status=400, content_type='application/json', charset='utf8')
            else:
                self.subtitles[language] = ""
                # We need to remove the old url for Polish subtitles so that they will not be re-imported
                if language == 'pl' and self.subtitle_url:
                    self.subtitle_url = None

        return {'result': 'success'}

    def create_subtitles_file(self, subtitle_text):
        if subtitle_text:
            path = settings.MEDIA_ROOT + 'subtitles/'
            if not os.path.exists(path):
                os.makedirs(path)

            name = hashlib.sha256(subtitle_text).hexdigest() + ".vtt"
            filepath = path + name
            url = settings.MEDIA_URL + 'subtitles/' + name

            if not os.path.isfile(filepath):
                try:
                    f = codecs.open(filepath, 'w', 'utf-8')
                    f.write(subtitle_text)
                    f.close()
                except IOError:
                    return None
            return url
        return None

    def resource_string(self, path):
        data = pkg_resources.resource_string(__name__, path)
        return data.decode('utf8')

    def get_translation_content(self):
        try:
            return self.resource_string('static/js/translations/{lang}/text.js'.format(
                lang=translation.get_language(),
            ))
        except IOError:
            return self.resource_string('static/js/translations/en/text.js')
