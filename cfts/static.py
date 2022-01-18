from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ManifestStaticFilesStorageSubClass(ManifestStaticFilesStorage):
    # fix for certain css files throwing valueError when collecting static files
    # source: https://code.djangoproject.com/ticket/21080#comment:12
    patterns = (
        ("*.css", (
            r"""(url\((?:['"]|%22|%27){0,1}\s*(.*?)(?:['"]|%22|%27){0,1}\))""",
            (r"""(@import\s*["']\s*(.*?)["'])""", """@import url("%s")"""),
        )),
    )
    max_post_process_passes = 15
    manifest_strict = False
