import difflib
import http.server
import requests
import os
import mimetypes

errors = {}
config = {
    "PROXY-HEADER": "REMOTE_ADDR",
    "HTTP-FALLBACK": "REDIRECT /",
    "DEFAULT-HEADERS": []
}

def get_base(source, strn):
    print(source)
    print(strn)
    x = {}
    for key, val in source.items():
        print("Source: "+strn+"=>"+str(val))
        x[key] = val
        if not strn in x: x[strn] = val
    print(x)
    return x


def assemble_url(source, strip):
    res = source.replace(strip,"", 1)
    if not res: res = "/"
    return res

class RequestThrottle(http.server.SimpleHTTPRequestHandler):
    def do_GET(self, *o):
        if not CrossOrigin:
            self.send_error(403, "Forbidden", "The Site Admin has disabled the CrossOrigin Policy, blocking off all Non-Same-Originating Requests.\n\nFaithfully yours, Actress")
        found = False
        runtimeMap = get_base(httpMap, self.path)
        print(runtimeMap[self.path])
        for n in runtimeMap.keys():
            print(self.path)
            print(runtimeMap[n][1])
            if runtimeMap[n][1] in self.path:
                found = True
        if found:
            if runtimeMap[self.path][0] == "FILE":
                self.send_response(200)
                self.send_header("content-type", mimetypes.guess_type(httpMap[self.path][2])[0])
                for key, val in config["DEFAULT-HEADERS"]:
                    self.send_header(key, val)
                self.end_headers()
                line= open(runtimeMap[self.path][2], "r+").read()
                self.wfile.write(line.encode())
                print("here")
            elif runtimeMap[self.path][0] == "WSGI/HTTP":
                print("e")
                url = assemble_url(self.path, runtimeMap[self.path][1]) 
                asmHeaders = {}
                asmHeaders[config["PROXY-HEADER"]] = self.client_address[0]
                for k, v in self.headers.items():
                    asmHeaders[k] = v
                if self.rfile and self.command == "POST":
                    data = self.rfile.read()
                    data = data.decode()
                else:
                    data = ""
                print(url)
                r = requests.request(self.command, f"http://localhost:{runtimeMap[self.path][2]}/{url}", headers=asmHeaders, data=data)
                self.send_response(r.status_code)
                for key, val in r.headers.items():
                    self.send_header(key, val)
                for key, val in config["DEFAULT-HEADERS"]:
                    self.send_header(key, val)
                self.end_headers()
                self.wfile.write(r.content)
        else:
            #self.send_error(404)
            self.headers
            self.send_response(404)
            self.send_header("X-URL-FORWARDED-FOR", "127.0.0.1")
            self.send_header("Content-type", mimetypes.guess_type(errors["404"]))
            for key, val in config["DEFAULT-HEADERS"]:
                    self.send_header(key, val)
            self.end_headers()
            
            line= open(errors["404"], "r+").read()
            self.wfile.write(line.encode())

SameOrigin = []
CrossOrigin = True
httpMap = {}

def load_app(maindir):
    global CrossOrigin
    with open(os.path.join(maindir, "actress.inst")) as f:
        data = f.readlines()
        for line in data:
            if line.startswith("#"): continue
            if line.startswith("FORWARD"):
                if len(line.split()) == 4:
                    vlt, endpoint, _type, url = line.split()
                    httpMap[endpoint] = (_type, endpoint, url)
                    print(url)
                    port = 80
                else:
                    vlt, endpoint, _type, url, port = line.split()
                    httpMap[endpoint] = (_type, endpoint, port)
            elif line.startswith("ERROR"):
                vlt, ecode, file = line.split()
                errors[str(ecode)] = file
            elif line.startswith("PROXY-HEADER"):
                config["PROXY-HEADER"] = line.split()[1]
            elif line == "CROSSORIGIN ENABLE":CrossOrigin = True
            elif line == "CROSSORIGIN DISABLE":CrossOrigin = False
            elif line.startswith("SET-GLOBAL-HEADER"):
                instruction, key, *value = line.split()
                config["DEFAULT-HEADERS"].append((key, " ".join(value)))


load_app(".")
with http.server.HTTPServer(("127.0.0.1", 5000), RequestThrottle) as server:
    server.serve_forever()