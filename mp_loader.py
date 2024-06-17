import os
import subprocess
import sys
import argparse
import shutil
from file_uploader import UARTUploader  # Ensure file_uploader.py is in PATH

def check_tool_exists(tool_name):
    return shutil.which(tool_name) is not None

def compile_script_to_mpy(script_path):
    if not check_tool_exists('mpy-cross'):
        print("Error: mpy-cross not found. Ensure it is installed and in PATH.")
        sys.exit(1)  # Exit code 1: Tool not found
    result = subprocess.run(['mpy-cross', script_path], capture_output=True)
    if result.returncode != 0:
        print(f"Compilation failed: {result.stderr.decode()}")
        sys.exit(2)  # Exit code 2: Compilation failed
    mpy_file = os.path.splitext(script_path)[0] + '.mpy'
    return mpy_file

def minify_script(script_path):
    if not check_tool_exists('pyminifier'):
        print("Warning: pyminifier not found. The script will be uploaded without "
              "minification and will take more flash space than necessary.")
        return script_path
    minified_script_path = os.path.splitext(script_path)[0] + '_minified.py'
    result = subprocess.run([sys.executable, '-m', 'pyminifier', '--remove-comments',
                             '--remove-docstrings', '--combine-imports', '--minify', 
                             script_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Minification failed: {result.stderr}")
        sys.exit(3)  # Exit code 3: Minification failed
    with open(minified_script_path, 'w') as minified_file:
        minified_file.write(result.stdout)
    return minified_script_path

def main():
    parser = argparse.ArgumentParser(description="Compile and upload a MicroPython "
                                                 "script to an embedded device over UART.")
    parser.add_argument("script", help="The Python script file to compile and upload")
    parser.add_argument("serial_port", help="The serial port to use for the connection")
    parser.add_argument("-t", "--text", action="store_true", help=argparse.SUPPRESS, 
                        default=False)
    parser.add_argument("-d", "--done", action="store_true", help="Use 'done' instead "
                                                                  "of 'end' for the "
                                                                  "transaction end "
                                                                  "response key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose "
                                                                     "output")
    parser.add_argument("-f", "--format", action="store_true", help="Format the flash "
                                                                    "file system before "
                                                                    "uploading")

    args = parser.parse_args()

    script_path = args.script
    port = args.serial_port
    is_text = args.text
    use_done_key = args.done
    verbose = args.verbose
    format_flash = args.format
    baudrate = 115200  # Default baudrate
    chunk_size = 64  # Default chunk size

    if is_text:
        processed_file = minify_script(script_path)
    else:
        processed_file = compile_script_to_mpy(script_path)

    filename = os.path.basename(processed_file)[:4]  # Use the first 4 characters of the 
                                                     # processed file name as the device 
                                                     # file name

    uploader = UARTUploader(port, baudrate, chunk_size, is_text=is_text, 
                            use_done_key=use_done_key, verbose=verbose)
    uploader.open_connection()

    if format_flash:
        if not uploader.ffs_format(timeout=10):
            sys.exit(9)  # Exit code 9: Failed to format flash file system

    free_space_before = uploader.get_free_space()
    if free_space_before is not None:
        print(f"Free space before upload: {free_space_before} bytes")

    uploader.upload_file(processed_file, filename)

    free_space_after = uploader.get_free_space()
    if free_space_after is not None:
        print(f"Free space after upload: {free_space_after} bytes")

    uploader.close_connection()

if __name__ == "__main__":
    main()
