import hashlib, os, tempfile, time, requests, re, socket
from collections import OrderedDict

socket.setdefaulttimeout(None);

#
#
#   SMS Gateway (BULK) (Version 3) integration with SMSLink.ro 
#   
#     using SMS Gateway (BULK) Version 3 Endpoint (New)
#
#     Supports HTTP and HTTPS protocols
#     (New) Supports concatenated SMS (longer than 160 characters)
#     (New) Supports all Romanian networks
#     (New) Supports all international networks
#     (New) Supports international phone numbers formatting
#     (New) Returns the remote Bulk Package ID
#
#   System Requirements:
#
#      Python 3 with the following packages: 
#
#          hashlib
#          OrderedDict from collections
#          os
#          requests
#          re
#          socket
#          tempfile
#          time  
#
#   Usage:
#
#     See Usage Examples for the SMSLinkSMSGatewayBulkPackage() class starting on line 346
#
#     Get your SMSLink / SMS Gateway Connection ID and Password from
#         https://www.smslink.ro/get-api-key/
#
#   @version    1.0
#   @updated    2022-06-13
#   @see        https://www.smslink.ro/sms-gateway-documentatie-sms-gateway.html
#
# 

class SMSLinkSMSGatewayHelpers :
  @staticmethod
  def default_key(d):
    result = 0
    for key, _ in d.items():          
      if(type(key) is int and key >= result) :                
        result = key + 1
    return result
        
