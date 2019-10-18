from ftplib import *
import os, io
from app import app

# If FTP configuration exists in config, use FTP server instead of local disk

def save_file(filename, binary):
    if os.environ.get("FTP_URL") != None:
        ftps = FTP_TLS(host=os.environ.get("FTP_URL"), user=os.environ.get("FTP_USER"), passwd=os.environ.get("FTP_PASSWORD"))
        ftps.storbinary("STOR " + filename, binary)
        ftps.quit()
    else:
        open(os.path.join(app.config["UPLOAD_DIRECTORY"], filename), "wb").write(binary.read())

def get_file(filename):
    if os.environ.get("FTP_URL") != None:
        ftps = FTP_TLS(host=os.environ.get("FTP_URL"), user=os.environ.get("FTP_USER"), passwd=os.environ.get("FTP_PASSWORD"))
        ftps = FTP_TLS(host=os.environ.get("FTP_URL"), user=os.environ.get("FTP_USER"), passwd=os.environ.get("FTP_PASSWORD"))
        file_binary = io.BytesIO()
        ftps.retrbinary("RETR %s" % filename, file_binary.write)
        ftps.quit()
        file_binary.seek(0)
        return file_binary
    else:
        return io.BytesIO(io.open(os.path.join(app.config["UPLOAD_DIRECTORY"], filename), "rb").read())
def get_file_size(filename):
    if os.environ.get("FTP_URL") != None:
        ftps = FTP_TLS(host=os.environ.get("FTP_URL"), user=os.environ.get("FTP_USER"), passwd=os.environ.get("FTP_PASSWORD"))
        ftps = FTP_TLS(host=os.environ.get("FTP_URL"), user=os.environ.get("FTP_USER"), passwd=os.environ.get("FTP_PASSWORD"))
        size = ftps.size(filename)
        ftps.quit()
        return size
    else:
        return os.stat(os.path.join(app.config["UPLOAD_DIRECTORY"], filename)).st_size

def delete_file(filename):
    if os.environ.get("FTP_URL") != None:
        ftps = FTP_TLS(host=os.environ.get("FTP_URL"), user=os.environ.get("FTP_USER"), passwd=os.environ.get("FTP_PASSWORD"))
        ftps = FTP_TLS(host=os.environ.get("FTP_URL"), user=os.environ.get("FTP_USER"), passwd=os.environ.get("FTP_PASSWORD"))
        ftps.delete(filename)
        ftps.quit()
    else:
        os.remove(os.path.join(app.config["UPLOAD_DIRECTORY"], filename))
