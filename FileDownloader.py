import socket
import sys
import time

# returns the status code from a given HTTP response message
def get_status_code(response):
	response_lines = response.split("\r\n")
	status_line = response_lines[0]
	stat_code_phrase = status_line[status_line.find(" ")+1:]
	return stat_code_phrase


'''
Base ceil power of 2 will be 4096 as we need to include header information
even if we do not have any object. Then, as we need more space to store
header in addition to the object, I simply multiply the ceil with 2.
'''
def ceil_power_2(length):
	ceil_pow = 4096
	while ceil_pow < length:
		ceil_pow *= 2

	ceil_pow *= 2
	return ceil_pow


# returns the content length from a given HTTP response message
def get_content_length(response):
	response_lines = response.split("\r\n")
	for line in response_lines:
		if line.split(' ')[0] == "Content-Length:":
			content_length = int(line.split(' ')[1])
			return content_length
	return 0


# returns the buffer size from a given HTTP response message
def find_buffer_size(response):
	content_length = get_content_length(response)
	buf_size = ceil_power_2(content_length)
	# print("Content length: {}, Buffer size: {}".format(content_length, buf_size))
	return buf_size


# returns content range from a given HTTP response message
def get_content_range(response):
	response_lines = response.split("\r\n")
	for line in response_lines:
		if line.split(' ')[0] == "Content-Range:":
			content_range = line.split(' ')[2]
			lower_range, upper_range = content_range.split('-')
			upper_range = upper_range.split('/')[0]
			return int(lower_range), int(upper_range)
	return 0, 0


# returns directory substring from a given URL
def get_directory(url):
	return url[url.find('/'):]


# returns the object from a response message
def get_object(response):
	idx = response.find("\r\n\r\n")
	return response[idx+4:]

def get_object_all(response):
	idx = response.find("\r\n\r\n")
	if idx == -1:
		return ""
	return response[idx+4:]


def recv_all(sock, response):
	timeout = 1
	sock.setblocking(False)
	data = bytearray()
	begin = time.time()
	content_length = get_content_length(response)
	while True:
		if data and time.time() - begin > timeout:
			break
		elif time.time() - begin > timeout * 2:
			break
		try:
			packet = sock.recv(8192)
			if packet:
				data.extend(packet)
				begin = time.time()
			else:
				time.sleep(0.2)
		except:
			pass
		if len(get_object_all(data.decode())) == content_length:
			break
	return data

def recv_all_range(sock, response, lrange, urange):
	n = (urange - lrange + 1)
	content_length = get_content_length(head_response)
	if content_length < (urange - lrange + 1):
		n = content_length - lrange

	timeout = 1
	sock.setblocking(False)
	data = bytearray()
	begin = time.time()
	while True:
		if data and time.time() - begin > timeout:
			break
		elif time.time() - begin > timeout * 2:
			break
		try:
			packet = sock.recv(8192)
			if packet:
				data.extend(packet)
				begin = time.time()
			else:
				time.sleep(0.2)
		except:
			pass
		if len(get_object_all(data.decode())) == n:
			break
	return data

'''

def recv_all(sock, head_response):
	data = bytearray()
	content_length = get_content_length(head_response)
	n = content_length + len(head_response)
	while len(get_object_all(data.decode())) != content_length:
		packet = sock.recv(8192)
		if not packet:
			return None
		data.extend(packet)
	return data


def recv_all_range(sock, head_response, lrange, urange):
	n = (urange - lrange + 1)
	content_length = get_content_length(head_response)
	if content_length < (urange - lrange + 1):
		n = content_length - lrange
	data = bytearray()
	while len(get_object_all(data.decode())) != n:
		packet = sock.recv(8192)
		if not packet:
			return None
		data.extend(packet)
	return data
'''

index_file = sys.argv[1]
range_exists = False
ranges = None
LOWER_ENDPOINT = 0
UPPER_ENDPOINT = 1

# get host URL from the index URL
host_url = index_file.split("/")[0]
print("URL of the index file: {}".format(index_file))

