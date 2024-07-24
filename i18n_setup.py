import gettext
import locale

# Define _ globally
_ = None


def setup_i18n(language):
    """
    Sets up internationalization for the application.
    """
    global _
    locale.setlocale(locale.LC_ALL, '')
    print(f"Setting up i18n for language: {language}")
    try:
        lang = gettext.translation('backup', localedir='locales', languages=[language], fallback=True)
        lang.install()
        _ = lang.gettext
        print("Translation setup successful")
    except Exception as e:
        print(f"Error setting up i18n: {e}")
        # Use default gettext if there's an error
        gettext.install('backup', localedir='locales', names=('ngettext',))
        _ = gettext.gettext
        print("Using default gettext")


# Call setup_i18n with default language to ensure _ is defined
setup_i18n('en')
