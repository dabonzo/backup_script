# i18n.py
import gettext

_ = None

def setup_translation(language):
    """
    Setup translation for the specified language.
    :param language: Language code for translation.
    """
    global _
    lang_translations = gettext.translation('backup', localedir='locales', languages=[language], fallback=True)
    lang_translations.install()
    _ = lang_translations.gettext

def get_translation():
    """
    Get the translation function.
    :return: The translation function _.
    :raises ValueError: If the translation function is not initialized.
    """
    global _
    if _ is None:
        raise ValueError("Translation function _ is not initialized. Call setup_translation() first.")
    return _
