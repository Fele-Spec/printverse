import os, sys; path = os.environ["PV_SCRIPT"]; sys.argv = [path]; code = compile(open(path, "rb").read(), path, "exec"); exec(code, {"__name__": "__main__", "__file__": path})
