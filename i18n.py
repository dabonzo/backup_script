# i18n.py
import gettext
from logger import Logger

_ = None

def setup_translation(language):
    """
    Setup translation for the specified language.
    :param language: Language code (e.g., 'en', 'de').
    """
    global _
    logger = Logger.get_instance()
    logger.debug_log(f"Setting up translation for language: {language}")
    try:
        lang_translations = gettext.translation('backup', localedir='locales', languages=[language], fallback=True)
        lang_translations.install()
        _ = lang_translations.gettext
        logger.debug_log(f"Translation setup successful for language: {language}")
    except Exception as e:
        logger.debug_log(f"Error setting up translation for language {language}: {e}")

def get_translation():
    """
    Get the translation function.
    :return: Translation function.
    """
    global _
    if _ is None:
        raise ValueError("Translation function _ is not initialized. Call setup_translation() first.")
    return _
