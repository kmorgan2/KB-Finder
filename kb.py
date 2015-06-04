#import the necessary libraries
import sys
import requests
import http.cookiejar as cookielib
import getpass
import multiprocessing

#remember kids, global variables are bad! And you should not use them!
global s, jar

#define our worker function, which needs access to the session and cookiejar.
def worker(n):
  print("Processing KB", n)
  kb_url = 'http://intranet.restech.niu.edu/knowledge.php?action=view&id=' + str(n)
  if "Sorry, but this article could not be found." in str(s.get(kb_url, cookies=jar).text.encode('utf-8')):
    return False
  return True

#define the session and cookiejar for the worker process
def init_worker(session, cookiejar):
  global s, jar
  s = session
  jar = cookiejar
  print("Starting", multiprocessing.current_process().name)

def do_main():
  #create a cookie store
  jar = cookielib.CookieJar()
  login_url = "http://intranet.restech.niu.edu/login"

  #prompt for username and then password
  user = input('Enter your A-ID: ')
  passw = getpass.getpass('Enter your password: ')
  
  #create a persistent session
  s = requests.Session()
      
  #load the login page and then login with the userdata and cookejar
  r = s.get(login_url, cookies=jar)
  r = s.post(login_url, cookies=jar, data = {'username' : user, 'password' : passw})
  
  if r.history: #login worked
    #prompt for max KB, pass/fail vals, max processes #
    max_kb = int(input('Enter the Maximum KB number: '))
    passval = str(input('Enter the pass string [OK]: '))
    failval = str(input('Enter the fail string [NA]: '))
    passval = passval if passval else 'OK' #errorcheck
    failval = failval if failval else 'NA' #errorcheck
    prprcor = input('How many processes per cpu: ')
    prprcor = int(prprcor) if prprcor  else 0 #errorcheck

    #Let the user know we are about to start
    print("Gathering KB1-" + str(max_kb), "With OK=" + passval, "and NA=" + failval)
    
    #multiprocessing setup 
    pool_size = multiprocessing.cpu_count() * prprcor
    print("Detected", multiprocessing.cpu_count(), "logical cores. Creating ", pool_size, "worker processes.")
    
    #create pool
    pool = multiprocessing.Pool(processes=pool_size, initializer=init_worker, initargs=(s, jar, ))

    #create list of KB numbers
    pool_inputs = list(range(1, max_kb+1))
    
    #map KBs with pool workers
    pool_outputs = pool.map(worker, pool_inputs)
    
    #block until all processes finish, then block until all processes close
    pool.close()
    pool.join()
    
    #file output
    f = open('kbs.csv', 'w')
    f.write("KB#, STATUS\n")
    
    #for everything in the map, translate true-false to pass-fail vals
    for i, c in enumerate(pool_outputs):
      kb_url = 'http://intranet.restech.niu.edu/knowledge.php?action=view&id=' + str(i)
      if c:
        f.write(str(i + 1) + "," + passval + "\n" )
      else:
        f.write(str(i + 1) + "," + failval + "\n")
    f.close()
    
    #delete things for security (even though garbage collect should handle it)
    print ("\nSecurely deleting Intranet session")
    del(s)
    print ("Securely deleting login password in memory")
    del(passw)
    print("Done! See kb.csv for results.")
    
  else:#login failed
    print("Login Failed. Please try again.")
    del(s)
    del(passw)
    do_main()
    
if __name__ == '__main__':
  #Makes the EXE not lock up
  multiprocessing.freeze_support()

  do_main()
