import socket
import os

# constants
IP = '127.0.0.1'
PORT = 8090
SOCKET_TIMEOUT = 5.0 # the time the server waits before raising error if there is no Get

#Get data from file
def get_file_data(file_root):
    file_data = open(file_root, 'rb')
    data = file_data.read()
    file_data.close()
    return data

def create_file(file_name, client_socket):
    """create a file using the data recieved from client

    Args:
        file_name (str)
        client_socket ([type]): the connection with the client
    """
    file_path = "webroot\\imgs\\" + file_name
    with open(file_path, 'wb') as image:
        data = 4096 * 'i'
        print("file opened")
        #run until reading all of the data
        while len(data) == 4096:
            print("recieving data...")
            data = client_socket.recv(4096)
            image.write(data)
        print("file recieved")

#Get content type
def get_content_type(type):
    contents = {"html": "text/html; charset=utf-8",
                    "txt": "text/html; charset=utf-8",
                    "jpg": "image/jpeg",
                    "js": "text/javascript; charset=UTF-8",
                    "css": "text/css",
                    "ico": "image/x-icon",
                    "gif": "image/gif"}
    return contents[type]

#Check the required resource, generate proper HTTP response and send to client
def handle_client_request(file_name, client_socket):
    http_header = "HTTP/1.1"
    data = ""

    if "image?" in file_name:
        image_name = file_name.split('=')[1]
        url = "webroot\\imgs\\" + image_name + '.jpg'
        with open(url, 'rb') as hamutzi:
            data = hamutzi.read()            
        status = " 200 OK\r\nContent-Length: " + str(os.path.getsize(url)) + "\r\nContent-Type: " + "image/jpeg" + "\r\n\r\n"

    #if one of the functions was called
    elif "calculate-next?" in file_name:
        num_sent = int(file_name.split('=')[-1])
        num_to_send = num_sent + 1
        status = " 200 OK\r\nContent-Length: " + str(len(str(num_to_send))) + "\r\nContent-Type: text/plain\r\n\r\n" + str(num_to_send)
    
    elif "calculate-area?" in file_name:
        parts = file_name.split('=')
        width = int(parts[-1])
        length = int(parts[-2].split('&')[0]) 
        area = (length * width) / 2
        status = " 200 OK\r\nContent-Length: " + str(len(str(area))) + "\r\nContent-Type: text/plain\r\n\r\n" + str(area)
    else:
        directory = 'webroot\\'
        DEFAULT_URL = directory + "index.html"
        
        if file_name == '': # in case no specific file was requested
            url = DEFAULT_URL
            file_name = 'index.html'
        else:
            url = directory + file_name # generating the url

        if os.path.isfile(url):# if the requested file exists
            print(url)
            response_dict = {"index.html": "ok",
            "css\\doremon.css": "ok",
            "js\\box.js": "ok",
            "js\\jquery.min.js": "ok",
            "js\\submit.js": "ok",
            "imgs\\abstract.jpg": "ok",
            "imgs\\favicon.ico": "ok",
            "imgs\\loading.gif": "ok",
            "imgs\\1546435417505.jpg" : "ok",
            "ido.html": "forbidden",
            "index1.html": "moved"}

            if response_dict[file_name] == "ok":
                file_type = url.split(".")[-1]
                status = " 200 OK\r\nContent-Length: " + str(os.path.getsize(url)) + "\r\nContent-Type: " + get_content_type(file_type) + "\r\n\r\n"
                data = get_file_data(url)
                print(data)
            elif response_dict[file_name] == "forbidden": 
                status = " 403 Forbidden"
            elif response_dict[file_name] == "moved":
                status = " 302 Temprarily Moved\r\nLocation: index.html"    
        else:# if the request was not understood
            status = " 500 Internal Server Error"    
            
    http_header += status
    print(http_header)
    print("the file name is " + file_name)

    # generating the response properly    
    if not isinstance(data, bytes):
        data = data.encode()
    http_header = http_header.encode()
    http_response = http_header + data
    print(http_response)
    client_socket.send(http_response)

#saving an image the client sent and generating propet HTTP response
def handle_post_request(request, client_socket):
    str_request = str(request)
    
    #if the client sent post request
    if "upload?" in str_request:
        image_name = str_request.split(' ')[1].split("file-name=")[1]
        print("the image name is: " + image_name)
        create_file(image_name, client_socket)
        status = " 200 OK\r\nContent-Length: " + "20" + "\r\nContent-Type: text/plain\r\n\r\n" + "successfuly uploaded"
    client_socket.send(("HTTP/1.1" + status).encode())  

#Check if request is a valid HTTP request and returns TRUE / FALSE and the requested file name
def validate_http_request(request):
    web_root = request.decode().split(r'\r\n')[0].split(' ')[1][1:]# take the requested file name
    if '/' in web_root:
        web_root = web_root.replace('/', '\\')
    decoded_request = str(request.decode())# it been received binary

    #ensure the request is valid
    if decoded_request[0:3] != 'GET':
        return False, web_root
    if decoded_request[3] != ' ':
        return False, web_root
    if "HTTP/1.1" not in decoded_request:
        return False, web_root
    return True, web_root

# checks if the request is a valid post request and return true or false 
def validate_post_request(request):  
    if request[0:4].decode() == 'POST':
        return True
    return False
    
#Handles client requests: verifies client's requests are legal HTTP, calls function to handle the requests
def handle_client(client_socket):

    print('Client connected')
    client_request = client_socket.recv(4096)# receiving the data the client sent
    print(client_request)
    valid_post = validate_post_request(client_request)
    if valid_post: 
        print('Got a valid POST request')
        handle_post_request(client_request, client_socket)
    else:   
        valid_http, file_name = validate_http_request(client_request)# valid the request
    
        if valid_http:# the request is valid
            print('Got a valid HTTP request')
            handle_client_request(file_name, client_socket)
        else:
            print('Error: Not a valid request')
        
    print('Closing connection')
    client_socket.close()

#main function - Open a socket and loop forever while waiting for clients
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# defining the socket
    server_socket.bind((IP, PORT))# setting the current ip and port
    server_socket.listen()# the time it listen to client until closing the socket
    print("Listening for connections on port %d" % PORT)

    while True:
        client_socket, client_address = server_socket.accept()# accept the request
        print('New connection received')
        # client_socket.settimeout(SOCKET_TIMEOUT)# defining the time until the socket will be shut down
        handle_client(client_socket)

if __name__ == "__main__":
    # Call the main handler function
    main()