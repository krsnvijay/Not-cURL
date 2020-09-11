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
#get|post: group arguments, Post can either have -d,-f but not both (optional arguments). GET has nothing
parser = argparse.ArgumentParser(
    description="httpc is a curl-like application but supports HTTP protocol only.", 
    formatter_class= argparse.RawDescriptionHelpFormatter,
    usage='''\n%(prog)s command [arguments]''',
    prog="httpc",
    add_help=False,
    epilog='Use "httpc help [command]" for more information about a command.')
# subparser = parser.add_subparsers()

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-get", help="executes a HTTP GET request and prints the response.", dest='get')
group.add_argument("-post", help="executes a HTTP POST request and prints the response.", dest='post')

# post_d = subparser.add_parser("-d", help="Associates an inline data to the body HTTP POST request.")
# post_f = subparser.add_parser("-f",help="Associates the content of a file to the body HTTP POST request.")
# post_d.add_argument("-post", help="executes a HTTP POST request and prints the response.")
# post_f.add_argument("-post", help="executes a HTTP POST request and prints the response.")

parser.add_argument("-v","--verbosity", help="Prints the detail of the response such as protocol, status, and headers.", action="store_true")
parser.add_argument("-help",action='help', help='prints this screen')
parser.add_argument("-h", help="Associates headers to HTTP Request with the format 'key:value'.", metavar="k:v", action='append', nargs="*")

parser.add_argument("-d",help="Associates an inline data to the body HTTP POST request.", metavar="inline-data")
parser.add_argument("-f",help="Associates the content of a file to the body HTTP POST request.", metavar="file")
# parser.add_argument("URL", help="URL for the GET|POST request")

args = parser.parse_args()