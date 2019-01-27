#!/usr/bin/python
# -*- coding: utf-8 -*-

import ftplib
import os

ftp_url = os.environ['FTP_URL']
ftp_user = os.environ['FTP_USER']
ftp_password = os.environ['FTP_PASSWORD']
ftp_remote_dir = os.environ['FTP_REMOTE_DIR']
ftp_local_dir = os.environ['FTP_LOCAL_DIR']


def is_ftp_folder(ftp, filename):
    try:
        res = ftp.mlst(filename)
        if 'type=dir;' in res:
            return True
        else:
            return False
    except:
        return False


def download_repo(repoid):
    # Connecting to FTP
    try:
        ftp = ftplib.FTP_TLS(ftp_url)
        ftp.login(ftp_user, ftp_password)
        ftp.prot_p()
    except:
        print("Error connecting to FTP")
        exit(1)

    try:
        ftp.cwd(ftp_remote_dir)
    except:
        print("Error changing to directory {}".format(ftp_remote_dir))
        exit(1)

    files = ftp.nlst()
    file = str(repoid) + '.json'

    if not os.path.exists(ftp_local_dir):
        os.makedirs(ftp_local_dir)

    if file in files:
        ftp.retrbinary('RETR ' + file, open(ftp_local_dir + '/' + file, 'wb').write)


def remove_repo(repoid):
    # Connecting to FTP
    try:
        ftp = ftplib.FTP_TLS(ftp_url)
        ftp.login(ftp_user, ftp_password)
        ftp.prot_p()
    except:
        print("Error connecting to FTP")
        exit(1)

    try:
        ftp.cwd(ftp_remote_dir)
    except:
        print("Error changing to directory {}".format(ftp_remote_dir))
        exit(1)

    files = ftp.nlst()
    file = str(repoid) + '.json'

    if file in files:
        ftp.delete(file)

    if os.path.exists(ftp_local_dir + '/' + file):
        os.remove(ftp_local_dir + '/' + file)


def main():
    download_repo(1)
    remove_repo(1)


if __name__ == '__main__':
    main()
