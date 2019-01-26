#!/usr/bin/python
# -*- coding: utf-8 -*-

import ftplib

ip = 'ec2-3-89-106-94.compute-1.amazonaws.com'
user = 'raq'
passwd = 'ekagJu9cgg46ukFMPdzVfPq6wfvpKBSCLY7G2SnU'
ftp_dir = '/ftp'
ftp_repo_dir = ftp_dir + '/raq/results'
local_dir = 'tmp/raq'


def is_ftp_folder(ftp, filename):
    try:
        res = ftp.mlst(filename)
        if 'type=dir;' in res:
            return True
        else:
            return False
    except:
        return False


def download_repo():
    # Connecting to FTP
    try:
        ftp = ftplib.FTP_TLS(ip)
        ftp.login(user, passwd)
        ftp.prot_p()
    except:
        print("Error connecting to FTP")
        exit(1)

    try:
        ftp.cwd(ftp_repo_dir)
    except:
        print("Error changing to directory {}".format(ftp_dir))
        exit(1)

    files = ftp.nlst()

    for file in files:
        print("Downloading {} ...".format(ftp_dir + '/' + file))
        ftp.retrbinary("RETR " + file, open(local_dir + '/' + file, 'wb').write)


def main():
    download_repo(154891766)


if __name__ == '__main__':
    main()
