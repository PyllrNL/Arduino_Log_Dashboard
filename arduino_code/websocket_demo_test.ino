#include <MsgPack.h>
#include <ArduinoHttpClient.h>

#define DEBUGGING 1
#include "arduino_secrets.h"
#include <WebSocketClient.h>
#include <b64.h>
#include <WiFiNINA_Generic.h>
// Here we define a maximum framelength to 64 bytes. Default is 256.
#define MAX_FRAME_LENGTH 64

// Define how many callback functions you have. Default is 1.
#define CALLBACK_FUNCTIONS 1

#define MAX_BUFFER_SIZE 128
#define MAX_BYTE_BUFFER ((MAX_BUFFER_SIZE / 6) * 8) - 3

///////please enter your sensitive data in the Secret tab/arduino_secrets.h
/////// Wifi Settings ///////
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
char path[] = "/device/03pwbIIosvgLQhC_USUHmN6Iz-86xyY_X7noo-jksMc";
char host[] = "167.71.68.242";

WiFiClient client;
WebSocketClient webSocketClient = WebSocketClient(client, host, (uint16_t)80);

int status = WL_IDLE_STATUS;

void setup() {
  Serial.begin(9600);
  
  while (!Serial);
  while ( status != WL_CONNECTED) {
    Serial.print("Attempting to connect to Network named: ");
    Serial.println(ssid);     // print the network name (SSID);

    // Connect to WPA/WPA2 network:
    status = WiFi.begin(ssid, pass);
    delay(5000);
  }

  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
  
  webSocketClient.begin(path);

  int messagesize = webSocketClient.parseMessage();
  if(messagesize > 0) {
    Serial.println(webSocketClient.readString());
  }
}

bool Write_Message(WebSocketClient client, float *voltage, float *current, uint8_t samples) {
  MsgPack::arr_t<float> v;
  MsgPack::arr_t<float> c;

  for(int i=0; i<samples; i++) {
    v.push_back(voltage[i]);
    c.push_back(current[i]);
  }

  MsgPack::fix_arr_t<MsgPack::arr_t<float>, 2> m {v, c};
  MsgPack::Packer packer;

  packer.serialize(m);

  char message[MAX_BUFFER_SIZE];

  unsigned int length = packer.size();
  unsigned int index = 0;
  const uint8_t *data = packer.data();
  unsigned int encoded_length;
  while ( length > MAX_BYTE_BUFFER ) {
    encoded_length = b64_encode(data + index, MAX_BYTE_BUFFER, (unsigned char*)message, MAX_BUFFER_SIZE);
    message[encoded_length] = '\0';
    client.beginMessage(TYPE_TEXT);
    unsigned int send_length = encoded_length+1;
    do {
      int write_len = client.write((uint8_t *)message, encoded_length+1);
      send_length = send_length - write_len;
    } while(send_length > 0);
    client.endMessage();
    length = length - MAX_BYTE_BUFFER;
    index = index + MAX_BYTE_BUFFER;
  }
  if (length > 0) {
    encoded_length = b64_encode(data + index, length, (unsigned char *)message, MAX_BUFFER_SIZE);
    message[encoded_length] = '\0';
    client.beginMessage(TYPE_TEXT);
    unsigned int send_length = encoded_length+1;
    do {
      int write_len = client.write((uint8_t *)message, encoded_length+1);
      send_length = send_length - write_len;
    } while(send_length > 0);
    client.endMessage();
  }

  return true;
}

float v[101] = {
  10.0, -20.0, 30.0, -39.0, 49.0, -59.0, 69.0, -79.0,
  88.0, -98.0, 108.0, -117.0, 126.0, -135.0, 144.0, -153.0,
  162.0, -171.0, 179.0, -187.0, 195.0, -203.0, 211.0, -218.0,
  225.0, -232.0, 239.0, -246.0, 252.0, -258.0, 264.0, -270.0,
  275.0, -280.0, 285.0, -289.0, 294.0, -297.0, 301.0, -304.0,
  308.0, -310.0, 313.0, -315.0, 317.0, -318.0, 320.0, -321.0,
  321.0, -321.0, 321.0, -321.0, 321.0, -320.0, 318.0, -317.0,
  315.0, -313.0, 310.0, -308.0, 304.0, -301.0, 297.0, -294.0,
  289.0, -285.0, 280.0, -275.0, 270.0, -264.0, 258.0, -252.0,
  246.0, -239.0, 232.0, -225.0, 218.0, -211.0, 203.0, -195.0,
  187.0, -179.0, 171.0, -162.0, 153.0, -144.0, 135.0, -126.0,
  117.0, -108.0, 98.0, -88.0, 79.0, -69.0, 59.0, -49.0, 39.0,
  -30.0, 20.0, -10.0, 0.0
};
    
float c[101] = {
  0, 0.9980655971335943, 0, 0.9922698723632764, 0, 0.982635248222263,
  0, 0.969198999199666, 0, 0.9520131075327285, 0, 0.931144062097659,
  0, 0.9066726011770702, 0, 0.8786934000992674, 0, 0.8473147049577776,
  0, 0.812657913828248, 0, 0.7748571071028802, 0, 0.7340585287594519,
  0, 0.6904200205717402, 0, 0.6441104114503822, 0, 0.5953088642766521,
  0, 0.5442041827560153, 0, 0.4909940809733123, 0, 0.4358844184753636,
  0, 0.37908840384036124, 0, 0.32082576981535194, 0, 0.26132192321284753,
  0, 0.20080707285569419, 0, 0.13951533894391552, 0, 0.07768384728898747,
  0, 0.015551811920320853, 0, -0.04664039038743034, 0, -0.10865215008549843,
  0, -0.17024355572243333, 0, -0.2311763221149872, 0, -0.29121471222728007,
  0, -0.350126449191402, 0, -0.40768361494171007, 0, -0.46366353198535787,
  0, -0.5178496248983402, 0, -0.5700322582138061, 0, -0.620009547460784,
  0, -0.6675881402161703, 0, -0.7125839641475306, 0, -0.7548229391532678,
  0, -0.7941416508447703, 0, -0.8303879827648034, 0, -0.8634217048966745,
  0, -0.8931150161868064, 0, -0.9193530389822537, 0, -0.9420342634700077,
  0, -0.9610709403987272, 0, -0.9763894205636116, 0, -0.9879304397407617,
  0, -0.9956493479690226, 0, -0.9995162822919897, 0
};

int i = 0;

void loop() {
    
    Write_Message(webSocketClient, v, c, 101);
    Serial.print("Written message: ");
    Serial.println(i);
    i++;
    delay(1000);

}
