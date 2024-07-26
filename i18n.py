# i18n.py
import gettext

_ = None

def setup_translation(language):
    global _
    lang_translations = gettext.translation('backup', localedir='locales', languages=[language], fallback=True)
    lang_translations.install()
    _ = lang_translations.gettext

def get_translation():
    global _
    if _ is None:
        raise ValueError("Translation function _ is not initialized. Call setup_translation() first.")
    return _
