"""###################################################################################################
# Author: Zach Stine
# Created: 2016-04-16
# Last Modified: 2016-04-20
#
# Description: Mines the necessary data from Twitter in order to construct a social-affiliation 
# network based on 2016 U.S. presidential candidate supporters.
###################################################################################################"""

import tweepy
from tweepy import OAuthHandler
import time
import datetime
import pprint
import networkx as nx
import matplotlib.pyplot as plt


"""******************************************************
* Function: connect_to_api()
* Input: none
* Output: connection to Twitter API
******************************************************"""
def connect_to_api():
    # Fill in user-specific fields to connect to API
    consumer_key = ''
    consumer_secret = ''
    access_token = ''
    access_secret = ''
    
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    return tweepy.API(auth)
    
    
    
"""******************************************************
* Function: get_supporters()
* Input: list of candidate-specific hashtags and a limit
*    of how many users should be collected.
* Output: list of users who used any of these hashtags
* TO DO:
*   -Store user info in DB
******************************************************"""
def get_supporters(candidate_hshtgs, limit, api):
    print("get_supporters()")
    print("----------------")
    
    users = []
    
    # search for hashtags (either search for each, or both at same time)
    # for multi-hashtag queries, use something like query = build_query(candidate_hshtgs)
    #query = "%23" + candidate_hshtgs[0]
    query = build_query(candidate_hshtgs)
    
    # Iterate through all statuses returned by a search on query
    for status in limit_handled(tweepy.Cursor(api.search, q=query).items()):
        user_info = status.user
        if user_info.screen_name in users:
            continue
        else:
            users.append(user_info.screen_name)
            
        #print("\n")
        #print("User info:")
        #print("user id: " + str(user_info.id))
        #print("user name: " + user_info.screen_name)
        #print("followers: " + str(user_info.followers_count))
        #print("following: " + str(user_info.friends_count)) # count of how many people user is following

        if len(users) >= limit:
            break
        
        #################################################
        # add user info to DB (skip for proof-of-concept) *************************[INCOMPLETE]
        #################################################

    print("Number of users collected: " + str(len(users)))
    print("end get_supporters()\n\n")
    return users



"""******************************************************
* Function: build_query()
* Input: List of hashtags (all for one candidate).
* Output: Query string to search for hashtags. If
*    multiple hashtags are given, they are combined with
*    logical OR.
******************************************************"""
def build_query(hashtag_list):
    query = ''
    
    # Iterate through all but last hashtag in list, combining with logical OR.
    for h in hashtag_list[:-1]:
        query += '%23' + h + '%20OR%20'
    # Last hashtag in list (or only hashtag given)
    query += '%23' + hashtag_list[-1]
    return query
            
        

