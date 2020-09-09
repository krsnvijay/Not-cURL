import socket
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
print(response.decode("utf-8"))
