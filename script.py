import ftplib as ftp
from configparser import ConfigParser
import shutil
import datetime

config_object = ConfigParser()
config_object.read("config.ini")
data_ftp = config_object["FTP"]
data_script = config_object["SCRIPT"]

host = data_ftp['host']
user = data_ftp['user']
password = data_ftp['password']
backup_to_keep = int(data_script['backuptokeep'])
backup_folder = data_script['backupfolder']
www_path = data_script['wwwpath']

class Connect :
    def __init__(self, host, user, password) :
        self.connect = ftp.FTP(host,user,password)

    def current(self) :
        return self.connect.pwd()

    def is_dir(self, name, orignal_dir) :
        try :
            self.connect.cwd(name)
            self.connect.cwd(orignal_dir)
            return True
        except :
            return False

    def ls(self, backup_folder) :
        self.connect.cwd(backup_folder)
        contents = self.connect.nlst()
        orignal_dir = self.current()
        files = []
        for content in contents :
            if not self.is_dir(content, orignal_dir) :
                files.append(content)
        self.connect.cwd('/')
        return files

    def mkdir(self, folder) :
        self.connect.mkd(folder)

    def sender(self, backup_folder, filename) :
        file = open(filename, 'rb')
        response = self.connect.storbinary(f'STOR {backup_folder}/{filename}', file)
        if  response == '226 Transfer complete.' :
            print('Archive backed up succefully !')
        else :
            log = open('log.txt', 'a+')
            log.write(response + '\n')
            log.close()
        file.close()

    def archiver(self, www_path, output_filename) :
        try :
            shutil.make_archive(output_filename, 'zip', www_path)
            return output_filename + '.zip'
        except Exception as e:
            print(e)
            log = open('log.txt', 'a+')
            log.write(f'Something went wrong while creating the archive : {e}\n')
            log.close()
            return 'error'

    def remove(self, backup_folder, file) :
        self.connect.delete(backup_folder + '/' + file)


def main() :
    connection = Connect(host, user,password)
    if not connection.is_dir(backup_folder, connection.current()) :
        print('Backup_folder not found on server, creating it ...')
        connection.mkdir(backup_folder)
    files = connection.ls(backup_folder)
    if len(files) == 0 :
        next_id = 0
    else :
        ids = []
        for file in files :
            ids.append(int(file.split('_')[1]))
        next_id = max(ids) + 1
    if len(files)>=backup_to_keep :
        connection.remove(backup_folder, files[ids.index(min(ids))])
    date = datetime.datetime.now().strftime('%x').replace('/', '-')
    name = f'backup_{next_id}_{date}'
    print(f'Archiving the folder as {name}.zip ...')
    archive = connection.archiver(www_path, name)
    if archive != 'error' :
        print('Sending archive to server ...')
        connection.sender(backup_folder, archive)

main()
