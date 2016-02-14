# SMLlogger
## read SML-data (OBIS) from Zweirichtungszähler eHZ-IW8E2Axxx

based on 
- http://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/edl21-ehz
- http://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/emh-ehz-h1
- http://volkszaehler.org/pipermail/volkszaehler-users/2012-September/000451.html
- http://wiki.volkszaehler.org/software/sml
- http://www.mscons.net/obis_kennzahlen.pdf
- https://www.mikrocontroller.net/attachment/89888/Q3Dx_D0_Spezifikation_v11.pdf
- https://eclipse.org/paho/clients/python/ 

requirements:
```
    sudo apt-get install python-dev python-pip python-serial python3-serial 
    sudo pip install RPi.GPIO
    sudo pip install paho-mqtt
```
Data is read via USB using a [http://wiki.volkszaehler.org/hardware/controllers/ir-schreib-lesekopf](http://wiki.volkszaehler.org/hardware/controllers/ir-schreib-lesekopf)

For details, please see: [volkszaehler.org](http://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/emh-ehz-h1)

Length of stream in my case is 792 chars

    1b1b1b1b
    01010101
    76
      07000b06d8119a
      6200
      6200
      72
      	630101
      	76
      	  01
      	  01
      	  07000b025c05de
      	  0b0901454d4800004735c7
      	  01
      	  01
      	  63a74e
     00
     76
       07000b06d8119b
       6200
       6200
       72
         630701
         77
           01
           0b0901454d4800004735c7 				serverID
           070100620affff               		<<--??????
           72
             6201
             65025cd8f87a
           77
             078181c78203ff   					objName 129-129:199.130.3*255 	Herstelleridentifikation
             01
             01
             01
             01          
             04454d48 							value
             01
           77
             070100000009ff 					objName 1-0:0.0.9*255 	Geräteidentifikation
             01
             01
             01
             01
             0b0901454d4800004735c7 			serverID
             01
           77
             070100010800ff 				 	objName 1-0:1.8.0*255 	Wirkarbeit Bezug total
             64010182 							status = unsigned 16
             01
             621e 								unit (unsigned8) 1E = Wh
             52ff 								scaler (int8) -1 = *10^-1 = /10
             56000308cff7 						value (kWh)
             01
           77
         070100020800ff  					objName 1-0:2.8.0*255 	
         64010182 							status = unsigned 16
         01
         621e 								unit (unsigned8) 1E = Wh
         52ff 								scaler (int8) -1 = *10^-1 = /10
         5600015fc145 						value (kWh)
         01
       77
         070100010801ff  					objName 1-0:1.8.1*255 	Wirkarbeit Bezug Tarif 1
         01
         01
         621e 								unit (unsigned8) 1E = Wh
         52ff 								scaler (int8) -1 = *10^-1 = /10
         56000308cff7 						value (kWh)
         01
       77
         070100020801ff 					objName 1-0:2.8.1*255 	
         01
         01
         621e 								unit (unsigned8) 1E = Wh
         52ff 								scaler (int8) -1 = *10^-1 = /10
         5600015fc145 						value (kWh)
         01
       77
         070100010802ff 					objName 1-0:1.8.2*255 	
         01
         01
         621e 								unit (unsigned8) 1E = Wh
         52ff 								scaler (int8) -1 = *10^-1 = /10
         560000000000 						value 0
         01
       77 
         070100020802ff 					objName 1-0:2.8.2*255 	
         01
         01
         621e 								unit (unsigned8) 1E = Wh
         52ff 								scaler (int8) -1 = *10^-1 = /10
         560000000000 						value 0
         01
       77
         070100100700ff 					objName 1-0:16.7.0*255
         01
         01
         621b 								unit (unsigned8) 1b = W
         52ff 								scaler (int8) -1 = *10^-1 = /10
         5500000b94 						value (W)
         01
       77
         078181c78205ff 					objName 129-129:199.130.5*255	Public Key des Zählers
         01
         72620165025cd8f8 					value ?
         01
         01
         8302841ead39cbefc83a615721f4639f94b453d6793c0f28883a1a2291deb9b7905b9af9e8bcc3955444cdb68d7078d1351b
         01
       01
     01      
       6323d4
     00
     76
       07000b06d8119e
       6200
       6200
       72
         630201
         71 
           01
       635271
     00
     00
     1b1b1b1b
     1a01684c 

