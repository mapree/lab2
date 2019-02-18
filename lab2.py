import os
import sys
import threading
import socket

BACKLOG = 5
DATA_RECV = 4096
BAD_WORDS = ["spongebob", "britney spears", "paris hilton", "norrköping", "viii"] #test
REDIRECT_URL_BAD_URL = "http://www.ida.liu.se/~TDTS04/labs/2011/ass2/error1.html"
REDIRECT_URL__BAD_CONTENT = "http://www.ida.liu.se/~TDTS04/labs/2011/ass2/error2.html"

# Search for bad words in a given string
def contains_bad_words(str):
    for word in BAD_WORDS:
        if(str.find(word) != -1):
            return True
    return False

# Initialize the proxy 
def main():

    # check if port number was given in command line
    if (len(sys.argv)<2):
        print ("No port given, using :8080 (http-alt)") 
        port = 8080
    else:
        port = int(sys.argv[1]) # port from argument
    
    host = '127.0.0.1' # get local machine name
    
    try:
        #create a socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        print("server on ", host, ": ", port)

        # associate socket to host and port
        s.bind((host, port))

        # wait for client connection
        s.listen(BACKLOG)

    except OSError as message:
        if s:
            s.close()
        print("Proxy socket problem", message)
        sys.exit(1)

    while True:
        # establish connection with client
        connection_socket, client_addr = s.accept()

        # create a thread to handle the request
        threading.Thread(target=proxy_server_side, args=(connection_socket, client_addr)).start()
    
    s.close()

# Server part of the proxy : send request to the client side of proxy or 
#       send 301 response to browser if censured words contained in url
def proxy_server_side(connection_socket, client_addr):

    # get the request from browser
    request = connection_socket.recv(DATA_RECV).decode('utf-8')
    
    # get first line
    first_line = request.split("\n")[0]
    
    print(first_line)
    # get the absolute url
    url = first_line.split(" ")[1]
    
    # check url for bad words
    if(contains_bad_words(url.lower())):
        print("Censured words found in url : web redirection")
        response = "HTTP/1.1 301 Moved Permanently\r\nLocation: " + REDIRECT_URL_BAD_URL + "\r\n"
        connection_socket.send(response.encode())
        connection_socket.close()
    
    else:
        proxy_client_side(connection_socket, client_addr, request)

def proxy_client_side(connection_socket, client_addr, request):
    
    # get first line
    first_line = request.split("\n")[0]
    
    # get the absolute url
    url = first_line.split(" ")[1]

    print(client_addr, "\tRequest\t", first_line)

    # find webserver name
    webserver_begin_pos = url.find("://")
    webserver_end_pos = url.find("/",webserver_begin_pos+3)
    web_server_name = url[webserver_begin_pos+3:webserver_end_pos]
    
    port_server = 80
       
    try:
        # create a socket to connect to the web server
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.connect((web_server_name, port_server))        
        s2.send(request.encode())
        
        # retrieve data
        data_encoded = s2.recv(DATA_RECV)
        
        # check if content-type header is text
        isText = False
        headers, sep, body = data_encoded.partition(b"\r\n\r\n")
        headers = headers.decode('utf-8')
        if (headers.find("Content-Type: text") != -1):
                isText = True

        print(headers)
        print("length header: ", len(headers.encode()))

        text_encoded = b""
        # receive data from web server and send it to browser
        while(len(data_encoded) != 0):
            #print("****PRINT*** ", data_encoded.decode('utf-8'))
            print("length data: ", len(data_encoded))
            
            # if the content is text
            if(isText):
                text_encoded += data_encoded
                # End of data transfer: check for censured words in text content
                if(len(data_encoded) < DATA_RECV): 
                    if(contains_bad_words(text_encoded.decode('utf-8').lower())):
                        print("Censured words found in content : web redirection")
                        response = "HTTP/1.1 301 Moved Permanently\r\nLocation: " + REDIRECT_URL__BAD_CONTENT + "\r\n"
                        connection_socket.send(response.encode())
                    else:
                        connection_socket.send(text_encoded) 
            else:
                connection_socket.send(data_encoded)     
            
            data_encoded = s2.recv(DATA_RECV)

        s2.close()
        connection_socket.close()
    except OSError as error:
        if s2:
            s2.close()
        if connection_socket:
            connection_socket.close()
        print("client side proxy problem", error)
        #sys.exit(1)

if __name__ == "__main__":
    main()