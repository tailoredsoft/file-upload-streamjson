import serial
import json
import sys
import os
import binascii
import argparse

class UARTUploader:
    def __init__(self, port, baudrate=115200, chunk_size=64, timeout=1, is_text=False, use_done_key=False, verbose=False, add_null=False):
        self.port = port
        self.baudrate = baudrate
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.is_text = is_text
        self.add_null = add_null
        self.use_done_key = use_done_key
        self.verbose = verbose
        self.serial_connection = None
        self.file_handle = None
        self.end_response_key = "done" if use_done_key else "end"

    def log_print(self, message):
        if self.verbose:
            print(message)

    def open_connection(self):
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.log_print(f"Opened connection to {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            print(f"Failed to open serial port: {e}")
            sys.exit(1)  # Exit code 1: Failed to open serial port

    def close_connection(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.log_print("Closed serial connection.")

    def get_free_space(self):
        command = {"ffsfree": []}
        self.serial_connection.write((json.dumps(command) + '\r').encode())
        self.log_print("Sent ffsfree command to get free space.")

        response = self.read_response()
        if response and "ffsfree" in response:
            free_space = response["ffsfree"][0]
            self.log_print(f"Free space: {free_space} bytes")
        else:
            free_space = None

        end_response = self.read_response()
        if end_response and self.end_response_key in end_response:
            self.on_end_response(end_response)
        
        return free_space

    def open_destination_file(self, filename, file_size):
        command = {"fopen": [filename, "w", file_size]}
        self.serial_connection.write((json.dumps(command) + '\r').encode())
        self.log_print(f"Sent fopen command for file {filename} with size {file_size}.")

        response = self.read_response()

        if response:
            if self.end_response_key in response:
                status_code, description = response[self.end_response_key]
                if status_code != 0:
                    print(f"Failed to open destination file: {description}")
                return status_code == 0
            elif "fopen" in response:
                self.file_handle = response["fopen"][0]
                self.log_print(f"Device opened file with handle {self.file_handle}.")
                end_response = self.read_response()
                if end_response and self.end_response_key in end_response:
                    status_code, description = end_response[self.end_response_key]
                    if status_code != 0:
                        print(f"Failed to open destination file: {description}")
                    return status_code == 0
            else:
                print("Received unexpected response. Device is not StreamJSON compliant.")
                self.close_file()
                self.close_connection()
                sys.exit(2)  # Exit code 2: Non-compliant StreamJSON response

        return False

    def write_chunk(self, chunk):
        if self.is_text:
            command = {"fwrite": [self.file_handle, chunk.decode()]}
        else:
            hex_chunk = binascii.hexlify(chunk).decode()
            command = {"fwritex": [self.file_handle, hex_chunk]}
        self.serial_connection.write((json.dumps(command) + '\r').encode())
        self.log_print(f"Sent chunk of size {len(chunk)}.")

        response = self.read_response()
        if response and self.end_response_key in response and response[self.end_response_key][0] == 0:
            self.log_print("Chunk acknowledged by the server.")
            return True
        else:
            print("Chunk not acknowledged by the server.")
            return False

    def write_null(self):
        command = {"fwritex": [self.file_handle, "00"]}
        self.serial_connection.write((json.dumps(command) + '\r').encode())
        self.log_print("Sent null byte before closing the file.")

        response = self.read_response()
        if response and self.end_response_key in response and response[self.end_response_key][0] == 0:
            self.log_print("Null acknowledged by the server.")
            return True
        else:
            print("Null not acknowledged by the server.")
            return False

    def close_file(self):
        if self.file_handle is not None:
            command = {"fclose": [self.file_handle]}
            self.serial_connection.write((json.dumps(command) + '\r').encode())
            self.log_print(f"Sent fclose command for handle {self.file_handle}.")

            response = self.read_response()
            if response and self.end_response_key in response and response[self.end_response_key][0] == 0:
                self.log_print("File closed successfully.")
                return True
            else:
                print("Failed to close file.")
                return False
        return True  # File was not opened

    def on_async_response(self, response):
        self.log_print(f"Received asynchronous response: {response}")
        return True

    def on_end_response(self, response):
        if self.end_response_key in response:
            status_code, description = response[self.end_response_key]
            if status_code != 0:
                print(f"Error {status_code}: {description}")

    def read_response(self, resp_timeout_sec=1):
        self.serial_connection.timeout = resp_timeout_sec
        while True:
            response = self.read_single_response()
            if response:
                try:
                    response_json = json.loads(response.decode())
                    if len(response_json) != 1:
                        print("Device is not StreamJSON compliant: multiple keys in response.")
                        self.close_file()
                        self.close_connection()
                        sys.exit(2)  # Exit code 2: Non-compliant StreamJSON response
                    key = next(iter(response_json))
                    if key.startswith("+"):
                        if self.on_async_response(response_json):
                            continue
                    if key == self.end_response_key:
                        self.on_end_response(response_json)
                    return response_json
                except json.JSONDecodeError:
                    print("Received invalid JSON response.")
                    self.close_file()
                    self.close_connection()
                    sys.exit(3)  # Exit code 3: Invalid JSON response
            return None

    def read_single_response(self):
        line = bytearray()
        while True:
            byte = self.serial_connection.read(1)
            if not byte:
                break  # Timeout or end of data
            line.extend(byte)
            if byte == b'\r':
                break
        return line

    def ffs_format(self, timeout=10):
        command = {"format": ["ffs"]}
        self.serial_connection.write((json.dumps(command) + '\r').encode())
        self.log_print("Sent format command for flash file system.")
        
        response = self.read_response(resp_timeout_sec=timeout)
        if response and self.end_response_key in response:
            status_code, description = response[self.end_response_key]
            if status_code == 0:
                self.log_print("Flash file system formatted successfully.")
                return True
            else:
                print(f"Failed to format flash file system: {description}")
                return False
        else:
            print("No response received for flash file system format.")
            return False

    def upload_file(self, file_path, filename):
        try:
            file_size = os.path.getsize(file_path)

            if self.add_null and self.is_text:
                file_size = file_size+1

            if not self.open_destination_file(filename, file_size):
                sys.exit(4)  # Exit code 4: Failed to open destination file

            with open(file_path, 'rb') as file:
                while chunk := file.read(self.chunk_size):
                    if not self.write_chunk(chunk):
                        print("Failed to send chunk. Aborting upload.")
                        sys.exit(5)  # Exit code 5: Failed to send chunk

            if self.add_null and self.is_text:
                if not self.write_null():
                    print("Failed to send null. Aborting upload.")
                    sys.exit(5)  # Exit code 5: Failed to send null chunk

            if not self.close_file():
                print("Failed to complete the transaction. Aborting upload.")
                sys.exit(6)  # Exit code 6: Failed to close file after upload
            else:
                self.log_print("File uploaded successfully.")
                print(f"File '{file_path}' uploaded successfully with size {file_size} bytes.")
        except FileNotFoundError:
            print(f"File {file_path} not found.")
            sys.exit(7)  # Exit code 7: File not found
        except Exception as e:
            print(f"Error during file upload: {e}")
            sys.exit(8)  # Exit code 8: General exception during file upload

def main():
    parser = argparse.ArgumentParser(description="Upload a file to an embedded device over UART.")
    parser.add_argument("filename", help="The file to upload")
    parser.add_argument("serial_port", help="The serial port to use for the connection")
    parser.add_argument("-t", "--text", action="store_true", help="Indicate if the file is a text file")
    parser.add_argument("-n", "--null", action="store_true", help="Add a null terminate if a text file")
    parser.add_argument("-d", "--done", action="store_true", help="Use 'done' instead of 'end' for the transaction end response key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-f", "--format", action="store_true", help="Format the flash file system before uploading")

    args = parser.parse_args()

    file_path = args.filename
    port = args.serial_port
    is_text = args.text
    add_null = args.null
    use_done_key = args.done
    verbose = args.verbose
    format_flash = args.format
    baudrate = 115200  # Default baudrate
    chunk_size = 64  # Default chunk size
    filename = os.path.basename(file_path)[:4]  # Use the first 4 characters of the file name as the device file name

    uploader = UARTUploader(port, baudrate, chunk_size, is_text=is_text, use_done_key=use_done_key, verbose=verbose, add_null=add_null)
    uploader.open_connection()
    
    if format_flash:
        if not uploader.ffs_format(timeout=10):
            sys.exit(9)  # Exit code 9: Failed to format flash file system

    free_space_before = uploader.get_free_space()
    if free_space_before is not None:
        print(f"Free space before upload: {free_space_before} bytes")

    uploader.upload_file(file_path, filename)
    
    free_space_after = uploader.get_free_space()
    if free_space_after is not None:
        print(f"Free space after upload: {free_space_after} bytes")

    uploader.close_connection()

if __name__ == "__main__":
    main()
