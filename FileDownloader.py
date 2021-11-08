import socket
import sys


index_file = sys.argv[1]
range_exists = False
range = None

host_url = index_file.split("/")[0] 
print("URL of the index file: {}".format(index_file))

if len(sys.argv) == 3:
	range_exists = True
	range = sys.argv[2].split("-")
	print(range)
elif len(sys.argv) != 2:
	print("Incorrect # of arguments")
	sys.exit()
else:
	print("No range is given")



s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((host_url, 80))

directory = index_file[index_file.find('/'):]
# print("directory:", directory)

request = "GET {} HTTP/1.1\r\nHost: {}\r\n\r\n".format(directory, host_url)

# print("request:", request)

s.sendall(request.encode())  

response = s.recv(16384).decode()

print("Index file is downloaded")

# print("Response")
# print(response)

response_lines = response.split("\r\n")
status_line = response_lines[0]
stat_code_phrase = status_line[status_line.find(" ")+1:]


if stat_code_phrase != "200 OK":
	print("Error")
	print("Status line:", status_line)
	print("Exiting!")
	sys.exit()


file_urls = response_lines[-1].split("\n")
file_urls = [url for url in file_urls if len(url) != 0]

# print("File URLs")
# print(repr(file_urls))
print("There are {} files in the index".format(len(file_urls)))
