import socket
import sys

def get_status_code(response):
	response_lines = response.split("\r\n")
	status_line = response_lines[0]
	stat_code_phrase = status_line[status_line.find(" ")+1:]
	return stat_code_phrase

def get_content_length(response):
	response_lines = response.split("\r\n")
	for line in response_lines:
		if line.split(' ')[0] == "Content-Length:":
			content_length = int(line.split(' ')[1])
			return content_length



index_file = sys.argv[1]
range_exists = False
range = None
LOWER_ENDPOINT = 0
UPPER_ENDPOINT = 1

host_url = index_file.split("/")[0] 
print("URL of the index file: {}".format(index_file))

if len(sys.argv) == 3:
	range_exists = True
	range = sys.argv[2].split("-")
	print("Lower endpoint = {}".format(range[0]))
	print("Upper endpoint = {}".format(range[1]))
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

stat_code_phrase = get_status_code(response)

if stat_code_phrase != "200 OK":
	print("Error")
	print("Status line:", status_line)
	print("Exiting!")
	sys.exit()

response_lines = response.split("\r\n")

# print("Response lines")
# print(response_lines)

file_urls = response_lines[-1].split("\n")
file_urls = [url for url in file_urls if len(url) != 0]

# print("File URLs")
# print(repr(file_urls))
print("There are {} files in the index".format(len(file_urls)))

s.shutdown(socket.SHUT_RDWR)
s.close()


for idx, url in enumerate(file_urls, 1):
	file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host_url = url.split("/")[0]
	file_socket.connect((host_url, 80))

	directory = url[url.find('/'):]

	request = "HEAD {} HTTP/1.1\r\nHost: {}\r\n\r\n".format(directory, host_url)
	file_socket.sendall(request.encode())  

	response = file_socket.recv(16384).decode()
	stat_code_phrase = get_status_code(response)

	if stat_code_phrase != "200 OK":
		print("{}. {} is not found".format(idx, url))
		continue

	if range_exists:
		content_length = get_content_length(response)

		if content_length < range[LOWER_ENDPOINT]:
			print("{}. {} (size = {}) is not downloaded".format(idx, url, content_length))
			continue

		















