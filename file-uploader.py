import serial
import json
import sys
import os
import binascii
import argparse

class UARTUploader:
    def __init__(self, port, baudrate=115200, chunk_size=64, timeout=1, is_text=False, use_done_key=False, verbose=False):
        self.port = port
        self.baudrate = baudrate
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.is_text = is_text
        self.use_done_key = use_done_key
        self.verbose = verbose
        self.serial_connection = None
        self.file_handle = None

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

    def open_destination_file(self, filename, file_size):
        command = {"fopen": [filename, "w", file_size]}
        self.serial_connection.write((json.dumps(command) + '\r').encode())
        self.log_print(f"Sent fopen command for file {filename} with size {file_size}.")

        fopen_response = self.read_response()
        if fopen_response and "fopen" in fopen_response:
            self.file_handle = fopen_response["fopen"][0]
            self.log_print(f"Device opened file with handle {self.file_handle}.")
            end_response_key = "done" if self.use_done_key else "end"
            end_response = self.read_response(end_response_key=end_response_key)
            if end_response and end_response_key in end_response and end_response[end_response_key][0] == 0:
                self.log_print("File open transaction completed successfully.")
                return True
            else:
                print("Failed to complete file open transaction.")
                return False
        else:
            print("Failed to open file.")
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
        end_response_key = "done" if self.use_done_key else "end"
        if response and end_response_key in response and response[end_response_key][0] == 0:
            self.log_print("Chunk acknowledged by the server.")
            return True
        else:
            print("Chunk not acknowledged by the server.")
            return False

    def close_file(self):
        if self.file_handle is not None:
            command = {"fclose": [self.file_handle]}
            self.serial_connection.write((json.dumps(command) + '\r').encode())
            self.log_print(f"Sent fclose command for handle {self.file_handle}.")

            response = self.read_response()
            end_response_key = "done" if self.use_done_key else "end"
            if response and end_response_key in response and response[end_response_key][0] == 0:
                self.log_print("File closed successfully.")
                return True
            else:
                print("Failed to close file.")
                return False
        return True  # File was not opened

    def on_async_response(self, response):
        self.log_print(f"Received asynchronous response: {response}")
        return True

    def read_response(self, resp_timeout_sec=1, end_response_key="end"):
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

    def upload_file(self, file_path, filename):
        try:
            file_size = os.path.getsize(file_path)
            if not self.open_destination_file(filename, file_size):
                print("Failed to open destination file.")
                sys.exit(4)  # Exit code 4: Failed to open destination file

            with open(file_path, 'rb') as file:
                while chunk := file.read(self.chunk_size):
                    if not self.write_chunk(chunk):
                        print("Failed to send chunk. Aborting upload.")
                        sys.exit(5)  # Exit code 5: Failed to send chunk

            if not self.close_file():
                print("Failed to complete the transaction. Aborting upload.")
                sys.exit(6)  # Exit code 6: Failed to close file after upload
            else:
                self.log_print("File uploaded successfully.")
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
    parser.add_argument("-d", "--done", action="store_true", help="Use 'done' instead of 'end' for the transaction end response key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    file_path = args.filename
    port = args.serial_port
    is_text = args.text
    use_done_key = args.done
    verbose = args.verbose
    baudrate = 115200  # Default baudrate
    chunk_size = 64  # Default chunk size
    filename = os.path.basename(file_path)[:4]  # Use the first 4 characters of the file name as the device file name

    uploader = UARTUploader(port, baudrate, chunk_size, is_text=is_text, use_done_key=use_done_key, verbose=verbose)
    uploader.open_connection()
    uploader.upload_file(file_path, filename)
    uploader.close_connection()

if __name__ == "__main__":
    main()