"""******************************************************
* Function: get_statuses()
* Input: -list of users supporting a candidate
*        -number of hashtags to get for each user (can be duplicate).
*        -max limit of tweets to search before giving up on user.
* Output: list that represents hashtag usage of each 
*    candidate supporter.
******************************************************"""
def get_statuses(user_list, num_hshtgs, status_limit, api):
    print("get_statuses()")
    print("--------------")

    # Variable to be returned. List of tuples wherein each tuple is of the form (user, {'hshtg1': count, 'hshtg2': count})
    hshtg_usage = []

    # Total number of tweets mined (Not being used at the moment)
    total_statuses = 0
    # Total number of tweets with hashtags (Not being used at the moment)
    total_hash_statuses = 0
    
    for user in user_list:
        
        # Dictionary of form {'hshtg_text': count}.
        hshtg_dict = {}

        # Total number of tweets mined for user
        user_total_statuses = 0
        # Total number of tweets with hashtags mined for users
        user_total_hash_statuses = 0

        # Iterate through statuses of current user, noting any hashtags used.
        for status in limit_handled(tweepy.Cursor(api.user_timeline, screen_name=user).items(status_limit)):
            total_statuses += 1
            user_total_statuses += 1
            
            # Get all hashtags used in status
            hshtg_list = status.entities['hashtags']
            hshtg_count = len(hshtg_list)
            
            # Update counts for each hashtag or add if new.
            if hshtg_count > 0:
                total_hash_statuses += 1
                user_total_hash_statuses += 1
                
                for hshtg in hshtg_list:
                    hshtg_text = hshtg['text']
                    if hshtg_text in hshtg_dict:
                        hshtg_dict[hshtg_text] += 1
                    else:
                        hshtg_dict[hshtg_text] = 1

            # Status information:
            status_id = status.id
            status_text = status.text
            time_created = status.created_at
            geo = status.geo
            coordinates = status.coordinates
            #print("Status Information:")
            #print("-------------------")
            #print("Status ID: " + str(status_id))
            #print("Text:")
            #print("  -" + status_text)
            #print("Hashtag count: " + str(hshtg_count))
            #print("Time created: " + str(time_created))
            #print("Geo: " + str(geo) + " | Coordinates: " + str(coordinates))
            #print("------------------\n\n")

            ###################################################
            # add status info to DB (skip for proof-of-concept) *************************[INCOMPLETE]
            ###################################################
            
            if len(hshtg_dict) >= num_hshtgs or user_total_statuses >= status_limit:
                break

        # Create user tuple and append to hshtg_usage[]
        user_tuple = (user, hshtg_dict)
        hshtg_usage.append(user_tuple)

    print("end get_statuses()\n")
    return hshtg_usage


    
"""******************************************************
* Function: create_network() [not currently used in main()]
* Input: list of users' hashtag usage as well as either
*    the candidate or candidate hashtags.
* Output: A new graph specific to this candidate.
******************************************************"""
def create_network(hshtg_usage, candidate):
    G = nx.DiGraph()

    #G.add_node(label, node_type, hashtag_type)
    # Two node types: user, hashtag, candidate
    # Hashtag types: none (for users), candidate, affiliations
    G.add_node(candidate, node_type='candidate', latitude=44)

    for user, hash_dict in hshtg_usage:
        
        # Create user node
        G.add_node(user, node_type='user', candidate=candidate, latitude=34)
        
        # Connect candidate node to user node
        G.add_edge(candidate, user)
        
        # Create node for hashtag if it doesn't already exist
        for hshtg in hash_dict:
            count = hash_dict[hshtg]
            hash_label = '#' + hshtg
            
            # Note: duplicate nodes cannot be added, so no problem if hshtg already exists in graph
            G.add_node(hash_label, node_type='hashtag', latitude=20)
            G.add_edge(user, hshtg, weight=count)
        
    return G



"""******************************************************
* Function: append_to_graph()
* Input: -Graph to append results to
         -Candidate that network portion is for
         -Hashtag usage by supporters
* Output: Graph now contains nodes for this candidate
* Note: -Original graph will be affected so long as the supplied
*   graph argument is never reassigned (due to how Python
*   passes values).
*       -Latitude values are given for Gephi layout purposes. Might need to be DOUBLE TYPE.
******************************************************"""
def append_to_graph(G, hshtg_usage, candidate):
    
    # Add candidate node (mostly for visual purposes) -94.58<--92.43->-90.18
    G.add_node(candidate, node_type='candidate')

    for user, hash_dict in hshtg_usage:
        user_label = '@' + user
        
        # Create user node
        G.add_node(user_label, node_type='user', candidate=candidate)
        
        # Connect candidate node to user node
        G.add_edge(candidate, user_label)
        
        # Create node for hashtag if it doesn't already exist
        for hshtg in hash_dict:
            count = hash_dict[hshtg]
            hash_label = '#' + hshtg
            
            # Note: duplicate nodes cannot be added, so no problem if hshtg already exists in graph
            G.add_node(hash_label, node_type='hashtag')
            G.add_edge(user_label, hash_label, weight=count)

