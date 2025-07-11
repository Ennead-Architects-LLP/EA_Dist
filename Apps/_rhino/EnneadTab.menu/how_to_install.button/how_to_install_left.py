__title__ = "HowToInstall"
__doc__ = """Access EnneadTab installation documentation.

Key Features:
- Step-by-step installation guide
- System requirements
- Troubleshooting tips
- Configuration instructions
- Team deployment guidance"""

import webbrowser

from EnneadTab import LOG, ERROR_HANDLE


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def how_to_install():
    webbrowser.open('https://ennead-architects-llp.github.io/EnneadTabWiki/index.html')



if __name__ == "__main__":
    how_to_install()