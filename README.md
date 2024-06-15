# UART File Uploader

This Python application uploads a file to an embedded device over a UART 
interface, supporting chunked transfers, file system formatting, and free 
space querying.

It uploads a file using a logical serial protocol described in 
serialjson_protocol.md using commands described in **binary_file_upload_protocol.md** 
and **text_file_upload_protocol.md**. It supports both binary and text files, and 
allows specifying the transaction end  response key to be “end” or “done”.  

The destination device will store the file with a name which is derived from the 
source filename by taking all the characters up to the first ‘.’ Character, and 
then taking up to 4 characters from that because the destination file system 
differentiates files using a 32-bit number.  

## Features

- **Upload a file**: Supports uploading both binary and text files.
- **Format the flash file system**: Formats the device's flash file system before uploading if specified.
- **Query free space**: Retrieves and displays the free space on the device before and after uploading the file.
- **Verbose mode**: Provides detailed logging of the upload process.

## Usage

### Command-Line Arguments

- `filename`: The path to the file to upload.
- `serial_port`: The serial port to use for the connection (e.g., `/dev/ttyUSB0` or `COM3`).
- `-t, --text`: Indicates that the file is a text file.
- `-d, --done`: Uses "done" instead of "end" for the transaction end response key.
- `-v, --verbose`: Enables verbose output for detailed logging.
- `-f, --format`: Formats the flash file system before uploading the file.

## Code Overview

### `UARTUploader` Class

- **Initialization**: Sets up the UART connection parameters.
- **Connection Management**: Methods to open and close the UART connection.
- **File Operations**:
  - `open_destination_file()`: Sends the `fopen` command to the device to open the file for writing.
  - `write_chunk()`: Writes a chunk of the file to the device.
  - `close_file()`: Closes the file on the device.
- **Flash File System Operations**:
  - `ffs_format()`: Formats the flash file system on the device.
  - `get_free_space()`: Retrieves the free space on the device.
- **Response Handling**: 
  - `read_response()`: Reads and processes responses from the device.
  - `on_end_response()`: Handles the end response, printing error messages if needed.

### `main()` Function

1. **Argument Parsing**: Parses command-line arguments.
2. **Connection Setup**: Initializes and opens the UART connection.
3. **Flash File System Formatting** (if specified): Formats the flash file system on the device.
4. **Free Space Query**: Retrieves and prints the free space on the device before uploading.
5. **File Upload**: Uploads the specified file to the device.
6. **Post-Upload Free Space Query**: Retrieves and prints the free space on the device after uploading.
7. **Connection Cleanup**: Closes the UART connection.

## Example Workflow

1. **Start the application** with the necessary arguments.
2. **Initialize** the UART connection.
3. **(Optional) Format** the flash file system if the `-f` option is specified.
4. **Query and display free space** before the upload.
5. **Upload the file** in chunks, ensuring each chunk is acknowledged by the device.
6. **Query and display free space** after the upload.
7. **Close the UART connection** and exit.

This application ensures reliable file uploads to embedded devices over UART by handling chunked transfers, optional file system formatting, and free space management.
