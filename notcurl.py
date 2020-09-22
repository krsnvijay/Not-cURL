import socket
import argparse
import json
import requests
from urllib.parse import urlparse

"""
Things to do:
1. Change the help message to display help for each command
2. Fix UGLY code
3. Headers aren't properly formatted
4. Saving to file always writes headers too. Can use if/else but it's very redundant so idk
5. Redirection (requests.get allows redirection by default)
6. changes to args.h so it works for multiple headers
7. Haven't tested -f
"""

# -v, -h(works with "key:value"): Optional Argument, URL(has to be split) : Positional argument 
#get|post: group arguments, Post can either have -d,-f but not both (optional arguments). GET has nothing
parser = argparse.ArgumentParser(
    description="httpc is a curl-like application but supports HTTP protocol only.", 
    formatter_class= argparse.RawDescriptionHelpFormatter,
    usage='''\n%(prog)s command [arguments]''',
    prog="httpc",
    add_help=False,
    epilog='Use "httpc help [command]" for more information about a command.')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-get", action="store_true", help="executes a HTTP GET request and prints the response.", dest='get')
group.add_argument("-post", action="store_true",help="executes a HTTP POST request and prints the response.", dest='post')

parser.add_argument("-v","--verbosity", help="Prints the detail of the response such as protocol, status, and headers.", action="store_true")
parser.add_argument("-help",action='help', help='prints this screen')
parser.add_argument("-h", help="Associates headers to HTTP Request with the format 'key:value'.", metavar="k:v", action='append', nargs="*")

parser.add_argument("-d",help="Associates an inline data to the body HTTP POST request.", metavar="inline-data")
parser.add_argument("-f",help="Associates the content of a file to the body HTTP POST request.", metavar="file")
parser.add_argument("URL", help="URL for the GET|POST request")
parser.add_argument("-o", help="write the body of the response to the specified file.")

args = parser.parse_args()

link = urlparse(args.URL)

# target_host = "httpbin.org"

# target_port = 80  # create a socket object
# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# # connect the client to the server
# client.connect((target_host, target_port))

# # make http request
# request_type = "GET"
# host = link.netloc #"httpbin.org"
# endpoint = link.path #"/status/418"
# request = f'''
# {request_type} {endpoint} HTTP/1.0
# Host:{host}

# '''

# # send http request over TCP
# client.send(request.encode())

# # receive http response
# response = client.recv(4096)

# # decode and display the response
# print(response.decode("utf-8"))

if args.h:
    header = dict()
    header[args.h[0][0].split(":")[0]] = args.h[0][0].split(":")[1] #UGLY and only works for one header. Need to change

if args.get and (args.d or args.f):
    parser.error("GET can't have d or f arguments")

elif args.post and not (bool(args.d) != bool(args.f)):
    parser.error("POST should only have either d or f argument")

elif args.get:
    if args.h:
        getStuff = requests.get(args.URL, headers=header)
    else:
        getStuff = requests.get(args.URL, allow_redirects=False)
    if args.o:
        outputFile = open(args.o, "w")
        contents = f'{getStuff.headers} \n {getStuff.text}' #always writes header to the file. If else can remove it but I dont wanna use it lol
        outputFile.write(contents)
        outputFile.close()
    else:
        if args.verbosity:
            print(getStuff.headers) #headers aren't properly formatted when printed
        print(getStuff.text)
   
elif args.post:
    print(args.h[0][0].split(":")[0])   #need to change. Really ugly
    if args.d:
        data = args.d
    else:
        data = args.f
    if args.h:
        postStuff= requests.post(args.URL, data, headers=header)
    else:
        postStuff = requests.post(args.URL, data)
    if args.o:
        outputFile = open(args.o, "w")
        contents = f'{postStuff.headers} \n {postStuff.text}'
        outputFile.write(contents)
        outputFile.close()
    else:
        if args.verbosity:
            print(postStuff.headers)
        print(postStuff.text)