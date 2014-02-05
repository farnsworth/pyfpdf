# -*- coding: utf-8 -*-

# common utilities for pyfpdf tests
# Note: 1) this file imported from both 2 and 3 version of python
#       2) import this file before import fpdf
#       3) assert this file in tests/cover folder

import sys, os, subprocess

PY3K = sys.version_info >= (3, 0)

basepath = os.path.abspath(os.path.join(__file__, "..", "..")) 

RESHASH = "7c6230f7ec99d40170503e513f825c43"

# if PYFPDFTESTLOCAL is not set - use instaled pyfpdf version
PYFPDFTESTLOCAL = ("PYFPDFTESTLOCAL" in os.environ)
if PYFPDFTESTLOCAL:
    sys.path = [os.path.join(basepath, "fpdf_local")] + sys.path
    

if PY3K:
    #import common3 as _common
    def tobytes(value):
        return value.encode("latin1")
    def frombytes(value):
        return value.decode("latin1")
    from hashlib import md5

else:
    #import common2 as _common
    def tobytes(value):
        return value
    def frombytes(value):
        return value
    try:
        from hashlib import md5
    except ImportError:
        import md5

def exec_cmd(cmd):
    "Execute command and return console output (stdout, stderr)"
    obj = subprocess.Popen(cmd, \
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE)
    std, err = obj.communicate()
    return (frombytes(std), frombytes(err))

def start_by_ext(fn):
    "Open file in associated progrom"
    try:
        try:
            os.startfile(fn)
        except WindowsError:
            os.system("start " + fn)
    except:
        subprocess.call(["xdg-open", fn])

def writer(stream, items):
    sep = ""
    for item in items:
        stream.write(sep)
        sep = " "
        if not isinstance(item, str):
            item = str(item)
        if not PY3K:
            if not isinstance(item, unicode):
                item = str(item)
        stream.write(item)
    stream.write("\n")
    
def log(*kw):
    writer(sys.stdout, kw)

def err(*kw):
    writer(sys.stderr, kw)
    
def test_putinfo(self):
    "Replace info stamp with defaults for all automated test objects"
    self._out('/Producer '+self._textstring('PyFPDF TEST http://pyfpdf.googlecode.com/'))
    if hasattr(self,'title'):
        self._out('/Title '+self._textstring(self.title))
    if hasattr(self,'subject'):
        self._out('/Subject '+self._textstring(self.subject))
    if hasattr(self,'author'):
        self._out('/Author '+self._textstring(self.author))
    if hasattr (self,'keywords'):
        self._out('/Keywords '+self._textstring(self.keywords))
    if hasattr(self,'creator'):
        self._out('/Creator '+self._textstring(self.creator))
    self._out('/CreationDate '+self._textstring('D:19700101000000'))

def file_hash(fn):
    "Calc MD5 hash for file"
    md = md5()
    f = open(fn, "rb")
    try:
        md.update(f.read())
    finally:
        f.close()
    return md.hexdigest()

def read_cover_info(fn):
    "Read cover test info"
    f = open(fn, "rb")
    da = {"res": []}
    mark = "#PyFPDF-cover-test:"
    encmark = "# -*- coding:"
    enc = None
    try:
        hdr = False
        for line in f.readlines():
            if enc is None:
                if line.decode("latin-1")[:len(encmark)] == encmark:
                    enc = line.decode("latin-1")[len(encmark)].strip()
                    if enc[-3:] == "-*-":
                        enc = enc[:-3].strip()
                        try:
                            line.decode("enc")
                        except:
                            enc = None                    
            line = line.decode(enc or "UTF-8").strip()
            if line[:len(mark)] == mark:
                hdr = True
                kv = line[len(mark):].split("=", 1)
                if len(kv) == 2:
                    if kv[0] == "res":
                        da["res"].append(kv[1])
                    else:
                        da[kv[0]] = kv[1]
            else:
                if hdr and len(line) == 0:
                    break
                
    finally:
        f.close()
    return da

def parse_test_args(args, deffn):
    "Parse test args, return (fn, autotest)"
    args = args[1:]
    da = {}
    da["fn"] = deffn
    da["autotest"] = False
    da["check"] = False
    while len(args) > 0:
        arg = args[0]
        if arg == "--help":
            log("Test usage: [--auto] [--check] [<outputname>]")
            log("  --auto - no version and timestamp in file, do not open")
            log("  --check - compare new file with stock")
            log("  <outputname> - output filename, default \"%s\"" % deffn)
            sys.exit(0)
        if arg == "--auto":
            da["autotest"] = True
        elif arg == "--check":
            da["check"] = True
        else:
            da["fn"] = arg
        args = args[1:]
    return da
    
def load_res_file(path):
    items = {}
    res = None
    for line in open(path):
        line = line.strip()
        if line[:1] == "#":
            continue
        kv = line.split("=", 1)
        if len(kv) != 2:
            continue
        if kv[0] == "res":
            res = kv[1]
            if res not in items:
                items[res] = ["", []]
        elif res is None:
            continue
        elif kv[0] == "hash":
            items[res][0] = kv[1]
        elif kv[0] == "tags":
            items[res][1] += [kv[1].split(",")]
    return items
    
def check_env(settings, args):
    "Check test environment"
    verbose = not args["autotest"]
    # check python version
    if PY3K:
        if settings.get("python3", "yes") == "no":
            # python 3 inacceptable
            if verbose:
                err("Python 3.x unsupported %s" % repr(sys.version_info))
            else:
                log("NOTFORPY3")
            return False
    else:
        if settings.get("python2", "yes") == "no":
            # python 2 inacceptable
            if verbose:
                err("Python 2.x unsupported %s" % repr(sys.version_info))
            else:
                log("NOTFORPY2")
            return False
    if settings.get("pil", "no") == "yes":
        # import PIL
        try:
            try:
                import Image
            except:
                from PIL import Image
        except ImportError:
            Image = None
        if Image is None:
            if verbose:
                err("PIL or Pillow module is required")
            else:
                log("NOPIL")
            return False
    # check res
    reslst = None
    for res in settings.get("res", []):
        if reslst is None:
            # check
            respath = os.path.join(basepath, "resources.txt")
            if file_hash(respath) != RESHASH:
                if verbose:
                    err("File resources.txt damaged (hash mismatch)")
                else:
                    log("RESHASH")
                return False
            # load data
            reslst = load_res_file(respath)
        if res not in reslst:
            err("Resource \"" + res + "\" not found")
            if not verbose:
                log("NORES")
            return False
        # check hash
        respath = os.path.join(basepath, res)
        hs = file_hash(respath)
        if hs != reslst[res][0]:
            err("Resource \"" + res + "\" damaged")
            err("      read = %s" % hs)
            err("  required = %s" % reslst[res][0])
            if not verbose:
                log("RESERR")
            return False
            
    return True
    
def check_result(settings, args):
    check = True
    if settings.get("fn"):        
        if args["check"]:
            # compare with hash
            hs = file_hash(args["fn"])
            fhs = settings.get("hash", "<not specified>")
            if hs != fhs:
                check = False
                err("Hash mismatch:")
                err("       new = %s" % hs)
                err("  required = %s" % fhs)

    if args["autotest"]:
        if check:
            log("OK")
        else:
            log("HASHERROR")
    else:
        if settings.get("fn"):        
            start_by_ext(args["fn"])
        else:
            log("Test passed")

def testmain(fn, testfunc):
    si = read_cover_info(fn)
    da = parse_test_args(sys.argv, si.get("fn"))
    if not check_env(si, da):
        return
    testfunc(da["fn"], da["autotest"] or da["check"])
    check_result(si, da)