def geo_format(G):
    center = -92.5
    
    candidate_lat = 44.0
    candidate_spacing = 5.0
    
    user_lat = 34.0
    user_spacing = 2
    
    hash_lat = 20.0
    hash_spacing = 2
    

    candidate_count = 0
    user_count = 0
    hash_count = 0

    for label, data in G.nodes(data=True):
        if data['node_type'] == 'candidate':
            candidate_count += 1
        elif data['node_type'] == 'user':
            user_count += 1
        elif data['node_type'] == 'hashtag':
            hash_count += 1
        else:
            print("Error in geo_format(G): encountered node with unrecognized node type.")
    
    candidate_offset = get_offset(candidate_count, candidate_spacing)
    user_offset = get_offset(user_count, user_spacing)
    hash_offset = get_offset(hash_count, hash_spacing)
    # Might not need the range, but just the leftmost (or rightmost) starting point ***
    #candidate_lon_range = get_lon_range(center, candidate_offset)
    candidate_lon = center - candidate_offset
    #user_lon_range = get_lon_range(center, user_offset)
    user_lon = center - user_offset
    #hash_lon_range = get_lon_range(center, hash_offset)
    hash_lon = center - hash_offset

    for label, data in G.nodes(data=True):
        if data['node_type'] == 'candidate':
            data['latitude'] = candidate_lat
            data['longitude'] = candidate_lon
            candidate_lon += candidate_spacing
        elif data['node_type'] == 'user':
            candidate_label = data['candidate']
            data['latitude'] = user_lat
            data['longitude'] = user_lon
            user_lon += user_spacing
            data['candidate'] = candidate_label
        elif data['node_type'] == 'hashtag':
            data['latitude'] = hash_lat
            data['longitude'] = hash_lon
            hash_lon += hash_spacing
        else:
            print("Unrecognized node type while assigning coordinates in geo_format(G).")
    
def get_offset(count, spacing):
    return (count / 2) * spacing

def get_lon_range(center, offset):
    return [(center - offset), (center + offset)]


"""******************************************************
* Function: draw_graph()
* Input: Graph to be visualized.
* Output: Displays graph.
******************************************************"""
def draw_graph(G):
    d = nx.degree(G)
    nx.draw_spectral(G, nodelist=d.keys(), node_size=[v * 100 for v in d.values()])
    plt.show()

"""******************************************************
* Function: count_unique_hashtags()
* Input: Hashtag usage dictionary.
* Output: Count of how many unique hashtags were present
*    in input.
******************************************************"""
def count_unique_hashtags(hash_usage):
    count = 0
    unique = []
    for user, hashtags in hash_usage:
        for h in hashtags:
            if h not in unique:
                unique.append(h)
                count += 1
    

"""******************************************************
* Function: limit_handled()
* Input: cursor
* Output: causes the program to sleep if rate limit is hit
* http://tweepy.readthedocs.org/en/v3.5.0/code_snippet.html#handling-the-rate-limit-using-cursors
******************************************************"""
def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print("\nRateLimitError... sleeping...\n")
            time.sleep(15 * 60)
        except tweepy.TweepError as e:
            if e.message.split()[-1] == '429':
                print("\nTweepError 429... sleeping...\n")
                time.sleep(15 * 60)
            else:
                print(e.message)

                
"""******************************************************
* Function: print_hshtg_usage()
* Input: hshtg_usage list
* Output: print of each user and their hashtag usage
******************************************************"""
def print_hshtg_usage(hshtg_usage):
    for user_usage in hshtg_usage:
        user, hash_dict = user_usage
        print("User: " + user)
        print("Hashtags Used:")
        for hshtg in hash_dict:
            hash_count = hash_dict[hshtg]
            print("  #" + hshtg + " :: " + str(hash_count))

def write_to_graphml(G):
    path = "republican_test2" + ".graphml"
    nx.write_graphml(G, path, encoding='utf-8', prettyprint=True)

            

