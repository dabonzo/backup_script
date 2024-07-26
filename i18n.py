import gettext

# Set up translation
# locales_dir = os.path.join(script_dir, 'locales')
# Set up translations
lang_translations = gettext.translation('backup', localedir='locales', languages=['de'], fallback=True)
lang_translations.install()
_ = lang_translations.gettext