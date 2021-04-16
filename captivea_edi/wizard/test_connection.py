from ftplib import FTP, FTP_TLS

# sftp = FTP_TLS('localhost')
sftp = FTP('localhost')
print(sftp)
res = sftp.connect('localhost', 21)
print("resssssssssss ",res)

r = sftp.login('konsultoo', 'kon123456')
print(r)
u = sftp.sendcmd('USER konsultoo') # '331 Please specify the password.'
print(u, type(u))
# if u == '331 Please specify the password.':
#     print("UUUUUUUUUU")
p = sftp.sendcmd('PASS kon123456')
print(p)
# if p == '230 Login successful.':
#     print("PPPPPPPPPPPPPPP ")