def main():
    """********************************
    * Single candidate implementation *
    ********************************"""
    '''
    # Sample hashtag list for Donald Trump
    candidate_hshtgs = ["Trump2016"]
    
    # Connect to Twitter API
    api = connect_to_api()
    
    # Get list of unique users that have used any of the candidate_hshtgs. Number of users returned is defined by unique_users.
    unique_users = 2000#5000 #consider increasing as much as possible: perhaps 15k?
    user_list = get_single_candidate_supporters(candidate_hshtgs, unique_users, api)
    
    # Get statuses for each user. Returns list of tuples of the form: 
    # [(user1, {"hshtg1": count, "hshtg2": count}), (user2, {"hshtg3": count}), ... , (userN, {"hshtg123": count, "hshtg1": count})]
    hshtgs_per_user = 1000#5000
    status_limit = 2500#5000 #consider increasing as much as possible
    hshtg_usage = get_statuses(user_list, hshtgs_per_user, status_limit, api)
    #print_hshtg_usage(hshtg_usage)

    # Create graph
    #test_hshtgs = [("user1", {"hash1": 1, "hash2": 2}), ("user2", {"hash2": 3, "hash3": 1, "hash4": 5}), ("user3", {"hash3": 4, "hash5": 5})]
    candidate = "Trump"
    graph = create_network(hshtg_usage, candidate)
    draw_graph(graph)

    # Export Graph to graphML
    write_to_graphml(graph)
    '''


    ##############################################################################################################################################

    """**********************************
    * Multiple candidate implementation *
    **********************************"""

    api = connect_to_api()
    
    # These contain all relevant candidate hashtags
    trump_tags = ['Trump2016', 'Trump', 'TrumpTrain']
    cruz_tags = ['Cruz2016', 'Cruz', 'CruzCrew']
    kasich_tags = ['Kasich2016', 'Kasich4Us']
    bernie_tags = ['Bernie2016', 'FeelTheBern', 'Bernie', 'WeAreBernie', 'Sanders2016']
    clinton_tags = ['Hillary2016', 'ImWithHer']
    
    # These contain only the standard Candidate2016 hashtags
    trump_t = ['Trump2016']
    cruz_t = ['Cruz2016']
    kasich_t = ['Kasich2016']
    bernie_t = ['Bernie2016']
    clinton_t = ['Hillary2016']
    
    # User either set of tags above for candidates_and_hashtags dictionary
    """candidates_and_hashtags = {'Trump': trump_t,
                               'Cruz': cruz_t,
                               'Kasich': kasich_t,
                               'Sanders': bernie_t,
                               'Clinton': clinton_t}"""
    candidates_and_hashtags = {'Trump': trump_t,
                               'Cruz': cruz_t,
                               'Kasich': kasich_t}
    
    unique_users = 50 # increase as much as possible
    hshtgs_per_user = 1 #1000
    status_limit = 80 #5000
    num_candidates = len(candidates_and_hashtags)

    # Create graph, iterate through each candidate, and add their results to the graph
    graph = nx.DiGraph()
    
    for candidate in candidates_and_hashtags:
        print("Collecting data for candidate: " + candidate)
        print("--------------------------------------------\n")
        hashtags = candidates_and_hashtags[candidate]
        
        # Get list of candidate's supporters (needs to be improved with sentiment analysis)
        supporters = get_supporters(hashtags, unique_users, api)
        
        # Get statuses from supporters, of the form:
        # [(user1, {"hshtg1": count, "hshtg2": count}), (user2, {"hshtg3": count}), ... , (userN, {"hshtg123": count, "hshtg1": count})]
        hashtag_usage = get_statuses(supporters, hshtgs_per_user, status_limit, api)
        
        # append results to graph
        append_to_graph(graph, hashtag_usage, candidate)

        print(candidate + " is finished.\n\n\n")

    # Format geo coordinates of nodes
    geo_format(graph)
    # Export Graph to graphML
    write_to_graphml(graph)

                              

if __name__ == "__main__":
    main()
