""" Information extracted from the laconic geneious user manual and a lot of errors and trial
Proper initialization procedure is creating a database with one admin via command line, remotely connect to this database with geneious user admin account. Geneious will offer to initialize the database, accept.
At the stage, the database is setup but the permissions geneious assigns to tables are not ok for multi user, so we will add users ourselves using the following functions.
Each folder belongs to exactly one group (column g_group_id of table folder).
The table g_group is listing the existing groups with their ids and names.
Each belongs primarily to one group (column primary_group_id of table g_user). When a user creates a folder, by default it will 'belongs' to his primary group. However user can change this and assigns his folders to every group on which he has Admin right (right click, "Change Group of Folder").
Each user can have a role in an unlimited number of groups. The three roles are View (allowing read access to this group folder), Edit (allowing write access), and Admin (no idea what it is allowing more than Edit, maybe the ability to add/remove folders in this group ?)
The table g_user_group_role is storing the roles of users in group.
For geneious to be able to work with the database, each user should be granted SELECT, INSERT, UPDATE, and DELETE rights on all tables, except the g_user, g_folder, g_group for which he should be given only SELECT right otherwise he could alter the permissions and promote himself as admin of everything.
"""


""" Conventions and implementation decisions
# We will make all folder belonging to groups with an odd id readable by everybody (all existing users will have VIEW right in addition to permissions given to particular users of the folder's group)
# We will make all folder belonging to groups with an even id not readable by everybody
# For each user, we create one public group (odd id) named $username_public that will be his primary group, on which he will have Admin right
# and optionally one private group named $username_private, on which he will also have Admin right
# In addition, we can have 'collaboration' groups. The idea is to allow several users to have write access on the same folder. The convention stays the same: if id is odd, everybody has read access on the folders belonging to this group.
"""


import psycopg2
#conn = psycopg2.connect(database="test",user="afrenoy",password="afrenoy", port="1111", host="localhost")



#conn.close()

def createuser(conn,name,createprivategroup=True,password='ChangeMe'):
    """ Create a new user, give him appropriate rights on the database, and modify g_* table to allow him to perform operations from geneious
    1) The user is created in the SQL system with appropriate permissions on tables
    2) A primary group is created (in table g_group) for the user, named $username_public, with odd id.
    3) The new user is created in table g_user
    4) If requested by parameter createprivategroup, a private group is also created for this user, with even id.
    5) The new user is given Admin right (table g_user_group_role) on both these primary group.
    6) The new user is given View right on every existing group with an odd id (= public groups).
    7) Every already existing user is given View right on new user's primary (public) group.
    """
    
    cur = conn.cursor()
    # Enter the user in postgresql
    SQL=("CREATE ROLE " + name + " LOGIN PASSWORD %s")
    data=(password, )
    cur.execute(SQL,data)
    
    # Grant appropriate permissions, ie SELECT, INSERT, UPDATE, DELETE on all tables except g_group, g_role, g_user, g_user_group_role on which we only allow SELECT
    cur.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO "+name)
    cur.execute("REVOKE INSERT,UPDATE,DELETE ON TABLE g_group FROM "+name)
    cur.execute("REVOKE INSERT,UPDATE,DELETE ON TABLE g_user FROM "+name)
    cur.execute("REVOKE INSERT,UPDATE,DELETE ON TABLE g_role FROM "+name)
    cur.execute("REVOKE INSERT,UPDATE,DELETE ON TABLE g_user_group_role FROM "+name)
    
    # Find a free user id
    cur.execute("SELECT * FROM g_user")
    userlist=cur.fetchall()
    allusers_ids=[userlist[i][0] for i in range(0,len(userlist))]
    newuserid=min(set(range(1,1000))-set(allusers_ids))
    
    # Find a free group id as primary group for the user. Must be an odd number
    cur.execute("SELECT * FROM g_group")
    grouplist=cur.fetchall()
    allgroup_ids=[grouplist[i][0] for i in range(0,len(grouplist))]
    newgroupid=min(set(range(1,1000,2))-set(allgroup_ids))
    
    # Create this new group
    newgroupname=name+'_public'
    cur.execute("INSERT INTO g_group VALUES (%s, %s)",(newgroupid, newgroupname))
    
    # Add the user to the g_user table
    cur.execute("INSERT INTO g_user VALUES (%s, %s, %s)",(newuserid, newgroupid, name))
    
    # Create a private group for the user if asked. Id must be an even number
    if createprivategroup:
        newprivategroupid=min(set(range(2,1000,2))-set(allgroup_ids)-set([newgroupid]))
        newprivategroupname=name+'_private'
        cur.execute("INSERT INTO g_group VALUES (%s, %s)",(newprivategroupid, newprivategroupname))
        
    # Give new user Admin right on his public group
    cur.execute("INSERT INTO g_user_group_role VALUES (%s, %s, %s)",(newuserid,newgroupid,0))
    
    # Give new user Admin right on his private group
    if createprivategroup:
        cur.execute("INSERT INTO g_user_group_role VALUES (%s, %s, %s)",(newuserid,newprivategroupid,0))
        
    # Give new user View right on all other users public group
    for i in [x for x in allgroup_ids if x%2==1 and x>2]:
        # group id 1 is 'Everybody' and group id 2 is 'Hidden', defined and internally used by geneious
        cur.execute("INSERT INTO g_user_group_role VALUES (%s, %s, %s)",(newuserid,i,2))
        
    # Give all other users View right on new user public group
    for i in [x for x in allusers_ids if x>0]:
        # user id -1 is 'Global', defined and internally used by geneious
        cur.execute("INSERT INTO g_user_group_role VALUES (%s, %s, %s)",(i,newgroupid,2))
        
    # Check and write
    print 'Creating user ' + name + ' with id ' + str(newuserid) + ' primary group ' + newgroupname + ' with id ' + str(newgroupid)
    cur.execute("SELECT * FROM g_user")
    print 'New state of g_user: '
    print cur.fetchall()
    cur.execute("SELECT * FROM g_group")
    print 'New state of g_group: '
    print cur.fetchall()
    cur.execute("SELECT * FROM g_user_group_role")
    print 'New state of g_user_group_role: '
    print cur.fetchall()
    print 'Last chance to cancel ! '
    while True:
        answer=raw_input('Press (y) to confirm you want to write this to remote database, (n) to cancel ')
        if answer=='y':
            conn.commit()
            print 'New user added to database'
            break
        elif answer=='n':
            conn.rollback()
            print 'Canceled, new user has not been added'
            break
        else:
            print 'Sorry, I did not understand your answer'
    cur.close()

