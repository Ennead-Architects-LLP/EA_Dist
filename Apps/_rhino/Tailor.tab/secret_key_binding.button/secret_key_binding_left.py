
__title__ = "SecretKeyBinding"
__doc__ = "Setup some secrete shortcut based on Sen's preference."


from EnneadTab import ERROR_HANDLE, LOG
from EnneadTab.RHINO import RHINO_ALIAS

@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def secret_key_binding():
    dict = {
        "CtrlD": "_copy",
        "CtrlQ": "_scale1d",
        "CtrlR": "_rotate",
        "Ctrl1": "_polyline",   
    }

    for key, value in dict.items():
        RHINO_ALIAS.register_shortcut(key, value)
        print ("Registered shortcut: {} -> {}".format(key, value))

    
    
if __name__ == "__main__":
    secret_key_binding()
