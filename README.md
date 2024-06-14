# UART File Uploader
## Overview
This Python application uploads a file to an embedded device over a UART interface
using a logical serial protocol described in serialjson_protocol.md using commands 
described in binary_file_upload_protocol.md and text_file_upload_protocol.md. It
 supports both binary and text files, and allows specifying the transaction end 
 response key to be “end” or “done”.  

The destination device will store the file with a name which is derived from the 
source filename by taking all the characters up to the first ‘.’ Character, and 
then taking up to 4 characters from that because the destination file system 
differentiates files using a 32-bit number.  

## Features
* Upload binary files to an embedded device.
* Upload text files to an embedded device.
* Choose between "end" or "done" as the transaction end response key. Default=”end”.

## Requirements
* Python 3.x
* pyserial library

## Installation
1. Install Python 3.x from python.org.
2. Install the pyserial library using pip:  

      `pip install pyserial`

## Usage
To run the application, use the following command:  
`python file-uploader.py <filename> <serial_port> [options]`

### Parameters
* `<filename>`: The path to the file you want to upload.
* `<serial_port>`: The serial port to use for the connection (e.g., **COM3** on
Windows or **/dev/ttyUSB0** on Linux).

### Options
* `-t, --text`: Indicates that the file is a text file. If this option is 
provided, the file will be uploaded without converting to hex.
* `-d, --done`: Use "done" instead of "end" for the transaction end response key.

### Examples
1. Upload a binary file:  
`python file-uploader.py file.bin COM3`  

2. Upload a text file:  
`python file-uploader.py file.txt COM3 -t`

3. Upload a binary file with "done" as the transaction end response key:  
`python file-uploader.py file.bin COM3 -d`

4. Upload a text file with "done" as the transaction end response key:  
`python file-uploader.py file.txt COM3 -t -d`

## Code Explanation
The application consists of a UARTUploader class and a main function.  
### UARTUploader Class
* **Initialization**:  
o Initializes the UART connection parameters, file upload settings, and 
transaction end response key.
* **open_connection**:  
o Opens the UART connection.
* **close_connection**:  
o Closes the UART connection.
* **open_destination_file**:  
o Sends a command to open a file on the device and waits for a response.
* **write_chunk**:  
o Sends a chunk of data to the device. If the file is text, it uses the fwrite 
command. Otherwise, it converts the chunk to hex and uses the fwritex command.
* **close_file**:  
o Sends a command to close the file on the device and waits for a response.
* **on_async_response**:  
o Handles asynchronous responses from the device.
* **read_response**:  
o Reads and parses responses from the device. Supports different transaction 
end response keys.
* **upload_file**:  
o Manages the file upload process, including opening the file, sending chunks, 
and closing the file.  

### Main Function
* Parses command-line arguments using argparse.
* Initializes a UARTUploader instance with the specified parameters.
* Opens the UART connection, uploads the file, and closes the connection.
## Error Handling
The application uses unique exit codes to identify the reason for termination:
* 1: Failed to open serial port
* 2: Non-compliant StreamJSON response
* 3: Invalid JSON response
* 4: Failed to open destination file
* 5: Failed to send chunk
* 6: Failed to close file after upload
* 7: File not found
* 8: General exception during file upload
* 9: Incorrect usage
## Conclusion
This application provides a robust solution for uploading files to an embedded 
device over UART, supporting both binary and text files, with configurable 
transaction end response keys. Use the command-line options to customize the 
upload process to your needs.

