import sys
#import rosbag
import json
#from bson import json_util
#from rospy_message_converter import message_converter
from datetime import datetime
#import pyprog
import argparse
#import sensor_msgs.point_cloud2 as pc2
#import numpy as np
#import uuid
from decimal import Decimal
#from google.protobuf.json_format import MessageToJson
# import datetime
# import time
from databaseinterface import DatabaseInterface#DatabaseDynamo, DatabaseMongo
import logging



def ProcessRosbagFile(file, dbobject, channelList, metadata, force):
    from RosReader import RosReader
    rr = RosReader()
    return rr.ProcessFile(dbobject=dbobject, metadatasource=metadata,
                          channelList=channelList, 
                          force=force, process_lidar=False)


def ProcessCyberFile(cyberfolder, cyberfilebase, dbobject, channelList, metadata, force):
    from CyberReader import CyberReader
    cr = CyberReader(cyberfolder, cyberfilebase)
    #check that deny/allow are present and set defaults
    if(channelList != None):
        if('deny' in channelList and channelList['deny'] != None):
            deny = channelList['deny']
        else:
            deny = None
        if('allow' in channelList and channelList['allow'] != None):
            allow = channelList['allow']
        else:
            allow = None
        channelList = {
                    'deny': deny,
                    'allow': allow
                    }  
    cr.InsertDataFromFolder(dbobject, metadata, channelList)   
    return 0

def checkKey(dict, key):
    if(key in dict):
        return True
    return False
    
def main(args):
    try:
        with open(args.config, 'r') as file:
            config = json.load(file)
        if(not checkKey(config, 'file')):
            logging.error("file is required")
        if(not checkKey(config['file'], 'type')):
            logging.error("file - type is required")
        if(not checkKey(config, 'metadata')):
            logging.error("metadata section is required")
        if(not checkKey(config, 'database')):
            logging.error("database section is required")
        if(not checkKey(config['database'], 'type')):
            logging.error("database - type is required")
        if(not checkKey(config['database'], 'databasename')):
            logging.error("database - databasename is required")
        if(not checkKey(config['database'], 'uri')):
            logging.error("database - uri is required")
        if(not checkKey(config['database'], 'collection')):
            logging.error("database - collection is required")
    except:
        logging.error(f"failed to load config from file {args.config}")
        return -1

    
    if (config['database']['type'] == 'mongo'):
        logging.info(f"Connecting to database at {config['database']['uri']} / {config['database']['collection']}")
        #dbobject = DatabaseMongo(args.mongodb)
        #dbobject.check()
    elif (config['database']['type'] ==  'dynamo'):
        logging.info(f"Connecting to database at {config['database']['uri']} / {config['database']['collection']}")
        #dbobject = DatabaseDynamo(args.dynamodb)
        #dbobject.check()    
    else:
        logging.error(f"No database specified: {config['database']['type']}")
        sys.exit()
    
    dbobject = DatabaseInterface.CreateDatabaseInterface(config['database']['type'], 
                                                         config['database']['uri'], 
                                                         config['database']['databasename'])

    dbobject.setCollectionName(config['database']['collection'])
    dbobject.db_connect()  
    
    json_channels = None
    if('channelList' in config):
        json_channels = config['channelList']
    
    if(config['file']['type'] == 'cyber'):
        logging.info('Processing Cyber data')
        ProcessCyberFile(cyberfolder=config['file']['folder'],cyberfilebase=config['file']['filebase'], 
                         dbobject=dbobject,
                         channelList=json_channels,
                         metadata=config['metadata'], force=args.force)
    elif(config['file']['type'] == 'rosbag'):
        logging.info("Loading rosbag")
        ProcessRosbagFile(file=config['file']['filename'],
                          dbobject=dbobject, 
                          channeList=json_channels, 
                          metadata=config['metadata'], force=args.force)  
    else:
        logging.error(f"No data file source specified: {config['file']['type']}")
        sys.exit()

    logging.info("All done")
      
if __name__ == '__main__':
    logging.basicConfig(filename="insert.log", encoding='utf-8', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    logging.info("datainsert start")
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help='JSON formatted settings file', required=True)
    # parser.add_argument('--dynamodb', help='dynamo url string', required=False)
    # parser.add_argument('--mongodb', help='mongodb url string', required=False)
    # parser.add_argument('--cyberfolder', help='cyber data folder', required=False)
    # parser.add_argument('--cyberfilebase', help='cyber file name w/o extension', required=False)
    # parser.add_argument('--rosbag', help='rosbag file', required=False)
    # parser.add_argument('--metadatafile', help='json metadata file',required=True)
    #parser.add_argument('-v', '--vehicleid', type=int, help='vehicle ID', required=True)
    #parser.add_argument('-e', '--experimentid', type=int, help='experiment ID', required=True)
    #parser.add_argument('--collection', default='rosbag', help='Collection Name', required=False)
    # parser.add_argument('--dbname', help='name of database',required=True)
    parser.add_argument('--lidar', default='', dest='lidar', action='store_true', help='Insert LiDAR', required=False)
    parser.add_argument('--force', default=False, dest='force', action='store_true', help='force insert')
    # parser.add_argument('--channellist', default=None, help='json file with accecpt/deny list of channels')
    try:
        args = parser.parse_args()
    except:
        logging.error("argument parsing failed")
        sys.exit(-1)
    
    main(args)