import socket
import argparse
import json
from urllib.parse import urlparse
"""
Things to do:
1. Change the help message to display help for each command
2. Fix UGLY code :)
3. Headers aren't properly formatted
4. Saving to file always writes headers too. Can use if/else but it's very redundant so idk :|
5. Redirection (requests.get allows redirection by default)
6. changes to args.h so it works for multiple headers  :)
7. Haven't tested -f :|
8. Handle Verbosity
"""


def headerToDict(headers):
    result = {}
    for header in headers:
        key, value = header.split(':')
        result[key] = value
    return result


# -v, -h(works with "key:value"): Optional Argument, URL(has to be split) : Positional argument
# get|post: group arguments, Post can either have -d,-f but not both (optional arguments). GET has nothing
parser = argparse.ArgumentParser(
    description="httpc is a curl-like application but supports HTTP protocol only.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    usage='''\n%(prog)s command [arguments]''',
    prog="httpc",
    add_help=False,
    epilog='Use "httpc help [command]" for more information about a command.')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-get", action="store_true",
                   help="executes a HTTP GET request and prints the response.", dest='get')
group.add_argument("-post", action="store_true",
                   help="executes a HTTP POST request and prints the response.", dest='post')

parser.add_argument("-v", "--verbosity",
                    help="Prints the detail of the response such as protocol, status, and headers.", action="store_true")
parser.add_argument("-help", action='help', help='prints this screen')
parser.add_argument(
    "-h", help="Associates headers to HTTP Request with the format 'key:value'.", metavar="k:v", action='append')

parser.add_argument(
    "-d", help="Associates an inline data to the body HTTP POST request.", metavar="inline-data")
parser.add_argument(
    "-f", help="Associates the content of a file to the body HTTP POST request.", metavar="file")
parser.add_argument("URL", help="URL for the GET|POST request")
parser.add_argument(
    "-o", help="write the body of the response to the specified file.")

args = parser.parse_args()
print(args)
header = ''
if args.h:
    header = '\n'.join(args.h)

if args.get and (args.d or args.f):
    parser.error("GET can't have d or f arguments")

elif args.post and not (bool(args.d) != bool(args.f)):
    parser.error("POST should only have either d or f argument")

link = urlparse(args.URL)

print(link)

target_port = 80  # create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = link.netloc  # "httpbin.org"
endpoint = link.path  # "/status/418"
query = link.query
endpoint = endpoint + "?" + query if query else endpoint

# connect the client to the server
client.connect((host, target_port))

request_type = "GET" if args.get else "POST"

data = ''
if request_type == "POST":
    data = args.d if args.d else open(args.f).read()
    print(data)
request = f'''
{request_type} {endpoint} HTTP/1.0
Host:{host}
{header}

{data}'''
print(request)
# send http request over TCP
client.send(request.encode())

# receive http response
response = client.recv(4096)

if args.o:
    outputFile = open(args.o, "w")
    outputFile.write(response.decode("utf-8"))
    outputFile.close()
else:
    print(response.decode("utf-8"))

# decode and display the response
print(response.decode("utf-8"))


# python notcurl.py -post -h Content-Type:application-json -h Nice:One -d '{"number":2}' http://httpbin.org/post
# python notcurl.py -post -h Content-Type:application-json -h Nice:One -f datafile.json http://httpbin.org/post
# python notcurl.py -get -h Nice:One "http://httpbin.org/get?course=networking&assignment=1"