class SMSLinkSMSGatewayBulkPackage :
  
    connection_id      = None;
    password           = None;
    doHTTPS            = True;
    testMode           = False;
    endpointHTTP       = "http://www.smslink.ro/sms/gateway/communicate/bulk-v3.php";
    endpointHTTPS      = "https://secure.smslink.ro/sms/gateway/communicate/bulk-v3.php";
    temporaryDirectory = "/tmp";
    remotePackageID    = 0;
    remoteMessageIDs   = OrderedDict([]);
    errorMessage       = "";
    packageContents    = OrderedDict([]);
    packageStatus      = 0;
    packageFile        = OrderedDict([("contentPlain",""),("contentCompressed","")]);
    packageValidation  = OrderedDict([("hashMD5",OrderedDict([("contentPlain",""),("contentCompressed","")]))]);
    clientVersion      = "1.0";
    compressionMethods = OrderedDict(
      [
        (0,OrderedDict([("CompressionID",0),("Compression","No Compression")])),
        (1,OrderedDict([("CompressionID",1),("Compression","Compression using Zlib Gzip")])),
        (2,OrderedDict([("CompressionID",2),("Compression","Compression using bzip2")])),
        (3,OrderedDict([("CompressionID",3),("Compression","Compression using LZF")]))
      ]
    );
  
    compressionMethod = 0;
  
    #
    #   Initialize SMSLink - SMS Gateway
    #
    #   Initializing SMS Gateway will require the parameters connection_id and password. connection_id and password can be generated at
    #   https://www.smslink.ro/sms/gateway/setup.php after authenticated with your account credentials.
    #
    #   @param string    connection_id     SMSLink - SMS Gateway - Connection ID
    #   @param string    password          SMSLink - SMS Gateway - Password
    #   @param bool      testMode          SMSLink - SMS Gateway - Test Mode (true or false)
    #
    #   @return void
    #         
    def __init__(this,connection_id, password, testMode = False) :
      if (not (connection_id == None)) :
        this.connection_id = connection_id;
      
      if (not (password == None)) :
        this.password = password;
      
      if (testMode == True or testMode == False) :
        this.testMode = testMode;
      
      if ((this.connection_id == None) or (this.password == None)) :
        exit("SMS Gateway initialization failed, credentials not provided. Please see documentation.");
      
    def __destruct(this) :
      this.connection_id = None;
      this.password = None;
      this.doHTTPS = True;
    
    #
    #   Sets the compression method to be used during sending
    #
    #   @param int    compressionMethod    the following values are accepted:
    #   
    #                                          0 for No Compression (default)
    #                                          1 for gzip   (not yet implemented in Python, use no compression)
    #                                          2 for bzip2  (not yet implemented in Python, use no compression)
    #                                          3 for LZF    (not yet implemented in Python, use no compression)
    #
    #   @return bool     true if method was set or false otherwise
    #         
    def setCompression(this,compressionMethod) :
      if (this.packageStatus == 0) :
        if ((compressionMethod in this.compressionMethods)) :
          this.compressionMethod = compressionMethod;            
        return True;        
      return False;
    
    def applyCompression(this,contentPlain) :
      contentCompressed = "";

      # no compression    
      if (this.compressionMethod == 0) :
        contentCompressed = contentPlain;
      # gzip (not yet implemented in Python, use no compression)      
      elif (this.compressionMethod == 1) :
        contentCompressed = contentPlain; 
      # bzip2 (not yet implemented in Python, use no compression)      
      elif (this.compressionMethod == 2) :
        contentCompressed = contentPlain;
      # LZF (not yet implemented in Python, use no compression)      
      elif (this.compressionMethod == 3) :
        contentCompressed = contentPlain;
      return contentCompressed;
    
    #
    #   Sets the protocol that will be used by SMS Gateway (HTTPS or HTTP).
    #
    #   @param string    protocolName     HTTPS or HTTP
    #
    #   @return bool     true if method was set or false otherwise
    #         
    def setProtocol(this,protocolName = "HTTPS") :
      protocolName = protocolName.upper();
      if (protocolName == "HTTPS") :
          this.doHTTPS = True;
      elif (protocolName == "HTTP") :
          this.doHTTPS = False;
      else : 
          return False;
      
      return True;
    
    #
    #   Returns the protocol that is used by SMS Gateway (HTTPS or HTTP)
    #
    #   @return string     HTTP or HTTPS possible values
    #         
    def getProtocol(this) :
      return "HTTPS" if this.doHTTPS else "HTTP";
    
    def structureCharactersEncode(this,messageText) :
      messageText = messageText.replace("\n", "%0A");
      messageText = messageText.replace(";", "%3B");
      return messageText;
  
    def cleanCharacters(this,messageText) :
      messageText = messageText.replace("\t", "");
      # Tab
      messageText = messageText.replace("\r", "");
      # Carriage Return
      return messageText;
    
    #
    #   Inserts a SMS to SMS Bulk Package
    #
    #   @param int       localMessageId           Local Message ID from Your System
    #   
    #   @param string    receiverNumber           Receiver mobile phone number. Phone numbers should be formatted as a Romanian national mobile phone number (07xyzzzzzz)
    #                                              or as an International mobile phone number (00 + Country Code + Phone Number, example 0044zzzzzzzzz).
    #
    #   @param string    senderId                 (Optional) Sender alphanumeric string:
    #
    #                                                 numeric    - sending will be done with a shortcode (ex. 18xy, 17xy)
    #                                                 SMSLink.ro - sending will be done with SMSLink.ro (use this for tests only)
    #
    #                                                 Any other preapproved alphanumeric sender assigned to your account:
    #
    #                                                     Your alphanumeric sender list:        
    # 															http://www.smslink.ro/sms/sender-list.php
    #
    #                                                     Your alphanumeric sender application: 
    # 															http://www.smslink.ro/sms/sender-id.php
    #
    #                                                 Please Note:
    #
    #                                                 SMSLink.ro sender should be used only for testing and is not recommended to be used in production. Instead, you
    #                                                 should use numeric sender or your alphanumeric sender, if you have an alphanumeric sender activated with us.
    #
    #                                                 If you set an alphanumeric sender for a mobile number that is in a network where the alphanumeric sender has not
    #                                                 been activated, the system will override that setting with numeric sender.
    #
    #   @param string    messageText              Message of the SMS, up to 160 alphanumeric characters, or longer than 160 characters.
    #
    #   @param int       timestampProgrammed    (Optional) Should be 0 (zero) for immediate sending or other UNIX timestamp in the future for future sending
    #
    #   @return bool     true on success or false on failure     
    #         
    def insertMessage(this,localMessageId, receiverNumber, senderId, messageText, timestampProgrammed = 0) :
      if (str(localMessageId).isnumeric() == False):
        return False;

      # Converts + to 00
      receiverNumber = receiverNumber.replace("+", "00");

      # Remove all non-numeric characters
      receiverNumber = re.sub("[^0-9]", "", receiverNumber);
            
      if (str(receiverNumber).isnumeric() == False):
        return False;
    
      messageText = messageText.strip();
      # Strip whitespace from the beginning and end of the message
      messageText = messageText.replace("\r\n", "\n");
      # Converts Carriage Return + Line Feed to Line Feed
      messageText = this.structureCharactersEncode(messageText);
      # Encode structure characters
      messageText = this.cleanCharacters(messageText);
      # Clean unsuported characters
      this.packageContents[SMSLinkSMSGatewayHelpers.default_key(this.packageContents)] = OrderedDict(
        [
          ("localMessageId",localMessageId),
          ("receiverNumber",receiverNumber),
          ("senderId",senderId),
          ("messageText",messageText),
          ("timestampProgrammed",timestampProgrammed)
        ]
      );
      
      return True;
    
    #
    #   Removes a SMS from SMS Bulk Package
    #
    #   @param int       localMessageId           Local Message ID from Your System
    #   
    #   @return void     
    #         
    def removeMessage(this,localMessageId) :
      for messageKey,messageData in this.packageContents.items() :
        if (messageData["localMessageId"] == localMessageId) :
          del this.packageContents[messageKey];
            
    #
    #   Returns the Size of the SMS Bulk Package
    #   
    #   @return int
    #         
    def packageSize(this) :
      return len(this.packageContents);
    
    #
    #   Sends the SMS Bulk Package to SMSLink
    #
    #   @return bool     true on success or false on failure
    #         
    def sendPackage(this) :
      this.remoteMessageIDs = OrderedDict([]);
      this.errorMessage = "";
      if (this.packageStatus == 0 and this.packageSize() > 0) :
        temporaryFileContent = [];        
        for messageKey, messageData in this.packageContents.items():
          temporaryFileContent.append(";".join(map(str, messageData.values())));  

        this.packageFile["contentPlain"] = '\r\n'.join(map(str, temporaryFileContent));        
        
        this.packageValidation["hashMD5"]["contentPlain"] = hashlib.md5(this.packageFile["contentPlain"].encode('utf-8')).hexdigest();
        
        this.packageFile["contentCompressed"] = this.applyCompression(this.packageFile["contentPlain"]);
        this.packageValidation["hashMD5"]["contentCompressed"] = hashlib.md5(this.packageFile["contentCompressed"].encode('utf-8')).hexdigest();

        try:
          temporaryFile = tempfile.NamedTemporaryFile(mode="w", delete=False);
          
          temporaryFilename = temporaryFile.name;              
          temporaryFile.write(this.packageFile["contentCompressed"]);
          temporaryFile.close();
          
          requestData = OrderedDict(
            [("connection_id",this.connection_id),
             ("password",this.password),
             ("test", 1 if this.testMode == True else 0),
             ("Compression",this.compressionMethod),
             ("MD5Plain",this.packageValidation["hashMD5"]["contentPlain"]),
             ("MD5Compressed",this.packageValidation["hashMD5"]["contentCompressed"]),
             ("SizePlain",len(this.packageFile["contentPlain"])),
             ("SizeCompressed",len(this.packageFile["contentCompressed"])),
             ("Timestamp",int(time.time())),
             ("Buffering",1),
             ("Version",this.clientVersion),
             ("Receivers",this.packageSize())
            ]
          );

          requestFiles = {'Package':open(temporaryFilename, "rb")}
          
          requestHeaders = {}
          requestParams = {"timestamp":str(int(time.time()))}

          try:              
            requestResponse = requests.post(this.endpointHTTPS if this.doHTTPS else this.endpointHTTP, headers=requestHeaders, params=requestParams, data=requestData, files=requestFiles);                                      
            if (requestResponse.status_code >= 200 and requestResponse.status_code <= 299) :
              requestResponse = requestResponse.text.split(";");
              if (len(requestResponse) >= 3) :
                if (requestResponse[0] == "MESSAGE") :
                  this.remotePackageID = requestResponse[3];
                  messagesAssoc = requestResponse[4].split(",");
                  
                  i = 0;
                  while ( i < len(messagesAssoc) ) :
                    temporaryMessageData = messagesAssoc[i].split(":");
                    this.remoteMessageIDs[temporaryMessageData[0]] = OrderedDict([
                      ("localMessageId",temporaryMessageData[0]),
                      ("remoteMessageId",temporaryMessageData[1]),
                      ("messageStatus",temporaryMessageData[2])
                    ]);
                    i+=1;
                  
                  this.packageStatus = 1;
                    
                  return True;
                else : 
                  this.errorMessage = ";".join(requestResponse);                          
              else : 
                this.errorMessage = "ERROR;0;Unexpected response format";                      
            else : 
              this.errorMessage = "ERROR;0;Unexpected HTTP code " + str(requestResponse.status_code);              
          except requests.exceptions.RequestException as connectionError:
            this.errorMessage = "ERROR;0;" + str(connectionError);
        finally:  
          os.unlink(temporaryFilename);
                  
      return False;    

