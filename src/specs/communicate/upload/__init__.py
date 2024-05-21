import http, os, pathlib
from ...hardware import ensure_libs

DISK_LIMIT = 2**40


# Receive streaming uploads
@ensure_libs(["uploadserver","multipart"])
def receive_streaming_upload(handler):
    """
    https://github.com/NteRySin/streaminguploadserver
    """
    import uploadserver
    import multipart
    assert hasattr(uploadserver.args, "allow_replace") and type(uploadserver.args.allow_replace) is bool
    assert hasattr(uploadserver.args, "directory") and type(uploadserver.args.directory) is str

    # Extract Content-Length and boundary
    content_length = int(handler.headers.get("Content-Length", -1))
    content_type = handler.headers.get("Content-Type", "")
    (content_type, options) = multipart.parse_options_header(content_type)
    boundary = options.get("boundary", None)
    if not boundary:
        return (http.HTTPStatus.BAD_REQUEST, "No boundary configured")

    # Initialize multipart parser
    multipart_parser = multipart.MultipartParser(
        handler.rfile, boundary, content_length=content_length, disk_limit=DISK_LIMIT
    )

    # Persist uploaded files to disk
    files_uploaded = 0
    destination_directory_path = pathlib.Path(uploadserver.args.directory)
    for multipart_part in multipart_parser.get_all("files"):
        if multipart_part.file and multipart_part.filename:
            destination_path = destination_directory_path / pathlib.Path(multipart_part.filename).resolve().name
            if os.path.exists(destination_path):
                if os.path.isfile(destination_path):
                    if uploadserver.args.allow_replace:
                        handler.log_message(f"Overwriting '{destination_path}'")
                    else:
                        destination_path = uploadserver.auto_rename(destination_path)
                else:
                    return (http.HTTPStatus.BAD_REQUEST, "Path already existing")

            multipart_part.save_as(destination_path)
            multipart_part.close()
            files_uploaded += 1
            handler.log_message(f'Uploaded "{destination_path}"')

    if files_uploaded < 1:
        return (http.HTTPStatus.BAD_REQUEST, "No files selected")

    # Upload successful
    handler.log_message(f"Finished uploading {files_uploaded} file(s)")
    return (http.HTTPStatus.NO_CONTENT, None)




@ensure_libs(["uploadserver","multipart"])
def stream_files():
    """
    specs.communicate.main()
    specs.communicate.upload.main()
    """
    import uploadserver
    import sys
    from unittest.mock import patch

    uploadserver.receive_upload = receive_streaming_upload
    args_list = ['8000', '--cgi', '--allow-replace', '--bind', '0.0.0.0', '--directory', './', '--theme', 'dark']
    try: 
        with patch.object(sys, 'argv', ['__main__.py'] + args_list):
            uploadserver.main()
    except: 
        print ("run:","python3 -m uploadserver -h" )
    
    