import socket
import argparse
import json
import re
from urllib.parse import urlparse
import json
from httplib import parse_http_response, make_http_request

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


def makeRequest(args, counter=0):
    if counter > 5:
        print("Max Redirection Limit Reached")
        return
    header = []
    if args.h:
        header = args.h[:]
    if args.get and (args.d or args.f):
        parser.error("GET can't have d or f arguments")

    elif args.post and not (bool(args.d) != bool(args.f)):
        parser.error("POST should only have either d or f argument")

    link = urlparse(args.URL)

    target_port = 8080  # create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = link.netloc  # "httpbin.org"
    endpoint = link.path  # "/status/418"
    query = link.query
    if endpoint == '':
        endpoint = "/"
    endpoint = endpoint + "?" + query if query else endpoint
    request_type = "GET" if args.get else "POST"

    # connect the client to the server
    client.connect((host, target_port))

    data = ''
    if request_type == "POST":
        data = args.d if args.d else open(args.f).read()
        data = data.strip("'")
        header.append(f"Content-Length: {len(data)}")
    header.insert(0, f'Host: {host}')
    request = make_http_request(request_type, endpoint, header, data)

    # send http request over TCP
    client.send(request.encode())
    # receive http response
    raw_response = client.recv(8192)
    receiveData = raw_response.decode("utf-8")
    response = parse_http_response(raw_response)

    if response["status"] == 301:
        # link for redirection but idk how to test this
        result = filter(lambda x: x.startswith('Location:'), response["headers"])
        args.URL = next(result).split(" ")[1]
        print(f'\nRedirecting to new URL {args.URL}\n')
        makeRequest(args, counter + 1)
        return

    content = receiveData if args.verbosity else response["body"]
    if args.o:
        with open(args.o, "w") as output_file:
            output_file.write(content)
    else:
        print(content)


def get_parser():
    # -v, -h(works with "key:value"): Optional Argument, URL(has to be split) : Positional argument
    # get|post: group arguments, Post can either have -d,-f but not both (optional arguments). GET has nothing
    parser = argparse.ArgumentParser(
        description="httpc is a curl-like application but supports HTTP protocol only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage='''\n%(prog)s command [arguments]''',
        prog="httpc",
        add_help=False,
        epilog='Use "httpc help [command]" for more information about a command.')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-get", action="store_true",
                       help="executes a HTTP GET request and prints the response.", dest='get')
    group.add_argument("-post", action="store_true",
                       help="executes a HTTP POST request and prints the response.", dest='post')

    parser.add_argument("-v", "--verbosity",
                        help="Prints the detail of the response such as protocol, status, and headers.",
                        action="store_true")
    parser.add_argument("-help", action='store_true', help='prints this screen')
    parser.add_argument(
        "-h", help="Associates headers to HTTP Request with the format 'key:value'.", metavar="k:v", action='append')

    parser.add_argument(
        "-d", help="Associates an inline data to the body HTTP POST request.", metavar="inline-data")
    parser.add_argument(
        "-f", help="Associates the content of a file to the body HTTP POST request.", metavar="file")
    parser.add_argument("URL", help="URL for the GET|POST request", nargs='?')
    parser.add_argument(
        "-o", help="write the body of the response to the specified file.")
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    if args.help:
        if args.get:
            helpMessage = f'''
            httpc help get
            usage: httpc get [-v] [-h key:value] URL 
            Get executes a HTTP GET request for a given URL. 
            
            -v Prints the detail of the response such as protocol, status, and headers. 
            -h key:value Associates headers to HTTP Request with the format 'key:value'.'''
        elif args.post:
            helpMessage = f'''
            httpc help post
            usage: httpc post [-v] [-h key:value] [-d inline-data] [-f file] URL 
            
            Post executes a HTTP POST request for a given URL with inline data or from file. 
            
            -v Prints the detail of the response such as protocol, status, and headers. 
            -h key:value Associates headers to HTTP Request with the format 'key:value'. 
            -d string Associates an inline data to the body HTTP POST request. 
            -f file Associates the content of a file to the body HTTP POST request. 
            
            Either [-d] or [-f] can be used but not both.'''
        else:
            helpMessage = f'''
            httpc is a curl-like application but supports HTTP protocol only. 
            Usage: 
                httpc command [arguments] 
            The commands are: 
                get     executes a HTTP GET request and prints the response. 
                post    executes a HTTP POST request and prints the response. 
                help    prints this screen. 
                
            Use "httpc help [command]" for more information about a command.'''
        print(helpMessage)
    else:
        makeRequest(args)
    # print(response.decode("utf-8"))

# python httpc.py -help
# python httpc.py -help -get
# python httpc.py -help -post

# decode and display the response
# print(response.decode("utf-8"))

# Get
# python httpc.py -get -h Nice:One "http://httpbin.org/get?course=networking&assignment=1"
# python httpc.py -get -v "http://httpbin.org/get?course=networking&assignment=1"

# Post
# python httpc.py -post -h Content-Type:application/json -d '{\"Assignment\":1}' "http://httpbin.org/post"
# python httpc.py -post -h Content-Type:application/json -h Nice:One -f datafile.json http://httpbin.org/post

# Redirection
# python httpc.py -get -h Authorization:None -h "Content-Type":"application/json" "http://httpbin.org/get?course=networking&assignment=1" -o output.txt
# python httpc.py -get http://bit.ly/ateapot -v
# python httpc.py -get http://ca.yahoo.com/


# python httpc.py -get "http://httpbin.org/get"
# python httpc.py -get -h Authorization:None "http://httpbin.org/get?course=networking&assignment=1" -o
# python httpc.py -get -h Authorization:None -h "Content-Type":"application/json" "http://httpbin.org/get?course=networking&assignment=1"
# python httpc.py -get -v Authorization:None -h "Content-Type":"application/json" "http://httpbin.org/get?course=networking&assignment=1"

# python httpc.py -post -h "Content-Type":"application/json" -d '{"Assignment":1,"Demo":10}' "http://httpbin.org/post"
# python httpc.py -post -h "Content-Type":"application/json" -h Authorization:None -f datafile.json "http://httpbin.org/post"

# python httpc.py -get -v http://bit.ly/cybernauts
# python httpc.py -get -v -h Authorization:None -h "Content-Type":"application/json" -o output.txt "http://httpbin.org/get?course=networking&assignment=1"
