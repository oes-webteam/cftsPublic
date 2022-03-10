# see comment in settings.py for a more detailed explanation of what this file is for
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from django.utils import version


class ManifestStaticFilesStorageSubClass(ManifestStaticFilesStorage):
    django_maj_version = version.get_complete_version()[0]
    # fix for certain css files throwing valueError when collecting static files
    # source: https://code.djangoproject.com/ticket/21080#comment:12

    if django_maj_version >= 4:
        # patterns for Django version > 4.0,
        patterns = (
            (
                ("*.css", (
                    r"""(?P<matched>url\((?:['"]|%22|%27){0,1}\s*(?P<url>.*?)(?:['"]|%22|%27){0,1}\))""",
                    (r"""(?P<matched>@import\s*["']\s*(?P<url>.*?)["'])""", """@import url("%s")"""),
                    (
                        r'(?m)(?P<matched>)^(/\*# (?-i:sourceMappingURL)=(?P<url>.*) \*/)$',
                        '/*# sourceMappingURL=%(url)s */',
                    ),
                )),
            )
        )
    elif django_maj_version < 4:
        # patterns for Django version < 4.0
        patterns = (
            ("*.css", (
                r"""(url\((?:['"]|%22|%27){0,1}\s*(.*?)(?:['"]|%22|%27){0,1}\))""",
                (r"""(@import\s*["']\s*(.*?)["'])""", """@import url("%s")"""),
            )),
        )

    max_post_process_passes = 15
    manifest_strict = False