# get arguments from the command line
if len(sys.argv) == 3:
	range_exists = True
	ranges = sys.argv[2].split("-")
	ranges = [int(i) for i in ranges]
	print("Lower endpoint = {}".format(ranges[0]))
	print("Upper endpoint = {}".format(ranges[1]))
elif len(sys.argv) != 2:
	print("Incorrect # of arguments")
	sys.exit()
else:
	print("No range is given")

# instantiate the socket and connect to host
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((host_url, 80))

directory = get_directory(index_file)
# print("directory:", directory)

# add HEAD request here

# send an additional HEAD request to determine the buffer size for the object
head_request = "HEAD {} HTTP/1.1\r\nHost: {}\r\n\r\n".format(directory, host_url)

s.sendall(head_request.encode())

head_response = s.recv(16384).decode()

# check the status code
stat_code_phrase = get_status_code(head_response)

if stat_code_phrase != "200 OK":
	print("Error")
	print("Status line:", stat_code_phrase)
	print("Exiting!")
	sys.exit()


buffer_size = find_buffer_size(head_response)

# send GET request to retrieve the index file
request = "GET {} HTTP/1.1\r\nHost: {}\r\n\r\n".format(directory, host_url)

# print("request:", request)

s.sendall(request.encode())

response = recv_all(s, head_response).decode()
# response = s.recv(buffer_size).decode()

print("Index file is downloaded")

# print("Response")
# print(response)

# check the status code
stat_code_phrase = get_status_code(response)

if stat_code_phrase != "200 OK":
	print("Error")
	print("Status line:", stat_code_phrase)
	print("Exiting!")
	sys.exit()

response_lines = response.split("\r\n")

# print("Response lines")
# print(response_lines)

# get file URLs from the index file
file_urls = response_lines[-1].split("\n")
file_urls = [url for url in file_urls if len(url) != 0]

# print("File URLs")
# print(repr(file_urls))
print("There are {} files in the index".format(len(file_urls)))

# close the initial socket
s.shutdown(socket.SHUT_RDWR)
s.close()


for idx, url in enumerate(file_urls, 1):
	# create new socket for each URL in the index file
	file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host_url = url.split("/")[0]
	filename = url.split("/")[-1]

	file_socket.connect((host_url, 80))

	directory = get_directory(url)

	# send HEAD request to check the range constraints
	request = "HEAD {} HTTP/1.1\r\nHost: {}\r\n\r\n".format(directory, host_url)
	file_socket.sendall(request.encode())

	response = file_socket.recv(16384).decode()

	stat_code_phrase = get_status_code(response)


	# check the status code
	if stat_code_phrase != "200 OK":
		print("{}. {} is not found".format(idx, url))
		continue

	# determine the buffer size
	content_length = get_content_length(response)

	if range_exists:
		if content_length - 1 < ranges[LOWER_ENDPOINT]:
			print("{}. {} (size = {}) is not downloaded".format(idx, url, content_length))
			continue

		# as range exists, we send request with the Range field in the header
		request = "GET {} HTTP/1.1\r\nHost: {}\r\nRange: bytes={}-{}\r\n\r\n".format(directory, host_url, ranges[LOWER_ENDPOINT], ranges[UPPER_ENDPOINT])
		file_socket.sendall(request.encode())

		response = recv_all_range(file_socket, response, ranges[LOWER_ENDPOINT], ranges[UPPER_ENDPOINT]).decode()
		# response = file_socket.recv(buffer_size).decode()

		l_content_rng, u_content_rng = get_content_range(response)

		print("{}. {} (range = {}-{}) is downloaded".format(idx, url, l_content_rng, u_content_rng))

		# write the object to a file
		with open(filename, "w") as file:
			obj = get_object(response)
			file.write(obj)
	else:
		# as range does not exist, we send request without the Range field in the header
		request = "GET {} HTTP/1.1\r\nHost: {}\r\n\r\n".format(directory, host_url)
		file_socket.sendall(request.encode())

		response = recv_all(file_socket, response).decode()
		# response = file_socket.recv(buffer_size).decode()

		print("{}. {} (size = {}) is downloaded".format(idx, url, content_length))

		# write the object to a file
		with open(filename, "w") as file:
			obj = get_object(response)
			file.write(obj)