#
#
#
#     Usage Examples for the SMSLinkSMSGatewayBulkPackage() class
#
#
#

#
#
#
#     Initialize SMS Gateway Bulk Package
#
#       Get your SMSLink / SMS Gateway Connection ID and Password from
#       https://www.smslink.ro/get-api-key/
#
#
#
# 

BulkSMSPackage =  SMSLinkSMSGatewayBulkPackage("MyConnectionID", "MyConnectionPassword");
 
#
# 
#    Insert Messages to SMS Package
#    
# 

BulkSMSPackage.insertMessage(1, "07xyzzzzzz", "numeric", "Test SMS 1");
BulkSMSPackage.insertMessage(2, "+407xyzzzzzz", "numeric", "Test SMS 2");
BulkSMSPackage.insertMessage(3, "00407xyzzzzzz", "numeric", "Test SMS 3");

#
# 
#    Send SMS Package to SMSLink
#    
# 

BulkSMSPackage.sendPackage();
#
# 
#    Process Result
#    
# 

print("Remote Package ID: " + str(BulkSMSPackage.remotePackageID) + "<br />");

statusCounters = OrderedDict([]);

statusCounters["successCounter"]           = 0;
statusCounters["failedSenderCounter"]      = 0;
statusCounters["failedNumberCounter"]      = 0;
statusCounters["failedInternalCounter"]    = 0;
statusCounters["failedInsufficientCredit"] = 0;
statusCounters["totalCounter"]             = 0;

