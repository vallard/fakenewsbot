# spark_handler is the starting point of our application.  Pipeline calls this function and executes
# whenever your bot is called.  
def spark_handler(post_data, message):
    # get the room id: 
    room_id = post_data["data"]["roomId"]

    # Paste in your Umbrella Security Token here: 
    token = 'YOUR UMBRELLA SECURITY TOKEN'

    # Get the last value and see if its fake news. 
    spark.messages.create(roomId=room_id, text=check_fake_news(token, message.text.split(" ")[-1]))


# umbrella_get performs a get operation against the investigate API
# pass in the umbrella token and the path to the API you wish to call. 
# See the API documentation for examples of paths: 
# https://docs.umbrella.com/developer/investigate-api/
def umbrella_get(token, path):
    from urllib2 import Request, urlopen, HTTPError
    headers = {  'Authorization': 'Bearer ' + token }
    url = 'https://investigate.api.opendns.com' + path
    req = Request(url, headers=headers)
    try:
        fh = urlopen(req)
    except HTTPError, e:
        if e.code == 403:
            return False, "error authenticating with investigate API. Bot creater didn't enter token correctly?"
        elif e.code == 404:
            return False, url + " doesn't seem to exist."
    return True, json.loads(fh.read())


# get_domain_score
# https://docs.umbrella.com/developer/investigate-api/domain-scores-1/
def get_domain_score(token, domain):
    ok, response =  umbrella_get(token, "/domains/score/" + domain + "?showLabels")
    return ok, response


# get_domain_categories gets categorization of the domain. 
# https://docs.umbrella.com/developer/investigate-api/domain-status-and-categorization-1/
def get_domain_categories(token, domain):
    ok, response =  umbrella_get(token, "/domains/categorization/" + domain + "?showLabels")
    return ok, response

# get_domain_whois gets the whois information from investigate
# https://docs.umbrella.com/developer/investigate-api/whois-information-for-a-domain-1/    
def get_domain_whois(token, domain):
    ok, response =  umbrella_get(token, "/whois/" + domain)
    return ok, response
   
# get_domains_by_email gets emails from users given an email and token 
# https://docs.umbrella.com/developer/investigate-api/whois-information-for-a-domain-1/
def get_domains_by_email(token, email):
    ok, response =  umbrella_get(token, "/whois/emails/" + email)
    return ok, response

# below we gather scores by parsing the data from the investigate primatives. 
def score_from_categories(token, domain):
    ok, response = get_domain_categories(token, domain)
    if ok:
        categories =  response[domain]["security_categories"]
        for c in categories:
            print c
            if c == "Malware" or c == "Phishing" or c == "Botnet" or c == "Suspicious":
                return ok, 50        
        else:
            return ok, 0
    return ok, response

   
# check_number_of_emails calls get_domains_by_email then returns the count 
def score_from_emails(token, email):
    ok, r = get_domains_by_email(token, email)
    if ok:
        if len(r[email]["domains"]) == 1:
            return 30
        else:
            return 0
    else:
        return r
   
# check_fake_news takes API token and a website.  The algorithm is pretty
# crude and can be modified by you.  
def check_fake_news(token, domain):
    score = 0
    # Is the domain associated with a known security category (malware, phishing, botnet)? 
    # if yes, score=score+50 
    ok, s = score_from_categories(token, domain)
    if not ok:
        return cats
    score += s
    return score

    ok, s = score_from_domain_share(token, domain)
    if not ok:
        return s
    score += s
    

    ok, whois_info = get_domain_whois(token, domain)
    if not ok:
        return  whois_info
    emails = whois_info["emails"]
    max_emails = 0
    max_admin = ""
    for e in emails:
        e_count =  check_number_of_emails(token, e)
        if e_count > max_emails:
            max_emails = e_count
            max_admin = e
    created = whois_info["created"]
    from datetime import datetime
  
    created_date = datetime.now()
    if created != None:
        created_date = datetime.strptime(created, '%Y-%m-%d')
    present = datetime.now()
    time_delta = present - created_date
    msg = "domain %s was registered %d days ago.\n" % (domain, time_delta.days)
    msg2 = "domain %s has %d other domains registered by %s" % (domain, max_emails, max_admin)
    return msg + msg2

import sys 
import json
if len(sys.argv) > 1:
    print check_fake_news(token, sys.argv[1])
else:
    print "Please call this program with a domain"
