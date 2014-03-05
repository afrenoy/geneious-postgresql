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