if (len(BulkSMSPackage.remoteMessageIDs) > 0) :
  for key,value in BulkSMSPackage.remoteMessageIDs.items() :
    
    if (value["messageStatus"] == "1") :
      
      timestamp_send = -1;
      
      # 
      #                
      #                    .. do something .. 
      #                    for example check the sender because is incorrect
      #
                  
      print("Error for Local Message ID: " + str(value["localMessageId"]) + " (Sender Failed).<br />");
      statusCounters["failedSenderCounter"]+=1;
      
    elif (value["messageStatus"] == "2") :
      timestamp_send = -2;
      
      # 
      #                
      #                    .. do something .. 
      #                    for example check the number because is incorrect    
      #
                  
      print("Error for Local Message ID: " + str(value["localMessageId"]) + " (Incorrect Number).<br />");
      statusCounters["failedNumberCounter"]+=1;
      
    elif (value["messageStatus"] == "3") :
      
      timestamp_send = int(time.time());
      # 
      #                
      #                    .. do something .. 
      #
      #                    Save in database the Remote Message ID, sent in variabile: value["RemoteMessageID"].
      #                    Delivery  reports will  identify  your SMS  using our Message ID. Data type  for the 
      #                    variabile should be considered to be hundred milions (example: 220000000)                    
      #
                  
      print("Succes for Local Message ID: " + str(value["localMessageId"]) + ", Remote Message ID: " + str(value["remoteMessageId"]) + "<br />");
      statusCounters["successCounter"]+=1;
      
    elif (value["messageStatus"] == "4") :
      timestamp_send = -4;
      
      # 
      #                
      #                    .. do something .. 
      #                    for example try again later
      #
      #                    Internal Error may occur in the following circumstances:
      #
      #                    (1) Number is Blacklisted (please check the Blacklist associated to your account), or
      #                    (2) An error occured at SMSLink (our technical support team is automatically notified)
      #
                  
      print("Error for Local Message ID: " + str(value["localMessageId"]) + " (Internal Error or Number Blacklisted).<br />");
      statusCounters["failedInternalCounter"]+=1;
      
    elif (value["messageStatus"] == "5") :
      
      timestamp_send = -5;
      
      # 
      #                
      #                    .. do something .. 
      #                    for example top-up the account
      #
                  
      print("Error for Local Message ID: " + str(value["localMessageId"]) + " (Insufficient Credit).<br />");
      statusCounters["failedInsufficientCredit"]+=1;
    
    statusCounters["totalCounter"]+=1;
      
else : 
  
  print("Error Transmitting Package to SMSLink: " + str(BulkSMSPackage.errorMessage) + "<br />");
  