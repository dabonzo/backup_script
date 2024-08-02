# i18n.py
import gettext

_ = None

def setup_translation(language):
    """
    Setup translation for the specified language.
    :param language: Language code (e.g., 'en', 'de').
    """
    global _
    print(f"Setting up translation for language: {language}")
    try:
        lang_translations = gettext.translation('backup', localedir='locales', languages=[language], fallback=True)
        lang_translations.install()
        _ = lang_translations.gettext
        print(f"Translation setup successful for language: {language}")
    except Exception as e:
        print(f"Error setting up translation for language {language}: {e}")

def get_translation():
    """
    Get the translation function.
    :return: Translation function.
    """
    global _
    if _ is None:
        raise ValueError("Translation function _ is not initialized. Call setup_translation() first.")
    return _
