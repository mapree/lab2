# check code status

import os
import sys
import threading
import socket

BACKLOG = 5
DATA_RECV = 4096
BAD_WORDS = ["palace", "britney spears", "paris hilton", "norrköping", "viii"] #test
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

    # get the absolute url
    if(len(first_line) == 0):
        print("first line empty")
        connection_socket.close()
        return
    url = first_line.split(" ")[1]
    
    print(client_addr, "\tRequest\t", first_line) 

    # check url for bad words
    if(contains_bad_words(url.lower())):
        print("Censured words found in url : web redirection")
        response = "HTTP/1.1 301 Moved Permanently\r\nLocation: " + REDIRECT_URL_BAD_URL + "\r\n"
        connection_socket.send(response.encode())     
    
    else:
        response = proxy_client_side(request)
        connection_socket.send(response)
    
    connection_socket.close()

def proxy_client_side(request):
    #print(request)

    # get first line
    first_line = request.split("\n")[0]
    
    # get the absolute url
    url = first_line.split(" ")[1]

    # find webserver name
    webserver_begin_pos = url.find("://")
    webserver_end_pos = url.find("/",webserver_begin_pos+3)
    web_server_name = url[webserver_begin_pos+3:webserver_end_pos]
    
    port_server = 80

    # modify the request
    if(url.find("://") != -1):
        print("Modify request")
        first_line_end_pos = request.find("\n")
        temp = request[first_line_end_pos+1:]
        abs_path = url[webserver_end_pos:]
        request = first_line.split(" ")[0] + " " + abs_path + " " + first_line.split(" ")[2] + "\n" + temp
        #print(request)

    try:
        # create a socket to connect to the web server
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.connect((web_server_name, port_server))        
        s2.send(request.encode())
        
        # retrieve data
        all_data_encoded = data_received = s2.recv(DATA_RECV)
        
        # check if content-type header is text and not compressed (gzip)
        isText = False
        headers, sep, body = all_data_encoded.partition(b"\r\n\r\n")
        headers = headers.decode('utf-8')
        if (headers.find("Content-Type: text") != -1):
            if(headers.find("gzip") == -1):
                isText = True

        #print(headers)
        #print("length header: ", len(headers.encode()))

        # receive data from web server and send it to browser
        while(len(data_received) != 0):
            
            #print("length all data: ", len(all_data_encoded))
            #print("length data received: ", len(data_received))
            
            # if the content is text
            if(isText):
                # check for censured words in text content 
                if(contains_bad_words(data_received.decode('utf-8').lower())):
                    print("Censured words found in content : web redirection")
                    response = "HTTP/1.1 301 Moved Permanently\r\nLocation: " + REDIRECT_URL__BAD_CONTENT + "\r\n"
                    s2.close()
                    return response.encode() 
            
            data_received = s2.recv(DATA_RECV)
            all_data_encoded += data_received   

        s2.close()
        return all_data_encoded

    except OSError as error:
        if s2:
            s2.close()
        print("client side proxy problem", error)
        #sys.exit(1)

if __name__ == "__main__":
    main()