import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

#Firebase database 인증 및 앱 초기화
cred = credentials.Certificate('mykey.json')
firebase_admin.initialize_app(cred,{
    'databaseURL' : 'https://mango-project-e71fa-default-rtdb.firebaseio.com/' 
})


ref = db.reference('email_ref')
a=ref.get()
print(type(a)) #json형태로 받아와 진다.
print(a)
print(a["anafVevjAbaoEw7CA53N5zMKDC83"])
print(a["anafVevjAbaoEw7CA53N5zMKDC83"]["-Nd-_wHurgRcX_9-IxSh"])
print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
print(len(a))

for k in a.keys():
    print(k)
    print(a[k])
    b=a[k]
    for kk in b.keys():
        print(b[kk])

