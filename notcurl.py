import socket
import argparse
import json

target_host = "httpbin.org"

target_port = 80  # create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client to the server
client.connect((target_host, target_port))

# make http request
request_type = "GET"
host = "httpbin.org"
endpoint = "/status/418"
request = f'''
{request_type} {endpoint} HTTP/1.0
Host:{host}

'''

# send http request over TCP
client.send(request.encode())

# receive http response
response = client.recv(4096)

# decode and display the response
# print(response.decode("utf-8"))


# -v, -h(works with "key:value"): Optional Argument, URL(has to be split) : Positional argument
# get|post: group arguments, Post can either have -d,-f but not both (optional arguments). GET has nothing
parser = argparse.ArgumentParser(
    description="httpc is a curl-like application but supports HTTP protocol only.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    prog="httpc",
    add_help=False,
    epilog='Use "httpc help [command]" for more information about a command.')

parser.add_argument("-help", action='help', help='prints this screen')
parser.add_argument("-v", "--verbosity",
                    help="Prints the detail of the response such as protocol, status, and headers.", action="store_true")
parser.add_argument("-h", help="Associates headers to HTTP Request with the format 'key:value'.",
                    metavar="k:v", action='append', nargs="*")

subparser = parser.add_subparsers(help='commands')

subparser_get = subparser.add_parser(
    "get", help="Get executes a HTTP GET request for a given URL.")


subparser_post = subparser.add_parser(
    "post", help="Post executes a HTTP POST request for a given URL with inline data or from file")

group = subparser_post.add_mutually_exclusive_group(required=True)
group.add_argument(
    "-d", help="Associates an inline data to the body HTTP POST request.", metavar="inline-data", action='store')
group.add_argument(
    "-f", help="Associates the content of a file to the body HTTP POST request.", metavar="file", action='store')

parser.add_argument("URL", help="URL for the GET|POST request")

# python notcurl.py post -d "x" httpbin.org

args = parser.parse_args()
print(args)
